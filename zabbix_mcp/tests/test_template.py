"""Tests for zabbix_mcp.tools.template — template, templategroup, valuemap, report."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from zabbix_mcp.tools.template import (
    zabbix_report_get,
    zabbix_template_get,
    zabbix_templategroup_get,
    zabbix_valuemap_get,
)


def _mock_client(return_value: object):
    mock = AsyncMock()
    mock.call = AsyncMock(return_value=return_value)
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock)
    cm.__aexit__ = AsyncMock(return_value=None)
    return mock, patch("zabbix_mcp.tools.template.ZabbixClient", return_value=cm)


class TestZabbixTemplateGet:
    async def test_returns_templates(self, zabbix_env: dict) -> None:
        expected = [{"templateid": "10", "host": "Linux by Zabbix agent", "name": "Linux by Zabbix agent"}]
        mock, ctx = _mock_client(expected)
        with ctx:
            result = await zabbix_template_get()
        assert result == expected

    async def test_calls_correct_method(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_template_get()
        assert mock.call.call_args[0][0] == "template.get"

    async def test_filter_by_templateids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_template_get(templateids=["10"])
        assert mock.call.call_args[0][1]["templateids"] == ["10"]

    async def test_filter_by_groupids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_template_get(groupids=["1"])
        assert mock.call.call_args[0][1]["groupids"] == ["1"]

    async def test_filter_by_hostids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_template_get(hostids=["5"])
        assert mock.call.call_args[0][1]["hostids"] == ["5"]

    async def test_search_by_name(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_template_get(name="Linux")
        assert mock.call.call_args[0][1]["search"] == {"name": "Linux"}

    async def test_empty_results(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            result = await zabbix_template_get()
        assert result == []


class TestZabbixTemplategroupGet:
    async def test_returns_groups(self, zabbix_env: dict) -> None:
        expected = [{"groupid": "1", "name": "Templates"}]
        mock, ctx = _mock_client(expected)
        with ctx:
            result = await zabbix_templategroup_get()
        assert result == expected

    async def test_calls_correct_method(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_templategroup_get()
        assert mock.call.call_args[0][0] == "templategroup.get"

    async def test_filter_by_groupids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_templategroup_get(groupids=["1"])
        assert mock.call.call_args[0][1]["groupids"] == ["1"]

    async def test_filter_by_templateids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_templategroup_get(templateids=["10"])
        assert mock.call.call_args[0][1]["templateids"] == ["10"]

    async def test_search_by_name(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_templategroup_get(name="Templates/OS")
        assert mock.call.call_args[0][1]["search"] == {"name": "Templates/OS"}


class TestZabbixValuemapGet:
    async def test_returns_valuemaps(self, zabbix_env: dict) -> None:
        expected = [{"valuemapid": "1", "name": "Service state", "hostid": "10"}]
        mock, ctx = _mock_client(expected)
        with ctx:
            result = await zabbix_valuemap_get()
        assert result == expected

    async def test_calls_correct_method(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_valuemap_get()
        assert mock.call.call_args[0][0] == "valuemap.get"

    async def test_filter_by_valuemapids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_valuemap_get(valuemapids=["1"])
        assert mock.call.call_args[0][1]["valuemapids"] == ["1"]

    async def test_filter_by_hostids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_valuemap_get(hostids=["10"])
        assert mock.call.call_args[0][1]["hostids"] == ["10"]

    async def test_filter_by_templateids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_valuemap_get(templateids=["20"])
        assert mock.call.call_args[0][1]["templateids"] == ["20"]

    async def test_search_by_name(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_valuemap_get(name="Service")
        assert mock.call.call_args[0][1]["search"] == {"name": "Service"}


class TestZabbixReportGet:
    async def test_returns_reports(self, zabbix_env: dict) -> None:
        expected = [{"reportid": "1", "name": "Weekly report", "userid": "1", "status": "1"}]
        mock, ctx = _mock_client(expected)
        with ctx:
            result = await zabbix_report_get()
        assert result == expected

    async def test_calls_correct_method(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_report_get()
        assert mock.call.call_args[0][0] == "report.get"

    async def test_filter_by_reportids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_report_get(reportids=["1"])
        assert mock.call.call_args[0][1]["reportids"] == ["1"]

    async def test_filter_by_userid(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_report_get(userid="2")
        assert mock.call.call_args[0][1]["userid"] == "2"

    async def test_search_by_name(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_report_get(name="Weekly")
        assert mock.call.call_args[0][1]["search"] == {"name": "Weekly"}


from zabbix_mcp.tools.template import (  # noqa: E402
    zabbix_report_create,
    zabbix_report_update,
    zabbix_template_create,
    zabbix_template_update,
    zabbix_templategroup_create,
    zabbix_templategroup_update,
    zabbix_valuemap_create,
    zabbix_valuemap_update,
)


class TestZabbixTemplateCreate:
    async def test_calls_template_create(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"templateids": ["20"]})
        with ctx:
            result = await zabbix_template_create(
                host="Linux by Zabbix agent",
                groups=[{"groupid": "1"}],
            )
        assert mock.call.call_args[0][0] == "template.create"
        assert result == {"templateids": ["20"]}

    async def test_required_params_sent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_template_create(host="T", groups=[{"groupid": "1"}])
        params = mock.call.call_args[0][1]
        assert params["host"] == "T"
        assert params["groups"] == [{"groupid": "1"}]

    async def test_optional_name(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_template_create(host="T", groups=[{"groupid": "1"}], name="Linux Template")
        assert mock.call.call_args[0][1]["name"] == "Linux Template"

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_template_create(host="T", groups=[{"groupid": "1"}])
        params = mock.call.call_args[0][1]
        assert "name" not in params
        assert "description" not in params
        assert "templates" not in params
        assert "macros" not in params


class TestZabbixTemplateUpdate:
    async def test_calls_template_update(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"templateids": ["20"]})
        with ctx:
            result = await zabbix_template_update(templateid="20", name="New name")
        assert mock.call.call_args[0][0] == "template.update"
        assert result == {"templateids": ["20"]}

    async def test_sends_templateid(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_template_update(templateid="99")
        assert mock.call.call_args[0][1]["templateid"] == "99"

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_template_update(templateid="1")
        params = mock.call.call_args[0][1]
        assert "host" not in params
        assert "groups" not in params
        assert "macros" not in params


class TestZabbixTemplategroupCreate:
    async def test_calls_templategroup_create(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"groupids": ["5"]})
        with ctx:
            result = await zabbix_templategroup_create(name="My Templates")
        assert mock.call.call_args[0][0] == "templategroup.create"
        assert result == {"groupids": ["5"]}

    async def test_sends_name(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_templategroup_create(name="Linux")
        assert mock.call.call_args[0][1]["name"] == "Linux"


class TestZabbixTemplategroupUpdate:
    async def test_calls_templategroup_update(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"groupids": ["5"]})
        with ctx:
            result = await zabbix_templategroup_update(groupid="5", name="New name")
        assert mock.call.call_args[0][0] == "templategroup.update"
        assert result == {"groupids": ["5"]}

    async def test_sends_groupid_and_name(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_templategroup_update(groupid="5", name="Updated")
        params = mock.call.call_args[0][1]
        assert params["groupid"] == "5"
        assert params["name"] == "Updated"


class TestZabbixValuemapCreate:
    _mappings = [{"value": "0", "newvalue": "Down"}, {"value": "1", "newvalue": "Up"}]

    async def test_calls_valuemap_create(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"valuemapids": ["8"]})
        with ctx:
            result = await zabbix_valuemap_create(
                hostid="1", name="Service state", mappings=self._mappings,
            )
        assert mock.call.call_args[0][0] == "valuemap.create"
        assert result == {"valuemapids": ["8"]}

    async def test_required_params_sent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_valuemap_create(hostid="1", name="M", mappings=self._mappings)
        params = mock.call.call_args[0][1]
        assert params["hostid"] == "1"
        assert params["name"] == "M"
        assert params["mappings"] == self._mappings


class TestZabbixValuemapUpdate:
    async def test_calls_valuemap_update(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"valuemapids": ["8"]})
        with ctx:
            result = await zabbix_valuemap_update(valuemapid="8", name="New name")
        assert mock.call.call_args[0][0] == "valuemap.update"
        assert result == {"valuemapids": ["8"]}

    async def test_sends_valuemapid(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_valuemap_update(valuemapid="8")
        assert mock.call.call_args[0][1]["valuemapid"] == "8"

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_valuemap_update(valuemapid="1")
        params = mock.call.call_args[0][1]
        assert "name" not in params
        assert "mappings" not in params


class TestZabbixReportCreate:
    async def test_calls_report_create(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"reportids": ["2"]})
        with ctx:
            result = await zabbix_report_create(
                name="Weekly report", dashboardid="3", userid="1",
            )
        assert mock.call.call_args[0][0] == "report.create"
        assert result == {"reportids": ["2"]}

    async def test_required_params_sent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_report_create(name="R", dashboardid="3", userid="1")
        params = mock.call.call_args[0][1]
        assert params["name"] == "R"
        assert params["dashboardid"] == "3"
        assert params["userid"] == "1"
        assert params["status"] == 0

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_report_create(name="R", dashboardid="3", userid="1")
        params = mock.call.call_args[0][1]
        assert "subject" not in params
        assert "message" not in params
        assert "users" not in params


class TestZabbixReportUpdate:
    async def test_calls_report_update(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"reportids": ["2"]})
        with ctx:
            result = await zabbix_report_update(reportid="2", status=1)
        assert mock.call.call_args[0][0] == "report.update"
        assert result == {"reportids": ["2"]}

    async def test_sends_reportid(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_report_update(reportid="7")
        assert mock.call.call_args[0][1]["reportid"] == "7"

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_report_update(reportid="1")
        params = mock.call.call_args[0][1]
        assert "name" not in params
        assert "users" not in params
        assert "subject" not in params


from zabbix_mcp.tools.template import (  # noqa: E402
    zabbix_template_delete,
    zabbix_templategroup_delete,
    zabbix_valuemap_delete,
    zabbix_report_delete,
)


class TestZabbixTemplateDelete:
    async def test_calls_template_delete(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"templateids": ["20"]})
        with ctx:
            result = await zabbix_template_delete(templateids=["20"])
        assert mock.call.call_args[0][0] == "template.delete"
        assert result == {"templateids": ["20"]}

    async def test_passes_ids_as_positional(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_template_delete(templateids=["1", "2"])
        assert mock.call.call_args[0][1] == ["1", "2"]

    async def test_destructive_annotation(self, zabbix_env: dict) -> None:
        from zabbix_mcp.tools.template import _DELETE
        assert _DELETE["destructiveHint"] is True


class TestZabbixTemplategroupDelete:
    async def test_calls_templategroup_delete(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"groupids": ["5"]})
        with ctx:
            result = await zabbix_templategroup_delete(groupids=["5"])
        assert mock.call.call_args[0][0] == "templategroup.delete"
        assert result == {"groupids": ["5"]}

    async def test_passes_ids_as_positional(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_templategroup_delete(groupids=["5"])
        assert mock.call.call_args[0][1] == ["5"]


class TestZabbixValuemapDelete:
    async def test_calls_valuemap_delete(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"valuemapids": ["8"]})
        with ctx:
            result = await zabbix_valuemap_delete(valuemapids=["8"])
        assert mock.call.call_args[0][0] == "valuemap.delete"
        assert result == {"valuemapids": ["8"]}

    async def test_passes_ids_as_positional(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_valuemap_delete(valuemapids=["8"])
        assert mock.call.call_args[0][1] == ["8"]


class TestZabbixReportDelete:
    async def test_calls_report_delete(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"reportids": ["2"]})
        with ctx:
            result = await zabbix_report_delete(reportids=["2"])
        assert mock.call.call_args[0][0] == "report.delete"
        assert result == {"reportids": ["2"]}

    async def test_passes_ids_as_positional(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_report_delete(reportids=["2"])
        assert mock.call.call_args[0][1] == ["2"]
