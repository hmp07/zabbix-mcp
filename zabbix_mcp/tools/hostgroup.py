"""Zabbix MCP tools — Host Groups (read, write, delete)."""

from __future__ import annotations
from typing import Annotated, Any
from pydantic import Field
from ..client import ZabbixClient
from ..app import mcp

_READ_ONLY = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_WRITE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False}
_WRITE_IDEMPOTENT = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_DELETE = {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": False}


@mcp.tool(name="zabbix_hostgroup_get", description="List Zabbix host groups. Filter by group ID, name, or by hosts they contain.", annotations=_READ_ONLY)
async def zabbix_hostgroup_get(
    groupids: Annotated[list[str] | None, Field(description="Return only groups with these IDs.")] = None,
    hostids: Annotated[list[str] | None, Field(description="Return groups containing these host IDs.")] = None,
    templateids: Annotated[list[str] | None, Field(description="Return groups containing these template IDs.")] = None,
    name: Annotated[str | None, Field(description="Search by group name (substring match).")] = None,
    real_hosts: Annotated[bool | None, Field(description="If true, return only groups with real hosts.")] = None,
    limit: Annotated[int, Field(description="Maximum number of results.", ge=1, le=1000)] = 100,
    output: Annotated[list[str], Field(description="Fields to return.")] = ["groupid", "name"],
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"output": output, "limit": limit}
    if groupids is not None: params["groupids"] = groupids
    if hostids is not None: params["hostids"] = hostids
    if templateids is not None: params["templateids"] = templateids
    if name is not None: params["search"] = {"name": name}
    if real_hosts is not None: params["real_hosts"] = 1 if real_hosts else 0
    async with ZabbixClient() as client:
        return await client.call("hostgroup.get", params)


@mcp.tool(name="zabbix_hostgroup_create", description="Create a new Zabbix host group.", annotations=_WRITE)
async def zabbix_hostgroup_create(name: Annotated[str, Field(description="Name of the new host group.")]) -> dict[str, Any]:
    async with ZabbixClient() as client:
        return await client.call("hostgroup.create", {"name": name})


@mcp.tool(name="zabbix_hostgroup_update", description="Rename an existing Zabbix host group.", annotations=_WRITE_IDEMPOTENT)
async def zabbix_hostgroup_update(
    groupid: Annotated[str, Field(description="ID of the host group to update.")],
    name: Annotated[str, Field(description="New name.")],
) -> dict[str, Any]:
    async with ZabbixClient() as client:
        return await client.call("hostgroup.update", {"groupid": groupid, "name": name})


@mcp.tool(name="zabbix_hostgroup_delete", description="⚠️ DESTRUCTIVE — Permanently delete Zabbix host groups. Groups containing hosts cannot be deleted.", annotations=_DELETE)
async def zabbix_hostgroup_delete(groupids: Annotated[list[str], Field(description="IDs of host groups to delete.")]) -> dict[str, Any]:
    async with ZabbixClient() as client:
        return await client.call("hostgroup.delete", groupids)
