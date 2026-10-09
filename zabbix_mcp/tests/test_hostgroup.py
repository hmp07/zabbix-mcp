"""Tests for zabbix_mcp.tools.hostgroup — hostgroup_get."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from zabbix_mcp.tools.hostgroup import zabbix_hostgroup_get


def _mock_client(return_value: object):
    mock = AsyncMock()
    mock.call = AsyncMock(return_value=return_value)
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock)
    cm.__aexit__ = AsyncMock(return_value=None)
    return mock, patch("zabbix_mcp.tools.hostgroup.shared_session", return_value=cm)


class TestZabbixHostgroupGet:
    async def test_returns_groups(self, zabbix_env: dict) -> None:
        expected = [{"groupid": "2", "name": "Linux servers"}]
        mock, ctx = _mock_client(expected)
        with ctx:
            result = await zabbix_hostgroup_get()
        assert result == expected

    async def test_calls_correct_method(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_hostgroup_get()
        assert mock.call.call_args[0][0] == "hostgroup.get"

    async def test_default_params(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_hostgroup_get()
        params = mock.call.call_args[0][1]
        assert params["output"] == ["groupid", "name"]
        assert params["limit"] == 100

    async def test_filter_by_groupids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_hostgroup_get(groupids=["2", "3"])
        params = mock.call.call_args[0][1]
        assert params["groupids"] == ["2", "3"]

    async def test_filter_by_hostids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_hostgroup_get(hostids=["1"])
        params = mock.call.call_args[0][1]
        assert params["hostids"] == ["1"]

    async def test_filter_by_templateids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_hostgroup_get(templateids=["10"])
        params = mock.call.call_args[0][1]
        assert params["templateids"] == ["10"]

    async def test_search_by_name(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_hostgroup_get(name="Linux")
        params = mock.call.call_args[0][1]
        assert params["search"] == {"name": "Linux"}

    async def test_real_hosts_true(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_hostgroup_get(real_hosts=True)
        params = mock.call.call_args[0][1]
        assert params["real_hosts"] == 1

    async def test_real_hosts_false(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_hostgroup_get(real_hosts=False)
        params = mock.call.call_args[0][1]
        assert params["real_hosts"] == 0

    async def test_real_hosts_none_not_in_params(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_hostgroup_get()
        params = mock.call.call_args[0][1]
        assert "real_hosts" not in params

    async def test_empty_results(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            result = await zabbix_hostgroup_get()
        assert result == []


from zabbix_mcp.tools.hostgroup import zabbix_hostgroup_create, zabbix_hostgroup_update  # noqa: E402


class TestZabbixHostgroupCreate:
    async def test_calls_hostgroup_create(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"groupids": ["6"]})
        with ctx:
            result = await zabbix_hostgroup_create(name="Linux Servers")
        assert mock.call.call_args[0][0] == "hostgroup.create"
        assert result == {"groupids": ["6"]}

    async def test_sends_name(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_hostgroup_create(name="Windows Servers")
        assert mock.call.call_args[0][1]["name"] == "Windows Servers"


class TestZabbixHostgroupUpdate:
    async def test_calls_hostgroup_update(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"groupids": ["6"]})
        with ctx:
            result = await zabbix_hostgroup_update(groupid="6", name="Updated Group")
        assert mock.call.call_args[0][0] == "hostgroup.update"
        assert result == {"groupids": ["6"]}

    async def test_sends_groupid_and_name(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_hostgroup_update(groupid="6", name="Renamed")
        params = mock.call.call_args[0][1]
        assert params["groupid"] == "6"
        assert params["name"] == "Renamed"


from zabbix_mcp.tools.hostgroup import zabbix_hostgroup_delete  # noqa: E402


class TestZabbixHostgroupDelete:
    async def test_calls_hostgroup_delete(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"groupids": ["6"]})
        with ctx:
            result = await zabbix_hostgroup_delete(groupids=["6"])
        assert mock.call.call_args[0][0] == "hostgroup.delete"
        assert result == {"groupids": ["6"]}

    async def test_passes_ids_as_positional(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_hostgroup_delete(groupids=["1", "2"])
        assert mock.call.call_args[0][1] == ["1", "2"]

    async def test_destructive_annotation(self, zabbix_env: dict) -> None:
        from zabbix_mcp.tools.hostgroup import DELETE
        assert DELETE["destructiveHint"] is True
