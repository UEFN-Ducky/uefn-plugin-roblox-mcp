"""Studio client helpers: studio_id inject, flatten, parse studios."""

from __future__ import annotations

from types import SimpleNamespace

from backend import client


def test_parse_studios_list_and_wrapped() -> None:
    rows = client.parse_studios(
        {"studios": [{"studio_id": "abc", "name": "Baseplate", "place_id": 1}]}
    )
    assert rows == [{"studio_id": "abc", "name": "Baseplate", "place_id": 1}]
    rows2 = client.parse_studios(
        [{"id": "x", "displayName": "Place", "placeId": 9}]
    )
    assert rows2[0]["studio_id"] == "x"
    assert rows2[0]["place_id"] == 9


def test_parse_studios_json_string() -> None:
    rows = client.parse_studios('{"data": [{"studioId": "s1", "name": "A"}]}')
    assert rows == [{"studio_id": "s1", "name": "A", "place_id": None}]


def test_parse_studios_empty() -> None:
    assert client.parse_studios("") == []
    assert client.parse_studios("not json") == []
    assert client.parse_studios({}) == []


def test_inject_skips_list_tool() -> None:
    args, err = client.inject_studio_id("list_roblox_studios", {}, [{"studio_id": "a"}], None)
    assert args == {}
    assert err is None


def test_inject_keeps_existing() -> None:
    args, err = client.inject_studio_id(
        "execute_luau",
        {"studio_id": "keep", "code": "1"},
        [{"studio_id": "other"}],
        None,
    )
    assert args["studio_id"] == "keep"
    assert err is None


def test_inject_single_studio() -> None:
    args, err = client.inject_studio_id("inspect_instance", {}, [{"studio_id": "only"}], None)
    assert args["studio_id"] == "only"
    assert err is None


def test_inject_cached_when_multiple() -> None:
    studios = [{"studio_id": "a", "name": "A"}, {"studio_id": "b", "name": "B"}]
    args, err = client.inject_studio_id("inspect_instance", {}, studios, "b")
    assert args["studio_id"] == "b"
    assert err is None


def test_inject_errors_when_multiple_uncached() -> None:
    studios = [{"studio_id": "a", "name": "A"}, {"studio_id": "b", "name": "B"}]
    args, err = client.inject_studio_id("inspect_instance", {}, studios, None)
    assert err is not None
    assert "studio_id" in err
    assert "studio_id" not in args


def test_inject_errors_when_none() -> None:
    _args, err = client.inject_studio_id("inspect_instance", {}, [], None)
    assert err is not None
    assert "Enable Studio as MCP server" in err


def test_flatten_content_and_images() -> None:
    blocks = [
        SimpleNamespace(type="text", text="ok"),
        SimpleNamespace(type="image", data="QQ==", mimeType="image/png"),
    ]
    assert client.flatten_content(blocks) == "ok\n[image]"
    imgs = client.extract_images(blocks)
    assert imgs == [{"mimeType": "image/png", "data": "QQ=="}]


def test_describe_error_unwraps_task_groups() -> None:
    group = ExceptionGroup(  # noqa: F821
        "unhandled errors in a TaskGroup",
        [ConnectionRefusedError("All connection attempts failed")],
    )
    assert client.describe_error(group) == (
        "ConnectionRefusedError: All connection attempts failed"
    )
