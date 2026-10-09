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

## Next release: ship compiled

This plugin still ships its Python source on the Store. Its next release has to ship compiled and signed, the way Ducky Account and Roguelike do:

1. Give `scripts/release.py` and `scripts/build_zip.py` the compiled build from `uefn-plugin-account` (`build_compiled_zip`, upload by ticket, `--plain` only as an escape hatch).
2. Bump `version` and set `min_app_version` to `1.2.356` or newer.
3. Publish, then check the download with the start-up license check (signature, id and version, compiled, team access), not only the signature.
4. The Store must hold the version back from apps older than `min_app_version`. Until it does, older apps install a build they can't run.

Remove this section once a compiled version is live.

## License

MIT. Copyright (c) 2026 Mindful Path Company, LLC. See [LICENSE](LICENSE).
