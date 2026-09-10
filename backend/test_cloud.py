"""Open Cloud helpers with mocked HTTPS — no real key."""

from __future__ import annotations

import io
import json
from pathlib import Path
from backend import cloud


class _Resp:
    def __init__(self, payload: dict, status: int = 200) -> None:
        self.status = status
        self.headers = {"Content-Type": "application/json"}
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "_Resp":
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_test_api_key_empty() -> None:
    assert cloud.test_api_key("")["ok"] is False
    assert "Paste" in cloud.test_api_key("")["detail"]


def test_introspect_ok(monkeypatch) -> None:
    body = {
        "name": "Ducky",
        "enabled": True,
        "expired": False,
        "authorizedUserId": 99,
        "scopes": [{"name": "universe-places", "universeId": "123"}],
    }
    monkeypatch.setattr(cloud.urllib.request, "urlopen", lambda *a, **k: _Resp(body))
    data = cloud.introspect("rk_test")
    assert data["ok"] is True
    assert data["authorizedUserId"] == 99


def test_universe_ids_from_scopes() -> None:
    ids = cloud._universe_ids_from_introspect(
        {
            "scopes": [
                {"universeId": "1"},
                {"universeIds": ["1", "2", "*"]},
                {"universeDatastores": [{"universeId": "3", "datastoreName": "p"}]},
            ]
        }
    )
    assert ids == ["1", "2", "3"]


def test_publish_place_rejects_bad_suffix(tmp_path: Path) -> None:
    f = tmp_path / "place.txt"
    f.write_text("nope", encoding="utf-8")
    try:
        cloud.publish_place("1", "2", str(f))
        raise AssertionError("expected CloudError")
    except cloud.CloudError as exc:
        assert ".rbxl" in str(exc)


def test_publish_place_posts_bytes(tmp_path: Path, monkeypatch) -> None:
    f = tmp_path / "place.rbxlx"
    f.write_text("<roblox/>", encoding="utf-8")
    captured: dict[str, object] = {}

    def fake_urlopen(req, timeout=0):  # type: ignore[no-untyped-def]
        captured["url"] = req.full_url
        captured["method"] = req.get_method()
        captured["body"] = req.data
        captured["ctype"] = req.headers.get("Content-type") or req.headers.get("Content-Type")
        return _Resp({"versionNumber": 7})

    monkeypatch.setattr(cloud, "_api_key", lambda explicit=None: "rk_test")
    monkeypatch.setattr(cloud.urllib.request, "urlopen", fake_urlopen)
    data = cloud.publish_place("10", "20", str(f))
    assert data["ok"] is True
    assert data["versionNumber"] == 7
    assert "universes/v1/10/places/20/versions" in str(captured["url"])
    assert captured["method"] == "POST"
    assert captured["body"] == b"<roblox/>"


def test_datastore_get_query(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def fake_urlopen(req, timeout=0):  # type: ignore[no-untyped-def]
        captured["url"] = req.full_url
        return _Resp({"value": "9"})

    monkeypatch.setattr(cloud, "_api_key", lambda explicit=None: "rk_test")
    monkeypatch.setattr(cloud.urllib.request, "urlopen", fake_urlopen)
    data = cloud.datastore_get("1", "coins", "p1")
    assert data["ok"] is True
    assert "datastoreName=coins" in captured["url"]
    assert "entryKey=p1" in captured["url"]


def test_http_error_becomes_cloud_error(monkeypatch) -> None:
    import email.message
    import urllib.error

    def boom(*a, **k):  # type: ignore[no-untyped-def]
        hdrs = email.message.Message()
        raise urllib.error.HTTPError(
            "https://apis.roblox.com/x",
            401,
            "nope",
            hdrs,
            io.BytesIO(b"unauthorized"),
        )

    monkeypatch.setattr(cloud.urllib.request, "urlopen", boom)
    try:
        cloud._request("GET", "https://apis.roblox.com/x", key="rk")
        raise AssertionError("expected CloudError")
    except cloud.CloudError as exc:
        assert exc.status == 401
        assert "401" in str(exc)


def test_multipart_contains_json_and_file() -> None:
    body, ctype = cloud._multipart(
        {"request": '{"assetType":"Model"}'},
        {"fileContent": ("a.fbx", b"FBX", "model/fbx")},
    )
    assert b'name="request"' in body
    assert b"FBX" in body
    assert "multipart/form-data" in ctype
