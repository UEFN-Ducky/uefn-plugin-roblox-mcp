# GUI

Player UI lives under `StarterGui` (cloned per player) or a ScreenGui you
parent to `PlayerGui` at runtime.

## Structure

```
StarterGui
  ScreenGui (ResetOnSpawn as needed)
    Frame / TextLabel / TextButton / ImageLabel / UIListLayout / UIPadding
```

- Scale with `UDim2.fromScale` for phone + desktop; offset for hairline borders.
- `IgnoreGuiInset` when you mean full-bleed.
- Buttons fire on the **client**. Server authority stays on remotes.

## Via MCP

`search_game_tree` with type `ScreenGui` / `TextButton`. Create with
`execute_luau` Edit. LocalScripts that drive UI go next to the ScreenGui or in
`StarterPlayerScripts`.

Do not build UEFN UMG for a Roblox place.
