"""Zabbix MCP tools — Templates, Template Groups, Value Maps, Reports."""

from __future__ import annotations
from typing import Annotated, Any
from pydantic import Field
from ..client import ZabbixClient
from ..app import mcp
from ._annotations import DELETE, READ_ONLY, WRITE, WRITE_IDEMPOTENT
from ._params import compact, search_params


@mcp.tool(
    name="zabbix_template_get",
    description=(
        "List Zabbix templates. Filter by template ID, group, or linked host. "
        "Templates define reusable sets of items, triggers, graphs, and LLD rules."
    ),
    annotations=READ_ONLY,
)
async def zabbix_template_get(
    templateids: Annotated[list[str] | None, Field(description="Return only templates with these IDs.")] = None,
    groupids: Annotated[list[str] | None, Field(description="Return templates in these template group IDs.")] = None,
    hostids: Annotated[list[str] | None, Field(description="Return templates linked to these host IDs.")] = None,
    name: Annotated[str | None, Field(description="Search by template name (substring match).")] = None,
    limit: Annotated[int, Field(description="Maximum number of results.", ge=1, le=1000)] = 100,
    output: Annotated[list[str], Field(description="Fields to return.")] = [
        "templateid", "host", "name", "description",
    ],
) -> list[dict[str, Any]]:
    """Return Zabbix templates matching the given filters."""
    params = compact({
        "output": output,
        "limit": limit,
        "templateids": templateids,
        "groupids": groupids,
        "hostids": hostids,
    })
    params.update(search_params(name=name))
    async with ZabbixClient() as client:
        return await client.call("template.get", params)


@mcp.tool(
    name="zabbix_templategroup_get",
    description="List Zabbix template groups. Filter by group ID, name, or linked template.",
    annotations=READ_ONLY,
)
async def zabbix_templategroup_get(
    groupids: Annotated[list[str] | None, Field(description="Return only groups with these IDs.")] = None,
    templateids: Annotated[list[str] | None, Field(description="Return groups containing these template IDs.")] = None,
    name: Annotated[str | None, Field(description="Search by group name (substring match).")] = None,
    limit: Annotated[int, Field(description="Maximum number of results.", ge=1, le=1000)] = 100,
    output: Annotated[list[str], Field(description="Fields to return.")] = ["groupid", "name"],
) -> list[dict[str, Any]]:
    """Return Zabbix template groups."""
    params = compact({
        "output": output,
        "limit": limit,
        "groupids": groupids,
        "templateids": templateids,
    })
    params.update(search_params(name=name))
    async with ZabbixClient() as client:
        return await client.call("templategroup.get", params)


@mcp.tool(
    name="zabbix_valuemap_get",
    description=(
        "List Zabbix value maps. Value maps translate raw numeric values into human-readable labels "
        "(e.g., 0 -> 'Down', 1 -> 'Up')."
    ),
    annotations=READ_ONLY,
)
async def zabbix_valuemap_get(
    valuemapids: Annotated[list[str] | None, Field(description="Return only value maps with these IDs.")] = None,
    hostids: Annotated[list[str] | None, Field(description="Return value maps on these host IDs.")] = None,
    templateids: Annotated[list[str] | None, Field(description="Return value maps from these template IDs.")] = None,
    name: Annotated[str | None, Field(description="Search by value map name (substring match).")] = None,
    limit: Annotated[int, Field(description="Maximum number of results.", ge=1, le=1000)] = 100,
    output: Annotated[list[str], Field(description="Fields to return.")] = [
        "valuemapid", "name", "hostid",
    ],
) -> list[dict[str, Any]]:
    """Return Zabbix value maps."""
    params = compact({
        "output": output,
        "limit": limit,
        "valuemapids": valuemapids,
        "hostids": hostids,
        "templateids": templateids,
    })
    params.update(search_params(name=name))
    async with ZabbixClient() as client:
        return await client.call("valuemap.get", params)


@mcp.tool(
    name="zabbix_report_get",
    description="List Zabbix scheduled reports. Filter by report ID or owner.",
    annotations=READ_ONLY,
)
async def zabbix_report_get(
    reportids: Annotated[list[str] | None, Field(description="Return only reports with these IDs.")] = None,
    userid: Annotated[str | None, Field(description="Return reports owned by this user ID.")] = None,
    name: Annotated[str | None, Field(description="Search by report name (substring match).")] = None,
    limit: Annotated[int, Field(description="Maximum number of results.", ge=1, le=1000)] = 100,
    output: Annotated[list[str], Field(description="Fields to return.")] = [
        "reportid", "name", "userid", "status",
    ],
) -> list[dict[str, Any]]:
    """Return Zabbix scheduled reports."""
    params = compact({
        "output": output,
        "limit": limit,
        "reportids": reportids,
        "userid": userid,
    })
    params.update(search_params(name=name))
    async with ZabbixClient() as client:
        return await client.call("report.get", params)


@mcp.tool(
    name="zabbix_template_create",
    description=(
        "Create a new Zabbix template. "
        "Templates group items, triggers, graphs, and LLD rules for reuse across hosts. "
        "Returns the new template ID."
    ),
    annotations=WRITE,
)
async def zabbix_template_create(
    host: Annotated[str, Field(description="Technical template name (unique identifier).")],
    groups: Annotated[list[dict[str, Any]], Field(description="Template groups to add this template to.")],
    name: Annotated[str | None, Field(description="Visible template name. Defaults to host if omitted.")] = None,
    description: Annotated[str | None, Field(description="Template description.")] = None,
    templates: Annotated[list[dict[str, Any]] | None, Field(description="Parent templates to link.")] = None,
    tags: Annotated[list[dict[str, Any]] | None, Field(description="Template tags.")] = None,
    macros: Annotated[list[dict[str, Any]] | None, Field(description="Template user macros.")] = None,
) -> dict[str, Any]:
    """Create a Zabbix template."""
    params = compact({
        "host": host,
        "groups": groups,
        "name": name,
        "description": description,
        "templates": templates,
        "tags": tags,
        "macros": macros,
    })
    async with ZabbixClient() as client:
        return await client.call("template.create", params)


@mcp.tool(
    name="zabbix_template_update",
    description="Update an existing Zabbix template. Only provided fields are changed. Returns the updated template ID.",
    annotations=WRITE_IDEMPOTENT,
)
async def zabbix_template_update(
    templateid: Annotated[str, Field(description="ID of the template to update.")],
    host: Annotated[str | None, Field(description="New technical template name.")] = None,
    name: Annotated[str | None, Field(description="New visible name.")] = None,
    description: Annotated[str | None, Field(description="New description.")] = None,
    groups: Annotated[list[dict[str, Any]] | None, Field(description="Replace template group memberships.")] = None,
    templates: Annotated[list[dict[str, Any]] | None, Field(description="Replace linked parent templates.")] = None,
    tags: Annotated[list[dict[str, Any]] | None, Field(description="Replace tags.")] = None,
    macros: Annotated[list[dict[str, Any]] | None, Field(description="Replace user macros.")] = None,
) -> dict[str, Any]:
    """Update a Zabbix template."""
    params = compact({
        "templateid": templateid,
        "host": host,
        "name": name,
        "description": description,
        "groups": groups,
        "templates": templates,
        "tags": tags,
        "macros": macros,
    })
    async with ZabbixClient() as client:
        return await client.call("template.update", params)


@mcp.tool(
    name="zabbix_templategroup_create",
    description="Create a new Zabbix template group. Returns the new group ID.",
    annotations=WRITE,
)
async def zabbix_templategroup_create(
    name: Annotated[str, Field(description="Template group name.")],
) -> dict[str, Any]:
    """Create a Zabbix template group."""
    async with ZabbixClient() as client:
        return await client.call("templategroup.create", {"name": name})


@mcp.tool(
    name="zabbix_templategroup_update",
    description="Update an existing Zabbix template group name. Returns the updated group ID.",
    annotations=WRITE_IDEMPOTENT,
)
async def zabbix_templategroup_update(
    groupid: Annotated[str, Field(description="ID of the template group to update.")],
    name: Annotated[str, Field(description="New group name.")],
) -> dict[str, Any]:
    """Update a Zabbix template group."""
    async with ZabbixClient() as client:
        return await client.call("templategroup.update", {"groupid": groupid, "name": name})


@mcp.tool(
    name="zabbix_valuemap_create",
    description=(
        "Create a Zabbix value map to translate raw values into human-readable labels. "
        "mappings define the translation rules. "
        "Returns the new value map ID."
    ),
    annotations=WRITE,
)
async def zabbix_valuemap_create(
    hostid: Annotated[str, Field(description="ID of the host or template to attach this value map to.")],
    name: Annotated[str, Field(description="Value map name.")],
    mappings: Annotated[list[dict[str, Any]], Field(description="Mapping rules.")],
) -> dict[str, Any]:
    """Create a Zabbix value map."""
    params = {"hostid": hostid, "name": name, "mappings": mappings}
    async with ZabbixClient() as client:
        return await client.call("valuemap.create", params)


@mcp.tool(
    name="zabbix_valuemap_update",
    description="Update an existing Zabbix value map. Only provided fields are changed. Returns the updated value map ID.",
    annotations=WRITE_IDEMPOTENT,
)
async def zabbix_valuemap_update(
    valuemapid: Annotated[str, Field(description="ID of the value map to update.")],
    name: Annotated[str | None, Field(description="New value map name.")] = None,
    mappings: Annotated[list[dict[str, Any]] | None, Field(description="Replace mapping rules.")] = None,
) -> dict[str, Any]:
    """Update a Zabbix value map."""
    params = compact({
        "valuemapid": valuemapid,
        "name": name,
        "mappings": mappings,
    })
    async with ZabbixClient() as client:
        return await client.call("valuemap.update", params)


@mcp.tool(
    name="zabbix_report_create",
    description=(
        "Create a Zabbix scheduled report. "
        "period: 0=daily, 1=weekly, 2=monthly, 3=yearly. "
        "Returns the new report ID."
    ),
    annotations=WRITE,
)
async def zabbix_report_create(
    name: Annotated[str, Field(description="Report name.")],
    dashboardid: Annotated[str, Field(description="ID of the dashboard to generate the report from.")],
    userid: Annotated[str, Field(description="ID of the user who owns the report.")],
    period: Annotated[int, Field(description="Recurrence period: 0=daily, 1=weekly, 2=monthly, 3=yearly.", ge=0, le=3)] = 0,
    cycle: Annotated[int, Field(description="Report cycle. Default: 1.", ge=1)] = 1,
    status: Annotated[int, Field(description="0=enabled (default), 1=disabled.", ge=0, le=1)] = 0,
    subject: Annotated[str | None, Field(description="Email subject.")] = None,
    message: Annotated[str | None, Field(description="Email message body.")] = None,
    users: Annotated[list[dict[str, Any]] | None, Field(description="Users to send the report to.")] = None,
    usergroups: Annotated[list[dict[str, Any]] | None, Field(description="User groups to send the report to.")] = None,
    description: Annotated[str | None, Field(description="Report description.")] = None,
) -> dict[str, Any]:
    """Create a Zabbix scheduled report."""
    params = compact({
        "name": name,
        "dashboardid": dashboardid,
        "userid": userid,
        "period": period,
        "cycle": cycle,
        "status": status,
        "subject": subject,
        "message": message,
        "users": users,
        "usergroups": usergroups,
        "description": description,
    })
    async with ZabbixClient() as client:
        return await client.call("report.create", params)


@mcp.tool(
    name="zabbix_report_update",
    description="Update an existing Zabbix scheduled report. Only provided fields are changed. Returns the updated report ID.",
    annotations=WRITE_IDEMPOTENT,
)
async def zabbix_report_update(
    reportid: Annotated[str, Field(description="ID of the report to update.")],
    name: Annotated[str | None, Field(description="New report name.")] = None,
    dashboardid: Annotated[str | None, Field(description="New dashboard ID.")] = None,
    period: Annotated[int | None, Field(description="New recurrence period: 0=daily, 1=weekly, 2=monthly, 3=yearly.", ge=0, le=3)] = None,
    status: Annotated[int | None, Field(description="0=enabled, 1=disabled.", ge=0, le=1)] = None,
    subject: Annotated[str | None, Field(description="New email subject.")] = None,
    message: Annotated[str | None, Field(description="New email message body.")] = None,
    users: Annotated[list[dict[str, Any]] | None, Field(description="Replace recipient users.")] = None,
    usergroups: Annotated[list[dict[str, Any]] | None, Field(description="Replace recipient user groups.")] = None,
    description: Annotated[str | None, Field(description="New description.")] = None,
) -> dict[str, Any]:
    """Update a Zabbix scheduled report."""
    params = compact({
        "reportid": reportid,
        "name": name,
        "dashboardid": dashboardid,
        "period": period,
        "status": status,
        "subject": subject,
        "message": message,
        "users": users,
        "usergroups": usergroups,
        "description": description,
    })
    async with ZabbixClient() as client:
        return await client.call("report.update", params)


@mcp.tool(
    name="zabbix_template_delete",
    description=(
        "DESTRUCTIVE — Permanently delete Zabbix templates. "
        "All items, triggers, and graphs defined in the template will be removed from linked hosts. "
        "This action cannot be undone. Returns the deleted template IDs."
    ),
    annotations=DELETE,
)
async def zabbix_template_delete(
    templateids: Annotated[list[str], Field(description="IDs of templates to delete.")],
) -> dict[str, Any]:
    """Permanently delete Zabbix templates."""
    async with ZabbixClient() as client:
        return await client.call("template.delete", templateids)


@mcp.tool(
    name="zabbix_templategroup_delete",
    description=(
        "DESTRUCTIVE — Permanently delete Zabbix template groups. "
        "Groups that contain templates cannot be deleted. "
        "Returns the deleted group IDs."
    ),
    annotations=DELETE,
)
async def zabbix_templategroup_delete(
    groupids: Annotated[list[str], Field(description="IDs of template groups to delete.")],
) -> dict[str, Any]:
    """Permanently delete Zabbix template groups."""
    async with ZabbixClient() as client:
        return await client.call("templategroup.delete", groupids)


@mcp.tool(
    name="zabbix_valuemap_delete",
    description=(
        "DESTRUCTIVE — Permanently delete Zabbix value maps. "
        "Items using these value maps will display raw values. "
        "Returns the deleted value map IDs."
    ),
    annotations=DELETE,
)
async def zabbix_valuemap_delete(
    valuemapids: Annotated[list[str], Field(description="IDs of value maps to delete.")],
) -> dict[str, Any]:
    """Permanently delete Zabbix value maps."""
    async with ZabbixClient() as client:
        return await client.call("valuemap.delete", valuemapids)


@mcp.tool(
    name="zabbix_report_delete",
    description=(
        "DESTRUCTIVE — Permanently delete Zabbix scheduled reports. "
        "This action cannot be undone. Returns the deleted report IDs."
    ),
    annotations=DELETE,
)
async def zabbix_report_delete(
    reportids: Annotated[list[str], Field(description="IDs of reports to delete.")],
) -> dict[str, Any]:
    """Permanently delete Zabbix scheduled reports."""
    async with ZabbixClient() as client:
        return await client.call("report.delete", reportids)
