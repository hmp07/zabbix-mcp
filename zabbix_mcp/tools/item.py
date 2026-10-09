"""Zabbix MCP tools — Items (read, write, delete)."""

from __future__ import annotations
from typing import Annotated, Any
from pydantic import Field
from ..client import shared_session
from ..app import mcp
from ._annotations import DELETE, READ_ONLY, WRITE, WRITE_IDEMPOTENT
from ._params import compact, filter_params, search_params


@mcp.tool(name="zabbix_item_get", description="List Zabbix items (metrics). Filter by host, group, template, item key, or name.", annotations=READ_ONLY)
async def zabbix_item_get(
    itemids: Annotated[list[str] | None, Field(description="Return only items with these IDs.")] = None,
    hostids: Annotated[list[str] | None, Field(description="Return items belonging to these host IDs.")] = None,
    groupids: Annotated[list[str] | None, Field(description="Return items on hosts in these group IDs.")] = None,
    templateids: Annotated[list[str] | None, Field(description="Return items inherited from these template IDs.")] = None,
    name: Annotated[str | None, Field(description="Search by item name (substring match).")] = None,
    key_: Annotated[str | None, Field(description="Search by item key (substring match).")] = None,
    status: Annotated[int | None, Field(description="0=enabled, 1=disabled.", ge=0, le=1)] = None,
    limit: Annotated[int, Field(description="Maximum number of results.", ge=1, le=1000)] = 100,
    output: Annotated[list[str], Field(description="Fields to return.")] = ["itemid", "hostid", "name", "key_", "type", "value_type", "status", "state"],
) -> list[dict[str, Any]]:
    params = compact({
        "output": output,
        "limit": limit,
        "itemids": itemids,
        "hostids": hostids,
        "groupids": groupids,
        "templateids": templateids,
    })
    params.update(filter_params(status=status))
    params.update(search_params(name=name, key_=key_))
    async with shared_session() as client:
        return await client.call("item.get", params)


@mcp.tool(name="zabbix_item_create", description="Create a new Zabbix item on a host. type: 0=agent, 2=trapper, 7=external, 14=active agent, 17=calculated, 18=dependent, 19=HTTP, 20=SNMP. value_type: 0=float, 1=char, 2=log, 3=unsigned int, 4=text.", annotations=WRITE)
async def zabbix_item_create(
    hostid: Annotated[str, Field(description="ID of the host.")],
    name: Annotated[str, Field(description="Item name.")],
    key_: Annotated[str, Field(description="Item key.")],
    type: Annotated[int, Field(description="Item type.", ge=0)],
    value_type: Annotated[int, Field(description="0=float, 1=char, 2=log, 3=unsigned int, 4=text.", ge=0, le=4)],
    interfaceid: Annotated[str | None, Field(description="Interface ID.")] = None,
    delay: Annotated[str | None, Field(description="Collection interval. Example: '30s'.")]=None,
    history: Annotated[str | None, Field(description="History retention. Example: '7d'.")]=None,
    trends: Annotated[str | None, Field(description="Trend retention. Example: '365d'.")]=None,
    units: Annotated[str | None, Field(description="Units. Example: 'B', '%'.")]=None,
    tags: Annotated[list[dict[str, Any]] | None, Field(description="Item tags.")]=None,
    status: Annotated[int, Field(description="0=enabled, 1=disabled.", ge=0, le=1)]=0,
    description: Annotated[str | None, Field(description="Description.")]=None,
) -> dict[str, Any]:
    params = compact({
        "hostid": hostid,
        "name": name,
        "key_": key_,
        "type": type,
        "value_type": value_type,
        "status": status,
        "interfaceid": interfaceid,
        "delay": delay,
        "history": history,
        "trends": trends,
        "units": units,
        "tags": tags,
        "description": description,
    })
    async with shared_session() as client:
        return await client.call("item.create", params)


@mcp.tool(name="zabbix_item_update", description="Update an existing Zabbix item. Only provided fields are changed.", annotations=WRITE_IDEMPOTENT)
async def zabbix_item_update(
    itemid: Annotated[str, Field(description="ID of the item to update.")],
    name: Annotated[str | None, Field(description="New name.")]=None,
    key_: Annotated[str | None, Field(description="New key.")]=None,
    type: Annotated[int | None, Field(description="New type.", ge=0)]=None,
    value_type: Annotated[int | None, Field(description="New value type.", ge=0, le=4)]=None,
    delay: Annotated[str | None, Field(description="New interval.")]=None,
    history: Annotated[str | None, Field(description="New history retention.")]=None,
    trends: Annotated[str | None, Field(description="New trend retention.")]=None,
    units: Annotated[str | None, Field(description="New units.")]=None,
    status: Annotated[int | None, Field(description="0=enabled, 1=disabled.", ge=0, le=1)]=None,
    tags: Annotated[list[dict[str, Any]] | None, Field(description="Replace tags.")]=None,
    description: Annotated[str | None, Field(description="New description.")]=None,
) -> dict[str, Any]:
    params = compact({
        "itemid": itemid,
        "name": name,
        "key_": key_,
        "type": type,
        "value_type": value_type,
        "delay": delay,
        "history": history,
        "trends": trends,
        "units": units,
        "status": status,
        "tags": tags,
        "description": description,
    })
    async with shared_session() as client:
        return await client.call("item.update", params)


@mcp.tool(name="zabbix_item_delete", description="⚠️ DESTRUCTIVE — Permanently delete Zabbix items and all their history. Cannot be undone.", annotations=DELETE)
async def zabbix_item_delete(itemids: Annotated[list[str], Field(description="IDs of items to delete.")]) -> dict[str, Any]:
    async with shared_session() as client:
        return await client.call("item.delete", itemids)
