"""Zabbix MCP tools — Maintenances (read, write, delete)."""

from __future__ import annotations
from typing import Annotated, Any
from pydantic import Field
from ..client import ZabbixClient
from ..app import mcp
from ._annotations import DELETE, READ_ONLY, WRITE, WRITE_IDEMPOTENT
from ._params import compact, search_params


@mcp.tool(
    name="zabbix_maintenance_get",
    description=(
        "List Zabbix maintenance windows. Filter by ID, name, host, group, or active time range. "
        "Maintenances suppress alerting for hosts during scheduled downtime."
    ),
    annotations=READ_ONLY,
)
async def zabbix_maintenance_get(
    maintenanceids: Annotated[list[str] | None, Field(description="Return only maintenances with these IDs.")] = None,
    groupids: Annotated[list[str] | None, Field(description="Return maintenances covering hosts in these group IDs.")] = None,
    hostids: Annotated[list[str] | None, Field(description="Return maintenances covering these host IDs.")] = None,
    name: Annotated[str | None, Field(description="Search by maintenance name (substring match).")] = None,
    active_till: Annotated[int | None, Field(description="Return maintenances active after this Unix timestamp.")] = None,
    limit: Annotated[int, Field(description="Maximum number of results.", ge=1, le=1000)] = 100,
    output: Annotated[list[str], Field(description="Fields to return.")] = [
        "maintenanceid", "name", "maintenance_type", "active_since", "active_till", "description",
    ],
) -> list[dict[str, Any]]:
    """Return Zabbix maintenance windows matching the given filters."""
    params = compact({
        "output": output,
        "limit": limit,
        "maintenanceids": maintenanceids,
        "groupids": groupids,
        "hostids": hostids,
        "active_till": active_till,
    })
    params.update(search_params(name=name))
    async with ZabbixClient() as client:
        return await client.call("maintenance.get", params)


@mcp.tool(
    name="zabbix_maintenance_create",
    description=(
        "Create a Zabbix maintenance window to suppress alerts during scheduled downtime. "
        "maintenance_type: 0=with data collection, 1=without data collection. "
        "timeperiods defines the maintenance schedule within the active window. "
        "Returns the new maintenance ID."
    ),
    annotations=WRITE,
)
async def zabbix_maintenance_create(
    name: Annotated[str, Field(description="Maintenance name.")],
    active_since: Annotated[int, Field(description="Start of the maintenance window (Unix timestamp).")],
    active_till: Annotated[int, Field(description="End of the maintenance window (Unix timestamp).")],
    timeperiods: Annotated[list[dict[str, Any]], Field(description="Maintenance time periods.")],
    maintenance_type: Annotated[int, Field(description="0=with data collection (default), 1=without.", ge=0, le=1)] = 0,
    groupids: Annotated[list[str] | None, Field(description="Apply maintenance to hosts in these group IDs.")] = None,
    hostids: Annotated[list[str] | None, Field(description="Apply maintenance to these host IDs.")] = None,
    description: Annotated[str | None, Field(description="Maintenance description.")] = None,
) -> dict[str, Any]:
    """Create a Zabbix maintenance window."""
    params = compact({
        "name": name,
        "active_since": active_since,
        "active_till": active_till,
        "timeperiods": timeperiods,
        "maintenance_type": maintenance_type,
        "groupids": groupids,
        "hostids": hostids,
        "description": description,
    })
    async with ZabbixClient() as client:
        return await client.call("maintenance.create", params)


@mcp.tool(
    name="zabbix_maintenance_update",
    description="Update an existing Zabbix maintenance window. Only provided fields are changed. Returns the updated maintenance ID.",
    annotations=WRITE_IDEMPOTENT,
)
async def zabbix_maintenance_update(
    maintenanceid: Annotated[str, Field(description="ID of the maintenance to update.")],
    name: Annotated[str | None, Field(description="New maintenance name.")] = None,
    active_since: Annotated[int | None, Field(description="New start timestamp.")] = None,
    active_till: Annotated[int | None, Field(description="New end timestamp.")] = None,
    timeperiods: Annotated[list[dict[str, Any]] | None, Field(description="Replace time periods.")] = None,
    groupids: Annotated[list[str] | None, Field(description="Replace host group assignments.")] = None,
    hostids: Annotated[list[str] | None, Field(description="Replace host assignments.")] = None,
    description: Annotated[str | None, Field(description="New description.")] = None,
) -> dict[str, Any]:
    """Update a Zabbix maintenance window."""
    params = compact({
        "maintenanceid": maintenanceid,
        "name": name,
        "active_since": active_since,
        "active_till": active_till,
        "timeperiods": timeperiods,
        "groupids": groupids,
        "hostids": hostids,
        "description": description,
    })
    async with ZabbixClient() as client:
        return await client.call("maintenance.update", params)


@mcp.tool(
    name="zabbix_maintenance_delete",
    description=(
        "DESTRUCTIVE — Permanently delete Zabbix maintenance windows. "
        "Hosts currently in maintenance will immediately resume alerting. "
        "Returns the deleted maintenance IDs."
    ),
    annotations=DELETE,
)
async def zabbix_maintenance_delete(
    maintenanceids: Annotated[list[str], Field(description="IDs of maintenance windows to delete.")],
) -> dict[str, Any]:
    """Permanently delete Zabbix maintenance windows."""
    async with ZabbixClient() as client:
        return await client.call("maintenance.delete", maintenanceids)
