"""Zabbix MCP tools — Graphs and Graph Items (read, write, delete)."""

from __future__ import annotations
from typing import Annotated, Any
from pydantic import Field
from ..client import shared_session
from ..app import mcp
from ._annotations import DELETE, READ_ONLY, WRITE, WRITE_IDEMPOTENT
from ._params import compact, search_params


@mcp.tool(name="zabbix_graph_get", description="List Zabbix graphs. Filter by host, group, template, or name.", annotations=READ_ONLY)
async def zabbix_graph_get(
    graphids: Annotated[list[str] | None, Field(description="Return only graphs with these IDs.")] = None,
    hostids: Annotated[list[str] | None, Field(description="Return graphs on these host IDs.")] = None,
    groupids: Annotated[list[str] | None, Field(description="Return graphs on hosts in these group IDs.")] = None,
    templateids: Annotated[list[str] | None, Field(description="Return graphs from these template IDs.")] = None,
    name: Annotated[str | None, Field(description="Search by graph name (substring match).")] = None,
    limit: Annotated[int, Field(description="Maximum number of results.", ge=1, le=1000)] = 100,
    output: Annotated[list[str], Field(description="Fields to return.")] = ["graphid", "name", "width", "height", "type"],
) -> list[dict[str, Any]]:
    params = compact({
        "output": output,
        "limit": limit,
        "graphids": graphids,
        "hostids": hostids,
        "groupids": groupids,
        "templateids": templateids,
    })
    params.update(search_params(name=name))
    async with shared_session() as client:
        return await client.call("graph.get", params)


@mcp.tool(name="zabbix_graph_item_get", description="List items included in Zabbix graphs. Use this to inspect which items compose an existing graph.", annotations=READ_ONLY)
async def zabbix_graph_item_get(
    graphids: Annotated[list[str] | None, Field(description="Return items for these graph IDs.")] = None,
    itemids: Annotated[list[str] | None, Field(description="Return graph items for these item IDs.")] = None,
    limit: Annotated[int, Field(description="Maximum number of results.", ge=1, le=1000)] = 100,
    output: Annotated[list[str], Field(description="Fields to return.")] = ["gitemid", "graphid", "itemid", "color", "type", "yaxisside"],
) -> list[dict[str, Any]]:
    params = compact({
        "output": output,
        "limit": limit,
        "graphids": graphids,
        "itemids": itemids,
    })
    async with shared_session() as client:
        return await client.call("graphitem.get", params)


@mcp.tool(name="zabbix_graph_create", description="Create a new Zabbix graph. type: 0=normal, 1=stacked, 2=pie, 3=exploded.", annotations=WRITE)
async def zabbix_graph_create(
    name: Annotated[str, Field(description="Graph name.")],
    gitems: Annotated[list[dict[str, Any]], Field(description="Items to plot.")],
    width: Annotated[int, Field(description="Width in pixels.", ge=20)] = 900,
    height: Annotated[int, Field(description="Height in pixels.", ge=20)] = 200,
    type: Annotated[int, Field(description="0=normal, 1=stacked, 2=pie, 3=exploded.", ge=0, le=3)] = 0,
    show_legend: Annotated[int, Field(description="1=show, 0=hide.", ge=0, le=1)] = 1,
) -> dict[str, Any]:
    params = {"name": name, "gitems": gitems, "width": width, "height": height, "graphtype": type, "show_legend": show_legend}
    async with shared_session() as client:
        return await client.call("graph.create", params)


@mcp.tool(name="zabbix_graph_update", description="Update an existing Zabbix graph. Only provided fields are changed.", annotations=WRITE_IDEMPOTENT)
async def zabbix_graph_update(
    graphid: Annotated[str, Field(description="ID of the graph to update.")],
    name: Annotated[str | None, Field(description="New name.")]=None,
    gitems: Annotated[list[dict[str, Any]] | None, Field(description="Replace graph items.")]=None,
    width: Annotated[int | None, Field(description="New width.", ge=20)]=None,
    height: Annotated[int | None, Field(description="New height.", ge=20)]=None,
    type: Annotated[int | None, Field(description="New graph type.", ge=0, le=3)]=None,
) -> dict[str, Any]:
    params = compact({
        "graphid": graphid,
        "name": name,
        "gitems": gitems,
        "width": width,
        "height": height,
        "graphtype": type,
    })
    async with shared_session() as client:
        return await client.call("graph.update", params)


@mcp.tool(name="zabbix_graph_delete", description="⚠️ DESTRUCTIVE — Permanently delete Zabbix graphs. Cannot be undone.", annotations=DELETE)
async def zabbix_graph_delete(graphids: Annotated[list[str], Field(description="IDs of graphs to delete.")]) -> dict[str, Any]:
    async with shared_session() as client:
        return await client.call("graph.delete", graphids)
