"""Tests for zabbix_mcp.tools.monitoring — problem, event, history, trend, alert."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from zabbix_mcp.tools.monitoring import (
    zabbix_alert_get,
    zabbix_event_get,
    zabbix_history_get,
    zabbix_problem_get,
    zabbix_trend_get,
)


def _mock_client(return_value: object):
    mock = AsyncMock()
    mock.call = AsyncMock(return_value=return_value)
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock)
    cm.__aexit__ = AsyncMock(return_value=None)
    return mock, patch("zabbix_mcp.tools.monitoring.ZabbixClient", return_value=cm)


class TestZabbixProblemGet:
    async def test_returns_problems(self, zabbix_env: dict) -> None:
        expected = [{"eventid": "1", "name": "High CPU", "severity": "4"}]
        mock, ctx = _mock_client(expected)
        with ctx:
            result = await zabbix_problem_get()
        assert result == expected

    async def test_calls_correct_method(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_problem_get()
        assert mock.call.call_args[0][0] == "problem.get"

    async def test_filter_by_hostids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_problem_get(hostids=["1"])
        assert mock.call.call_args[0][1]["hostids"] == ["1"]

    async def test_filter_by_groupids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_problem_get(groupids=["2"])
        assert mock.call.call_args[0][1]["groupids"] == ["2"]

    async def test_filter_by_severities(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_problem_get(severities=[3, 4, 5])
        assert mock.call.call_args[0][1]["severities"] == [3, 4, 5]

    async def test_filter_by_time_range(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_problem_get(time_from=1700000000, time_till=1700100000)
        params = mock.call.call_args[0][1]
        assert params["time_from"] == 1700000000
        assert params["time_till"] == 1700100000

    async def test_recent_flag(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_problem_get(recent=True)
        assert mock.call.call_args[0][1]["recent"] is True

    async def test_filter_by_objectids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_problem_get(objectids=["100"])
        assert mock.call.call_args[0][1]["objectids"] == ["100"]


class TestZabbixEventGet:
    async def test_returns_events(self, zabbix_env: dict) -> None:
        expected = [{"eventid": "10", "name": "CPU", "value": "1", "severity": "4"}]
        mock, ctx = _mock_client(expected)
        with ctx:
            result = await zabbix_event_get()
        assert result == expected

    async def test_calls_correct_method(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_event_get()
        assert mock.call.call_args[0][0] == "event.get"

    async def test_filter_by_value(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_event_get(value=1)
        assert mock.call.call_args[0][1]["value"] == 1

    async def test_filter_by_severities(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_event_get(severities=[4, 5])
        assert mock.call.call_args[0][1]["severities"] == [4, 5]

    async def test_filter_by_time_range(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_event_get(time_from=1700000000, time_till=1700100000)
        params = mock.call.call_args[0][1]
        assert params["time_from"] == 1700000000
        assert params["time_till"] == 1700100000

    async def test_filter_by_hostids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_event_get(hostids=["1"])
        assert mock.call.call_args[0][1]["hostids"] == ["1"]


class TestZabbixHistoryGet:
    async def test_returns_history(self, zabbix_env: dict) -> None:
        expected = [{"itemid": "100", "clock": "1700000000", "value": "42.5"}]
        mock, ctx = _mock_client(expected)
        with ctx:
            result = await zabbix_history_get(itemids=["100"])
        assert result == expected

    async def test_calls_correct_method(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_history_get(itemids=["100"])
        assert mock.call.call_args[0][0] == "history.get"

    async def test_passes_itemids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_history_get(itemids=["100", "101"])
        assert mock.call.call_args[0][1]["itemids"] == ["100", "101"]

    async def test_default_history_type(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_history_get(itemids=["100"])
        assert mock.call.call_args[0][1]["history"] == 3

    async def test_custom_history_type(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_history_get(itemids=["100"], history=0)
        assert mock.call.call_args[0][1]["history"] == 0

    async def test_time_range(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_history_get(itemids=["100"], time_from=1700000000, time_till=1700100000)
        params = mock.call.call_args[0][1]
        assert params["time_from"] == 1700000000
        assert params["time_till"] == 1700100000

    async def test_default_sort_order_desc(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_history_get(itemids=["100"])
        params = mock.call.call_args[0][1]
        assert params["sortorder"] == "DESC"
        assert params["sortfield"] == "clock"


class TestZabbixTrendGet:
    async def test_returns_trends(self, zabbix_env: dict) -> None:
        expected = [{"itemid": "100", "clock": "1700000000", "value_avg": "50.0"}]
        mock, ctx = _mock_client(expected)
        with ctx:
            result = await zabbix_trend_get(itemids=["100"])
        assert result == expected

    async def test_calls_correct_method(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_trend_get(itemids=["100"])
        assert mock.call.call_args[0][0] == "trend.get"

    async def test_passes_itemids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_trend_get(itemids=["100", "101"])
        assert mock.call.call_args[0][1]["itemids"] == ["100", "101"]

    async def test_default_type(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_trend_get(itemids=["100"])
        assert mock.call.call_args[0][1]["type"] == 3

    async def test_time_range(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_trend_get(itemids=["100"], time_from=1700000000, time_till=1700100000)
        params = mock.call.call_args[0][1]
        assert params["time_from"] == 1700000000
        assert params["time_till"] == 1700100000


class TestZabbixAlertGet:
    async def test_returns_alerts(self, zabbix_env: dict) -> None:
        expected = [{"alertid": "1", "eventid": "10", "sendto": "admin@example.com", "status": "1"}]
        mock, ctx = _mock_client(expected)
        with ctx:
            result = await zabbix_alert_get()
        assert result == expected

    async def test_calls_correct_method(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_alert_get()
        assert mock.call.call_args[0][0] == "alert.get"

    async def test_filter_by_eventids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_alert_get(eventids=["10"])
        assert mock.call.call_args[0][1]["eventids"] == ["10"]

    async def test_filter_by_hostids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_alert_get(hostids=["1"])
        assert mock.call.call_args[0][1]["hostids"] == ["1"]

    async def test_filter_by_mediatypeids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_alert_get(mediatypeids=["3"])
        assert mock.call.call_args[0][1]["mediatypeids"] == ["3"]

    async def test_filter_by_time_range(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_alert_get(time_from=1700000000, time_till=1700100000)
        params = mock.call.call_args[0][1]
        assert params["time_from"] == 1700000000
        assert params["time_till"] == 1700100000

    async def test_empty_results(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            result = await zabbix_alert_get()
        assert result == []


from zabbix_mcp.tools.monitoring import zabbix_event_acknowledge  # noqa: E402


class TestZabbixEventAcknowledge:
    async def test_calls_event_acknowledge(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"eventids": ["100"]})
        with ctx:
            result = await zabbix_event_acknowledge(eventids=["100"], action=2)
        assert mock.call.call_args[0][0] == "event.acknowledge"
        assert result == {"eventids": ["100"]}

    async def test_required_params_sent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_event_acknowledge(eventids=["1", "2"], action=6)
        params = mock.call.call_args[0][1]
        assert params["eventids"] == ["1", "2"]
        assert params["action"] == 6

    async def test_optional_message(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_event_acknowledge(eventids=["1"], action=4, message="Acknowledged")
        assert mock.call.call_args[0][1]["message"] == "Acknowledged"

    async def test_optional_severity(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_event_acknowledge(eventids=["1"], action=8, severity=3)
        assert mock.call.call_args[0][1]["severity"] == 3

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_event_acknowledge(eventids=["1"], action=2)
        params = mock.call.call_args[0][1]
        assert "message" not in params
        assert "severity" not in params
