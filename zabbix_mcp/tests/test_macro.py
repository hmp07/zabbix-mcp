"""Tests for zabbix_mcp.tools.macro — usermacro_get."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from zabbix_mcp.tools.macro import zabbix_usermacro_get


def _mock_client(return_value: object):
    mock = AsyncMock()
    mock.call = AsyncMock(return_value=return_value)
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock)
    cm.__aexit__ = AsyncMock(return_value=None)
    return mock, patch("zabbix_mcp.tools.macro.shared_session", return_value=cm)


class TestZabbixUsermacroGet:
    async def test_returns_macros(self, zabbix_env: dict) -> None:
        expected = [{"hostmacroid": "1", "hostid": "10", "macro": "{$SNMP_COMMUNITY}", "value": "public"}]
        mock, ctx = _mock_client(expected)
        with ctx:
            result = await zabbix_usermacro_get()
        assert result == expected

    async def test_calls_correct_method(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_usermacro_get()
        assert mock.call.call_args[0][0] == "usermacro.get"

    async def test_default_globalmacro_false(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_usermacro_get()
        assert mock.call.call_args[0][1]["globalmacro"] is False

    async def test_globalmacro_true(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_usermacro_get(globalmacro=True)
        assert mock.call.call_args[0][1]["globalmacro"] is True

    async def test_filter_by_hostids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_usermacro_get(hostids=["10"])
        assert mock.call.call_args[0][1]["hostids"] == ["10"]

    async def test_filter_by_templateids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_usermacro_get(templateids=["20"])
        assert mock.call.call_args[0][1]["templateids"] == ["20"]

    async def test_filter_by_hostmacroids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_usermacro_get(hostmacroids=["1"])
        assert mock.call.call_args[0][1]["hostmacroids"] == ["1"]

    async def test_search_by_macro_name(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_usermacro_get(macro="{$SNMP")
        assert mock.call.call_args[0][1]["search"] == {"macro": "{$SNMP"}

    async def test_no_search_when_none(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_usermacro_get()
        params = mock.call.call_args[0][1]
        assert "search" not in params

    async def test_empty_results(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            result = await zabbix_usermacro_get()
        assert result == []


from zabbix_mcp.tools.macro import zabbix_usermacro_create, zabbix_usermacro_update  # noqa: E402


class TestZabbixUsermacroCreate:
    async def test_calls_usermacro_create(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"hostmacroids": ["15"]})
        with ctx:
            result = await zabbix_usermacro_create(
                hostid="1", macro="{$SNMP_COMMUNITY}", value="public",
            )
        assert mock.call.call_args[0][0] == "usermacro.create"
        assert result == {"hostmacroids": ["15"]}

    async def test_required_params_sent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_usermacro_create(hostid="1", macro="{$TIMEOUT}", value="30s")
        params = mock.call.call_args[0][1]
        assert params["hostid"] == "1"
        assert params["macro"] == "{$TIMEOUT}"
        assert params["value"] == "30s"
        assert params["type"] == 0

    async def test_secret_type(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_usermacro_create(hostid="1", macro="{$PASSWORD}", value="secret", type=1)
        assert mock.call.call_args[0][1]["type"] == 1

    async def test_optional_description(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_usermacro_create(
                hostid="1", macro="{$M}", value="v", description="My macro",
            )
        assert mock.call.call_args[0][1]["description"] == "My macro"

    async def test_no_description_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_usermacro_create(hostid="1", macro="{$M}", value="v")
        assert "description" not in mock.call.call_args[0][1]


class TestZabbixUsermacroUpdate:
    async def test_calls_usermacro_update(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"hostmacroids": ["15"]})
        with ctx:
            result = await zabbix_usermacro_update(hostmacroid="15", value="new_value")
        assert mock.call.call_args[0][0] == "usermacro.update"
        assert result == {"hostmacroids": ["15"]}

    async def test_sends_hostmacroid(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_usermacro_update(hostmacroid="42")
        assert mock.call.call_args[0][1]["hostmacroid"] == "42"

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_usermacro_update(hostmacroid="1")
        params = mock.call.call_args[0][1]
        assert "value" not in params
        assert "type" not in params
        assert "description" not in params


from zabbix_mcp.tools.macro import zabbix_usermacro_delete  # noqa: E402


class TestZabbixUsermacroDelete:
    async def test_calls_usermacro_delete(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"hostmacroids": ["15"]})
        with ctx:
            result = await zabbix_usermacro_delete(hostmacroids=["15"])
        assert mock.call.call_args[0][0] == "usermacro.delete"
        assert result == {"hostmacroids": ["15"]}

    async def test_passes_ids_as_positional(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_usermacro_delete(hostmacroids=["1", "2"])
        assert mock.call.call_args[0][1] == ["1", "2"]

    async def test_destructive_annotation(self, zabbix_env: dict) -> None:
        from zabbix_mcp.tools.macro import DELETE
        assert DELETE["destructiveHint"] is True
