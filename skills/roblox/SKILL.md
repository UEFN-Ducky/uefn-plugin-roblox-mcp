---
name: roblox
description: >-
  Control Roblox Studio through the ROBLOX MCP Store plugin. Call roblox_status,
  then roblox_list_tools / roblox_call for the official Studio MCP (scripts,
  Luau, playtest, assets). Open Cloud tools (publish, assets, DataStores) need
  a Creator Dashboard API key. Use when the user mentions Roblox, Luau, Studio,
  or Open Cloud. Do not wait for UEFN.
license: MIT
metadata:
  label: ROBLOX MCP
  version: 2
  author: UEFN-Ducky
  copyright: Copyright 2026 Mindful Path Company, LLC
  allow_redistribute: true
  managed_by: uefn-ducky
  source_plugin_id: roblox-mcp
---

# ROBLOX MCP — Studio + Open Cloud

You control **Roblox Studio** through the **ROBLOX MCP** Store plugin. Official
Studio tools are reached with `roblox_list_tools` + `roblox_call`, not as
separate `roblox__*` entries. Open Cloud is `roblox_cloud_*`. File hops to UEFN
use `roblox_bridge_*` then UEFN `import_asset`.

**Roblox work does NOT need the UEFN / Fortnite listener.** If ROBLOX MCP is
ready, proceed. Do not wait for UEFN.

**Do not mix stacks:** Verse / `spawn_actor` / island devices are Fortnite.
Luau / instances / Studio MCP are Roblox. Same chat can do both — pick the
stack the user asked for. There is no live Fortnite↔Roblox multiplayer.

## Zero-setup (user)

1. Install / enable Store plugin **ROBLOX MCP** (`roblox-mcp`).
2. Open Roblox Studio with a place.
3. Assistant → ⋯ → **Manage MCP Servers** → **Enable Studio as MCP server**.

That is the only Studio click. Do **not** add a `Roblox_Studio` row to Cursor
`mcp.json` — Ducky owns stdio (`%LOCALAPPDATA%\Roblox\mcp.bat`).

Open Cloud (publish / cloud assets / DataStores): Settings → Roblox → paste a
key from [create.roblox.com/credentials](https://create.roblox.com/credentials).

## Calling Studio

1. `roblox_status` — see `state` before guessing.
2. `roblox_list_tools` — live names + schemas. Never invent a Studio tool.
3. `roblox_call(tool="<name>", arguments={...})` — JSON object string is ok.
   `studio_id` is injected when one Studio is open. If several windows are open,
   pass `studio_id` from `list_roblox_studios`.

## Status

| state | Meaning |
|-------|---------|
| `missing_studio` | mcp.bat / StudioMCP not found — install/open Studio |
| `mcp_disabled` | Launcher exists but stdio failed — enable Studio MCP, then `roblox_redeploy` |
| `connecting` | Starting stdio |
| `waiting_for_place` | MCP up, no listed place — open a place |
| `ready` | `roblox_list_tools` then `roblox_call` |
| `error` | See `error`; `roblox_redeploy` after fix |

## Route — `skill_read_subskill("roblox", "<id>")`

| Id | When |
|----|------|
| `connection` | Status, Assistant toggle, no mcp.json |
| `studio_mcp` | Tool catalog, `studio_id`, never invent instance state |
| `luau` | Scripts, services, no Verse effects |
| `instances` | Data model, properties, parenting |
| `scripts` | `script_read` / `multi_edit` / grep / search |
| `gui` | ScreenGui / StarterGui |
| `remotes` | RemoteEvent / RemoteFunction |
| `playtest` | Play, console, input, `datamodel_type` |
| `assets` | generate_mesh/material, Creator Store insert |
| `open_cloud` | Key scopes, publish, asset upload |
| `datastores` | Open Cloud vs in-experience DataStoreService |
| `uefn_bridge` | AppData hop only — no live cross-play, no Verse↔Luau |

## Hard rules

- Never invent the game tree — `search_game_tree` / `inspect_instance` first.
- Never use UEFN `spawn_actor` / Verse for a Roblox place.
- If `waiting_for_place` / `mcp_disabled`, teach the Assistant toggle — do not
  paste JSON into Cursor.
- If Studio is unreachable, `roblox_redeploy` — do not retry UEFN tools as a substitute.
- Open Cloud needs a key. Live Studio editing does not.

## Verify

`roblox_status` then the Studio/Cloud read that proves the change.
