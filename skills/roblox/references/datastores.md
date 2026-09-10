# DataStores

Two APIs, same data:

| Where | API |
|-------|-----|
| Live / Studio Luau | `DataStoreService` |
| This plugin | `roblox_cloud_datastore_list` / `_get` / `_set` |

Cloud calls need a key with `universe-datastores.*` on that universe.

`list` → names. `get` / `set` take `universe_id`, `datastore_name`, `entry_key`,
optional `scope` (default `global`). `set` accepts a JSON object/list or a string.

Never delete player keys as a “cleanup” unless the user asked — same caution as
Verse persist maps.

In-experience:

```lua
local ds = game:GetService("DataStoreService"):GetDataStore("PlayerData")
```

Use `pcall` around Get/Set. Do not store Instances — JSON-like tables only.
