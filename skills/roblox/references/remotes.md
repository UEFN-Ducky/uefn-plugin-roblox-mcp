# Remotes

Client cannot trust itself. Server owns money, inventory, damage.

## Setup

`ReplicatedStorage` → `RemoteEvent` or `RemoteFunction` (names like `Remotes/BuyItem`).

```lua
-- server
remote.OnServerEvent:Connect(function(player, itemId)
	-- validate itemId, debounce, then grant
end)

-- client
remote:FireServer(itemId)
```

- `RemoteEvent`: one-way (client→server or server→client).
- `RemoteFunction`: request/response; avoid long yields; never let the client
  decide the result of a purchase.
- Validate every argument. Rate-limit. Ignore malformed types.

Studio MCP cannot invent a live session between Fortnite and Roblox. Remotes
are in-experience only.
