"""Shared constants for the ROBLOX MCP Store plugin."""

from __future__ import annotations

PLUGIN_ID = "roblox-mcp"
SECRET_KEY = "roblox_open_cloud_key"
INTENT = (
    r"\b(roblox|luau|roblox\s*studio|studio\s*mcp|datamodel|open\s*cloud)\b"
)

CONNECT_TIMEOUT_S = 45.0
CALL_TIMEOUT_S = 180.0
CLOUD_TIMEOUT_S = 60

CLOUD_BASE = "https://apis.roblox.com"
INTROSPECT_URL = f"{CLOUD_BASE}/api-keys/v1/introspect"
LIST_ROBLOX_STUDIOS = "list_roblox_studios"

MAC_STUDIO_MCP = "/Applications/RobloxStudio.app/Contents/MacOS/StudioMCP"
