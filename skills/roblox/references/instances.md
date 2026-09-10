# Instances

The Data Model is a tree. Query it; do not guess.

1. `search_game_tree` — filter by path, class, keywords, depth.
2. `inspect_instance` — properties, attributes, children summary.
3. Mutate with `execute_luau` (`datamodel_type=Edit`) or `multi_edit` for scripts.

## Conventions

- Gameplay parts under `Workspace` (folders by area).
- Shared modules in `ReplicatedStorage`.
- Do not parent scripts randomly under `Workspace` unless they must be there.
- `Name` is not unique — use full paths from search results.
- Anchored parts for level geo; unanchored + `AssemblyLinearVelocity` only when you mean physics.

## Create (Edit Luau)

```lua
local part = Instance.new("Part")
part.Name = "Block"
part.Size = Vector3.new(4, 1, 4)
part.Position = Vector3.new(0, 2, 0)
part.Anchored = true
part.Parent = workspace
```

Set properties from `inspect_instance` names. If a property is missing, it is
not writable in that datamodel (Edit vs Play).
