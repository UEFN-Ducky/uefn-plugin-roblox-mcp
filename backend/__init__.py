"""ROBLOX MCP — Store desktop plugin; official Studio MCP + Open Cloud."""

from __future__ import annotations

import json
import logging
import threading
from typing import Any

from .constants import INTENT, PLUGIN_ID, SECRET_KEY

log = logging.getLogger("uefn.plugin.roblox-mcp")

_RUNTIME_THREAD: threading.Thread | None = None
_STOP = threading.Event()


def register(api: Any) -> None:
    if api.is_enabled():
        _start_runtime_async(api.log)

    if hasattr(api, "register_secret_test"):
        from .cloud import test_api_key

        api.register_secret_test(SECRET_KEY, test_api_key)

    connect = getattr(api, "connection", None)
    if callable(connect):
        connect(_connection_row, label="Roblox MCP", program="roblox")

    @api.tool(name="roblox_status", intent=INTENT, listener=False)
    def roblox_status() -> str:
        """Report ROBLOX MCP readiness: Studio stdio, open places, Open Cloud key."""
        return json.dumps(_build_status(), indent=2, default=str)

    @api.tool(name="roblox_list_tools", intent=INTENT, listener=False)
    def roblox_list_tools() -> str:
        """List live Roblox Studio MCP tools with input schemas. Never guess names."""
        from . import client

        try:
            tools = client.list_tools()
        except Exception as exc:
            return json.dumps(
                {"ok": False, "error": str(exc), "status": _build_status()},
                indent=2,
                default=str,
            )
        return json.dumps({"ok": True, "count": len(tools), "tools": tools}, indent=2)

    @api.tool(name="roblox_call", intent=INTENT, listener=False)
    def roblox_call(tool: str, arguments: dict[str, Any] | None = None) -> str:
        """Call one Studio MCP tool by name. studio_id is injected when a single place is open."""
        from . import client

        name = (tool or "").strip()
        if not name:
            return json.dumps({"ok": False, "error": "tool name is required"}, indent=2)
        try:
            args = _coerce_arguments(arguments)
        except ValueError as exc:
            return json.dumps({"ok": False, "error": str(exc)}, indent=2)
        try:
            return json.dumps(client.call_tool(name, args), indent=2, default=str)
        except Exception as exc:
            return json.dumps(
                {"ok": False, "tool": name, "error": str(exc), "status": _build_status()},
                indent=2,
                default=str,
            )

    @api.tool(name="roblox_redeploy", intent=INTENT, listener=False)
    def roblox_redeploy() -> str:
        """Drop and recreate the Studio MCP stdio session."""
        from . import client

        client.close_session()
        status = client.ensure_session()
        return json.dumps(
            {"ok": status.get("phase") == "ready", "session": status, "status": _build_status()},
            indent=2,
            default=str,
        )

    @api.tool(name="roblox_cloud_status", intent=INTENT, listener=False)
    def roblox_cloud_status() -> str:
        """Introspect the saved Open Cloud API key (enabled, scopes, user)."""
        from . import cloud

        if not cloud.key_present():
            return json.dumps(
                {
                    "ok": False,
                    "key_present": False,
                    "hint": "Paste a key in Settings → Roblox. Studio editing does not need it.",
                },
                indent=2,
            )
        try:
            data = cloud.introspect()
            data["key_present"] = True
            return json.dumps(data, indent=2, default=str)
        except cloud.CloudError as exc:
            return json.dumps({"ok": False, "key_present": True, "error": str(exc)}, indent=2)

    @api.tool(name="roblox_cloud_list_universes", intent=INTENT, listener=False)
    def roblox_cloud_list_universes() -> str:
        """List universes visible to the Open Cloud key (introspect scopes + user universes)."""
        return _cloud_json(lambda cloud: cloud.list_universes())

    @api.tool(name="roblox_cloud_get_place", intent=INTENT, listener=False)
    def roblox_cloud_get_place(universe_id: str, place_id: str) -> str:
        """GET one place via Open Cloud v2."""
        return _cloud_json(lambda cloud: cloud.get_place(universe_id, place_id))

    @api.tool(name="roblox_cloud_publish_place", intent=INTENT, listener=False)
    def roblox_cloud_publish_place(
        universe_id: str,
        place_id: str,
        file_path: str,
        version_type: str = "Published",
    ) -> str:
        """Upload a local .rbxl / .rbxlx as a new place version (Published or Saved)."""
        return _cloud_json(
            lambda cloud: cloud.publish_place(
                universe_id, place_id, file_path, version_type=version_type
            )
        )

    @api.tool(name="roblox_cloud_upload_asset", intent=INTENT, listener=False)
    def roblox_cloud_upload_asset(
        file_path: str,
        display_name: str,
        asset_type: str = "Model",
        description: str = "",
        user_id: str = "",
        group_id: str = "",
    ) -> str:
        """Upload a file (FBX/image/audio) through Open Cloud Assets API."""
        return _cloud_json(
            lambda cloud: cloud.upload_asset(
                file_path,
                display_name=display_name,
                asset_type=asset_type,
                description=description,
                user_id=user_id,
                group_id=group_id,
            )
        )

    @api.tool(name="roblox_cloud_get_asset", intent=INTENT, listener=False)
    def roblox_cloud_get_asset(asset_id: str) -> str:
        """GET Open Cloud asset metadata by numeric id."""
        return _cloud_json(lambda cloud: cloud.get_asset(asset_id))

    @api.tool(name="roblox_cloud_datastore_list", intent=INTENT, listener=False)
    def roblox_cloud_datastore_list(universe_id: str, prefix: str = "", limit: int = 50) -> str:
        """List standard DataStores in a universe."""
        return _cloud_json(lambda cloud: cloud.datastore_list(universe_id, prefix=prefix, limit=limit))

    @api.tool(name="roblox_cloud_datastore_get", intent=INTENT, listener=False)
    def roblox_cloud_datastore_get(
        universe_id: str,
        datastore_name: str,
        entry_key: str,
        scope: str = "global",
    ) -> str:
        """Read one standard DataStore entry."""
        return _cloud_json(
            lambda cloud: cloud.datastore_get(universe_id, datastore_name, entry_key, scope=scope)
        )

    @api.tool(name="roblox_cloud_datastore_set", intent=INTENT, listener=False)
    def roblox_cloud_datastore_set(
        universe_id: str,
        datastore_name: str,
        entry_key: str,
        value: Any,
        scope: str = "global",
    ) -> str:
        """Write one standard DataStore entry (JSON object/list or string)."""
        return _cloud_json(
            lambda cloud: cloud.datastore_set(
                universe_id, datastore_name, entry_key, value, scope=scope
            )
        )

    @api.tool(name="roblox_bridge_export", intent=INTENT, listener=False)
    def roblox_bridge_export(
        kind: str,
        path: str = "",
        asset_id: str = "",
        name: str = "",
    ) -> str:
        """Save a screenshot, local file, or Open Cloud asset metadata into AppData roblox_bridge/."""
        from . import bridge

        try:
            return json.dumps(
                bridge.export(kind, path=path, asset_id=asset_id, name=name),
                indent=2,
                default=str,
            )
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, indent=2)

    @api.tool(name="roblox_bridge_import", intent=INTENT, listener=False)
    def roblox_bridge_import(path: str, target: str = "studio") -> str:
        """Send a local file into Studio (store_image / upload+insert) or return a UEFN import_asset path."""
        from . import bridge

        try:
            return json.dumps(bridge.import_file(path, target=target), indent=2, default=str)
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, indent=2)

    api.log("ROBLOX MCP tools registered")


def unload() -> None:
    _stop_runtime()


def _cloud_json(fn: Any) -> str:
    from . import cloud

    try:
        return json.dumps(fn(cloud), indent=2, default=str)
    except cloud.CloudError as exc:
        return json.dumps({"ok": False, "error": str(exc)}, indent=2)


def _coerce_arguments(arguments: Any) -> dict[str, Any]:
    if arguments is None or arguments == "":
        return {}
    if isinstance(arguments, dict):
        return dict(arguments)
    if isinstance(arguments, str):
        try:
            parsed = json.loads(arguments)
        except json.JSONDecodeError as exc:
            raise ValueError(f"arguments is not valid JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise ValueError("arguments must be a JSON object")
        return parsed
    raise ValueError("arguments must be an object")


def _retry_wait(phase: str, launch_ok: bool) -> float:
    """How long to sit before the next auto-connect attempt."""
    if phase == "ready":
        return 12.0
    if not launch_ok:
        return 30.0
    if phase == "mcp_disabled":
        return 60.0
    return 12.0


def _start_runtime_async(log_fn: Any) -> None:
    global _RUNTIME_THREAD
    _STOP.clear()

    def _run() -> None:
        from . import client, runtime

        try:
            log_fn("ROBLOX MCP auto-connect")
        except Exception:
            pass
        try:
            while not _STOP.is_set():
                launch = runtime.mcp_launch()
                phase = str(client.session_status().get("phase") or "idle")
                if launch.get("ok") and phase != "ready":
                    try:
                        status = client.ensure_session()
                        phase = str(status.get("phase") or phase)
                        try:
                            log_fn(f"ROBLOX MCP session phase={phase}")
                        except Exception:
                            pass
                    except Exception as exc:
                        log.warning("session ensure failed: %s", exc)
                        phase = "error"
                if _STOP.wait(_retry_wait(phase, bool(launch.get("ok")))):
                    break
        except Exception as exc:
            log.warning("roblox runtime failed: %s", exc)
            try:
                log_fn(f"ROBLOX MCP runtime failed: {exc}")
            except Exception:
                pass

    thread = threading.Thread(target=_run, daemon=True, name="roblox-mcp-runtime")
    _RUNTIME_THREAD = thread
    thread.start()


def _stop_runtime() -> None:
    global _RUNTIME_THREAD
    _STOP.set()
    try:
        from . import client

        client.close_session()
    except Exception:
        pass
    thread = _RUNTIME_THREAD
    _RUNTIME_THREAD = None
    if thread and thread.is_alive() and thread is not threading.current_thread():
        thread.join(timeout=2.0)


def _connection_row() -> dict[str, Any]:
    """Cheap Connections probe — session state only, no Studio tool list."""
    from . import client, runtime

    launch = runtime.mcp_launch()
    session = client.session_status()
    phase = str(session.get("phase") or "idle")
    if not launch.get("ok"):
        return {"online": False, "detail": "Offline · open Roblox Studio"}
    if phase == "ready":
        return {"online": True, "detail": "Connected · Studio MCP"}
    if phase == "mcp_disabled":
        return {"online": False, "warn": True, "detail": "Offline · enable Studio as MCP server"}
    if phase in {"starting", "idle"}:
        return {"online": False, "warn": True, "detail": "Connecting · Studio MCP"}
    if phase == "error":
        err = str(session.get("error") or session.get("detail") or "error")
        return {"online": False, "detail": f"Offline · {err}"[:160]}
    return {"online": False, "detail": "Offline · Studio MCP"}


def _tools_status(phase: str) -> dict[str, Any]:
    if phase != "ready":
        return {"available": False, "reason": phase}
    from . import client

    try:
        tools = client.list_tools()
    except Exception as exc:
        return {"available": False, "error": str(exc)}
    return {
        "available": True,
        "count": len(tools),
        "names": [str(t.get("name") or "") for t in tools],
    }


def _build_status() -> dict[str, Any]:
    from . import client, cloud, runtime

    launch = runtime.mcp_launch()
    session = client.session_status()
    phase = str(session.get("phase") or "idle")
    if not launch.get("ok"):
        overall = "missing_studio"
    elif phase == "mcp_disabled":
        overall = "mcp_disabled"
    elif phase == "starting":
        overall = "connecting"
    elif phase == "ready":
        try:
            studios = client.list_studios()
        except Exception:
            studios = []
        if studios:
            overall = "ready"
        else:
            overall = "waiting_for_place"
    elif phase == "missing_studio":
        overall = "missing_studio"
    elif phase == "error":
        overall = "error"
    else:
        overall = "connecting" if launch.get("ok") else "missing_studio"

    hint = {
        "missing_studio": "Install/open Roblox Studio. Official launcher is %LOCALAPPDATA%\\Roblox\\mcp.bat (macOS: StudioMCP in the app bundle).",
        "mcp_disabled": "In Studio: Assistant → ⋯ → Manage MCP Servers → Enable Studio as MCP server. Then roblox_redeploy.",
        "connecting": "Starting Studio MCP stdio…",
        "waiting_for_place": "Studio MCP is up but no place is listed. Open a place, then roblox_status.",
        "ready": "Ready. Call roblox_list_tools, then roblox_call. Pass studio_id if multiple Studio windows are open.",
        "error": "See error fields; call roblox_redeploy after fixing the issue.",
    }.get(overall, "")

    tools = _tools_status("ready" if overall in {"ready", "waiting_for_place"} else overall)
    studios: list[Any] = []
    if overall in {"ready", "waiting_for_place"}:
        try:
            studios = client.list_studios()
        except Exception as exc:
            studios = [{"error": str(exc)}]

    return {
        "ok": overall == "ready",
        "plugin_id": PLUGIN_ID,
        "state": overall,
        "hint": hint,
        "launch": launch,
        "session": session,
        "studios": studios,
        "tools": tools,
        "open_cloud": {"key_present": cloud.key_present()},
    }
