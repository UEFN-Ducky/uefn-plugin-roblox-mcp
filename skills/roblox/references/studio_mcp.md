# Studio MCP tools

Source of truth is `roblox_list_tools` (schemas change with Studio). Official
catalog (2026): https://create.roblox.com/docs/studio/mcp

## Always

- `list_roblox_studios` first when status is unclear or several windows are open.
- Every mutating call needs `studio_id`. `roblox_call` injects it when exactly
  one Studio is listed. If injection errors, pass `studio_id` yourself.
- Do not call `set_active_studio` — removed; pass `studio_id` instead.

## Groups (typical names)

Scripts: `script_read`, `multi_edit`, `script_search`, `script_grep`

Tree: `search_game_tree`, `inspect_instance`

Luau: `execute_luau` with `datamodel_type` = `Edit` | `Client` | `Server`

Play: `get_studio_state`, `start_stop_play`, `get_console_output`, `screen_capture`

Input: `character_navigation`, `user_keyboard_input`, `user_mouse_input`

Assets: `generate_mesh`, `generate_material`, `generate_procedural_model`,
`wait_job_finished`, `search_asset`, `insert_asset`, `upload_image`, `store_image`

Docs: `http_get` (Roblox docs allowlist), `skill` (Studio’s own skills)

Subagents: `subagent` type `explore` | `playtest`

## Discipline

Never invent instance paths. `search_game_tree` → `inspect_instance` → edit.

Arguments must match the live `input_schema`. Prefer `roblox_list_tools` over
this file when a name disagrees.
