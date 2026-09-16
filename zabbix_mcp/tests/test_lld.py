"""Tests for zabbix_mcp.tools.lld — all LLD _get tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from zabbix_mcp.tools.lld import (
    zabbix_lld_graph_prototype_get,
    zabbix_lld_host_prototype_get,
    zabbix_lld_item_prototype_get,
    zabbix_lld_rule_get,
    zabbix_lld_trigger_prototype_get,
)


def _mock_client(module_path: str, return_value: object):
    mock = AsyncMock()
    mock.call = AsyncMock(return_value=return_value)
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock)
    cm.__aexit__ = AsyncMock(return_value=None)
    return mock, patch(f"zabbix_mcp.tools.lld.ZabbixClient", return_value=cm)


class TestZabbixLldRuleGet:
    async def test_returns_rules(self, zabbix_env: dict) -> None:
        expected = [{"itemid": "100", "hostid": "1", "name": "Discover filesystems", "key_": "vfs.fs.discovery"}]
        mock, ctx = _mock_client("lld", expected)
        with ctx:
            result = await zabbix_lld_rule_get()
        assert result == expected

    async def test_calls_discoveryrule_get(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", [])
        with ctx:
            await zabbix_lld_rule_get()
        assert mock.call.call_args[0][0] == "discoveryrule.get"

    async def test_filter_by_itemids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", [])
        with ctx:
            await zabbix_lld_rule_get(itemids=["100"])
        assert mock.call.call_args[0][1]["itemids"] == ["100"]

    async def test_filter_by_hostids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", [])
        with ctx:
            await zabbix_lld_rule_get(hostids=["1"])
        assert mock.call.call_args[0][1]["hostids"] == ["1"]

    async def test_filter_by_templateids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", [])
        with ctx:
            await zabbix_lld_rule_get(templateids=["20"])
        assert mock.call.call_args[0][1]["templateids"] == ["20"]

    async def test_filter_by_status(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", [])
        with ctx:
            await zabbix_lld_rule_get(status=0)
        assert mock.call.call_args[0][1]["filter"] == {"status": 0}

    async def test_search_by_name(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", [])
        with ctx:
            await zabbix_lld_rule_get(name="filesystem")
        assert mock.call.call_args[0][1]["search"]["name"] == "filesystem"

    async def test_search_by_key(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", [])
        with ctx:
            await zabbix_lld_rule_get(key_="vfs.fs")
        assert mock.call.call_args[0][1]["search"]["key_"] == "vfs.fs"


class TestZabbixLldItemPrototypeGet:
    async def test_returns_prototypes(self, zabbix_env: dict) -> None:
        expected = [{"itemid": "200", "name": "Free space on {#FSNAME}"}]
        mock, ctx = _mock_client("lld", expected)
        with ctx:
            result = await zabbix_lld_item_prototype_get()
        assert result == expected

    async def test_calls_itemprototype_get(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", [])
        with ctx:
            await zabbix_lld_item_prototype_get()
        assert mock.call.call_args[0][0] == "itemprototype.get"

    async def test_filter_by_discoveryids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", [])
        with ctx:
            await zabbix_lld_item_prototype_get(discoveryids=["100"])
        assert mock.call.call_args[0][1]["discoveryids"] == ["100"]

    async def test_filter_by_hostids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", [])
        with ctx:
            await zabbix_lld_item_prototype_get(hostids=["1"])
        assert mock.call.call_args[0][1]["hostids"] == ["1"]

    async def test_search_by_name(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", [])
        with ctx:
            await zabbix_lld_item_prototype_get(name="Free space")
        assert mock.call.call_args[0][1]["search"]["name"] == "Free space"


class TestZabbixLldTriggerPrototypeGet:
    async def test_calls_triggerprototype_get(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", [])
        with ctx:
            await zabbix_lld_trigger_prototype_get()
        assert mock.call.call_args[0][0] == "triggerprototype.get"

    async def test_filter_by_discoveryids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", [])
        with ctx:
            await zabbix_lld_trigger_prototype_get(discoveryids=["100"])
        assert mock.call.call_args[0][1]["discoveryids"] == ["100"]

    async def test_filter_by_status(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", [])
        with ctx:
            await zabbix_lld_trigger_prototype_get(status=1)
        assert mock.call.call_args[0][1]["filter"] == {"status": 1}

    async def test_search_by_name(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", [])
        with ctx:
            await zabbix_lld_trigger_prototype_get(name="disk")
        assert mock.call.call_args[0][1]["search"] == {"description": "disk"}


class TestZabbixLldGraphPrototypeGet:
    async def test_calls_graphprototype_get(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", [])
        with ctx:
            await zabbix_lld_graph_prototype_get()
        assert mock.call.call_args[0][0] == "graphprototype.get"

    async def test_filter_by_discoveryids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", [])
        with ctx:
            await zabbix_lld_graph_prototype_get(discoveryids=["100"])
        assert mock.call.call_args[0][1]["discoveryids"] == ["100"]

    async def test_filter_by_graphids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", [])
        with ctx:
            await zabbix_lld_graph_prototype_get(graphids=["5"])
        assert mock.call.call_args[0][1]["graphids"] == ["5"]


class TestZabbixLldHostPrototypeGet:
    async def test_calls_hostprototype_get(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", [])
        with ctx:
            await zabbix_lld_host_prototype_get()
        assert mock.call.call_args[0][0] == "hostprototype.get"

    async def test_filter_by_discoveryids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", [])
        with ctx:
            await zabbix_lld_host_prototype_get(discoveryids=["100"])
        assert mock.call.call_args[0][1]["discoveryids"] == ["100"]

    async def test_filter_by_groupids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", [])
        with ctx:
            await zabbix_lld_host_prototype_get(groupids=["2"])
        assert mock.call.call_args[0][1]["groupids"] == ["2"]

    async def test_search_by_name(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", [])
        with ctx:
            await zabbix_lld_host_prototype_get(name="router")
        assert mock.call.call_args[0][1]["search"] == {"name": "router"}


from zabbix_mcp.tools.lld import (  # noqa: E402
    zabbix_lld_graph_prototype_create,
    zabbix_lld_graph_prototype_update,
    zabbix_lld_host_prototype_create,
    zabbix_lld_host_prototype_update,
    zabbix_lld_item_prototype_create,
    zabbix_lld_item_prototype_update,
    zabbix_lld_rule_create,
    zabbix_lld_rule_update,
    zabbix_lld_trigger_prototype_create,
    zabbix_lld_trigger_prototype_update,
)


class TestZabbixLldRuleCreate:
    async def test_calls_discoveryrule_create(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {"itemids": ["200"]})
        with ctx:
            result = await zabbix_lld_rule_create(
                hostid="1", name="Discover FS", key_="vfs.fs.discovery",
            )
        assert mock.call.call_args[0][0] == "discoveryrule.create"
        assert result == {"itemids": ["200"]}

    async def test_required_params_sent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {})
        with ctx:
            await zabbix_lld_rule_create(hostid="1", name="FS", key_="vfs.fs.discovery")
        params = mock.call.call_args[0][1]
        assert params["hostid"] == "1"
        assert params["name"] == "FS"
        assert params["key_"] == "vfs.fs.discovery"
        assert params["delay"] == "1m"
        assert params["status"] == 0

    async def test_optional_filter(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {})
        f = {"evaltype": 0, "conditions": [{"macro": "{#FSTYPE}", "value": "ext4"}]}
        with ctx:
            await zabbix_lld_rule_create(hostid="1", name="N", key_="k", filter=f)
        assert mock.call.call_args[0][1]["filter"] == f

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {})
        with ctx:
            await zabbix_lld_rule_create(hostid="1", name="N", key_="k")
        params = mock.call.call_args[0][1]
        assert "filter" not in params
        assert "preprocessing" not in params
        assert "description" not in params


class TestZabbixLldRuleUpdate:
    async def test_calls_discoveryrule_update(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {"itemids": ["200"]})
        with ctx:
            result = await zabbix_lld_rule_update(itemid="200", status=1)
        assert mock.call.call_args[0][0] == "discoveryrule.update"
        assert result == {"itemids": ["200"]}

    async def test_sends_itemid(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {})
        with ctx:
            await zabbix_lld_rule_update(itemid="42")
        assert mock.call.call_args[0][1]["itemid"] == "42"

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {})
        with ctx:
            await zabbix_lld_rule_update(itemid="1")
        params = mock.call.call_args[0][1]
        assert "name" not in params
        assert "delay" not in params
        assert "filter" not in params


class TestZabbixLldItemPrototypeCreate:
    async def test_calls_itemprototype_create(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {"itemids": ["300"]})
        with ctx:
            result = await zabbix_lld_item_prototype_create(
                hostid="1", ruleid="100",
                name="Free space on {#FSNAME}", key_="vfs.fs.size[{#FSNAME},free]",
            )
        assert mock.call.call_args[0][0] == "itemprototype.create"
        assert result == {"itemids": ["300"]}

    async def test_required_params_sent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {})
        with ctx:
            await zabbix_lld_item_prototype_create(
                hostid="1", ruleid="100", name="N", key_="k",
            )
        params = mock.call.call_args[0][1]
        assert params["hostid"] == "1"
        assert params["ruleid"] == "100"
        assert params["value_type"] == 3
        assert params["delay"] == "1m"

    async def test_optional_units(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {})
        with ctx:
            await zabbix_lld_item_prototype_create(
                hostid="1", ruleid="100", name="N", key_="k", units="B",
            )
        assert mock.call.call_args[0][1]["units"] == "B"

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {})
        with ctx:
            await zabbix_lld_item_prototype_create(hostid="1", ruleid="100", name="N", key_="k")
        params = mock.call.call_args[0][1]
        assert "units" not in params
        assert "tags" not in params
        assert "description" not in params


class TestZabbixLldItemPrototypeUpdate:
    async def test_calls_itemprototype_update(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {"itemids": ["300"]})
        with ctx:
            result = await zabbix_lld_item_prototype_update(itemid="300", delay="5m")
        assert mock.call.call_args[0][0] == "itemprototype.update"
        assert result == {"itemids": ["300"]}

    async def test_sends_itemid(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {})
        with ctx:
            await zabbix_lld_item_prototype_update(itemid="55")
        assert mock.call.call_args[0][1]["itemid"] == "55"

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {})
        with ctx:
            await zabbix_lld_item_prototype_update(itemid="1")
        params = mock.call.call_args[0][1]
        assert "name" not in params
        assert "units" not in params
        assert "tags" not in params


class TestZabbixLldTriggerPrototypeCreate:
    async def test_calls_triggerprototype_create(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {"triggerids": ["400"]})
        with ctx:
            result = await zabbix_lld_trigger_prototype_create(
                description="Low disk on {#FSNAME}",
                expression="last(/h/vfs.fs.size[{#FSNAME},pfree])<10",
                ruleid="100",
            )
        assert mock.call.call_args[0][0] == "triggerprototype.create"
        assert result == {"triggerids": ["400"]}

    async def test_required_params_sent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {})
        with ctx:
            await zabbix_lld_trigger_prototype_create(
                description="D", expression="E", ruleid="100",
            )
        params = mock.call.call_args[0][1]
        assert params["ruleid"] == "100"
        assert params["priority"] == 2
        assert params["status"] == 0

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {})
        with ctx:
            await zabbix_lld_trigger_prototype_create(description="D", expression="E", ruleid="100")
        params = mock.call.call_args[0][1]
        assert "tags" not in params
        assert "comments" not in params
        assert "url" not in params


class TestZabbixLldTriggerPrototypeUpdate:
    async def test_calls_triggerprototype_update(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {"triggerids": ["400"]})
        with ctx:
            result = await zabbix_lld_trigger_prototype_update(triggerid="400", priority=4)
        assert mock.call.call_args[0][0] == "triggerprototype.update"
        assert result == {"triggerids": ["400"]}

    async def test_sends_triggerid(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {})
        with ctx:
            await zabbix_lld_trigger_prototype_update(triggerid="77")
        assert mock.call.call_args[0][1]["triggerid"] == "77"

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {})
        with ctx:
            await zabbix_lld_trigger_prototype_update(triggerid="1")
        params = mock.call.call_args[0][1]
        assert "description" not in params
        assert "priority" not in params
        assert "tags" not in params


class TestZabbixLldGraphPrototypeCreate:
    async def test_calls_graphprototype_create(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {"graphids": ["500"]})
        gitems = [{"itemid": "300", "color": "00FF00", "drawtype": 0, "sortorder": 0}]
        with ctx:
            result = await zabbix_lld_graph_prototype_create(name="I/O {#DEVNAME}", gitems=gitems)
        assert mock.call.call_args[0][0] == "graphprototype.create"
        assert result == {"graphids": ["500"]}

    async def test_graphtype_param_name(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {})
        gitems = [{"itemid": "300", "color": "0", "drawtype": 0, "sortorder": 0}]
        with ctx:
            await zabbix_lld_graph_prototype_create(name="G", gitems=gitems, type=1)
        params = mock.call.call_args[0][1]
        assert params["graphtype"] == 1
        assert "type" not in params


class TestZabbixLldGraphPrototypeUpdate:
    async def test_calls_graphprototype_update(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {"graphids": ["500"]})
        with ctx:
            result = await zabbix_lld_graph_prototype_update(graphid="500", name="Updated")
        assert mock.call.call_args[0][0] == "graphprototype.update"
        assert result == {"graphids": ["500"]}

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {})
        with ctx:
            await zabbix_lld_graph_prototype_update(graphid="1")
        params = mock.call.call_args[0][1]
        assert "name" not in params
        assert "gitems" not in params


class TestZabbixLldHostPrototypeCreate:
    async def test_calls_hostprototype_create(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {"hostids": ["600"]})
        with ctx:
            result = await zabbix_lld_host_prototype_create(ruleid="100", host="{#HOST}")
        assert mock.call.call_args[0][0] == "hostprototype.create"
        assert result == {"hostids": ["600"]}

    async def test_required_params_sent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {})
        with ctx:
            await zabbix_lld_host_prototype_create(ruleid="100", host="{#HOST}")
        params = mock.call.call_args[0][1]
        assert params["ruleid"] == "100"
        assert params["host"] == "{#HOST}"
        assert params["status"] == 0

    async def test_optional_group_links(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {})
        with ctx:
            await zabbix_lld_host_prototype_create(
                ruleid="100", host="{#HOST}",
                groupLinks=[{"groupid": "10"}],
            )
        assert mock.call.call_args[0][1]["groupLinks"] == [{"groupid": "10"}]

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {})
        with ctx:
            await zabbix_lld_host_prototype_create(ruleid="100", host="{#HOST}")
        params = mock.call.call_args[0][1]
        assert "name" not in params
        assert "groupLinks" not in params
        assert "templates" not in params


class TestZabbixLldHostPrototypeUpdate:
    async def test_calls_hostprototype_update(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {"hostids": ["600"]})
        with ctx:
            result = await zabbix_lld_host_prototype_update(hostid="600", status=1)
        assert mock.call.call_args[0][0] == "hostprototype.update"
        assert result == {"hostids": ["600"]}

    async def test_sends_hostid(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {})
        with ctx:
            await zabbix_lld_host_prototype_update(hostid="33")
        assert mock.call.call_args[0][1]["hostid"] == "33"

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {})
        with ctx:
            await zabbix_lld_host_prototype_update(hostid="1")
        params = mock.call.call_args[0][1]
        assert "host" not in params
        assert "groupLinks" not in params
        assert "templates" not in params


from zabbix_mcp.tools.lld import (  # noqa: E402
    zabbix_lld_rule_delete,
    zabbix_lld_item_prototype_delete,
    zabbix_lld_trigger_prototype_delete,
    zabbix_lld_graph_prototype_delete,
    zabbix_lld_host_prototype_delete,
)


class TestZabbixLldRuleDelete:
    async def test_calls_discoveryrule_delete(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {"itemids": ["200"]})
        with ctx:
            result = await zabbix_lld_rule_delete(itemids=["200"])
        assert mock.call.call_args[0][0] == "discoveryrule.delete"
        assert result == {"itemids": ["200"]}

    async def test_passes_ids_as_positional(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {})
        with ctx:
            await zabbix_lld_rule_delete(itemids=["1", "2"])
        assert mock.call.call_args[0][1] == ["1", "2"]

    async def test_destructive_annotation(self, zabbix_env: dict) -> None:
        from zabbix_mcp.tools.lld import DELETE
        assert DELETE["destructiveHint"] is True


class TestZabbixLldItemPrototypeDelete:
    async def test_calls_itemprototype_delete(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {"itemids": ["300"]})
        with ctx:
            result = await zabbix_lld_item_prototype_delete(itemids=["300"])
        assert mock.call.call_args[0][0] == "itemprototype.delete"
        assert result == {"itemids": ["300"]}

    async def test_passes_ids_as_positional(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {})
        with ctx:
            await zabbix_lld_item_prototype_delete(itemids=["300"])
        assert mock.call.call_args[0][1] == ["300"]


class TestZabbixLldTriggerPrototypeDelete:
    async def test_calls_triggerprototype_delete(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {"triggerids": ["400"]})
        with ctx:
            result = await zabbix_lld_trigger_prototype_delete(triggerids=["400"])
        assert mock.call.call_args[0][0] == "triggerprototype.delete"
        assert result == {"triggerids": ["400"]}

    async def test_passes_ids_as_positional(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {})
        with ctx:
            await zabbix_lld_trigger_prototype_delete(triggerids=["400"])
        assert mock.call.call_args[0][1] == ["400"]


class TestZabbixLldGraphPrototypeDelete:
    async def test_calls_graphprototype_delete(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {"graphids": ["500"]})
        with ctx:
            result = await zabbix_lld_graph_prototype_delete(graphids=["500"])
        assert mock.call.call_args[0][0] == "graphprototype.delete"
        assert result == {"graphids": ["500"]}

    async def test_passes_ids_as_positional(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {})
        with ctx:
            await zabbix_lld_graph_prototype_delete(graphids=["500"])
        assert mock.call.call_args[0][1] == ["500"]


class TestZabbixLldHostPrototypeDelete:
    async def test_calls_hostprototype_delete(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {"hostids": ["600"]})
        with ctx:
            result = await zabbix_lld_host_prototype_delete(hostids=["600"])
        assert mock.call.call_args[0][0] == "hostprototype.delete"
        assert result == {"hostids": ["600"]}

    async def test_passes_ids_as_positional(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client("lld", {})
        with ctx:
            await zabbix_lld_host_prototype_delete(hostids=["600"])
        assert mock.call.call_args[0][1] == ["600"]
