"""Zabbix MCP tools — Host Groups (read, write, delete)."""

from __future__ import annotations
from typing import Annotated, Any
from pydantic import Field
from ..client import shared_session
from ..app import mcp
from ._annotations import DELETE, READ_ONLY, WRITE, WRITE_IDEMPOTENT
from ._params import as_int_flag, compact, search_params


@mcp.tool(name="zabbix_hostgroup_get", description="List Zabbix host groups. Filter by group ID, name, or by hosts they contain.", annotations=READ_ONLY)
async def zabbix_hostgroup_get(
    groupids: Annotated[list[str] | None, Field(description="Return only groups with these IDs.")] = None,
    hostids: Annotated[list[str] | None, Field(description="Return groups containing these host IDs.")] = None,
    templateids: Annotated[list[str] | None, Field(description="Return groups containing these template IDs.")] = None,
    name: Annotated[str | None, Field(description="Search by group name (substring match).")] = None,
    real_hosts: Annotated[bool | None, Field(description="If true, return only groups with real hosts.")] = None,
    limit: Annotated[int, Field(description="Maximum number of results.", ge=1, le=1000)] = 100,
    output: Annotated[list[str], Field(description="Fields to return.")] = ["groupid", "name"],
) -> list[dict[str, Any]]:
    params = compact({
        "output": output,
        "limit": limit,
        "groupids": groupids,
        "hostids": hostids,
        "templateids": templateids,
        "real_hosts": as_int_flag(real_hosts),
    })
    params.update(search_params(name=name))
    async with shared_session() as client:
        return await client.call("hostgroup.get", params)


@mcp.tool(name="zabbix_hostgroup_create", description="Create a new Zabbix host group.", annotations=WRITE)
async def zabbix_hostgroup_create(name: Annotated[str, Field(description="Name of the new host group.")]) -> dict[str, Any]:
    async with shared_session() as client:
        return await client.call("hostgroup.create", {"name": name})


@mcp.tool(name="zabbix_hostgroup_update", description="Rename an existing Zabbix host group.", annotations=WRITE_IDEMPOTENT)
async def zabbix_hostgroup_update(
    groupid: Annotated[str, Field(description="ID of the host group to update.")],
    name: Annotated[str, Field(description="New name.")],
) -> dict[str, Any]:
    async with shared_session() as client:
        return await client.call("hostgroup.update", {"groupid": groupid, "name": name})


@mcp.tool(name="zabbix_hostgroup_delete", description="⚠️ DESTRUCTIVE — Permanently delete Zabbix host groups. Groups containing hosts cannot be deleted.", annotations=DELETE)
async def zabbix_hostgroup_delete(groupids: Annotated[list[str], Field(description="IDs of host groups to delete.")]) -> dict[str, Any]:
    async with shared_session() as client:
        return await client.call("hostgroup.delete", groupids)
