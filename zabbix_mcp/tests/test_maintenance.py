"""Tests for zabbix_mcp.tools.maintenance — maintenance_get."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from zabbix_mcp.tools.maintenance import zabbix_maintenance_get


def _mock_client(return_value: object):
    mock = AsyncMock()
    mock.call = AsyncMock(return_value=return_value)
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock)
    cm.__aexit__ = AsyncMock(return_value=None)
    return mock, patch("zabbix_mcp.tools.maintenance.shared_session", return_value=cm)


class TestZabbixMaintenanceGet:
    async def test_returns_maintenances(self, zabbix_env: dict) -> None:
        expected = [{"maintenanceid": "1", "name": "Weekend maintenance", "maintenance_type": "0"}]
        mock, ctx = _mock_client(expected)
        with ctx:
            result = await zabbix_maintenance_get()
        assert result == expected

    async def test_calls_correct_method(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_maintenance_get()
        assert mock.call.call_args[0][0] == "maintenance.get"

    async def test_default_params(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_maintenance_get()
        params = mock.call.call_args[0][1]
        assert params["limit"] == 100
        assert "maintenanceid" in params["output"]

    async def test_filter_by_maintenanceids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_maintenance_get(maintenanceids=["1", "2"])
        assert mock.call.call_args[0][1]["maintenanceids"] == ["1", "2"]

    async def test_filter_by_groupids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_maintenance_get(groupids=["2"])
        assert mock.call.call_args[0][1]["groupids"] == ["2"]

    async def test_filter_by_hostids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_maintenance_get(hostids=["10"])
        assert mock.call.call_args[0][1]["hostids"] == ["10"]

    async def test_search_by_name(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_maintenance_get(name="Weekend")
        assert mock.call.call_args[0][1]["search"] == {"name": "Weekend"}

    async def test_filter_by_active_till(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_maintenance_get(active_till=1700000000)
        assert mock.call.call_args[0][1]["active_till"] == 1700000000

    async def test_empty_results(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            result = await zabbix_maintenance_get()
        assert result == []


from zabbix_mcp.tools.maintenance import zabbix_maintenance_create, zabbix_maintenance_update  # noqa: E402


class TestZabbixMaintenanceCreate:
    _timeperiods = [{"timeperiod_type": 0, "start_date": 1700000000, "period": 3600}]

    async def test_calls_maintenance_create(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"maintenanceids": ["5"]})
        with ctx:
            result = await zabbix_maintenance_create(
                name="Planned downtime",
                active_since=1700000000,
                active_till=1700003600,
                timeperiods=self._timeperiods,
            )
        assert mock.call.call_args[0][0] == "maintenance.create"
        assert result == {"maintenanceids": ["5"]}

    async def test_required_params_sent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_maintenance_create(
                name="M",
                active_since=1700000000,
                active_till=1700003600,
                timeperiods=self._timeperiods,
            )
        params = mock.call.call_args[0][1]
        assert params["name"] == "M"
        assert params["active_since"] == 1700000000
        assert params["active_till"] == 1700003600
        assert params["timeperiods"] == self._timeperiods
        assert params["maintenance_type"] == 0

    async def test_optional_hostids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_maintenance_create(
                name="M", active_since=1, active_till=2,
                timeperiods=self._timeperiods, hostids=["10"],
            )
        assert mock.call.call_args[0][1]["hostids"] == ["10"]

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_maintenance_create(
                name="M", active_since=1, active_till=2, timeperiods=self._timeperiods,
            )
        params = mock.call.call_args[0][1]
        assert "groupids" not in params
        assert "hostids" not in params
        assert "description" not in params


class TestZabbixMaintenanceUpdate:
    async def test_calls_maintenance_update(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"maintenanceids": ["5"]})
        with ctx:
            result = await zabbix_maintenance_update(maintenanceid="5", name="Updated")
        assert mock.call.call_args[0][0] == "maintenance.update"
        assert result == {"maintenanceids": ["5"]}

    async def test_sends_maintenanceid(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_maintenance_update(maintenanceid="42")
        assert mock.call.call_args[0][1]["maintenanceid"] == "42"

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_maintenance_update(maintenanceid="1")
        params = mock.call.call_args[0][1]
        assert "name" not in params
        assert "active_since" not in params
        assert "hostids" not in params


from zabbix_mcp.tools.maintenance import zabbix_maintenance_delete  # noqa: E402


class TestZabbixMaintenanceDelete:
    async def test_calls_maintenance_delete(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"maintenanceids": ["5"]})
        with ctx:
            result = await zabbix_maintenance_delete(maintenanceids=["5"])
        assert mock.call.call_args[0][0] == "maintenance.delete"
        assert result == {"maintenanceids": ["5"]}

    async def test_passes_ids_as_positional(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_maintenance_delete(maintenanceids=["1", "2"])
        assert mock.call.call_args[0][1] == ["1", "2"]

    async def test_destructive_annotation(self, zabbix_env: dict) -> None:
        from zabbix_mcp.tools.maintenance import DELETE
        assert DELETE["destructiveHint"] is True
