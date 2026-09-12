"""Status aggregation + register surface."""

from __future__ import annotations

import json
from unittest.mock import patch

import backend as plugin


class FakeApi:
    def __init__(self, enabled: bool = False) -> None:
        self.enabled = enabled
        self.tools: dict[str, object] = {}
        self.secret_tests: dict[str, object] = {}
        self.connection_fn = None
        self.connection_kwargs: dict[str, object] = {}

    def is_enabled(self) -> bool:
        return self.enabled

    def log(self, msg: str) -> None:
        return None

    def tool(self, **kwargs):  # type: ignore[no-untyped-def]
        def deco(fn):  # type: ignore[no-untyped-def]
            self.tools[kwargs.get("name") or fn.__name__] = fn
            return fn

        return deco

    def register_secret_test(self, key: str, fn: object) -> None:
        self.secret_tests[key] = fn

    def connection(self, fn: object, **kwargs: object) -> None:
        self.connection_fn = fn
        self.connection_kwargs = kwargs


def _register(api: FakeApi | None = None) -> FakeApi:
    api = api or FakeApi()
    plugin.register(api)
    return api


def test_build_status_missing_studio() -> None:
    with (
        patch("backend.runtime.mcp_launch", return_value={"ok": False, "state": "missing_studio"}),
        patch("backend.client.session_status", return_value={"phase": "idle"}),
        patch("backend.cloud.key_present", return_value=False),
    ):
        status = plugin._build_status()
    assert status["state"] == "missing_studio"
    assert status["ok"] is False
    assert "mcp.bat" in status["hint"]


def test_build_status_mcp_disabled() -> None:
    with (
        patch("backend.runtime.mcp_launch", return_value={"ok": True, "path": "mcp.bat"}),
        patch("backend.client.session_status", return_value={"phase": "mcp_disabled"}),
        patch("backend.cloud.key_present", return_value=False),
    ):
        status = plugin._build_status()
    assert status["state"] == "mcp_disabled"
    assert "Enable Studio as MCP server" in status["hint"]


def test_build_status_waiting_for_place() -> None:
    with (
        patch("backend.runtime.mcp_launch", return_value={"ok": True}),
        patch("backend.client.session_status", return_value={"phase": "ready"}),
        patch("backend.client.list_studios", return_value=[]),
        patch("backend.client.list_tools", return_value=[{"name": "list_roblox_studios"}]),
        patch("backend.cloud.key_present", return_value=False),
    ):
        status = plugin._build_status()
    assert status["state"] == "waiting_for_place"
    assert status["ok"] is False


def test_build_status_ready() -> None:
    studios = [{"studio_id": "s1", "name": "Baseplate"}]
    with (
        patch("backend.runtime.mcp_launch", return_value={"ok": True}),
        patch("backend.client.session_status", return_value={"phase": "ready"}),
        patch("backend.client.list_studios", return_value=studios),
        patch(
            "backend.client.list_tools",
            return_value=[{"name": "execute_luau"}, {"name": "list_roblox_studios"}],
        ),
        patch("backend.cloud.key_present", return_value=True),
    ):
        status = plugin._build_status()
    assert status["state"] == "ready"
    assert status["ok"] is True
    assert status["tools"]["count"] == 2
    assert status["open_cloud"]["key_present"] is True
    assert "roblox_list_tools" in status["hint"]


def test_register_tools_and_secret_test() -> None:
    api = _register()
    assert "roblox_status" in api.tools
    assert "roblox_list_tools" in api.tools
    assert "roblox_call" in api.tools
    assert "roblox_redeploy" in api.tools
    assert "roblox_cloud_status" in api.tools
    assert "roblox_cloud_publish_place" in api.tools
    assert "roblox_bridge_export" in api.tools
    assert "roblox_open_cloud_key" in api.secret_tests
    assert api.connection_fn is plugin._connection_row
    assert api.connection_kwargs.get("label") == "Roblox MCP"
    assert api.connection_kwargs.get("program") == "roblox"


def test_connection_row_ready() -> None:
    with (
        patch("backend.runtime.mcp_launch", return_value={"ok": True}),
        patch("backend.client.session_status", return_value={"phase": "ready"}),
    ):
        row = plugin._connection_row()
    assert row["online"] is True
    assert "Studio MCP" in row["detail"]


def test_connection_row_connecting_while_idle() -> None:
    with (
        patch("backend.runtime.mcp_launch", return_value={"ok": True}),
        patch("backend.client.session_status", return_value={"phase": "idle"}),
    ):
        row = plugin._connection_row()
    assert row["online"] is False
    assert row["warn"] is True
    assert "Connecting" in row["detail"]


def test_register_starts_runtime_when_enabled() -> None:
    with patch.object(plugin, "_start_runtime_async") as start:
        _register(FakeApi(enabled=True))
    assert start.called


def test_register_skips_runtime_when_disabled() -> None:
    with patch.object(plugin, "_start_runtime_async") as start:
        _register(FakeApi(enabled=False))
    assert not start.called


def test_retry_wait_backs_off_when_studio_missing() -> None:
    assert plugin._retry_wait("idle", False) == 30.0
    assert plugin._retry_wait("mcp_disabled", True) == 60.0
    assert plugin._retry_wait("ready", True) == 12.0


def test_connection_row_missing_studio() -> None:
    with (
        patch("backend.runtime.mcp_launch", return_value={"ok": False}),
        patch("backend.client.session_status", return_value={"phase": "missing_studio"}),
    ):
        row = plugin._connection_row()
    assert row["online"] is False
    assert "Roblox Studio" in row["detail"]


def test_roblox_status_tool_json() -> None:
    api = _register()
    with patch.object(
        plugin,
        "_build_status",
        return_value={"ok": False, "state": "missing_studio", "plugin_id": "roblox-mcp"},
    ):
        payload = json.loads(api.tools["roblox_status"]())
    assert payload["state"] == "missing_studio"


def test_roblox_call_forwards_arguments() -> None:
    api = _register()
    with patch("backend.client.call_tool", return_value={"ok": True, "text": "done"}) as call:
        payload = json.loads(api.tools["roblox_call"]("execute_luau", {"code": "return 1"}))
    call.assert_called_once_with("execute_luau", {"code": "return 1"})
    assert payload["text"] == "done"


def test_roblox_call_accepts_json_string_arguments() -> None:
    api = _register()
    with patch("backend.client.call_tool", return_value={"ok": True}) as call:
        api.tools["roblox_call"]("inspect_instance", '{"path": "Workspace"}')
    call.assert_called_once_with("inspect_instance", {"path": "Workspace"})


def test_roblox_call_rejects_bad_arguments() -> None:
    api = _register()
    payload = json.loads(api.tools["roblox_call"]("execute_luau", "not json"))
    assert payload["ok"] is False
    assert "valid JSON" in payload["error"]


def test_roblox_call_requires_tool_name() -> None:
    api = _register()
    payload = json.loads(api.tools["roblox_call"](" "))
    assert payload["ok"] is False


def test_unload_closes_session() -> None:
    with patch("backend.client.close_session") as close:
        plugin.unload()
    assert close.called
