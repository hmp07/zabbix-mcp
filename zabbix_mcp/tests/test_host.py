"""Tests for zabbix_mcp.tools.host — host_get and host_interface_get."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from zabbix_mcp.tools.host import zabbix_host_get, zabbix_host_interface_get
from zabbix_mcp.errors import ZabbixAuthError


def _mock_client(return_value: object):
    mock = AsyncMock()
    mock.call = AsyncMock(return_value=return_value)
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock)
    cm.__aexit__ = AsyncMock(return_value=None)
    return mock, patch("zabbix_mcp.tools.host.ZabbixClient", return_value=cm)


class TestZabbixHostGet:
    async def test_returns_hosts(self, zabbix_env: dict) -> None:
        expected = [{"hostid": "1", "host": "server1", "name": "Server 1", "status": "0"}]
        mock, ctx = _mock_client(expected)
        with ctx:
            result = await zabbix_host_get()
        assert result == expected

    async def test_default_params(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_host_get()
        mock.call.assert_awaited_once_with("host.get", {
            "output": ["hostid", "host", "name", "status"],
            "limit": 100,
        })

    async def test_filter_by_hostids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_host_get(hostids=["1", "2"])
        params = mock.call.call_args[0][1]
        assert params["hostids"] == ["1", "2"]

    async def test_filter_by_groupids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_host_get(groupids=["5"])
        params = mock.call.call_args[0][1]
        assert params["groupids"] == ["5"]

    async def test_filter_by_templateids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_host_get(templateids=["10"])
        params = mock.call.call_args[0][1]
        assert params["templateids"] == ["10"]

    async def test_filter_by_status(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_host_get(status=0)
        params = mock.call.call_args[0][1]
        assert params["filter"] == {"status": 0}

    async def test_search_by_name(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_host_get(name="web")
        params = mock.call.call_args[0][1]
        assert params["search"] == {"name": "web"}

    async def test_custom_limit(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_host_get(limit=50)
        params = mock.call.call_args[0][1]
        assert params["limit"] == 50

    async def test_custom_output(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_host_get(output=["hostid", "host", "interfaces"])
        params = mock.call.call_args[0][1]
        assert params["output"] == ["hostid", "host", "interfaces"]

    async def test_empty_results(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            result = await zabbix_host_get()
        assert result == []

    async def test_propagates_auth_error(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client(None)
        mock.call.side_effect = ZabbixAuthError("Not authorized")
        with ctx:
            with pytest.raises(ZabbixAuthError):
                await zabbix_host_get()


class TestZabbixHostInterfaceGet:
    async def test_returns_interfaces(self, zabbix_env: dict) -> None:
        expected = [{"interfaceid": "1", "hostid": "1", "ip": "192.168.1.10", "port": "10050"}]
        mock, ctx = _mock_client(expected)
        with ctx:
            result = await zabbix_host_interface_get(hostids=["1"])
        assert result == expected

    async def test_calls_correct_method(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_host_interface_get()
        assert mock.call.call_args[0][0] == "hostinterface.get"

    async def test_filter_by_hostids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_host_interface_get(hostids=["1", "2"])
        params = mock.call.call_args[0][1]
        assert params["hostids"] == ["1", "2"]

    async def test_filter_by_type(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_host_interface_get(type=2)
        params = mock.call.call_args[0][1]
        assert params["filter"] == {"type": 2}

    async def test_filter_by_interfaceids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_host_interface_get(interfaceids=["10"])
        params = mock.call.call_args[0][1]
        assert params["interfaceids"] == ["10"]


from zabbix_mcp.tools.host import (  # noqa: E402
    zabbix_host_create,
    zabbix_host_update,
    zabbix_host_interface_create,
    zabbix_host_interface_update,
)


class TestZabbixHostCreate:
    async def test_calls_host_create(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"hostids": ["10"]})
        with ctx:
            result = await zabbix_host_create(
                host="web-server-01",
                groups=[{"groupid": "2"}],
                interfaces=[{"type": 1, "main": 1, "useip": 1, "ip": "192.168.1.10", "dns": "", "port": "10050"}],
            )
        assert mock.call.call_args[0][0] == "host.create"
        assert result == {"hostids": ["10"]}

    async def test_required_params_sent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        iface = [{"type": 1, "main": 1, "useip": 1, "ip": "10.0.0.1", "dns": "", "port": "10050"}]
        with ctx:
            await zabbix_host_create(host="h", groups=[{"groupid": "1"}], interfaces=iface)
        params = mock.call.call_args[0][1]
        assert params["host"] == "h"
        assert params["groups"] == [{"groupid": "1"}]
        assert params["interfaces"] == iface

    async def test_optional_templates(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_host_create(
                host="h", groups=[{"groupid": "1"}],
                templates=[{"templateid": "10"}],
            )
        assert mock.call.call_args[0][1]["templates"] == [{"templateid": "10"}]

    async def test_default_status_enabled(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_host_create(host="h", groups=[{"groupid": "1"}])
        assert mock.call.call_args[0][1]["status"] == 0

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_host_create(host="h", groups=[{"groupid": "1"}])
        params = mock.call.call_args[0][1]
        assert "interfaces" not in params
        assert "templates" not in params
        assert "inventory_mode" not in params


class TestZabbixHostUpdate:
    async def test_calls_host_update(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"hostids": ["10"]})
        with ctx:
            result = await zabbix_host_update(hostid="10", status=1)
        assert mock.call.call_args[0][0] == "host.update"
        assert result == {"hostids": ["10"]}

    async def test_sends_hostid(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_host_update(hostid="42")
        assert mock.call.call_args[0][1]["hostid"] == "42"

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_host_update(hostid="1")
        params = mock.call.call_args[0][1]
        assert "host" not in params
        assert "templates" not in params
        assert "status" not in params


class TestZabbixHostInterfaceCreate:
    async def test_calls_hostinterface_create(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"interfaceids": ["5"]})
        with ctx:
            result = await zabbix_host_interface_create(
                hostid="10", type=1, main=1, useip=1,
                ip="192.168.1.1", dns="", port="10050",
            )
        assert mock.call.call_args[0][0] == "hostinterface.create"
        assert result == {"interfaceids": ["5"]}

    async def test_required_params_sent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_host_interface_create(
                hostid="10", type=1, main=1, useip=1, ip="1.2.3.4", dns="", port="10050",
            )
        params = mock.call.call_args[0][1]
        assert params["hostid"] == "10"
        assert params["type"] == 1
        assert params["ip"] == "1.2.3.4"
        assert params["port"] == "10050"


class TestZabbixHostInterfaceUpdate:
    async def test_calls_hostinterface_update(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"interfaceids": ["5"]})
        with ctx:
            result = await zabbix_host_interface_update(interfaceid="5", port="161")
        assert mock.call.call_args[0][0] == "hostinterface.update"
        assert result == {"interfaceids": ["5"]}

    async def test_sends_interfaceid(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_host_interface_update(interfaceid="99")
        assert mock.call.call_args[0][1]["interfaceid"] == "99"

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_host_interface_update(interfaceid="1")
        params = mock.call.call_args[0][1]
        assert "ip" not in params
        assert "port" not in params
        assert "dns" not in params


from zabbix_mcp.tools.host import zabbix_host_delete, zabbix_host_interface_delete  # noqa: E402


class TestZabbixHostDelete:
    async def test_calls_host_delete(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"hostids": ["10", "11"]})
        with ctx:
            result = await zabbix_host_delete(hostids=["10", "11"])
        assert mock.call.call_args[0][0] == "host.delete"
        assert result == {"hostids": ["10", "11"]}

    async def test_passes_ids_as_positional(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_host_delete(hostids=["5"])
        assert mock.call.call_args[0][1] == ["5"]

    async def test_destructive_annotation(self, zabbix_env: dict) -> None:
        from zabbix_mcp.tools.host import DELETE
        assert DELETE["destructiveHint"] is True


class TestZabbixHostInterfaceDelete:
    async def test_calls_hostinterface_delete(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"interfaceids": ["3"]})
        with ctx:
            result = await zabbix_host_interface_delete(interfaceids=["3"])
        assert mock.call.call_args[0][0] == "hostinterface.delete"
        assert result == {"interfaceids": ["3"]}

    async def test_passes_ids_as_positional(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_host_interface_delete(interfaceids=["3"])
        assert mock.call.call_args[0][1] == ["3"]
