# ROBLOX MCP

Official [Roblox Studio MCP](https://create.roblox.com/docs/studio/mcp) plus
Open Cloud for [UEFN-Ducky](https://github.com/UEFN-Ducky/UEFN-Ducky)
(`roblox-mcp`). Install or update from the Store — do not install from a zip
by hand.

## User flow

1. Install / enable **ROBLOX MCP**.
2. Open Roblox Studio with a place.
3. Assistant → ⋯ → Manage MCP Servers → **Enable Studio as MCP server**.

The plugin owns stdio to `%LOCALAPPDATA%\Roblox\mcp.bat` (macOS: `StudioMCP`).
It writes no Cursor `mcp.json` row. Uninstalling the plugin removes the tools.

Optional: Settings → Roblox → Open Cloud API key (publish, assets, DataStores).

## Agent tools

| Tool | Purpose |
|------|---------|
| `roblox_status` | Ready-state |
| `roblox_list_tools` | Live Studio tools + schemas |
| `roblox_call` | One Studio tool (`studio_id` injected when unique) |
| `roblox_redeploy` | Recreate stdio session |
| `roblox_cloud_*` | Open Cloud (key required) |
| `roblox_bridge_*` | AppData hop to/from UEFN |

## Tests

```bash
py -m pytest backend -q
```

## Publish

```bash
py -3 scripts/release.py --publish --changelog "v1.0.0: ROBLOX MCP Studio + Open Cloud"
```

Requires `DUCKYOS_API_KEY`. Do not publish a dirty clone.

## License

MIT. Copyright (c) 2026 Mindful Path Company, LLC. See [LICENSE](LICENSE).
