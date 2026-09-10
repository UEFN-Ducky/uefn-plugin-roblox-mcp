# Scripts

Studio MCP script tools use **dot paths** (`game.ServerScriptService.MyScript`).

| Tool | Use |
|------|-----|
| `script_search` | Fuzzy name, up to ~10 hits |
| `script_grep` | String across scripts, up to ~50 hits |
| `script_read` | Whole file or line range |
| `multi_edit` | Patch or create; `datamodel_type=Edit` |

## Workflow

1. `script_search` / `script_grep` to find the module.
2. `script_read` the region you will change.
3. One `multi_edit` with unique old strings — do not rewrite 400 lines if 8 will do.
4. If the path does not exist, `multi_edit` can create a new script (see live schema).

Do not keep two copies of the same system. Fix the existing ModuleScript.

After edits: `get_console_output` or a short `execute_luau` probe. Playtest via
`playtest` when behavior matters.
