# Playtest

| Tool | Use |
|------|-----|
| `get_studio_state` | Play vs edit; available datamodel types |
| `start_stop_play` | Start or stop play |
| `get_console_output` | Output window |
| `screen_capture` | Viewport (optional camera) |
| `execute_luau` | `datamodel_type` Edit / Client / Server |
| `user_keyboard_input` / `user_mouse_input` | Simulated input in play |
| `character_navigation` | Path to a position / instance (not real input) |
| `subagent` `playtest` | Multi-step play verification |

## Loop

1. Edit in `datamodel_type=Edit`.
2. `start_stop_play` start.
3. Wait; `get_studio_state` until playing.
4. Client/server `execute_luau` or input tools.
5. `screen_capture` / console.
6. Stop play before the next Edit mutation if Studio errors with “Target is not reachable”.

If play-mode tools fail, stop play, `roblox_status`, retry Edit. Do not hammer.
