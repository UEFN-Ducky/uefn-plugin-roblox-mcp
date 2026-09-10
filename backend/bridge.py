"""AppData file hop between Roblox Studio and UEFN. Never writes into an island."""

from __future__ import annotations

import base64
import json
import re
import time
from pathlib import Path
from typing import Any

from . import client, cloud, runtime

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def _safe(name: str) -> str:
    cleaned = _SAFE_NAME.sub("_", (name or "file").strip())[:80]
    return cleaned or "file"


def list_bridge_files() -> list[dict[str, Any]]:
    root = runtime.bridge_root()
    rows: list[dict[str, Any]] = []
    for path in sorted(root.iterdir()):
        if path.is_file():
            rows.append({"name": path.name, "path": str(path), "bytes": path.stat().st_size})
    return rows


def _write_images(result: dict[str, Any], dest: Path, stem: str) -> list[str]:
    saved: list[str] = []
    for i, img in enumerate(result.get("images") or []):
        if not isinstance(img, dict):
            continue
        data = str(img.get("data") or "")
        if not data:
            continue
        mime = str(img.get("mimeType") or "image/png")
        ext = ".jpg" if "jpeg" in mime else ".png"
        path = dest / f"{stem}_{i}{ext}"
        path.write_bytes(base64.b64decode(data))
        saved.append(str(path))
    return saved


def export(
    kind: str,
    *,
    path: str = "",
    asset_id: str = "",
    name: str = "",
) -> dict[str, Any]:
    dest = runtime.bridge_root()
    stamp = time.strftime("%Y%m%d_%H%M%S")
    kind = (kind or "").strip().lower()
    if kind == "screenshot":
        result = client.call_tool("screen_capture", {})
        if not result.get("ok"):
            return result
        stem = _safe(name or f"capture_{stamp}")
        saved = _write_images(result, dest, stem)
        text_path = dest / f"{stem}.json"
        text_path.write_text(json.dumps(result, indent=2, default=str)[:20000], encoding="utf-8")
        return {
            "ok": True,
            "kind": kind,
            "dir": str(dest),
            "files": saved or [str(text_path)],
            "hint": "UEFN: import_asset on a saved PNG if you need it in the island. Studio: roblox_bridge_import.",
        }
    if kind == "file":
        src = Path(path)
        if not src.is_file():
            return {"ok": False, "error": f"file not found: {src}"}
        target = dest / _safe(name or src.name)
        target.write_bytes(src.read_bytes())
        return {"ok": True, "kind": kind, "path": str(target), "bytes": target.stat().st_size}
    if kind == "asset":
        meta = cloud.get_asset(asset_id)
        out = dest / f"{_safe(name or asset_id)}_{stamp}.json"
        out.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
        return {
            "ok": True,
            "kind": kind,
            "path": str(out),
            "asset": meta,
            "hint": "Open Cloud metadata only. Insert in Studio with insert_asset(asset_id). Meshes hop as FBX via roblox_cloud_upload_asset / UEFN import_asset.",
        }
    return {"ok": False, "error": "kind must be screenshot, file, or asset"}


def import_file(path: str, *, target: str = "studio") -> dict[str, Any]:
    src = Path(path)
    if not src.is_file():
        return {"ok": False, "error": f"file not found: {src}"}
    dest = (target or "studio").strip().lower()
    if dest == "uefn":
        return {
            "ok": True,
            "target": "uefn",
            "path": str(src.resolve()),
            "hint": "Call UEFN import_asset with this path. Do not copy into the island folder by hand.",
        }
    if dest != "studio":
        return {"ok": False, "error": "target must be studio or uefn"}
    suffix = src.suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return client.call_tool("store_image", {"path": str(src.resolve())})
    if suffix in {".fbx", ".png", ".mp3", ".ogg"}:
        uploaded = cloud.upload_asset(
            str(src),
            display_name=src.stem,
            asset_type="Model" if suffix == ".fbx" else "Image" if suffix in {".png", ".jpg"} else "Audio",
        )
        asset_id = (
            str(uploaded.get("assetId") or uploaded.get("asset_id") or "")
            or str((uploaded.get("path") or "")).rsplit("/", 1)[-1]
        )
        if asset_id.isdigit():
            inserted = client.call_tool("insert_asset", {"assetId": int(asset_id)})
            return {"ok": True, "upload": uploaded, "insert": inserted}
        return {
            "ok": True,
            "upload": uploaded,
            "hint": "Upload started (Open Cloud operations are async). Poll get_asset, then roblox_call insert_asset with the numeric id.",
        }
    return {
        "ok": False,
        "error": f"Studio import does not take {suffix or 'this file'} directly",
        "hint": "Images → store_image. FBX/audio → Open Cloud upload then insert_asset. Place files → roblox_cloud_publish_place.",
    }
