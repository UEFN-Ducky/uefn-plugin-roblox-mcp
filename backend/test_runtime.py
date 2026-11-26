"""Studio MCP launcher per OS."""

from __future__ import annotations

import sys
from pathlib import Path

from backend import runtime


def test_mac_launches_studio_mcp_from_the_app_bundle(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(sys, "platform", "darwin")
    exe = tmp_path / "RobloxStudio.app" / "Contents" / "MacOS" / "StudioMCP"
    monkeypatch.setattr(runtime, "MAC_STUDIO_MCP", str(exe))
    missing = runtime.mcp_launch()
    assert missing["ok"] is False and missing["state"] == "missing_studio" and missing["platform"] == "darwin"
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"\xcf\xfa\xed\xfe")
    out = runtime.mcp_launch()
    assert out == {"ok": True, "command": str(exe), "args": [], "path": str(exe), "platform": "darwin"}


def test_mac_default_points_at_applications() -> None:
    assert runtime.MAC_STUDIO_MCP == "/Applications/RobloxStudio.app/Contents/MacOS/StudioMCP"
