"""Zabbix MCP tools — Monitoring (problems, events, history, trends, alerts)."""

from __future__ import annotations
from typing import Annotated, Any
from pydantic import Field
from ..client import ZabbixClient
from ..app import mcp

_READ_ONLY = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_WRITE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False}


@mcp.tool(name="zabbix_problem_get", description="List active Zabbix problems (open alerts). Filter by host, group, severity, or time range.", annotations=_READ_ONLY)
async def zabbix_problem_get(
    eventids: Annotated[list[str] | None, Field(description="Return only problems with these event IDs.")] = None,
    groupids: Annotated[list[str] | None, Field(description="Return problems on hosts in these group IDs.")] = None,
    hostids: Annotated[list[str] | None, Field(description="Return problems on these host IDs.")] = None,
    objectids: Annotated[list[str] | None, Field(description="Return problems caused by these trigger IDs.")] = None,
    severities: Annotated[list[int] | None, Field(description="Filter by severities: 0=not classified, 1=info, 2=warning, 3=average, 4=high, 5=disaster.")] = None,
    time_from: Annotated[int | None, Field(description="Return problems after this Unix timestamp.")] = None,
    time_till: Annotated[int | None, Field(description="Return problems before this Unix timestamp.")] = None,
    recent: Annotated[bool | None, Field(description="If true, return only problems from the last hour.")] = None,
    limit: Annotated[int, Field(description="Maximum number of results.", ge=1, le=1000)] = 100,
    output: Annotated[list[str], Field(description="Fields to return.")] = ["eventid", "objectid", "name", "severity", "clock", "acknowledged"],
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"output": output, "limit": limit}
    if eventids is not None: params["eventids"] = eventids
    if groupids is not None: params["groupids"] = groupids
    if hostids is not None: params["hostids"] = hostids
    if objectids is not None: params["objectids"] = objectids
    if severities is not None: params["severities"] = severities
    if time_from is not None: params["time_from"] = time_from
    if time_till is not None: params["time_till"] = time_till
    if recent: params["recent"] = True
    async with ZabbixClient() as client:
        return await client.call("problem.get", params)


@mcp.tool(name="zabbix_event_get", description="List Zabbix events (state changes). Unlike problems, events include resolved and historical entries.", annotations=_READ_ONLY)
async def zabbix_event_get(
    eventids: Annotated[list[str] | None, Field(description="Return only events with these IDs.")] = None,
    groupids: Annotated[list[str] | None, Field(description="Return events on hosts in these group IDs.")] = None,
    hostids: Annotated[list[str] | None, Field(description="Return events on these host IDs.")] = None,
    objectids: Annotated[list[str] | None, Field(description="Return events from these trigger IDs.")] = None,
    value: Annotated[int | None, Field(description="0=OK, 1=PROBLEM.", ge=0, le=1)] = None,
    severities: Annotated[list[int] | None, Field(description="Filter by severities.")] = None,
    time_from: Annotated[int | None, Field(description="Return events after this Unix timestamp.")] = None,
    time_till: Annotated[int | None, Field(description="Return events before this Unix timestamp.")] = None,
    limit: Annotated[int, Field(description="Maximum number of results.", ge=1, le=1000)] = 100,
    output: Annotated[list[str], Field(description="Fields to return.")] = ["eventid", "objectid", "name", "source", "object", "value", "severity", "clock"],
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"output": output, "limit": limit}
    if eventids is not None: params["eventids"] = eventids
    if groupids is not None: params["groupids"] = groupids
    if hostids is not None: params["hostids"] = hostids
    if objectids is not None: params["objectids"] = objectids
    if value is not None: params["value"] = value
    if severities is not None: params["severities"] = severities
    if time_from is not None: params["time_from"] = time_from
    if time_till is not None: params["time_till"] = time_till
    async with ZabbixClient() as client:
        return await client.call("event.get", params)


@mcp.tool(name="zabbix_history_get", description="Retrieve raw historical values for Zabbix items. history type: 0=float, 1=string, 2=log, 3=unsigned int, 4=text.", annotations=_READ_ONLY)
async def zabbix_history_get(
    itemids: Annotated[list[str], Field(description="Return history for these item IDs.")],
    history: Annotated[int, Field(description="Value type: 0=float, 1=string, 2=log, 3=unsigned int, 4=text.", ge=0, le=4)] = 3,
    time_from: Annotated[int | None, Field(description="Return values after this Unix timestamp.")] = None,
    time_till: Annotated[int | None, Field(description="Return values before this Unix timestamp.")] = None,
    sortorder: Annotated[str, Field(description="'ASC' or 'DESC'.")] = "DESC",
    limit: Annotated[int, Field(description="Maximum number of results.", ge=1, le=1000)] = 100,
    output: Annotated[list[str], Field(description="Fields to return.")] = ["itemid", "clock", "value", "ns"],
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"output": output, "limit": limit, "history": history, "itemids": itemids, "sortfield": "clock", "sortorder": sortorder}
    if time_from is not None: params["time_from"] = time_from
    if time_till is not None: params["time_till"] = time_till
    async with ZabbixClient() as client:
        return await client.call("history.get", params)


@mcp.tool(name="zabbix_trend_get", description="Retrieve aggregated trend data (min/avg/max) for Zabbix items over hourly intervals. type: 0=float, 3=unsigned int.", annotations=_READ_ONLY)
async def zabbix_trend_get(
    itemids: Annotated[list[str], Field(description="Return trends for these item IDs.")],
    type: Annotated[int, Field(description="0=float, 3=unsigned int.", ge=0, le=3)] = 3,
    time_from: Annotated[int | None, Field(description="Return values after this Unix timestamp.")] = None,
    time_till: Annotated[int | None, Field(description="Return values before this Unix timestamp.")] = None,
    limit: Annotated[int, Field(description="Maximum number of results.", ge=1, le=1000)] = 100,
    output: Annotated[list[str], Field(description="Fields to return.")] = ["itemid", "clock", "num", "value_min", "value_avg", "value_max"],
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"output": output, "limit": limit, "type": type, "itemids": itemids}
    if time_from is not None: params["time_from"] = time_from
    if time_till is not None: params["time_till"] = time_till
    async with ZabbixClient() as client:
        return await client.call("trend.get", params)


@mcp.tool(name="zabbix_alert_get", description="List Zabbix alerts (notifications already sent — email, webhook, etc.). Use to diagnose why an alert was or was not sent.", annotations=_READ_ONLY)
async def zabbix_alert_get(
    alertids: Annotated[list[str] | None, Field(description="Return only alerts with these IDs.")] = None,
    eventids: Annotated[list[str] | None, Field(description="Return alerts for these event IDs.")] = None,
    groupids: Annotated[list[str] | None, Field(description="Return alerts for hosts in these group IDs.")] = None,
    hostids: Annotated[list[str] | None, Field(description="Return alerts for these host IDs.")] = None,
    mediatypeids: Annotated[list[str] | None, Field(description="Return alerts sent via these media type IDs.")] = None,
    time_from: Annotated[int | None, Field(description="Return alerts after this Unix timestamp.")] = None,
    time_till: Annotated[int | None, Field(description="Return alerts before this Unix timestamp.")] = None,
    limit: Annotated[int, Field(description="Maximum number of results.", ge=1, le=1000)] = 100,
    output: Annotated[list[str], Field(description="Fields to return.")] = ["alertid", "eventid", "userid", "mediatypeid", "sendto", "subject", "status", "clock"],
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"output": output, "limit": limit}
    if alertids is not None: params["alertids"] = alertids
    if eventids is not None: params["eventids"] = eventids
    if groupids is not None: params["groupids"] = groupids
    if hostids is not None: params["hostids"] = hostids
    if mediatypeids is not None: params["mediatypeids"] = mediatypeids
    if time_from is not None: params["time_from"] = time_from
    if time_till is not None: params["time_till"] = time_till
    async with ZabbixClient() as client:
        return await client.call("alert.get", params)


@mcp.tool(name="zabbix_event_acknowledge", description="Acknowledge, close, or add a message to Zabbix events. action bitmask: 1=close, 2=acknowledge, 4=add message, 8=change severity, 16=unacknowledge.", annotations=_WRITE)
async def zabbix_event_acknowledge(
    eventids: Annotated[list[str], Field(description="IDs of events to act on.")],
    action: Annotated[int, Field(description="Bitmask: 1=close, 2=acknowledge, 4=message, 8=change severity, 16=unacknowledge.", ge=1)],
    message: Annotated[str | None, Field(description="Message text (required if action includes 4).")]=None,
    severity: Annotated[int | None, Field(description="New severity (required if action includes 8).", ge=0, le=5)]=None,
) -> dict[str, Any]:
    params: dict[str, Any] = {"eventids": eventids, "action": action}
    if message is not None: params["message"] = message
    if severity is not None: params["severity"] = severity
    async with ZabbixClient() as client:
        return await client.call("event.acknowledge", params)
