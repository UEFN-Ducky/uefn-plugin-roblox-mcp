# Connection

## Layers

| Layer | Meaning |
|-------|---------|
| Store plugin **ROBLOX MCP** enabled | Ducky has `roblox_*` tools |
| `%LOCALAPPDATA%\Roblox\mcp.bat` (Windows) or `StudioMCP` (macOS) | Official Studio MCP launcher exists |
| Assistant → Manage MCP Servers → **Enable Studio as MCP server** | Studio will accept stdio clients |
| Open place | `list_roblox_studios` returns a `studio_id` |
| Open Cloud key (optional) | `roblox_cloud_*` only |

Store plugin ≠ live Studio. `roblox_status` → `ready` is the only green light.

## Diagnose

1. `roblox_status`.
2. `missing_studio` — install Studio, open it once so `mcp.bat` appears, retry.
3. `mcp_disabled` — user enables MCP in Assistant, then `roblox_redeploy`.
4. `waiting_for_place` — user opens a place (File → Open / New).
5. `ready` — `roblox_list_tools`.

## Teach the user (copy)

1. Open **Roblox Studio** with the place you want to edit.
2. Click **Assistant** (upper right).
3. **⋯ → Manage MCP Servers**.
4. Turn on **Enable Studio as MCP server**.
5. Keep Studio open. Ask the agent again.

## Do not tell the user

- Paste a `Roblox_Studio` block into Cursor `mcp.json`
- Install a community Studio MCP plugin / OSS server
- That “Studio is open” alone means the agent can control it
- Settings → Store → Update (panel auto-applies Store plugins)
