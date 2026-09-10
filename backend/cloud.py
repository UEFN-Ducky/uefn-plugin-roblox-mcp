"""Open Cloud HTTPS — named tools only, stdlib urllib."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .constants import CLOUD_BASE, CLOUD_TIMEOUT_S, INTROSPECT_URL, SECRET_KEY

USER_AGENT = "UEFN-Ducky-ROBLOX-MCP/1.0.0"


class CloudError(Exception):
    def __init__(self, message: str, *, status: int | None = None, detail: Any = None):
        super().__init__(message)
        self.status = status
        self.detail = detail


def _api_key(explicit: str | None = None) -> str:
    if explicit is not None:
        return explicit.strip()
    try:
        from backend.agent.secrets import get_key

        return (get_key(SECRET_KEY) or "").strip()
    except ImportError:
        return (os.environ.get("ROBLOX_OPEN_CLOUD_KEY") or "").strip()


def key_present() -> bool:
    return bool(_api_key())


def _request(
    method: str,
    url: str,
    *,
    key: str,
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = CLOUD_TIMEOUT_S,
) -> tuple[int, bytes, dict[str, str]]:
    hdrs = {
        "x-api-key": key,
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            info = {k.lower(): v for k, v in resp.headers.items()}
            return int(resp.status), raw, info
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise CloudError(
            f"Open Cloud HTTP {exc.code}: {detail[:800]}",
            status=exc.code,
            detail=detail,
        ) from exc
    except urllib.error.URLError as exc:
        raise CloudError(f"Open Cloud network error: {exc.reason}") from exc


def _json_body(status: int, raw: bytes) -> Any:
    text = raw.decode("utf-8", "replace")
    if not text.strip():
        return {"ok": True, "status": status}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"ok": True, "status": status, "text": text[:4000]}


def introspect(api_key: str = "") -> dict[str, Any]:
    key = _api_key(api_key or None)
    if not key:
        raise CloudError("Paste an Open Cloud API key in Settings → Roblox first")
    body = json.dumps({"apiKey": key}).encode("utf-8")
    status, raw, _hdrs = _request(
        "POST",
        INTROSPECT_URL,
        key=key,
        body=body,
        headers={"Content-Type": "application/json"},
    )
    data = _json_body(status, raw)
    if not isinstance(data, dict):
        return {"ok": True, "status": status, "raw": data}
    data["ok"] = bool(data.get("enabled", True)) and not bool(data.get("expired"))
    return data


def test_api_key(api_key: str = "") -> dict[str, Any]:
    """Settings → Test."""
    key = (api_key or "").strip()
    if not key:
        return {"ok": False, "detail": "Paste an Open Cloud API key first"}
    try:
        data = introspect(key)
    except CloudError as exc:
        return {"ok": False, "detail": str(exc)}
    name = str(data.get("name") or "").strip()
    scopes = data.get("scopes") if isinstance(data.get("scopes"), list) else []
    n = len(scopes)
    enabled = data.get("enabled")
    expired = data.get("expired")
    bits = [name or "key ok", f"{n} scope(s)"]
    if enabled is False:
        bits.append("disabled")
    if expired:
        bits.append("expired")
    return {"ok": bool(data.get("ok")), "detail": " — ".join(bits)}


test_api_key.__test__ = False  # Settings helper; pytest must not collect this


def _universe_ids_from_introspect(data: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for scope in data.get("scopes") or []:
        if not isinstance(scope, dict):
            continue
        for key in ("universeId", "universeIds"):
            val = scope.get(key)
            if isinstance(val, list):
                ids.extend(str(x) for x in val if str(x).strip() and str(x) != "*")
            elif val not in (None, "", "*"):
                ids.append(str(val))
        for row in scope.get("universeDatastores") or []:
            if isinstance(row, dict) and row.get("universeId"):
                ids.append(str(row["universeId"]))
    seen: set[str] = set()
    out: list[str] = []
    for uid in ids:
        if uid not in seen:
            seen.add(uid)
            out.append(uid)
    return out


def list_universes() -> dict[str, Any]:
    info = introspect()
    key = _api_key()
    universes: list[Any] = []
    errors: list[str] = []
    user_id = info.get("authorizedUserId")
    if user_id:
        url = f"{CLOUD_BASE}/cloud/v2/users/{user_id}/universes?maxPageSize=50"
        try:
            _status, raw, _h = _request("GET", url, key=key)
            payload = _json_body(_status, raw)
            rows = payload.get("universes") if isinstance(payload, dict) else None
            if isinstance(rows, list):
                universes.extend(rows)
            elif isinstance(payload, dict) and isinstance(payload.get("data"), list):
                universes.extend(payload["data"])
        except CloudError as exc:
            errors.append(str(exc))
    for uid in _universe_ids_from_introspect(info):
        url = f"{CLOUD_BASE}/cloud/v2/universes/{uid}"
        try:
            _status, raw, _h = _request("GET", url, key=key)
            universes.append(_json_body(_status, raw))
        except CloudError as exc:
            universes.append({"universeId": uid, "error": str(exc)})
    return {
        "ok": True,
        "authorizedUserId": user_id,
        "scopes": info.get("scopes") or [],
        "universes": universes,
        "errors": errors,
    }


def get_place(universe_id: str, place_id: str) -> dict[str, Any]:
    uid = str(universe_id or "").strip()
    pid = str(place_id or "").strip()
    if not uid or not pid:
        raise CloudError("universe_id and place_id are required")
    key = _api_key()
    if not key:
        raise CloudError("Open Cloud API key is required")
    url = f"{CLOUD_BASE}/cloud/v2/universes/{uid}/places/{pid}"
    _status, raw, _h = _request("GET", url, key=key)
    data = _json_body(_status, raw)
    if isinstance(data, dict):
        data["ok"] = True
    return data if isinstance(data, dict) else {"ok": True, "data": data}


def publish_place(
    universe_id: str,
    place_id: str,
    file_path: str,
    version_type: str = "Published",
) -> dict[str, Any]:
    uid = str(universe_id or "").strip()
    pid = str(place_id or "").strip()
    path = Path(file_path)
    if not uid or not pid:
        raise CloudError("universe_id and place_id are required")
    if not path.is_file():
        raise CloudError(f"place file not found: {path}")
    suffix = path.suffix.lower()
    if suffix not in {".rbxl", ".rbxlx"}:
        raise CloudError("place file must be .rbxl or .rbxlx")
    key = _api_key()
    if not key:
        raise CloudError("Open Cloud API key is required")
    vt = version_type if version_type in {"Published", "Saved"} else "Published"
    ctype = "application/xml" if suffix == ".rbxlx" else "application/octet-stream"
    url = (
        f"{CLOUD_BASE}/universes/v1/{uid}/places/{pid}/versions"
        f"?versionType={urllib.parse.quote(vt)}"
    )
    _status, raw, _h = _request(
        "POST",
        url,
        key=key,
        body=path.read_bytes(),
        headers={"Content-Type": ctype},
        timeout=180,
    )
    data = _json_body(_status, raw)
    if isinstance(data, dict):
        data["ok"] = True
        data["universe_id"] = uid
        data["place_id"] = pid
        return data
    return {"ok": True, "data": data}


def get_asset(asset_id: str) -> dict[str, Any]:
    aid = str(asset_id or "").strip()
    if not aid:
        raise CloudError("asset_id is required")
    key = _api_key()
    if not key:
        raise CloudError("Open Cloud API key is required")
    url = f"{CLOUD_BASE}/assets/v1/assets/{urllib.parse.quote(aid)}"
    _status, raw, _h = _request("GET", url, key=key)
    data = _json_body(_status, raw)
    if isinstance(data, dict):
        data["ok"] = True
        return data
    return {"ok": True, "data": data}


def upload_asset(
    file_path: str,
    *,
    display_name: str,
    asset_type: str = "Model",
    description: str = "",
    user_id: str = "",
    group_id: str = "",
) -> dict[str, Any]:
    path = Path(file_path)
    if not path.is_file():
        raise CloudError(f"asset file not found: {path}")
    key = _api_key()
    if not key:
        raise CloudError("Open Cloud API key is required")
    if not user_id and not group_id:
        info = introspect()
        user_id = str(info.get("authorizedUserId") or "")
    if not user_id and not group_id:
        raise CloudError("user_id or group_id is required to upload an asset")
    creator: dict[str, str] = {}
    if group_id:
        creator["groupId"] = str(group_id)
    else:
        creator["userId"] = str(user_id)
    request = {
        "assetType": asset_type or "Model",
        "displayName": display_name or path.stem,
        "description": description or display_name or path.stem,
        "creationContext": {"creator": creator},
    }
    mime = {
        ".fbx": "model/fbx",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".mp3": "audio/mpeg",
        ".ogg": "audio/ogg",
    }.get(path.suffix.lower(), "application/octet-stream")
    body, ctype = _multipart(
        {"request": json.dumps(request)},
        {"fileContent": (path.name, path.read_bytes(), mime)},
    )
    url = f"{CLOUD_BASE}/assets/v1/assets"
    _status, raw, _h = _request(
        "POST",
        url,
        key=key,
        body=body,
        headers={"Content-Type": ctype},
        timeout=180,
    )
    data = _json_body(_status, raw)
    if isinstance(data, dict):
        data["ok"] = True
        return data
    return {"ok": True, "data": data}


def _multipart(
    fields: dict[str, str],
    files: dict[str, tuple[str, bytes, str]],
) -> tuple[bytes, str]:
    boundary = "----DuckyRobloxBoundary7MA4YWxkTrZu0gW"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        )
        chunks.append(value.encode("utf-8"))
        chunks.append(b"\r\n")
    for name, (filename, content, mime) in files.items():
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(
            (
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
                f"Content-Type: {mime}\r\n\r\n"
            ).encode()
        )
        chunks.append(content)
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def datastore_list(universe_id: str, prefix: str = "", limit: int = 50) -> dict[str, Any]:
    uid = str(universe_id or "").strip()
    if not uid:
        raise CloudError("universe_id is required")
    key = _api_key()
    if not key:
        raise CloudError("Open Cloud API key is required")
    q = urllib.parse.urlencode({k: v for k, v in {"prefix": prefix, "limit": str(limit)}.items() if v})
    url = f"{CLOUD_BASE}/datastores/v1/universes/{uid}/standard-datastores"
    if q:
        url += f"?{q}"
    _status, raw, _h = _request("GET", url, key=key)
    data = _json_body(_status, raw)
    if isinstance(data, dict):
        data["ok"] = True
        return data
    return {"ok": True, "data": data}


def datastore_get(
    universe_id: str,
    datastore_name: str,
    entry_key: str,
    scope: str = "global",
) -> dict[str, Any]:
    uid = str(universe_id or "").strip()
    name = str(datastore_name or "").strip()
    entry = str(entry_key or "").strip()
    if not uid or not name or not entry:
        raise CloudError("universe_id, datastore_name, and entry_key are required")
    key = _api_key()
    if not key:
        raise CloudError("Open Cloud API key is required")
    q = urllib.parse.urlencode(
        {"datastoreName": name, "entryKey": entry, "scope": scope or "global"}
    )
    url = (
        f"{CLOUD_BASE}/datastores/v1/universes/{uid}/standard-datastores"
        f"/datastore/entries/entry?{q}"
    )
    _status, raw, _h = _request("GET", url, key=key)
    data = _json_body(_status, raw)
    if isinstance(data, dict):
        data["ok"] = True
        return data
    return {"ok": True, "value": data}


def datastore_set(
    universe_id: str,
    datastore_name: str,
    entry_key: str,
    value: Any,
    scope: str = "global",
) -> dict[str, Any]:
    uid = str(universe_id or "").strip()
    name = str(datastore_name or "").strip()
    entry = str(entry_key or "").strip()
    if not uid or not name or not entry:
        raise CloudError("universe_id, datastore_name, and entry_key are required")
    key = _api_key()
    if not key:
        raise CloudError("Open Cloud API key is required")
    if isinstance(value, (dict, list)):
        payload = json.dumps(value).encode("utf-8")
        ctype = "application/json"
    else:
        payload = str(value).encode("utf-8")
        ctype = "text/plain"
    q = urllib.parse.urlencode(
        {"datastoreName": name, "entryKey": entry, "scope": scope or "global"}
    )
    url = (
        f"{CLOUD_BASE}/datastores/v1/universes/{uid}/standard-datastores"
        f"/datastore/entries/entry?{q}"
    )
    _status, raw, _h = _request(
        "POST",
        url,
        key=key,
        body=payload,
        headers={"Content-Type": ctype},
    )
    data = _json_body(_status, raw)
    if isinstance(data, dict):
        data["ok"] = True
        return data
    return {"ok": True, "data": data}
