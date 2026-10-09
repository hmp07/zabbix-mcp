"""Zabbix MCP tools — Triggers (read, write, delete)."""

from __future__ import annotations
from typing import Annotated, Any
from pydantic import Field
from ..client import ZabbixClient
from ..app import mcp
from ._annotations import DELETE, READ_ONLY, WRITE, WRITE_IDEMPOTENT
from ._params import as_int_flag, compact, filter_params, search_params


@mcp.tool(name="zabbix_trigger_get", description="List Zabbix triggers. Filter by host, group, status, severity, or current value. Use value=1 to see only triggers in PROBLEM state.", annotations=READ_ONLY)
async def zabbix_trigger_get(
    triggerids: Annotated[list[str] | None, Field(description="Return only triggers with these IDs.")] = None,
    hostids: Annotated[list[str] | None, Field(description="Return triggers for these host IDs.")] = None,
    groupids: Annotated[list[str] | None, Field(description="Return triggers on hosts in these group IDs.")] = None,
    templateids: Annotated[list[str] | None, Field(description="Return triggers from these template IDs.")] = None,
    status: Annotated[int | None, Field(description="0=enabled, 1=disabled.", ge=0, le=1)] = None,
    value: Annotated[int | None, Field(description="0=OK, 1=PROBLEM.", ge=0, le=1)] = None,
    priority: Annotated[int | None, Field(description="0=not classified, 1=info, 2=warning, 3=average, 4=high, 5=disaster.", ge=0, le=5)] = None,
    only_true: Annotated[bool | None, Field(description="If true, return only triggers that have been in PROBLEM at least once.")] = None,
    name: Annotated[str | None, Field(description="Search by trigger description (substring match).")] = None,
    limit: Annotated[int, Field(description="Maximum number of results.", ge=1, le=1000)] = 100,
    output: Annotated[list[str], Field(description="Fields to return.")] = ["triggerid", "description", "expression", "priority", "status", "value"],
) -> list[dict[str, Any]]:
    params = compact({
        "output": output,
        "limit": limit,
        "triggerids": triggerids,
        "hostids": hostids,
        "groupids": groupids,
        "templateids": templateids,
        "only_true": as_int_flag(only_true),
    })
    params.update(filter_params(status=status, value=value, priority=priority))
    params.update(search_params(description=name))
    async with ZabbixClient() as client:
        return await client.call("trigger.get", params)


@mcp.tool(name="zabbix_trigger_create", description="Create a new Zabbix trigger. Expression must use Zabbix trigger syntax, e.g. 'last(/host/system.cpu.util)>90'.", annotations=WRITE)
async def zabbix_trigger_create(
    description: Annotated[str, Field(description="Trigger name.")],
    expression: Annotated[str, Field(description="Trigger expression.")],
    priority: Annotated[int, Field(description="0=not classified, 1=info, 2=warning, 3=average, 4=high, 5=disaster.", ge=0, le=5)] = 2,
    status: Annotated[int, Field(description="0=enabled, 1=disabled.", ge=0, le=1)] = 0,
    tags: Annotated[list[dict[str, Any]] | None, Field(description="Trigger tags.")]=None,
    dependencies: Annotated[list[dict[str, Any]] | None, Field(description="Trigger dependencies.")]=None,
    comments: Annotated[str | None, Field(description="Extended description.")]=None,
    url: Annotated[str | None, Field(description="URL (e.g. runbook link).")]=None,
    recovery_mode: Annotated[int | None, Field(description="0=expression, 1=recovery expression, 2=none.", ge=0, le=2)]=None,
    recovery_expression: Annotated[str | None, Field(description="Recovery expression.")]=None,
) -> dict[str, Any]:
    params = compact({
        "description": description,
        "expression": expression,
        "priority": priority,
        "status": status,
        "tags": tags,
        "dependencies": dependencies,
        "comments": comments,
        "url": url,
        "recovery_mode": recovery_mode,
        "recovery_expression": recovery_expression,
    })
    async with ZabbixClient() as client:
        return await client.call("trigger.create", params)


@mcp.tool(name="zabbix_trigger_update", description="Update an existing Zabbix trigger. Only provided fields are changed.", annotations=WRITE_IDEMPOTENT)
async def zabbix_trigger_update(
    triggerid: Annotated[str, Field(description="ID of the trigger to update.")],
    description: Annotated[str | None, Field(description="New description.")]=None,
    expression: Annotated[str | None, Field(description="New expression.")]=None,
    priority: Annotated[int | None, Field(description="New severity.", ge=0, le=5)]=None,
    status: Annotated[int | None, Field(description="0=enabled, 1=disabled.", ge=0, le=1)]=None,
    tags: Annotated[list[dict[str, Any]] | None, Field(description="Replace tags.")]=None,
    comments: Annotated[str | None, Field(description="New description.")]=None,
    url: Annotated[str | None, Field(description="New URL.")]=None,
) -> dict[str, Any]:
    params = compact({
        "triggerid": triggerid,
        "description": description,
        "expression": expression,
        "priority": priority,
        "status": status,
        "tags": tags,
        "comments": comments,
        "url": url,
    })
    async with ZabbixClient() as client:
        return await client.call("trigger.update", params)


@mcp.tool(name="zabbix_trigger_delete", description="⚠️ DESTRUCTIVE — Permanently delete Zabbix triggers. Cannot be undone.", annotations=DELETE)
async def zabbix_trigger_delete(triggerids: Annotated[list[str], Field(description="IDs of triggers to delete.")]) -> dict[str, Any]:
    async with ZabbixClient() as client:
        return await client.call("trigger.delete", triggerids)
