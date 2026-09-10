"""AppData hop helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from backend import bridge


def test_export_file_copies_into_bridge(tmp_path: Path, monkeypatch) -> None:
    src = tmp_path / "mesh.fbx"
    src.write_bytes(b"fbx")
    dest = tmp_path / "bridge"
    dest.mkdir()
    monkeypatch.setattr("backend.runtime.bridge_root", lambda: dest)
    result = bridge.export("file", path=str(src), name="SM_Thing.fbx")
    assert result["ok"] is True
    out = Path(result["path"])
    assert out.parent == dest
    assert out.read_bytes() == b"fbx"


def test_export_rejects_unknown_kind() -> None:
    result = bridge.export("teleport")
    assert result["ok"] is False


def test_import_uefn_returns_path(tmp_path: Path) -> None:
    f = tmp_path / "a.fbx"
    f.write_bytes(b"x")
    result = bridge.import_file(str(f), target="uefn")
    assert result["ok"] is True
    assert result["path"].endswith("a.fbx")
    assert "import_asset" in result["hint"]


def test_import_studio_image_calls_store_image(tmp_path: Path) -> None:
    f = tmp_path / "shot.png"
    f.write_bytes(b"png")
    with patch("backend.client.call_tool", return_value={"ok": True, "text": "rbxasset://x"}) as call:
        result = bridge.import_file(str(f), target="studio")
    call.assert_called_once()
    assert call.call_args[0][0] == "store_image"
    assert result["ok"] is True
