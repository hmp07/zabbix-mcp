"""Transport and registration tests.

Verifies that:
- All expected tools are registered on the FastMCP server.
- Tool annotations are correct per category (read-only, write, delete).
- Tool descriptions are present and non-empty.
- All tools have openWorldHint=False (closed-world API).
- is_read_only_mode() parses ZABBIX_READ_ONLY correctly.
- get_transport_config() parses MCP_TRANSPORT/MCP_HOST/MCP_PORT correctly.
- Client raises ValueError for malformed method names.
"""

from __future__ import annotations

import pytest

from zabbix_mcp.app import mcp

# ── helpers ──────────────────────────────────────────────────────────────────

def _get_tools() -> dict:
    """Return {name: tool} mapping from the live FastMCP server."""
    return {t.name: t for t in mcp._tool_manager.list_tools()}


# ── coverage: expected tool names ────────────────────────────────────────────

# Every tool that should be registered (78 endpoint-aligned + 3 workflow = 86 total
# including zabbix_graph_item_get and zabbix_host_interface_get/create/update/delete)
_EXPECTED_TOOLS = [
    # Hosts
    "zabbix_host_get", "zabbix_host_create", "zabbix_host_update", "zabbix_host_delete",
    "zabbix_host_interface_get", "zabbix_host_interface_create",
    "zabbix_host_interface_update", "zabbix_host_interface_delete",
    # Host groups
    "zabbix_hostgroup_get", "zabbix_hostgroup_create",
    "zabbix_hostgroup_update", "zabbix_hostgroup_delete",
    # Items
    "zabbix_item_get", "zabbix_item_create", "zabbix_item_update", "zabbix_item_delete",
    # Triggers
    "zabbix_trigger_get", "zabbix_trigger_create",
    "zabbix_trigger_update", "zabbix_trigger_delete",
    # LLD rules
    "zabbix_lld_rule_get", "zabbix_lld_rule_create",
    "zabbix_lld_rule_update", "zabbix_lld_rule_delete",
    # LLD item prototypes
    "zabbix_lld_item_prototype_get", "zabbix_lld_item_prototype_create",
    "zabbix_lld_item_prototype_update", "zabbix_lld_item_prototype_delete",
    # LLD trigger prototypes
    "zabbix_lld_trigger_prototype_get", "zabbix_lld_trigger_prototype_create",
    "zabbix_lld_trigger_prototype_update", "zabbix_lld_trigger_prototype_delete",
    # LLD graph prototypes
    "zabbix_lld_graph_prototype_get", "zabbix_lld_graph_prototype_create",
    "zabbix_lld_graph_prototype_update", "zabbix_lld_graph_prototype_delete",
    # LLD host prototypes
    "zabbix_lld_host_prototype_get", "zabbix_lld_host_prototype_create",
    "zabbix_lld_host_prototype_update", "zabbix_lld_host_prototype_delete",
    # Graphs
    "zabbix_graph_get", "zabbix_graph_item_get",
    "zabbix_graph_create", "zabbix_graph_update", "zabbix_graph_delete",
    # Dashboards
    "zabbix_dashboard_get", "zabbix_dashboard_create",
    "zabbix_dashboard_update", "zabbix_dashboard_delete",
    "zabbix_template_dashboard_get", "zabbix_template_dashboard_create",
    "zabbix_template_dashboard_update", "zabbix_template_dashboard_delete",
    # Monitoring
    "zabbix_problem_get", "zabbix_event_get", "zabbix_history_get",
    "zabbix_trend_get", "zabbix_alert_get", "zabbix_event_acknowledge",
    # Templates
    "zabbix_template_get", "zabbix_template_create",
    "zabbix_template_update", "zabbix_template_delete",
    "zabbix_templategroup_get", "zabbix_templategroup_create",
    "zabbix_templategroup_update", "zabbix_templategroup_delete",
    # Value maps
    "zabbix_valuemap_get", "zabbix_valuemap_create",
    "zabbix_valuemap_update", "zabbix_valuemap_delete",
    # Reports
    "zabbix_report_get", "zabbix_report_create",
    "zabbix_report_update", "zabbix_report_delete",
    # Maintenances
    "zabbix_maintenance_get", "zabbix_maintenance_create",
    "zabbix_maintenance_update", "zabbix_maintenance_delete",
    # User macros
    "zabbix_usermacro_get", "zabbix_usermacro_create",
    "zabbix_usermacro_update", "zabbix_usermacro_delete",
    # Workflow
    "zabbix_host_problems_summary", "zabbix_lld_scaffold", "zabbix_template_link",
]

_READ_ONLY_TOOLS = [t for t in _EXPECTED_TOOLS if t.endswith("_get") or t in (
    "zabbix_host_problems_summary",
)]

_DELETE_TOOLS = [t for t in _EXPECTED_TOOLS if t.endswith("_delete")]

_WRITE_TOOLS = [
    t for t in _EXPECTED_TOOLS
    if not t.endswith("_get") and not t.endswith("_delete")
    and t not in ("zabbix_host_problems_summary",)
]


# ── registration tests ───────────────────────────────────────────────────────

class TestToolRegistration:
    def test_total_tool_count(self) -> None:
        tools = _get_tools()
        assert len(tools) == len(_EXPECTED_TOOLS)

    @pytest.mark.parametrize("name", _EXPECTED_TOOLS)
    def test_tool_is_registered(self, name: str) -> None:
        tools = _get_tools()
        assert name in tools, f"Tool '{name}' is not registered on the server"

    @pytest.mark.parametrize("name", _EXPECTED_TOOLS)
    def test_tool_has_description(self, name: str) -> None:
        tools = _get_tools()
        desc = tools[name].description
        assert desc and len(desc.strip()) > 10, f"Tool '{name}' has an empty or trivial description"

    @pytest.mark.parametrize("name", _EXPECTED_TOOLS)
    def test_tool_has_parameters_schema(self, name: str) -> None:
        tools = _get_tools()
        params = tools[name].parameters
        assert params is not None
        assert "properties" in params


# ── annotation tests ─────────────────────────────────────────────────────────

class TestReadOnlyAnnotations:
    @pytest.mark.parametrize("name", _READ_ONLY_TOOLS)
    def test_read_only_hint_true(self, name: str) -> None:
        tools = _get_tools()
        ann = tools[name].annotations
        assert ann.readOnlyHint is True, f"'{name}' should have readOnlyHint=True"

    @pytest.mark.parametrize("name", _READ_ONLY_TOOLS)
    def test_destructive_hint_false(self, name: str) -> None:
        tools = _get_tools()
        ann = tools[name].annotations
        assert ann.destructiveHint is False, f"'{name}' should have destructiveHint=False"

    @pytest.mark.parametrize("name", _READ_ONLY_TOOLS)
    def test_idempotent_hint_true(self, name: str) -> None:
        tools = _get_tools()
        ann = tools[name].annotations
        assert ann.idempotentHint is True, f"'{name}' should have idempotentHint=True"


class TestDeleteAnnotations:
    @pytest.mark.parametrize("name", _DELETE_TOOLS)
    def test_destructive_hint_true(self, name: str) -> None:
        tools = _get_tools()
        ann = tools[name].annotations
        assert ann.destructiveHint is True, f"'{name}' should have destructiveHint=True"

    @pytest.mark.parametrize("name", _DELETE_TOOLS)
    def test_read_only_hint_false(self, name: str) -> None:
        tools = _get_tools()
        ann = tools[name].annotations
        assert ann.readOnlyHint is False, f"'{name}' should have readOnlyHint=False"

    @pytest.mark.parametrize("name", _DELETE_TOOLS)
    def test_delete_description_warns_destructive(self, name: str) -> None:
        tools = _get_tools()
        desc = tools[name].description.upper()
        assert "DESTRUCTIVE" in desc or "PERMANENTLY" in desc or "CANNOT BE UNDONE" in desc, (
            f"'{name}' description should warn about destructive nature"
        )


class TestWriteAnnotations:
    @pytest.mark.parametrize("name", _WRITE_TOOLS)
    def test_read_only_hint_false(self, name: str) -> None:
        tools = _get_tools()
        ann = tools[name].annotations
        assert ann.readOnlyHint is False, f"'{name}' should have readOnlyHint=False"

    @pytest.mark.parametrize("name", _WRITE_TOOLS)
    def test_destructive_hint_false(self, name: str) -> None:
        tools = _get_tools()
        ann = tools[name].annotations
        assert ann.destructiveHint is False, f"'{name}' should have destructiveHint=False"


class TestClosedWorldAnnotation:
    @pytest.mark.parametrize("name", _EXPECTED_TOOLS)
    def test_open_world_hint_false(self, name: str) -> None:
        tools = _get_tools()
        ann = tools[name].annotations
        assert ann.openWorldHint is False, f"'{name}' should have openWorldHint=False"


# ── naming convention ─────────────────────────────────────────────────────────

class TestNamingConvention:
    def test_all_tools_prefixed_zabbix(self) -> None:
        tools = _get_tools()
        for name in tools:
            assert name.startswith("zabbix_"), f"Tool '{name}' does not follow zabbix_<resource>_<action> convention"

    def test_all_tool_names_use_underscores(self) -> None:
        tools = _get_tools()
        for name in tools:
            assert "-" not in name, f"Tool '{name}' uses hyphens instead of underscores"


# ── read-only mode ────────────────────────────────────────────────────────────

class TestReadOnlyMode:
    """Verify is_read_only_mode() parsing and tool annotation consistency."""

    def test_is_read_only_false_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ZABBIX_READ_ONLY", raising=False)
        from zabbix_mcp.auth import is_read_only_mode
        assert is_read_only_mode() is False

    @pytest.mark.parametrize("value", ["true", "True", "TRUE", "1", "yes"])
    def test_is_read_only_true_variants(self, monkeypatch: pytest.MonkeyPatch, value: str) -> None:
        monkeypatch.setenv("ZABBIX_READ_ONLY", value)
        from zabbix_mcp.auth import is_read_only_mode
        assert is_read_only_mode() is True

    @pytest.mark.parametrize("value", ["false", "False", "0", "no", ""])
    def test_is_read_only_false_variants(self, monkeypatch: pytest.MonkeyPatch, value: str) -> None:
        monkeypatch.setenv("ZABBIX_READ_ONLY", value)
        from zabbix_mcp.auth import is_read_only_mode
        assert is_read_only_mode() is False

    def test_write_and_delete_tools_have_read_only_hint_false(self) -> None:
        """All write/delete tools must have readOnlyHint=False so read-only mode can filter them."""
        tools = _get_tools()
        for name in _DELETE_TOOLS + _WRITE_TOOLS:
            ann = tools[name].annotations
            assert ann.readOnlyHint is False, (
                f"'{name}' has readOnlyHint=True but is a write/delete tool"
            )

    def test_read_only_tools_are_correctly_identified_by_annotation(self) -> None:
        """readOnlyHint=True tools exactly match the expected read-only set."""
        tools = _get_tools()
        annotated_read_only = {
            name for name, t in tools.items()
            if t.annotations and t.annotations.readOnlyHint
        }
        assert annotated_read_only == set(_READ_ONLY_TOOLS)

    def test_non_read_only_tools_would_be_removed_count(self) -> None:
        """The set of non-read-only tools equals write + delete tools."""
        tools = _get_tools()
        non_read_only = {
            name for name, t in tools.items()
            if not (t.annotations and t.annotations.readOnlyHint)
        }
        expected = set(_DELETE_TOOLS) | set(_WRITE_TOOLS)
        assert non_read_only == expected


# ── transport config ──────────────────────────────────────────────────────────

class TestTransportConfig:
    """Verify get_transport_config() parses environment variables correctly."""

    def test_default_transport_is_stdio(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MCP_TRANSPORT", raising=False)
        from zabbix_mcp.auth import get_transport_config
        assert get_transport_config()["transport"] == "stdio"

    @pytest.mark.parametrize("value", ["http", "sse", "stdio"])
    def test_valid_transport_values(self, monkeypatch: pytest.MonkeyPatch, value: str) -> None:
        monkeypatch.setenv("MCP_TRANSPORT", value)
        from zabbix_mcp.auth import get_transport_config
        assert get_transport_config()["transport"] == value

    def test_unknown_transport_falls_back_to_stdio(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MCP_TRANSPORT", "websocket")
        from zabbix_mcp.auth import get_transport_config
        assert get_transport_config()["transport"] == "stdio"

    def test_default_host_is_localhost(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MCP_HOST", raising=False)
        from zabbix_mcp.auth import get_transport_config
        assert get_transport_config()["host"] == "127.0.0.1"

    def test_custom_host(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MCP_HOST", "192.168.1.10")
        from zabbix_mcp.auth import get_transport_config
        assert get_transport_config()["host"] == "192.168.1.10"

    def test_default_port_is_8000(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MCP_PORT", raising=False)
        from zabbix_mcp.auth import get_transport_config
        assert get_transport_config()["port"] == 8000

    def test_custom_port(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MCP_PORT", "9090")
        from zabbix_mcp.auth import get_transport_config
        assert get_transport_config()["port"] == 9090

    def test_invalid_port_falls_back_to_8000(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MCP_PORT", "not_a_number")
        from zabbix_mcp.auth import get_transport_config
        assert get_transport_config()["port"] == 8000

    def test_transport_config_returns_all_keys(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MCP_TRANSPORT", raising=False)
        from zabbix_mcp.auth import get_transport_config
        config = get_transport_config()
        assert {"transport", "host", "port"} == set(config.keys())


# ── client method validation ──────────────────────────────────────────────────

class TestClientMethodValidation:
    async def test_invalid_method_format_raises_value_error(self, zabbix_env: dict) -> None:
        from zabbix_mcp.client import ZabbixClient
        from unittest.mock import AsyncMock, patch

        async with ZabbixClient() as client:
            with pytest.raises(ValueError, match="Invalid Zabbix method format"):
                await client.call("invalidmethod")

    async def test_valid_method_format_does_not_raise_immediately(self, zabbix_env: dict) -> None:
        """A valid dot-notation method passes format check (may fail at network level)."""
        from zabbix_mcp.client import ZabbixClient
        from unittest.mock import AsyncMock, patch

        mock_api = AsyncMock()
        mock_api.host = AsyncMock()
        mock_api.host.get = AsyncMock(return_value=[])

        with patch.object(ZabbixClient, "_connect", return_value=mock_api):
            async with ZabbixClient() as client:
                client._api = mock_api
                result = await client.call("host.get", {"output": ["hostid"]})
                assert result == []
