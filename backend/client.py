"""In-process stdio MCP client for official Roblox Studio MCP.

One background asyncio loop owns the session. Tool calls arrive on many
threads (FastMCP), so work is submitted with run_coroutine_threadsafe.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
from contextlib import AsyncExitStack
from typing import Any, Awaitable, Callable

from .constants import CALL_TIMEOUT_S, CONNECT_TIMEOUT_S, LIST_ROBLOX_STUDIOS
from . import runtime

log = logging.getLogger("uefn.plugin.roblox-mcp.client")


class RobloxMcpError(RuntimeError):
    """Readable failure talking to Studio MCP."""


def describe_error(exc: BaseException) -> str:
    nested = getattr(exc, "exceptions", None)
    if nested:
        return "; ".join(describe_error(sub) for sub in nested)
    text = str(exc).strip()
    return f"{type(exc).__name__}: {text}" if text else type(exc).__name__


def flatten_content(content: Any) -> str:
    parts: list[str] = []
    for block in content or []:
        text = getattr(block, "text", None)
        if isinstance(text, str):
            parts.append(text)
            continue
        kind = str(getattr(block, "type", "") or type(block).__name__)
        parts.append(f"[{kind}]")
    return "\n".join(parts)


def extract_images(content: Any) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for block in content or []:
        data = getattr(block, "data", None)
        mime = getattr(block, "mimeType", None) or getattr(block, "mime_type", None)
        if isinstance(data, str) and data and mime:
            out.append({"mimeType": str(mime), "data": data})
    return out


def parse_studios(payload: Any) -> list[dict[str, Any]]:
    """Normalize list_roblox_studios output into {studio_id, name, place_id}."""
    if isinstance(payload, str):
        text = payload.strip()
        if not text:
            return []
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return []
    rows: Any = payload
    if isinstance(payload, dict):
        for key in ("studios", "data", "result", "items", "instances"):
            if isinstance(payload.get(key), list):
                rows = payload[key]
                break
        else:
            if payload.get("studio_id") or payload.get("studioId") or payload.get("id"):
                rows = [payload]
            else:
                rows = []
    if not isinstance(rows, list):
        return []
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        sid = str(
            row.get("studio_id")
            or row.get("studioId")
            or row.get("id")
            or row.get("instance_id")
            or ""
        ).strip()
        if not sid:
            continue
        place = row.get("place_id") or row.get("placeId") or row.get("placeID")
        out.append(
            {
                "studio_id": sid,
                "name": str(row.get("name") or row.get("place_name") or row.get("displayName") or sid),
                "place_id": place,
            }
        )
    return out


def inject_studio_id(
    tool: str,
    arguments: dict[str, Any],
    studios: list[dict[str, Any]],
    cached: str | None,
) -> tuple[dict[str, Any], str | None]:
    """Add studio_id when the agent omitted it. list_roblox_studios is left alone."""
    args = dict(arguments)
    if tool == LIST_ROBLOX_STUDIOS:
        return args, None
    existing = str(args.get("studio_id") or args.get("studioId") or "").strip()
    if existing:
        return args, None
    ids = [str(s.get("studio_id") or "") for s in studios if s.get("studio_id")]
    if cached and cached in ids:
        args["studio_id"] = cached
        return args, None
    if len(ids) == 1:
        args["studio_id"] = ids[0]
        return args, None
    if not ids:
        return args, (
            "No open Studio place. Open a place in Roblox Studio, enable "
            "Assistant → Manage MCP Servers → Enable Studio as MCP server, "
            "then call roblox_status."
        )
    names = ", ".join(f"{s.get('name')} ({s.get('studio_id')})" for s in studios)
    return args, (
        f"Multiple Studio instances are open. Pass studio_id on roblox_call. "
        f"Studios: {names}"
    )


_LOCK = threading.Lock()
_STATE: dict[str, Any] = {
    "phase": "idle",
    "error": "",
    "detail": "",
    "path": "",
}
_LOOP: asyncio.AbstractEventLoop | None = None
_THREAD: threading.Thread | None = None
_STACK: AsyncExitStack | None = None
_SESSION: Any = None
_CACHED_STUDIO_ID: str | None = None


def session_status() -> dict[str, Any]:
    with _LOCK:
        return dict(_STATE)


def close_session() -> None:
    global _LOOP, _THREAD, _STACK, _SESSION, _CACHED_STUDIO_ID
    with _LOCK:
        loop = _LOOP
        stack = _STACK
        thread = _THREAD
        _STACK = None
        _SESSION = None
        _CACHED_STUDIO_ID = None
        _STATE["phase"] = "idle"
        _STATE["error"] = ""
        _STATE["detail"] = "stopped"

    if loop and stack is not None:

        async def _aclose() -> None:
            try:
                await stack.aclose()
            except Exception:
                pass

        try:
            fut = asyncio.run_coroutine_threadsafe(_aclose(), loop)
            fut.result(timeout=5)
        except Exception as exc:
            log.warning("stdio close: %s", exc)
        try:
            loop.call_soon_threadsafe(loop.stop)
        except Exception:
            pass
    if thread and thread.is_alive() and thread is not threading.current_thread():
        thread.join(timeout=2.0)
    with _LOCK:
        _LOOP = None
        _THREAD = None


def ensure_session() -> dict[str, Any]:
    """Connect stdio if needed. Safe to call from any thread."""
    launch = runtime.mcp_launch()
    if not launch.get("ok"):
        with _LOCK:
            _STATE.update(
                {
                    "phase": "missing_studio",
                    "error": str(launch.get("hint") or "Studio MCP launcher not found"),
                    "detail": str(launch.get("path") or ""),
                    "path": str(launch.get("path") or ""),
                    "launch": launch,
                }
            )
        return session_status()

    with _LOCK:
        if _SESSION is not None and _STATE.get("phase") == "ready":
            return dict(_STATE)
        _STATE.update(
            {
                "phase": "starting",
                "error": "",
                "detail": "starting stdio",
                "path": str(launch.get("path") or ""),
                "launch": launch,
            }
        )

    try:
        _start_locked(str(launch["command"]), list(launch.get("args") or []))
    except Exception as exc:
        close_session()
        with _LOCK:
            _STATE.update(
                {
                    "phase": "mcp_disabled",
                    "error": describe_error(exc),
                    "detail": (
                        "Studio MCP did not connect. In Studio: Assistant → ⋯ → "
                        "Manage MCP Servers → Enable Studio as MCP server. Keep a place open."
                    ),
                    "path": str(launch.get("path") or ""),
                    "launch": launch,
                }
            )
        return session_status()
    with _LOCK:
        _STATE.update({"phase": "ready", "error": "", "detail": "connected", "launch": launch})
        return dict(_STATE)


def _start_locked(command: str, args: list[str]) -> None:
    global _LOOP, _THREAD, _STACK, _SESSION
    close_session()

    ready = threading.Event()
    box: dict[str, Any] = {}

    def _run_loop() -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        box["loop"] = loop
        ready.set()
        loop.run_forever()
        loop.close()

    thread = threading.Thread(target=_run_loop, daemon=True, name="roblox-mcp-stdio")
    thread.start()
    if not ready.wait(5):
        raise RobloxMcpError("stdio event loop did not start")
    loop: asyncio.AbstractEventLoop = box["loop"]

    async def _connect() -> Any:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        stack = AsyncExitStack()
        params = StdioServerParameters(
            command=command,
            args=args,
            env={str(k): str(v) for k, v in os.environ.items()},
        )
        transport = await stack.enter_async_context(stdio_client(params))
        read, write = transport[0], transport[1]
        session = await stack.enter_async_context(ClientSession(read, write))
        await asyncio.wait_for(session.initialize(), timeout=CONNECT_TIMEOUT_S)
        return stack, session

    fut = asyncio.run_coroutine_threadsafe(_connect(), loop)
    try:
        stack, session = fut.result(timeout=CONNECT_TIMEOUT_S + 5)
    except Exception:
        try:
            loop.call_soon_threadsafe(loop.stop)
        except Exception:
            pass
        thread.join(timeout=2.0)
        raise

    with _LOCK:
        _LOOP = loop
        _THREAD = thread
        _STACK = stack
        _SESSION = session


def _on_session(run: Callable[[Any], Awaitable[Any]], *, timeout: float) -> Any:
    status = ensure_session()
    if status.get("phase") != "ready":
        raise RobloxMcpError(status.get("error") or status.get("detail") or "Studio MCP not ready")
    with _LOCK:
        loop = _LOOP
        session = _SESSION
    if loop is None or session is None:
        raise RobloxMcpError("Studio MCP session is down")

    async def _inner() -> Any:
        return await run(session)

    fut = asyncio.run_coroutine_threadsafe(_inner(), loop)
    try:
        return fut.result(timeout=timeout)
    except Exception as exc:
        raise RobloxMcpError(describe_error(exc)) from exc


def list_tools() -> list[dict[str, Any]]:
    async def run(session: Any) -> list[dict[str, Any]]:
        result = await asyncio.wait_for(session.list_tools(), timeout=CALL_TIMEOUT_S)
        return [
            {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema or {},
            }
            for tool in (result.tools or [])
        ]

    return _on_session(run, timeout=CALL_TIMEOUT_S + 5)


def _raw_call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    async def run(session: Any) -> dict[str, Any]:
        result = await asyncio.wait_for(
            session.call_tool(name, arguments),
            timeout=CALL_TIMEOUT_S,
        )
        return {
            "ok": not bool(getattr(result, "isError", False)),
            "tool": name,
            "arguments": arguments,
            "text": flatten_content(getattr(result, "content", None)),
            "structured": getattr(result, "structuredContent", None),
            "images": extract_images(getattr(result, "content", None)),
        }

    return _on_session(run, timeout=CALL_TIMEOUT_S + 5)


def list_studios() -> list[dict[str, Any]]:
    global _CACHED_STUDIO_ID
    result = _raw_call(LIST_ROBLOX_STUDIOS, {})
    payload: Any = result.get("structured")
    if payload is None:
        payload = result.get("text") or ""
    studios = parse_studios(payload)
    if len(studios) == 1:
        _CACHED_STUDIO_ID = str(studios[0]["studio_id"])
    elif _CACHED_STUDIO_ID and _CACHED_STUDIO_ID not in {
        str(s["studio_id"]) for s in studios
    }:
        _CACHED_STUDIO_ID = None
    return studios


def call_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    global _CACHED_STUDIO_ID
    args = dict(arguments or {})
    if name != LIST_ROBLOX_STUDIOS:
        studios = list_studios()
        args, err = inject_studio_id(name, args, studios, _CACHED_STUDIO_ID)
        if err:
            return {
                "ok": False,
                "tool": name,
                "error": err,
                "studios": studios,
            }
        sid = str(args.get("studio_id") or "").strip()
        if sid:
            _CACHED_STUDIO_ID = sid
    return _raw_call(name, args)
