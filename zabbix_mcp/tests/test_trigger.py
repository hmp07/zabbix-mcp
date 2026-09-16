"""Tests for zabbix_mcp.tools.trigger — trigger_get."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from zabbix_mcp.tools.trigger import zabbix_trigger_get


def _mock_client(return_value: object):
    mock = AsyncMock()
    mock.call = AsyncMock(return_value=return_value)
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock)
    cm.__aexit__ = AsyncMock(return_value=None)
    return mock, patch("zabbix_mcp.tools.trigger.ZabbixClient", return_value=cm)


class TestZabbixTriggerGet:
    async def test_returns_triggers(self, zabbix_env: dict) -> None:
        expected = [{"triggerid": "1", "description": "High CPU", "priority": "4", "value": "1"}]
        mock, ctx = _mock_client(expected)
        with ctx:
            result = await zabbix_trigger_get()
        assert result == expected

    async def test_calls_correct_method(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_trigger_get()
        assert mock.call.call_args[0][0] == "trigger.get"

    async def test_default_params(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_trigger_get()
        params = mock.call.call_args[0][1]
        assert params["limit"] == 100
        assert "triggerid" in params["output"]

    async def test_filter_by_triggerids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_trigger_get(triggerids=["1", "2"])
        params = mock.call.call_args[0][1]
        assert params["triggerids"] == ["1", "2"]

    async def test_filter_by_hostids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_trigger_get(hostids=["10"])
        params = mock.call.call_args[0][1]
        assert params["hostids"] == ["10"]

    async def test_filter_by_groupids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_trigger_get(groupids=["2"])
        params = mock.call.call_args[0][1]
        assert params["groupids"] == ["2"]

    async def test_filter_by_templateids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_trigger_get(templateids=["20"])
        params = mock.call.call_args[0][1]
        assert params["templateids"] == ["20"]

    async def test_filter_by_status(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_trigger_get(status=0)
        params = mock.call.call_args[0][1]
        assert params["filter"]["status"] == 0

    async def test_filter_by_value_problem(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_trigger_get(value=1)
        params = mock.call.call_args[0][1]
        assert params["filter"]["value"] == 1

    async def test_filter_by_priority(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_trigger_get(priority=4)
        params = mock.call.call_args[0][1]
        assert params["filter"]["priority"] == 4

    async def test_multiple_filter_fields(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_trigger_get(status=0, value=1, priority=3)
        params = mock.call.call_args[0][1]
        assert params["filter"] == {"status": 0, "value": 1, "priority": 3}

    async def test_no_filter_when_none(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_trigger_get()
        params = mock.call.call_args[0][1]
        assert "filter" not in params

    async def test_only_true(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_trigger_get(only_true=True)
        params = mock.call.call_args[0][1]
        assert params["only_true"] == 1

    async def test_search_by_name(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_trigger_get(name="CPU")
        params = mock.call.call_args[0][1]
        assert params["search"] == {"description": "CPU"}

    async def test_empty_results(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            result = await zabbix_trigger_get()
        assert result == []


from zabbix_mcp.tools.trigger import zabbix_trigger_create, zabbix_trigger_update  # noqa: E402


class TestZabbixTriggerCreate:
    async def test_calls_trigger_create(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"triggerids": ["10"]})
        with ctx:
            result = await zabbix_trigger_create(
                description="High CPU on {HOST.NAME}",
                expression="last(/web/system.cpu.util)>90",
            )
        assert mock.call.call_args[0][0] == "trigger.create"
        assert result == {"triggerids": ["10"]}

    async def test_required_params_sent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_trigger_create(
                description="High CPU",
                expression="last(/h/k)>90",
            )
        params = mock.call.call_args[0][1]
        assert params["description"] == "High CPU"
        assert params["expression"] == "last(/h/k)>90"
        assert params["priority"] == 2
        assert params["status"] == 0

    async def test_optional_tags(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_trigger_create(
                description="T",
                expression="last(/h/k)>1",
                tags=[{"tag": "scope", "value": "perf"}],
            )
        params = mock.call.call_args[0][1]
        assert params["tags"] == [{"tag": "scope", "value": "perf"}]

    async def test_optional_recovery_expression(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_trigger_create(
                description="T",
                expression="last(/h/k)>90",
                recovery_mode=1,
                recovery_expression="last(/h/k)<80",
            )
        params = mock.call.call_args[0][1]
        assert params["recovery_mode"] == 1
        assert params["recovery_expression"] == "last(/h/k)<80"

    async def test_no_optional_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_trigger_create(description="T", expression="last(/h/k)>1")
        params = mock.call.call_args[0][1]
        assert "tags" not in params
        assert "dependencies" not in params
        assert "comments" not in params
        assert "url" not in params


class TestZabbixTriggerUpdate:
    async def test_calls_trigger_update(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"triggerids": ["10"]})
        with ctx:
            result = await zabbix_trigger_update(triggerid="10", status=1)
        assert mock.call.call_args[0][0] == "trigger.update"
        assert result == {"triggerids": ["10"]}

    async def test_sends_triggerid(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_trigger_update(triggerid="42")
        params = mock.call.call_args[0][1]
        assert params["triggerid"] == "42"

    async def test_optional_fields_sent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_trigger_update(triggerid="1", description="New name", priority=4)
        params = mock.call.call_args[0][1]
        assert params["description"] == "New name"
        assert params["priority"] == 4

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_trigger_update(triggerid="1")
        params = mock.call.call_args[0][1]
        assert "description" not in params
        assert "expression" not in params
        assert "status" not in params


from zabbix_mcp.tools.trigger import zabbix_trigger_delete  # noqa: E402


class TestZabbixTriggerDelete:
    async def test_calls_trigger_delete(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"triggerids": ["10"]})
        with ctx:
            result = await zabbix_trigger_delete(triggerids=["10"])
        assert mock.call.call_args[0][0] == "trigger.delete"
        assert result == {"triggerids": ["10"]}

    async def test_passes_ids_as_positional(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_trigger_delete(triggerids=["1", "2"])
        assert mock.call.call_args[0][1] == ["1", "2"]

    async def test_destructive_annotation(self, zabbix_env: dict) -> None:
        from zabbix_mcp.tools.trigger import DELETE
        assert DELETE["destructiveHint"] is True
