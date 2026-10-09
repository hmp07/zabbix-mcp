"""Tests for zabbix_mcp.tools.dashboard — dashboard_get and template_dashboard_get."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from zabbix_mcp.tools.dashboard import zabbix_dashboard_get, zabbix_template_dashboard_get


def _mock_client(return_value: object):
    mock = AsyncMock()
    mock.call = AsyncMock(return_value=return_value)
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock)
    cm.__aexit__ = AsyncMock(return_value=None)
    return mock, patch("zabbix_mcp.tools.dashboard.shared_session", return_value=cm)


class TestZabbixDashboardGet:
    async def test_returns_dashboards(self, zabbix_env: dict) -> None:
        expected = [{"dashboardid": "1", "name": "Global view", "userid": "1"}]
        mock, ctx = _mock_client(expected)
        with ctx:
            result = await zabbix_dashboard_get()
        assert result == expected

    async def test_calls_correct_method(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_dashboard_get()
        assert mock.call.call_args[0][0] == "dashboard.get"

    async def test_filter_by_dashboardids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_dashboard_get(dashboardids=["1"])
        assert mock.call.call_args[0][1]["dashboardids"] == ["1"]

    async def test_filter_by_userids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_dashboard_get(userids=["2"])
        assert mock.call.call_args[0][1]["userids"] == ["2"]

    async def test_search_by_name(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_dashboard_get(name="Global")
        assert mock.call.call_args[0][1]["search"] == {"name": "Global"}

    async def test_empty_results(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            result = await zabbix_dashboard_get()
        assert result == []


class TestZabbixTemplateDashboardGet:
    async def test_returns_template_dashboards(self, zabbix_env: dict) -> None:
        expected = [{"dashboardid": "5", "name": "Template overview", "templateid": "20"}]
        mock, ctx = _mock_client(expected)
        with ctx:
            result = await zabbix_template_dashboard_get()
        assert result == expected

    async def test_calls_correct_method(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_template_dashboard_get()
        assert mock.call.call_args[0][0] == "templatedashboard.get"

    async def test_filter_by_templateids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_template_dashboard_get(templateids=["20"])
        assert mock.call.call_args[0][1]["templateids"] == ["20"]

    async def test_filter_by_dashboardids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_template_dashboard_get(dashboardids=["5"])
        assert mock.call.call_args[0][1]["dashboardids"] == ["5"]

    async def test_search_by_name(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_template_dashboard_get(name="overview")
        assert mock.call.call_args[0][1]["search"] == {"name": "overview"}


from zabbix_mcp.tools.dashboard import (  # noqa: E402
    zabbix_dashboard_create,
    zabbix_dashboard_update,
    zabbix_template_dashboard_create,
    zabbix_template_dashboard_update,
)


class TestZabbixDashboardCreate:
    async def test_calls_dashboard_create(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"dashboardids": ["3"]})
        with ctx:
            result = await zabbix_dashboard_create(name="My Dashboard")
        assert mock.call.call_args[0][0] == "dashboard.create"
        assert result == {"dashboardids": ["3"]}

    async def test_default_private(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_dashboard_create(name="D")
        params = mock.call.call_args[0][1]
        assert params["private"] == 1

    async def test_optional_pages(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        pages = [{"widgets": []}]
        with ctx:
            await zabbix_dashboard_create(name="D", pages=pages)
        assert mock.call.call_args[0][1]["pages"] == pages

    async def test_no_pages_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_dashboard_create(name="D")
        assert "pages" not in mock.call.call_args[0][1]


class TestZabbixDashboardUpdate:
    async def test_calls_dashboard_update(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"dashboardids": ["3"]})
        with ctx:
            result = await zabbix_dashboard_update(dashboardid="3", name="New name")
        assert mock.call.call_args[0][0] == "dashboard.update"
        assert result == {"dashboardids": ["3"]}

    async def test_sends_dashboardid(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_dashboard_update(dashboardid="7")
        assert mock.call.call_args[0][1]["dashboardid"] == "7"

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_dashboard_update(dashboardid="1")
        params = mock.call.call_args[0][1]
        assert "name" not in params
        assert "pages" not in params
        assert "private" not in params


class TestZabbixTemplateDashboardCreate:
    async def test_calls_templatedashboard_create(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"dashboardids": ["9"]})
        with ctx:
            result = await zabbix_template_dashboard_create(templateid="10", name="Tmpl Dashboard")
        assert mock.call.call_args[0][0] == "templatedashboard.create"
        assert result == {"dashboardids": ["9"]}

    async def test_required_params(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_template_dashboard_create(templateid="10", name="D")
        params = mock.call.call_args[0][1]
        assert params["templateid"] == "10"
        assert params["name"] == "D"


class TestZabbixTemplateDashboardUpdate:
    async def test_calls_templatedashboard_update(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"dashboardids": ["9"]})
        with ctx:
            result = await zabbix_template_dashboard_update(dashboardid="9", name="Updated")
        assert mock.call.call_args[0][0] == "templatedashboard.update"
        assert result == {"dashboardids": ["9"]}

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_template_dashboard_update(dashboardid="9")
        params = mock.call.call_args[0][1]
        assert "name" not in params
        assert "pages" not in params


from zabbix_mcp.tools.dashboard import zabbix_dashboard_delete, zabbix_template_dashboard_delete  # noqa: E402


class TestZabbixDashboardDelete:
    async def test_calls_dashboard_delete(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"dashboardids": ["3"]})
        with ctx:
            result = await zabbix_dashboard_delete(dashboardids=["3"])
        assert mock.call.call_args[0][0] == "dashboard.delete"
        assert result == {"dashboardids": ["3"]}

    async def test_passes_ids_as_positional(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_dashboard_delete(dashboardids=["1", "2"])
        assert mock.call.call_args[0][1] == ["1", "2"]

    async def test_destructive_annotation(self, zabbix_env: dict) -> None:
        from zabbix_mcp.tools.dashboard import DELETE
        assert DELETE["destructiveHint"] is True


class TestZabbixTemplateDashboardDelete:
    async def test_calls_templatedashboard_delete(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"dashboardids": ["9"]})
        with ctx:
            result = await zabbix_template_dashboard_delete(dashboardids=["9"])
        assert mock.call.call_args[0][0] == "templatedashboard.delete"
        assert result == {"dashboardids": ["9"]}

    async def test_passes_ids_as_positional(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_template_dashboard_delete(dashboardids=["9"])
        assert mock.call.call_args[0][1] == ["9"]
