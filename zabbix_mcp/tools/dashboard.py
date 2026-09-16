"""Zabbix MCP tools — Dashboards and Template Dashboards (read, write, delete)."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from ..client import ZabbixClient
from ..app import mcp
from ._annotations import DELETE, READ_ONLY, WRITE, WRITE_IDEMPOTENT


@mcp.tool(
    name="zabbix_dashboard_get",
    description="List Zabbix dashboards. Filter by dashboard ID, name, or owner.",
    annotations=READ_ONLY,
)
async def zabbix_dashboard_get(
    dashboardids: Annotated[list[str] | None, Field(description="Return only dashboards with these IDs.")] = None,
    userids: Annotated[list[str] | None, Field(description="Return dashboards owned by these user IDs.")] = None,
    name: Annotated[str | None, Field(description="Search by dashboard name (substring match).")] = None,
    limit: Annotated[int, Field(description="Maximum number of results.", ge=1, le=1000)] = 100,
    output: Annotated[list[str], Field(description="Fields to return.")] = [
        "dashboardid", "name", "userid", "private",
    ],
) -> list[dict[str, Any]]:
    """Return Zabbix dashboards matching the given filters."""
    params: dict[str, Any] = {"output": output, "limit": limit}
    if dashboardids is not None:
        params["dashboardids"] = dashboardids
    if userids is not None:
        params["userids"] = userids
    if name is not None:
        params["search"] = {"name": name}
    async with ZabbixClient() as client:
        return await client.call("dashboard.get", params)


@mcp.tool(
    name="zabbix_template_dashboard_get",
    description="List dashboards defined inside Zabbix templates.",
    annotations=READ_ONLY,
)
async def zabbix_template_dashboard_get(
    dashboardids: Annotated[list[str] | None, Field(description="Return only template dashboards with these IDs.")] = None,
    templateids: Annotated[list[str] | None, Field(description="Return dashboards belonging to these template IDs.")] = None,
    name: Annotated[str | None, Field(description="Search by dashboard name (substring match).")] = None,
    limit: Annotated[int, Field(description="Maximum number of results.", ge=1, le=1000)] = 100,
    output: Annotated[list[str], Field(description="Fields to return.")] = [
        "dashboardid", "name", "templateid",
    ],
) -> list[dict[str, Any]]:
    """Return Zabbix template dashboards."""
    params: dict[str, Any] = {"output": output, "limit": limit}
    if dashboardids is not None:
        params["dashboardids"] = dashboardids
    if templateids is not None:
        params["templateids"] = templateids
    if name is not None:
        params["search"] = {"name": name}
    async with ZabbixClient() as client:
        return await client.call("templatedashboard.get", params)


@mcp.tool(
    name="zabbix_dashboard_create",
    description=(
        "Create a new Zabbix dashboard. "
        "pages defines the dashboard pages and their widgets. "
        "private: 0=public (all users), 1=private (owner only). "
        "Returns the new dashboard ID."
    ),
    annotations=WRITE,
)
async def zabbix_dashboard_create(
    name: Annotated[str, Field(description="Dashboard name.")],
    pages: Annotated[list[dict[str, Any]] | None, Field(description="Dashboard pages with widgets.")] = None,
    private: Annotated[int, Field(description="0=public, 1=private (default).", ge=0, le=1)] = 1,
    userid: Annotated[str | None, Field(description="Owner user ID. Defaults to the authenticated user.")] = None,
) -> dict[str, Any]:
    """Create a Zabbix dashboard."""
    params: dict[str, Any] = {"name": name, "private": private}
    if pages is not None:
        params["pages"] = pages
    if userid is not None:
        params["userid"] = userid
    async with ZabbixClient() as client:
        return await client.call("dashboard.create", params)


@mcp.tool(
    name="zabbix_dashboard_update",
    description="Update an existing Zabbix dashboard. Only provided fields are changed. Returns the updated dashboard ID.",
    annotations=WRITE_IDEMPOTENT,
)
async def zabbix_dashboard_update(
    dashboardid: Annotated[str, Field(description="ID of the dashboard to update.")],
    name: Annotated[str | None, Field(description="New dashboard name.")] = None,
    pages: Annotated[list[dict[str, Any]] | None, Field(description="Replace dashboard pages and widgets.")] = None,
    private: Annotated[int | None, Field(description="0=public, 1=private.", ge=0, le=1)] = None,
) -> dict[str, Any]:
    """Update a Zabbix dashboard."""
    params: dict[str, Any] = {"dashboardid": dashboardid}
    if name is not None:
        params["name"] = name
    if pages is not None:
        params["pages"] = pages
    if private is not None:
        params["private"] = private
    async with ZabbixClient() as client:
        return await client.call("dashboard.update", params)


@mcp.tool(
    name="zabbix_template_dashboard_create",
    description="Create a dashboard inside a Zabbix template. Returns the new dashboard ID.",
    annotations=WRITE,
)
async def zabbix_template_dashboard_create(
    templateid: Annotated[str, Field(description="ID of the template to add the dashboard to.")],
    name: Annotated[str, Field(description="Dashboard name.")],
    pages: Annotated[list[dict[str, Any]] | None, Field(description="Dashboard pages with widgets.")] = None,
) -> dict[str, Any]:
    """Create a template dashboard."""
    params: dict[str, Any] = {"templateid": templateid, "name": name}
    if pages is not None:
        params["pages"] = pages
    async with ZabbixClient() as client:
        return await client.call("templatedashboard.create", params)


@mcp.tool(
    name="zabbix_template_dashboard_update",
    description="Update an existing Zabbix template dashboard. Returns the updated dashboard ID.",
    annotations=WRITE_IDEMPOTENT,
)
async def zabbix_template_dashboard_update(
    dashboardid: Annotated[str, Field(description="ID of the template dashboard to update.")],
    name: Annotated[str | None, Field(description="New dashboard name.")] = None,
    pages: Annotated[list[dict[str, Any]] | None, Field(description="Replace dashboard pages.")] = None,
) -> dict[str, Any]:
    """Update a template dashboard."""
    params: dict[str, Any] = {"dashboardid": dashboardid}
    if name is not None:
        params["name"] = name
    if pages is not None:
        params["pages"] = pages
    async with ZabbixClient() as client:
        return await client.call("templatedashboard.update", params)


@mcp.tool(
    name="zabbix_dashboard_delete",
    description=(
        "DESTRUCTIVE — Permanently delete Zabbix dashboards. "
        "This action cannot be undone. Returns the deleted dashboard IDs."
    ),
    annotations=DELETE,
)
async def zabbix_dashboard_delete(
    dashboardids: Annotated[list[str], Field(description="IDs of dashboards to delete.")],
) -> dict[str, Any]:
    """Permanently delete Zabbix dashboards."""
    async with ZabbixClient() as client:
        return await client.call("dashboard.delete", dashboardids)


@mcp.tool(
    name="zabbix_template_dashboard_delete",
    description=(
        "DESTRUCTIVE — Permanently delete Zabbix template dashboards. "
        "This action cannot be undone. Returns the deleted dashboard IDs."
    ),
    annotations=DELETE,
)
async def zabbix_template_dashboard_delete(
    dashboardids: Annotated[list[str], Field(description="IDs of template dashboards to delete.")],
) -> dict[str, Any]:
    """Permanently delete Zabbix template dashboards."""
    async with ZabbixClient() as client:
        return await client.call("templatedashboard.delete", dashboardids)
