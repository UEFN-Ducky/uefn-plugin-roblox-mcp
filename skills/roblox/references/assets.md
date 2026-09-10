# Assets (Studio)

Studio MCP can generate and insert without Open Cloud:

| Tool | Use |
|------|-----|
| `generate_mesh` | Textured mesh from a prompt |
| `generate_material` | Material variant |
| `generate_procedural_model` | Primitive assemblies; `wait_job_finished` |
| `search_asset` | Creator Store + inventory |
| `insert_asset` | Numeric Roblox asset id |
| `store_image` | Local file → image URI for other tools |
| `upload_image` | HTTP URLs → asset ids |

Always `search_asset` before generating if a catalog item is enough.

Open Cloud upload (FBX from disk, group/user creator) is `roblox_cloud_upload_asset`.
Then `insert_asset` with the returned id when the operation finishes.

Do not drop files into a UEFN island to “share” them — `uefn_bridge`.
