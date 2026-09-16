"""Zabbix MCP tools — Hosts and Host Interfaces (read, write, delete)."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from ..client import ZabbixClient
from ..app import mcp
from ._annotations import DELETE, READ_ONLY, WRITE, WRITE_IDEMPOTENT


@mcp.tool(
    name="zabbix_host_get",
    description=(
        "Find and list Zabbix hosts. Filter by name, group, status, or linked template. "
        "Returns monitored and unmonitored hosts matching the given criteria."
    ),
    annotations=READ_ONLY,
)
async def zabbix_host_get(
    hostids: Annotated[list[str] | None, Field(description="Return only hosts with these IDs.")] = None,
    groupids: Annotated[list[str] | None, Field(description="Return hosts that belong to these host group IDs.")] = None,
    templateids: Annotated[list[str] | None, Field(description="Return hosts linked to these template IDs.")] = None,
    status: Annotated[int | None, Field(description="Filter by status: 0=monitored, 1=not monitored.", ge=0, le=1)] = None,
    name: Annotated[str | None, Field(description="Search by visible name (substring match). Example: 'web-server'.")] = None,
    limit: Annotated[int, Field(description="Maximum number of results.", ge=1, le=1000)] = 100,
    output: Annotated[list[str], Field(description="Fields to return.")] = ["hostid", "host", "name", "status"],
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"output": output, "limit": limit}
    if hostids is not None:
        params["hostids"] = hostids
    if groupids is not None:
        params["groupids"] = groupids
    if templateids is not None:
        params["templateids"] = templateids
    if status is not None:
        params["filter"] = {"status": status}
    if name is not None:
        params["search"] = {"name": name}
    async with ZabbixClient() as client:
        return await client.call("host.get", params)


@mcp.tool(
    name="zabbix_host_interface_get",
    description=(
        "List network interfaces for one or more Zabbix hosts. "
        "Returns IP, DNS, port, and interface type (Agent/SNMP/IPMI/JMX)."
    ),
    annotations=READ_ONLY,
)
async def zabbix_host_interface_get(
    hostids: Annotated[list[str] | None, Field(description="Return interfaces for these host IDs.")] = None,
    interfaceids: Annotated[list[str] | None, Field(description="Return only interfaces with these IDs.")] = None,
    type: Annotated[int | None, Field(description="Interface type: 1=Agent, 2=SNMP, 3=IPMI, 4=JMX.", ge=1, le=4)] = None,
    limit: Annotated[int, Field(description="Maximum number of results.", ge=1, le=1000)] = 100,
    output: Annotated[list[str], Field(description="Fields to return.")] = [
        "interfaceid", "hostid", "ip", "dns", "port", "type", "main", "useip",
    ],
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"output": output, "limit": limit}
    if hostids is not None:
        params["hostids"] = hostids
    if interfaceids is not None:
        params["interfaceids"] = interfaceids
    if type is not None:
        params["filter"] = {"type": type}
    async with ZabbixClient() as client:
        return await client.call("hostinterface.get", params)


@mcp.tool(name="zabbix_host_create", description="Create a new Zabbix host. Requires a hostname, at least one host group, and typically a network interface. Returns the new host ID.", annotations=WRITE)
async def zabbix_host_create(
    host: Annotated[str, Field(description="Technical hostname (unique).")],
    groups: Annotated[list[dict[str, Any]], Field(description="Host groups to assign. Example: [{'groupid': '2'}].")],
    interfaces: Annotated[list[dict[str, Any]] | None, Field(description="Network interfaces.")] = None,
    templates: Annotated[list[dict[str, Any]] | None, Field(description="Templates to link.")] = None,
    name: Annotated[str | None, Field(description="Visible name.")] = None,
    status: Annotated[int, Field(description="0=monitored (default), 1=not monitored.", ge=0, le=1)] = 0,
    tags: Annotated[list[dict[str, Any]] | None, Field(description="Host tags.")] = None,
    macros: Annotated[list[dict[str, Any]] | None, Field(description="Host macros.")] = None,
    description: Annotated[str | None, Field(description="Host description.")] = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {"host": host, "groups": groups, "status": status}
    if interfaces is not None: params["interfaces"] = interfaces
    if templates is not None: params["templates"] = templates
    if name is not None: params["name"] = name
    if tags is not None: params["tags"] = tags
    if macros is not None: params["macros"] = macros
    if description is not None: params["description"] = description
    async with ZabbixClient() as client:
        return await client.call("host.create", params)


@mcp.tool(name="zabbix_host_update", description="Update an existing Zabbix host. Only the fields you provide are changed.", annotations=WRITE_IDEMPOTENT)
async def zabbix_host_update(
    hostid: Annotated[str, Field(description="ID of the host to update.")],
    host: Annotated[str | None, Field(description="New technical hostname.")] = None,
    name: Annotated[str | None, Field(description="New visible name.")] = None,
    status: Annotated[int | None, Field(description="0=monitored, 1=not monitored.", ge=0, le=1)] = None,
    groups: Annotated[list[dict[str, Any]] | None, Field(description="Replace host group assignments.")] = None,
    templates: Annotated[list[dict[str, Any]] | None, Field(description="Replace linked templates.")] = None,
    tags: Annotated[list[dict[str, Any]] | None, Field(description="Replace host tags.")] = None,
    macros: Annotated[list[dict[str, Any]] | None, Field(description="Replace host macros.")] = None,
    description: Annotated[str | None, Field(description="New description.")] = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {"hostid": hostid}
    if host is not None: params["host"] = host
    if name is not None: params["name"] = name
    if status is not None: params["status"] = status
    if groups is not None: params["groups"] = groups
    if templates is not None: params["templates"] = templates
    if tags is not None: params["tags"] = tags
    if macros is not None: params["macros"] = macros
    if description is not None: params["description"] = description
    async with ZabbixClient() as client:
        return await client.call("host.update", params)


@mcp.tool(name="zabbix_host_interface_create", description="Add a network interface to a Zabbix host.", annotations=WRITE)
async def zabbix_host_interface_create(
    hostid: Annotated[str, Field(description="ID of the host.")],
    type: Annotated[int, Field(description="1=Agent, 2=SNMP, 3=IPMI, 4=JMX.", ge=1, le=4)],
    main: Annotated[int, Field(description="1=default, 0=additional.", ge=0, le=1)],
    useip: Annotated[int, Field(description="1=IP, 0=DNS.", ge=0, le=1)],
    ip: Annotated[str, Field(description="IP address.")],
    dns: Annotated[str, Field(description="DNS name.")],
    port: Annotated[str, Field(description="Port. Example: '10050'.")],
    details: Annotated[dict[str, Any] | None, Field(description="SNMP details.")] = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {"hostid": hostid, "type": type, "main": main, "useip": useip, "ip": ip, "dns": dns, "port": port}
    if details is not None: params["details"] = details
    async with ZabbixClient() as client:
        return await client.call("hostinterface.create", params)


@mcp.tool(name="zabbix_host_interface_update", description="Update an existing Zabbix host interface.", annotations=WRITE_IDEMPOTENT)
async def zabbix_host_interface_update(
    interfaceid: Annotated[str, Field(description="ID of the interface to update.")],
    ip: Annotated[str | None, Field(description="New IP address.")] = None,
    dns: Annotated[str | None, Field(description="New DNS name.")] = None,
    port: Annotated[str | None, Field(description="New port.")] = None,
    main: Annotated[int | None, Field(description="1=default, 0=not default.", ge=0, le=1)] = None,
    useip: Annotated[int | None, Field(description="1=IP, 0=DNS.", ge=0, le=1)] = None,
    details: Annotated[dict[str, Any] | None, Field(description="Updated SNMP details.")] = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {"interfaceid": interfaceid}
    if ip is not None: params["ip"] = ip
    if dns is not None: params["dns"] = dns
    if port is not None: params["port"] = port
    if main is not None: params["main"] = main
    if useip is not None: params["useip"] = useip
    if details is not None: params["details"] = details
    async with ZabbixClient() as client:
        return await client.call("hostinterface.update", params)


@mcp.tool(name="zabbix_host_delete", description="⚠️ DESTRUCTIVE — Permanently delete Zabbix hosts and all their items, triggers, graphs, and history. Cannot be undone.", annotations=DELETE)
async def zabbix_host_delete(hostids: Annotated[list[str], Field(description="IDs of hosts to delete.")]) -> dict[str, Any]:
    async with ZabbixClient() as client:
        return await client.call("host.delete", hostids)


@mcp.tool(name="zabbix_host_interface_delete", description="⚠️ DESTRUCTIVE — Permanently delete host interfaces. Cannot be undone.", annotations=DELETE)
async def zabbix_host_interface_delete(interfaceids: Annotated[list[str], Field(description="IDs of interfaces to delete.")]) -> dict[str, Any]:
    async with ZabbixClient() as client:
        return await client.call("hostinterface.delete", interfaceids)
