# Open Cloud

Needs Settings → Roblox → API key. `roblox_cloud_status` first.

Create keys at https://create.roblox.com/credentials

Suggested scopes:

- `universe-places` write — `roblox_cloud_publish_place`
- `asset` read/write — upload/get
- `universe-datastores.objects` list/read/update — DataStores
- `universe-datastores.control` list — list store names

## Tools

| Tool | Use |
|------|-----|
| `roblox_cloud_status` | Introspect (enabled, scopes, user id) |
| `roblox_cloud_list_universes` | Universes from scopes + user list |
| `roblox_cloud_get_place` | One place |
| `roblox_cloud_publish_place` | POST `.rbxl` / `.rbxlx` (`Published` or `Saved`) |
| `roblox_cloud_upload_asset` | Multipart create (FBX/image/audio) |
| `roblox_cloud_get_asset` | Metadata by id |

Publish overwrites that place version — confirm universe_id + place_id (Creator
Dashboard URL `experiences/{universe}/places/{place}`).

Asset create often returns an **operation**. Poll `get_asset` / operation id
from the response; do not assume the mesh is in Studio until `insert_asset`.
