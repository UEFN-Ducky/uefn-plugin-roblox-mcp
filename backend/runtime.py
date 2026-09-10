"""Locate official Roblox Studio MCP (mcp.bat / StudioMCP)."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from .constants import MAC_STUDIO_MCP, PLUGIN_ID


def _localappdata() -> Path:
    local = os.environ.get("LOCALAPPDATA") or os.environ.get("HOME") or "."
    return Path(local)


def appdata_root() -> Path:
    try:
        from backend.skills.store import appdata_dir

        return Path(appdata_dir()) / "roblox_mcp"
    except Exception:
        return _localappdata() / "UEFN-Ducky" / "roblox_mcp"


def bridge_root() -> Path:
    """File hop directory — AppData only, never the UEFN island."""
    try:
        from backend.skills.store import appdata_dir

        root = Path(appdata_dir()) / "roblox_bridge"
    except Exception:
        root = _localappdata() / "UEFN-Ducky" / "roblox_bridge"
    root.mkdir(parents=True, exist_ok=True)
    return root


def mcp_launch() -> dict[str, Any]:
    """Command + args to spawn official Studio MCP over stdio."""
    if sys.platform == "win32":
        bat = _localappdata() / "Roblox" / "mcp.bat"
        if bat.is_file():
            return {
                "ok": True,
                "command": "cmd.exe",
                "args": ["/c", str(bat)],
                "path": str(bat),
                "platform": "win32",
            }
        return {
            "ok": False,
            "state": "missing_studio",
            "path": str(bat),
            "hint": (
                "Install Roblox Studio and open a place. The official MCP launcher "
                "is %LOCALAPPDATA%\\Roblox\\mcp.bat."
            ),
            "platform": "win32",
        }
    if sys.platform == "darwin":
        exe = Path(MAC_STUDIO_MCP)
        if exe.is_file():
            return {
                "ok": True,
                "command": str(exe),
                "args": [],
                "path": str(exe),
                "platform": "darwin",
            }
        return {
            "ok": False,
            "state": "missing_studio",
            "path": str(exe),
            "hint": "Install Roblox Studio. Expected StudioMCP at /Applications/RobloxStudio.app/Contents/MacOS/StudioMCP.",
            "platform": "darwin",
        }
    return {
        "ok": False,
        "state": "missing_studio",
        "path": "",
        "hint": "Roblox Studio MCP is Windows/macOS only.",
        "platform": sys.platform,
        "plugin_id": PLUGIN_ID,
    }
