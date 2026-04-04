"""Zabbix MCP tools — Triggers (read, write, delete)."""

from __future__ import annotations
from typing import Annotated, Any
from pydantic import Field
from ..client import ZabbixClient
from ..app import mcp

_READ_ONLY = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_WRITE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False}
_WRITE_IDEMPOTENT = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_DELETE = {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": False}


@mcp.tool(name="zabbix_trigger_get", description="List Zabbix triggers. Filter by host, group, status, severity, or current value. Use value=1 to see only triggers in PROBLEM state.", annotations=_READ_ONLY)
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
    params: dict[str, Any] = {"output": output, "limit": limit}
    if triggerids is not None: params["triggerids"] = triggerids
    if hostids is not None: params["hostids"] = hostids
    if groupids is not None: params["groupids"] = groupids
    if templateids is not None: params["templateids"] = templateids
    filter_: dict[str, Any] = {}
    if status is not None: filter_["status"] = status
    if value is not None: filter_["value"] = value
    if priority is not None: filter_["priority"] = priority
    if filter_: params["filter"] = filter_
    if only_true is not None: params["only_true"] = 1 if only_true else 0
    if name is not None: params["search"] = {"description": name}
    async with ZabbixClient() as client:
        return await client.call("trigger.get", params)


@mcp.tool(name="zabbix_trigger_create", description="Create a new Zabbix trigger. Expression must use Zabbix trigger syntax, e.g. 'last(/host/system.cpu.util)>90'.", annotations=_WRITE)
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
    params: dict[str, Any] = {"description": description, "expression": expression, "priority": priority, "status": status}
    if tags is not None: params["tags"] = tags
    if dependencies is not None: params["dependencies"] = dependencies
    if comments is not None: params["comments"] = comments
    if url is not None: params["url"] = url
    if recovery_mode is not None: params["recovery_mode"] = recovery_mode
    if recovery_expression is not None: params["recovery_expression"] = recovery_expression
    async with ZabbixClient() as client:
        return await client.call("trigger.create", params)


@mcp.tool(name="zabbix_trigger_update", description="Update an existing Zabbix trigger. Only provided fields are changed.", annotations=_WRITE_IDEMPOTENT)
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
    params: dict[str, Any] = {"triggerid": triggerid}
    if description is not None: params["description"] = description
    if expression is not None: params["expression"] = expression
    if priority is not None: params["priority"] = priority
    if status is not None: params["status"] = status
    if tags is not None: params["tags"] = tags
    if comments is not None: params["comments"] = comments
    if url is not None: params["url"] = url
    async with ZabbixClient() as client:
        return await client.call("trigger.update", params)


@mcp.tool(name="zabbix_trigger_delete", description="⚠️ DESTRUCTIVE — Permanently delete Zabbix triggers. Cannot be undone.", annotations=_DELETE)
async def zabbix_trigger_delete(triggerids: Annotated[list[str], Field(description="IDs of triggers to delete.")]) -> dict[str, Any]:
    async with ZabbixClient() as client:
        return await client.call("trigger.delete", triggerids)
