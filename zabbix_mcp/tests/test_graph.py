"""Tests for zabbix_mcp.tools.graph — graph_get and graph_item_get."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from zabbix_mcp.tools.graph import zabbix_graph_get, zabbix_graph_item_get


def _mock_client(return_value: object):
    mock = AsyncMock()
    mock.call = AsyncMock(return_value=return_value)
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock)
    cm.__aexit__ = AsyncMock(return_value=None)
    return mock, patch("zabbix_mcp.tools.graph.ZabbixClient", return_value=cm)


class TestZabbixGraphGet:
    async def test_returns_graphs(self, zabbix_env: dict) -> None:
        expected = [{"graphid": "1", "name": "CPU load", "width": "900", "height": "200"}]
        mock, ctx = _mock_client(expected)
        with ctx:
            result = await zabbix_graph_get()
        assert result == expected

    async def test_calls_correct_method(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_graph_get()
        assert mock.call.call_args[0][0] == "graph.get"

    async def test_filter_by_graphids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_graph_get(graphids=["1", "2"])
        assert mock.call.call_args[0][1]["graphids"] == ["1", "2"]

    async def test_filter_by_hostids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_graph_get(hostids=["10"])
        assert mock.call.call_args[0][1]["hostids"] == ["10"]

    async def test_filter_by_groupids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_graph_get(groupids=["2"])
        assert mock.call.call_args[0][1]["groupids"] == ["2"]

    async def test_filter_by_templateids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_graph_get(templateids=["20"])
        assert mock.call.call_args[0][1]["templateids"] == ["20"]

    async def test_search_by_name(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_graph_get(name="CPU")
        assert mock.call.call_args[0][1]["search"] == {"name": "CPU"}

    async def test_empty_results(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            result = await zabbix_graph_get()
        assert result == []


class TestZabbixGraphItemGet:
    async def test_returns_graph_items(self, zabbix_env: dict) -> None:
        expected = [{"gitemid": "10", "graphid": "1", "itemid": "100", "color": "FF0000"}]
        mock, ctx = _mock_client(expected)
        with ctx:
            result = await zabbix_graph_item_get(graphids=["1"])
        assert result == expected

    async def test_calls_correct_method(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_graph_item_get()
        assert mock.call.call_args[0][0] == "graphitem.get"

    async def test_filter_by_graphids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_graph_item_get(graphids=["1", "2"])
        assert mock.call.call_args[0][1]["graphids"] == ["1", "2"]

    async def test_filter_by_itemids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_graph_item_get(itemids=["100"])
        assert mock.call.call_args[0][1]["itemids"] == ["100"]

    async def test_no_filter_passes_no_ids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_graph_item_get()
        params = mock.call.call_args[0][1]
        assert "graphids" not in params
        assert "itemids" not in params


from zabbix_mcp.tools.graph import zabbix_graph_create, zabbix_graph_update  # noqa: E402


class TestZabbixGraphCreate:
    async def test_calls_graph_create(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"graphids": ["5"]})
        gitems = [{"itemid": "100", "color": "FF0000", "drawtype": 0, "sortorder": 0}]
        with ctx:
            result = await zabbix_graph_create(name="CPU graph", gitems=gitems)
        assert mock.call.call_args[0][0] == "graph.create"
        assert result == {"graphids": ["5"]}

    async def test_default_params(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        gitems = [{"itemid": "1", "color": "00FF00", "drawtype": 0, "sortorder": 0}]
        with ctx:
            await zabbix_graph_create(name="G", gitems=gitems)
        params = mock.call.call_args[0][1]
        assert params["name"] == "G"
        assert params["gitems"] == gitems
        assert params["width"] == 900
        assert params["height"] == 200
        assert params["graphtype"] == 0
        assert params["show_legend"] == 1

    async def test_custom_type_maps_to_graphtype(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_graph_create(name="G", gitems=[{"itemid": "1", "color": "0", "drawtype": 0, "sortorder": 0}], type=2)
        params = mock.call.call_args[0][1]
        assert params["graphtype"] == 2
        assert "type" not in params


class TestZabbixGraphUpdate:
    async def test_calls_graph_update(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"graphids": ["5"]})
        with ctx:
            result = await zabbix_graph_update(graphid="5", name="New name")
        assert mock.call.call_args[0][0] == "graph.update"
        assert result == {"graphids": ["5"]}

    async def test_sends_graphid(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_graph_update(graphid="99")
        params = mock.call.call_args[0][1]
        assert params["graphid"] == "99"

    async def test_optional_type_maps_to_graphtype(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_graph_update(graphid="1", type=1)
        params = mock.call.call_args[0][1]
        assert params["graphtype"] == 1
        assert "type" not in params

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_graph_update(graphid="1")
        params = mock.call.call_args[0][1]
        assert "name" not in params
        assert "gitems" not in params
        assert "width" not in params


from zabbix_mcp.tools.graph import zabbix_graph_delete  # noqa: E402


class TestZabbixGraphDelete:
    async def test_calls_graph_delete(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"graphids": ["5"]})
        with ctx:
            result = await zabbix_graph_delete(graphids=["5"])
        assert mock.call.call_args[0][0] == "graph.delete"
        assert result == {"graphids": ["5"]}

    async def test_passes_ids_as_positional(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_graph_delete(graphids=["1", "2"])
        assert mock.call.call_args[0][1] == ["1", "2"]

    async def test_destructive_annotation(self, zabbix_env: dict) -> None:
        from zabbix_mcp.tools.graph import _DELETE
        assert _DELETE["destructiveHint"] is True
