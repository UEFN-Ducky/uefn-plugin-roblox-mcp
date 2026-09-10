# Luau (Studio)

Roblox scripts are **Luau**, not Verse. No effect specifiers, no `spawn_actor`.

## Where code lives

| Service | Use |
|---------|-----|
| `ServerScriptService` | Server `Script` |
| `ReplicatedStorage` | `ModuleScript` shared |
| `StarterPlayer.StarterPlayerScripts` | Client `LocalScript` |
| `StarterGui` | UI LocalScripts |

Prefer ModuleScripts + `require`. Avoid giant Scripts.

## Patterns

```lua
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local function onPlayer(player: Player)
	print(player.Name)
end

Players.PlayerAdded:Connect(onPlayer)
```

- Type as you go (`player: Player`) when it helps; do not invent APIs.
- `task.wait` / `task.spawn` / `task.defer` — not `wait()` / `spawn()`.
- Remote traffic: see `remotes`. FilteringEnabled is always on.
- Persistence in-experience is `DataStoreService` — cloud edits use `datastores`.

## Via MCP

Read/write scripts with `script_read` / `multi_edit` (dot paths like
`game.ServerScriptService.Game`). `execute_luau` is for probes, not for dumping
a whole game into the command bar.

If a name is unknown, `roblox_call` → `http_get` on Creator docs, or Studio `skill`.
