"""Tests for zabbix_mcp.tools.item — item_get."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from zabbix_mcp.tools.item import zabbix_item_get


def _mock_client(return_value: object):
    mock = AsyncMock()
    mock.call = AsyncMock(return_value=return_value)
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock)
    cm.__aexit__ = AsyncMock(return_value=None)
    return mock, patch("zabbix_mcp.tools.item.ZabbixClient", return_value=cm)


class TestZabbixItemGet:
    async def test_returns_items(self, zabbix_env: dict) -> None:
        expected = [{"itemid": "10", "hostid": "1", "name": "CPU load", "key_": "system.cpu.load"}]
        mock, ctx = _mock_client(expected)
        with ctx:
            result = await zabbix_item_get()
        assert result == expected

    async def test_calls_correct_method(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_item_get()
        assert mock.call.call_args[0][0] == "item.get"

    async def test_filter_by_itemids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_item_get(itemids=["10", "11"])
        params = mock.call.call_args[0][1]
        assert params["itemids"] == ["10", "11"]

    async def test_filter_by_hostids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_item_get(hostids=["1"])
        params = mock.call.call_args[0][1]
        assert params["hostids"] == ["1"]

    async def test_filter_by_groupids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_item_get(groupids=["2"])
        params = mock.call.call_args[0][1]
        assert params["groupids"] == ["2"]

    async def test_filter_by_status(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_item_get(status=0)
        params = mock.call.call_args[0][1]
        assert params["filter"] == {"status": 0}

    async def test_search_by_name(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_item_get(name="CPU")
        params = mock.call.call_args[0][1]
        assert params["search"]["name"] == "CPU"

    async def test_search_by_key(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_item_get(key_="system.cpu")
        params = mock.call.call_args[0][1]
        assert params["search"]["key_"] == "system.cpu"

    async def test_search_by_name_and_key(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_item_get(name="CPU", key_="system.cpu")
        params = mock.call.call_args[0][1]
        assert params["search"] == {"name": "CPU", "key_": "system.cpu"}

    async def test_no_search_when_none(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_item_get()
        params = mock.call.call_args[0][1]
        assert "search" not in params

    async def test_empty_results(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            result = await zabbix_item_get()
        assert result == []


from zabbix_mcp.tools.item import zabbix_item_create, zabbix_item_update  # noqa: E402


class TestZabbixItemCreate:
    async def test_calls_item_create(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"itemids": ["50"]})
        with ctx:
            result = await zabbix_item_create(
                hostid="1", name="CPU utilization", key_="system.cpu.util",
                type=0, value_type=0,
            )
        assert mock.call.call_args[0][0] == "item.create"
        assert result == {"itemids": ["50"]}

    async def test_required_params_sent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_item_create(
                hostid="1", name="CPU", key_="system.cpu.util", type=0, value_type=0,
            )
        params = mock.call.call_args[0][1]
        assert params["hostid"] == "1"
        assert params["name"] == "CPU"
        assert params["key_"] == "system.cpu.util"
        assert params["type"] == 0
        assert params["value_type"] == 0

    async def test_optional_units(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_item_create(
                hostid="1", name="CPU", key_="k", type=0, value_type=0, units="%",
            )
        assert mock.call.call_args[0][1]["units"] == "%"

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_item_create(hostid="1", name="N", key_="k", type=0, value_type=0)
        params = mock.call.call_args[0][1]
        assert "interfaceid" not in params
        assert "units" not in params
        assert "tags" not in params
        assert "description" not in params


class TestZabbixItemUpdate:
    async def test_calls_item_update(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"itemids": ["50"]})
        with ctx:
            result = await zabbix_item_update(itemid="50", delay="5m")
        assert mock.call.call_args[0][0] == "item.update"
        assert result == {"itemids": ["50"]}

    async def test_sends_itemid(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_item_update(itemid="77")
        assert mock.call.call_args[0][1]["itemid"] == "77"

    async def test_optional_fields_sent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_item_update(itemid="1", name="New name", status=1)
        params = mock.call.call_args[0][1]
        assert params["name"] == "New name"
        assert params["status"] == 1

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_item_update(itemid="1")
        params = mock.call.call_args[0][1]
        assert "name" not in params
        assert "key_" not in params
        assert "units" not in params


from zabbix_mcp.tools.item import zabbix_item_delete  # noqa: E402


class TestZabbixItemDelete:
    async def test_calls_item_delete(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"itemids": ["50"]})
        with ctx:
            result = await zabbix_item_delete(itemids=["50"])
        assert mock.call.call_args[0][0] == "item.delete"
        assert result == {"itemids": ["50"]}

    async def test_passes_ids_as_positional(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_item_delete(itemids=["1", "2"])
        assert mock.call.call_args[0][1] == ["1", "2"]

    async def test_destructive_annotation(self, zabbix_env: dict) -> None:
        from zabbix_mcp.tools.item import _DELETE
        assert _DELETE["destructiveHint"] is True
