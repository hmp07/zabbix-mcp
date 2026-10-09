"""Tests for zabbix_mcp.tools.workflow — multi-step workflow tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, call, patch

from zabbix_mcp.tools.workflow import (
    zabbix_host_problems_summary,
    zabbix_lld_scaffold,
    zabbix_template_link,
)


def _mock_client_multi(side_effects: list):
    """Mock ZabbixClient.call with multiple sequential return values."""
    mock = AsyncMock()
    mock.call = AsyncMock(side_effect=side_effects)
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock)
    cm.__aexit__ = AsyncMock(return_value=None)
    return mock, patch("zabbix_mcp.tools.workflow.shared_session", return_value=cm)


class TestZabbixHostProblemsSummary:
    async def test_returns_host_with_problems(self, zabbix_env: dict) -> None:
        hosts = [{"hostid": "10", "host": "web-01", "name": "Web Server 01"}]
        problems = [{"eventid": "1", "objectid": "100", "name": "High CPU", "severity": "4"}]
        triggers = [{"triggerid": "100", "hosts": [{"hostid": "10"}]}]
        mock, ctx = _mock_client_multi([hosts, problems, triggers])
        with ctx:
            result = await zabbix_host_problems_summary(hostids=["10"])
        assert len(result) == 1
        assert result[0]["hostid"] == "10"
        assert result[0]["total"] == 1
        assert result[0]["problems"]["high"] == 1

    async def test_returns_empty_when_no_hosts(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client_multi([[]])
        with ctx:
            result = await zabbix_host_problems_summary()
        assert result == []

    async def test_calls_host_get_first(self, zabbix_env: dict) -> None:
        hosts = [{"hostid": "10", "host": "h", "name": "H"}]
        mock, ctx = _mock_client_multi([hosts, [], []])
        with ctx:
            await zabbix_host_problems_summary(hostids=["10"])
        first_call = mock.call.call_args_list[0]
        assert first_call[0][0] == "host.get"

    async def test_passes_hostids_filter(self, zabbix_env: dict) -> None:
        hosts = [{"hostid": "10", "host": "h", "name": "H"}]
        mock, ctx = _mock_client_multi([hosts, [], []])
        with ctx:
            await zabbix_host_problems_summary(hostids=["10"])
        host_params = mock.call.call_args_list[0][0][1]
        assert host_params["hostids"] == ["10"]

    async def test_passes_groupids_filter(self, zabbix_env: dict) -> None:
        hosts = [{"hostid": "10", "host": "h", "name": "H"}]
        mock, ctx = _mock_client_multi([hosts, [], []])
        with ctx:
            await zabbix_host_problems_summary(groupids=["2"])
        host_params = mock.call.call_args_list[0][0][1]
        assert host_params["groupids"] == ["2"]

    async def test_min_severity_filters_problems(self, zabbix_env: dict) -> None:
        hosts = [{"hostid": "10", "host": "h", "name": "H"}]
        mock, ctx = _mock_client_multi([hosts, [], []])
        with ctx:
            await zabbix_host_problems_summary(hostids=["10"], min_severity=3)
        problem_params = mock.call.call_args_list[1][0][1]
        assert problem_params["severities"] == [3, 4, 5]

    async def test_no_severity_filter_when_zero(self, zabbix_env: dict) -> None:
        hosts = [{"hostid": "10", "host": "h", "name": "H"}]
        mock, ctx = _mock_client_multi([hosts, [], []])
        with ctx:
            await zabbix_host_problems_summary(hostids=["10"], min_severity=0)
        problem_params = mock.call.call_args_list[1][0][1]
        assert "severities" not in problem_params

    async def test_skips_hosts_with_no_problems_when_no_filter(self, zabbix_env: dict) -> None:
        hosts = [
            {"hostid": "10", "host": "h1", "name": "H1"},
            {"hostid": "11", "host": "h2", "name": "H2"},
        ]
        problems = [{"eventid": "1", "objectid": "100", "name": "Alert", "severity": "4"}]
        triggers = [{"triggerid": "100", "hosts": [{"hostid": "10"}]}]
        mock, ctx = _mock_client_multi([hosts, problems, triggers])
        with ctx:
            result = await zabbix_host_problems_summary()
        assert len(result) == 1
        assert result[0]["hostid"] == "10"

    async def test_includes_all_hosts_when_hostids_given(self, zabbix_env: dict) -> None:
        hosts = [
            {"hostid": "10", "host": "h1", "name": "H1"},
            {"hostid": "11", "host": "h2", "name": "H2"},
        ]
        mock, ctx = _mock_client_multi([hosts, [], []])
        with ctx:
            result = await zabbix_host_problems_summary(hostids=["10", "11"])
        assert len(result) == 2

    async def test_severity_counts_mapped_correctly(self, zabbix_env: dict) -> None:
        hosts = [{"hostid": "10", "host": "h", "name": "H"}]
        problems = [
            {"eventid": "1", "objectid": "100", "name": "Disaster", "severity": "5"},
            {"eventid": "2", "objectid": "100", "name": "Warning", "severity": "2"},
        ]
        triggers = [{"triggerid": "100", "hosts": [{"hostid": "10"}]}]
        mock, ctx = _mock_client_multi([hosts, problems, triggers])
        with ctx:
            result = await zabbix_host_problems_summary(hostids=["10"])
        assert result[0]["problems"]["disaster"] == 1
        assert result[0]["problems"]["warning"] == 1
        assert result[0]["total"] == 2

    async def test_results_sorted_by_total_descending(self, zabbix_env: dict) -> None:
        hosts = [
            {"hostid": "10", "host": "h1", "name": "H1"},
            {"hostid": "11", "host": "h2", "name": "H2"},
        ]
        problems = [
            {"eventid": "1", "objectid": "100", "name": "A", "severity": "4"},
            {"eventid": "2", "objectid": "100", "name": "B", "severity": "4"},
            {"eventid": "3", "objectid": "101", "name": "C", "severity": "2"},
        ]
        triggers = [
            {"triggerid": "100", "hosts": [{"hostid": "10"}]},
            {"triggerid": "101", "hosts": [{"hostid": "11"}]},
        ]
        mock, ctx = _mock_client_multi([hosts, problems, triggers])
        with ctx:
            result = await zabbix_host_problems_summary(hostids=["10", "11"])
        assert result[0]["hostid"] == "10"
        assert result[0]["total"] == 2
        assert result[1]["hostid"] == "11"
        assert result[1]["total"] == 1


class TestZabbixLldScaffold:
    _rule_result = {"itemids": ["200"]}
    _item_result = {"itemids": ["300"]}
    _trigger_result = {"triggerids": ["400"]}

    async def test_returns_all_created_ids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client_multi([self._rule_result, self._item_result, self._trigger_result])
        with ctx:
            result = await zabbix_lld_scaffold(
                hostid="1",
                rule_name="Discover FS",
                rule_key="vfs.fs.discovery",
                item_name="Free space on {#FSNAME}",
                item_key="vfs.fs.size[{#FSNAME},free]",
                trigger_description="Low disk on {#FSNAME}",
                trigger_expression="last(/h/vfs.fs.size[{#FSNAME},pfree])<10",
            )
        assert result == {
            "ruleid": "200",
            "item_prototypeid": "300",
            "trigger_prototypeid": "400",
        }

    async def test_creates_in_correct_order(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client_multi([self._rule_result, self._item_result, self._trigger_result])
        with ctx:
            await zabbix_lld_scaffold(
                hostid="1",
                rule_name="N", rule_key="k",
                item_name="I", item_key="ik",
                trigger_description="T", trigger_expression="E",
            )
        calls = [c[0][0] for c in mock.call.call_args_list]
        assert calls == ["discoveryrule.create", "itemprototype.create", "triggerprototype.create"]

    async def test_rule_uses_correct_hostid(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client_multi([self._rule_result, self._item_result, self._trigger_result])
        with ctx:
            await zabbix_lld_scaffold(
                hostid="42",
                rule_name="N", rule_key="k",
                item_name="I", item_key="ik",
                trigger_description="T", trigger_expression="E",
            )
        rule_params = mock.call.call_args_list[0][0][1]
        assert rule_params["hostid"] == "42"

    async def test_item_prototype_uses_ruleid_from_rule_result(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client_multi([self._rule_result, self._item_result, self._trigger_result])
        with ctx:
            await zabbix_lld_scaffold(
                hostid="1",
                rule_name="N", rule_key="k",
                item_name="I", item_key="ik",
                trigger_description="T", trigger_expression="E",
            )
        item_params = mock.call.call_args_list[1][0][1]
        assert item_params["ruleid"] == "200"

    async def test_trigger_prototype_uses_ruleid_from_rule_result(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client_multi([self._rule_result, self._item_result, self._trigger_result])
        with ctx:
            await zabbix_lld_scaffold(
                hostid="1",
                rule_name="N", rule_key="k",
                item_name="I", item_key="ik",
                trigger_description="T", trigger_expression="E",
            )
        trigger_params = mock.call.call_args_list[2][0][1]
        assert trigger_params["ruleid"] == "200"

    async def test_optional_item_units(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client_multi([self._rule_result, self._item_result, self._trigger_result])
        with ctx:
            await zabbix_lld_scaffold(
                hostid="1",
                rule_name="N", rule_key="k",
                item_name="I", item_key="ik",
                trigger_description="T", trigger_expression="E",
                item_units="B",
            )
        item_params = mock.call.call_args_list[1][0][1]
        assert item_params["units"] == "B"

    async def test_no_units_absent_by_default(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client_multi([self._rule_result, self._item_result, self._trigger_result])
        with ctx:
            await zabbix_lld_scaffold(
                hostid="1",
                rule_name="N", rule_key="k",
                item_name="I", item_key="ik",
                trigger_description="T", trigger_expression="E",
            )
        item_params = mock.call.call_args_list[1][0][1]
        assert "units" not in item_params

    async def test_trigger_priority_passed(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client_multi([self._rule_result, self._item_result, self._trigger_result])
        with ctx:
            await zabbix_lld_scaffold(
                hostid="1",
                rule_name="N", rule_key="k",
                item_name="I", item_key="ik",
                trigger_description="T", trigger_expression="E",
                trigger_priority=4,
            )
        trigger_params = mock.call.call_args_list[2][0][1]
        assert trigger_params["priority"] == 4


class TestZabbixTemplateLink:
    async def test_returns_updated_hostids(self, zabbix_env: dict) -> None:
        hosts = [{"hostid": "10", "parentTemplates": []}]
        update_result = {"hostids": ["10"]}
        mock, ctx = _mock_client_multi([hosts, update_result])
        with ctx:
            result = await zabbix_template_link(hostids=["10"], templateids=["20"])
        assert result == {"hostids": ["10"]}

    async def test_calls_host_get_then_host_update(self, zabbix_env: dict) -> None:
        hosts = [{"hostid": "10", "parentTemplates": []}]
        update_result = {"hostids": ["10"]}
        mock, ctx = _mock_client_multi([hosts, update_result])
        with ctx:
            await zabbix_template_link(hostids=["10"], templateids=["20"])
        calls = [c[0][0] for c in mock.call.call_args_list]
        assert calls[0] == "host.get"
        assert calls[1] == "host.update"

    async def test_merges_with_existing_templates(self, zabbix_env: dict) -> None:
        hosts = [{"hostid": "10", "parentTemplates": [{"templateid": "15"}]}]
        update_result = {"hostids": ["10"]}
        mock, ctx = _mock_client_multi([hosts, update_result])
        with ctx:
            await zabbix_template_link(hostids=["10"], templateids=["20"])
        update_params = mock.call.call_args_list[1][0][1]
        template_ids_sent = {t["templateid"] for t in update_params["templates"]}
        assert "15" in template_ids_sent
        assert "20" in template_ids_sent

    async def test_does_not_duplicate_existing_template(self, zabbix_env: dict) -> None:
        hosts = [{"hostid": "10", "parentTemplates": [{"templateid": "20"}]}]
        update_result = {"hostids": ["10"]}
        mock, ctx = _mock_client_multi([hosts, update_result])
        with ctx:
            await zabbix_template_link(hostids=["10"], templateids=["20"])
        update_params = mock.call.call_args_list[1][0][1]
        ids = [t["templateid"] for t in update_params["templates"]]
        assert ids.count("20") == 1

    async def test_multiple_hosts_each_updated(self, zabbix_env: dict) -> None:
        hosts = [
            {"hostid": "10", "parentTemplates": []},
            {"hostid": "11", "parentTemplates": []},
        ]
        mock, ctx = _mock_client_multi([
            hosts,
            {"hostids": ["10"]},
            {"hostids": ["11"]},
        ])
        with ctx:
            result = await zabbix_template_link(hostids=["10", "11"], templateids=["20"])
        update_calls = [c for c in mock.call.call_args_list if c[0][0] == "host.update"]
        assert len(update_calls) == 2
        assert result == {"hostids": ["10", "11"]}

    async def test_uses_selectparenttemplates(self, zabbix_env: dict) -> None:
        hosts = [{"hostid": "10", "parentTemplates": []}]
        mock, ctx = _mock_client_multi([hosts, {"hostids": ["10"]}])
        with ctx:
            await zabbix_template_link(hostids=["10"], templateids=["20"])
        host_params = mock.call.call_args_list[0][0][1]
        assert "selectParentTemplates" in host_params
