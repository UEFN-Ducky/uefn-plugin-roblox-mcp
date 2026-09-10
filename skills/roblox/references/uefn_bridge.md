# UEFN ↔ Roblox hop

Same Ducky chat can call both stacks. That is **not** a shared game session.

**Impossible:** Fortnite players in a Roblox place, matchmaking, Verse↔Luau
translation, live property sync.

**Possible:** files through `%LOCALAPPDATA%/UEFN-Ducky/roblox_bridge/`.

## Roblox → UEFN

1. `roblox_bridge_export` `kind=screenshot` (viewport PNG) or `kind=file` (FBX on disk)
   or `kind=asset` (Open Cloud metadata JSON).
2. `roblox_bridge_import(path, target="uefn")` returns the path.
3. UEFN `import_asset` into the **project content root** (never `/Game/Materials` invented paths).

## UEFN / Blender → Roblox

1. Export FBX/PNG into AppData (Blender `uefn_export` or a path you already have).
2. `roblox_bridge_export` `kind=file` to copy into `roblox_bridge/`.
3. `roblox_bridge_import(path, target="studio")` — images use `store_image`;
   FBX uses Open Cloud upload then `insert_asset`.

Never write captures or scratch into the UEFN island. Never `.py` in the project.

If the user asked only for Roblox, do not touch UEFN tools. If only Fortnite,
do not `roblox_call`.
