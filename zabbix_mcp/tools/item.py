"""Zabbix MCP tools — Items (read, write, delete)."""

from __future__ import annotations
from typing import Annotated, Any
from pydantic import Field
from ..client import ZabbixClient
from ..app import mcp

_READ_ONLY = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_WRITE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False}
_WRITE_IDEMPOTENT = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_DELETE = {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": False}


@mcp.tool(name="zabbix_item_get", description="List Zabbix items (metrics). Filter by host, group, template, item key, or name.", annotations=_READ_ONLY)
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
    params: dict[str, Any] = {"output": output, "limit": limit}
    if itemids is not None: params["itemids"] = itemids
    if hostids is not None: params["hostids"] = hostids
    if groupids is not None: params["groupids"] = groupids
    if templateids is not None: params["templateids"] = templateids
    if status is not None: params["filter"] = {"status": status}
    search: dict[str, str] = {}
    if name is not None: search["name"] = name
    if key_ is not None: search["key_"] = key_
    if search: params["search"] = search
    async with ZabbixClient() as client:
        return await client.call("item.get", params)


@mcp.tool(name="zabbix_item_create", description="Create a new Zabbix item on a host. type: 0=agent, 2=trapper, 7=external, 14=active agent, 17=calculated, 18=dependent, 19=HTTP, 20=SNMP. value_type: 0=float, 1=char, 2=log, 3=unsigned int, 4=text.", annotations=_WRITE)
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
    params: dict[str, Any] = {"hostid": hostid, "name": name, "key_": key_, "type": type, "value_type": value_type, "status": status}
    if interfaceid is not None: params["interfaceid"] = interfaceid
    if delay is not None: params["delay"] = delay
    if history is not None: params["history"] = history
    if trends is not None: params["trends"] = trends
    if units is not None: params["units"] = units
    if tags is not None: params["tags"] = tags
    if description is not None: params["description"] = description
    async with ZabbixClient() as client:
        return await client.call("item.create", params)


@mcp.tool(name="zabbix_item_update", description="Update an existing Zabbix item. Only provided fields are changed.", annotations=_WRITE_IDEMPOTENT)
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
    params: dict[str, Any] = {"itemid": itemid}
    if name is not None: params["name"] = name
    if key_ is not None: params["key_"] = key_
    if type is not None: params["type"] = type
    if value_type is not None: params["value_type"] = value_type
    if delay is not None: params["delay"] = delay
    if history is not None: params["history"] = history
    if trends is not None: params["trends"] = trends
    if units is not None: params["units"] = units
    if status is not None: params["status"] = status
    if tags is not None: params["tags"] = tags
    if description is not None: params["description"] = description
    async with ZabbixClient() as client:
        return await client.call("item.update", params)


@mcp.tool(name="zabbix_item_delete", description="⚠️ DESTRUCTIVE — Permanently delete Zabbix items and all their history. Cannot be undone.", annotations=_DELETE)
async def zabbix_item_delete(itemids: Annotated[list[str], Field(description="IDs of items to delete.")]) -> dict[str, Any]:
    async with ZabbixClient() as client:
        return await client.call("item.delete", itemids)
