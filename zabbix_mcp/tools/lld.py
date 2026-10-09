"""Zabbix MCP tools — Low-Level Discovery (rules and prototypes)."""

from __future__ import annotations
from typing import Annotated, Any
from pydantic import Field
from ..client import ZabbixClient
from ..app import mcp
from ._annotations import DELETE, READ_ONLY, WRITE, WRITE_IDEMPOTENT
from ._params import compact, filter_params, search_params


@mcp.tool(
    name="zabbix_lld_rule_get",
    description=(
        "List Zabbix LLD (Low-Level Discovery) rules. Filter by host, template, or key. "
        "LLD rules automatically discover and create items, triggers, and graphs."
    ),
    annotations=READ_ONLY,
)
async def zabbix_lld_rule_get(
    itemids: Annotated[list[str] | None, Field(description="Return only LLD rules with these IDs.")] = None,
    hostids: Annotated[list[str] | None, Field(description="Return LLD rules on these host IDs.")] = None,
    templateids: Annotated[list[str] | None, Field(description="Return LLD rules inherited from these template IDs.")] = None,
    name: Annotated[str | None, Field(description="Search by rule name (substring match).")] = None,
    key_: Annotated[str | None, Field(description="Search by rule key (substring match).")] = None,
    status: Annotated[int | None, Field(description="Filter by status: 0=enabled, 1=disabled.", ge=0, le=1)] = None,
    limit: Annotated[int, Field(description="Maximum number of results.", ge=1, le=1000)] = 100,
    output: Annotated[list[str], Field(description="Fields to return.")] = [
        "itemid", "hostid", "name", "key_", "type", "status", "state",
    ],
) -> list[dict[str, Any]]:
    """Return Zabbix LLD discovery rules."""
    params = compact({
        "output": output,
        "limit": limit,
        "itemids": itemids,
        "hostids": hostids,
        "templateids": templateids,
    })
    params.update(filter_params(status=status))
    params.update(search_params(name=name, key_=key_))
    async with ZabbixClient() as client:
        return await client.call("discoveryrule.get", params)


@mcp.tool(
    name="zabbix_lld_item_prototype_get",
    description=(
        "List item prototypes for LLD rules. "
        "Item prototypes define which items get created when the LLD rule discovers new entities."
    ),
    annotations=READ_ONLY,
)
async def zabbix_lld_item_prototype_get(
    itemids: Annotated[list[str] | None, Field(description="Return only item prototypes with these IDs.")] = None,
    discoveryids: Annotated[list[str] | None, Field(description="Return item prototypes belonging to these LLD rule IDs.")] = None,
    hostids: Annotated[list[str] | None, Field(description="Return item prototypes on these host IDs.")] = None,
    name: Annotated[str | None, Field(description="Search by prototype name (substring match).")] = None,
    key_: Annotated[str | None, Field(description="Search by prototype key (substring match).")] = None,
    limit: Annotated[int, Field(description="Maximum number of results.", ge=1, le=1000)] = 100,
    output: Annotated[list[str], Field(description="Fields to return.")] = [
        "itemid", "hostid", "name", "key_", "type", "value_type", "status",
    ],
) -> list[dict[str, Any]]:
    """Return item prototypes for Zabbix LLD rules."""
    params = compact({
        "output": output,
        "limit": limit,
        "itemids": itemids,
        "discoveryids": discoveryids,
        "hostids": hostids,
    })
    params.update(search_params(name=name, key_=key_))
    async with ZabbixClient() as client:
        return await client.call("itemprototype.get", params)


@mcp.tool(
    name="zabbix_lld_trigger_prototype_get",
    description=(
        "List trigger prototypes for LLD rules. "
        "Trigger prototypes define which triggers get created for each discovered entity."
    ),
    annotations=READ_ONLY,
)
async def zabbix_lld_trigger_prototype_get(
    triggerids: Annotated[list[str] | None, Field(description="Return only trigger prototypes with these IDs.")] = None,
    discoveryids: Annotated[list[str] | None, Field(description="Return trigger prototypes for these LLD rule IDs.")] = None,
    hostids: Annotated[list[str] | None, Field(description="Return trigger prototypes on these host IDs.")] = None,
    status: Annotated[int | None, Field(description="Filter by status: 0=enabled, 1=disabled.", ge=0, le=1)] = None,
    name: Annotated[str | None, Field(description="Search by prototype description (substring match).")] = None,
    limit: Annotated[int, Field(description="Maximum number of results.", ge=1, le=1000)] = 100,
    output: Annotated[list[str], Field(description="Fields to return.")] = [
        "triggerid", "description", "expression", "priority", "status",
    ],
) -> list[dict[str, Any]]:
    """Return trigger prototypes for Zabbix LLD rules."""
    params = compact({
        "output": output,
        "limit": limit,
        "triggerids": triggerids,
        "discoveryids": discoveryids,
        "hostids": hostids,
    })
    params.update(filter_params(status=status))
    params.update(search_params(description=name))
    async with ZabbixClient() as client:
        return await client.call("triggerprototype.get", params)


@mcp.tool(
    name="zabbix_lld_graph_prototype_get",
    description="List graph prototypes for LLD rules.",
    annotations=READ_ONLY,
)
async def zabbix_lld_graph_prototype_get(
    graphids: Annotated[list[str] | None, Field(description="Return only graph prototypes with these IDs.")] = None,
    discoveryids: Annotated[list[str] | None, Field(description="Return graph prototypes for these LLD rule IDs.")] = None,
    hostids: Annotated[list[str] | None, Field(description="Return graph prototypes on these host IDs.")] = None,
    name: Annotated[str | None, Field(description="Search by prototype name (substring match).")] = None,
    limit: Annotated[int, Field(description="Maximum number of results.", ge=1, le=1000)] = 100,
    output: Annotated[list[str], Field(description="Fields to return.")] = ["graphid", "name"],
) -> list[dict[str, Any]]:
    """Return graph prototypes for Zabbix LLD rules."""
    params = compact({
        "output": output,
        "limit": limit,
        "graphids": graphids,
        "discoveryids": discoveryids,
        "hostids": hostids,
    })
    params.update(search_params(name=name))
    async with ZabbixClient() as client:
        return await client.call("graphprototype.get", params)


@mcp.tool(
    name="zabbix_lld_host_prototype_get",
    description=(
        "List host prototypes for LLD rules. "
        "Host prototypes define which hosts get created for each entity discovered by network-level LLD."
    ),
    annotations=READ_ONLY,
)
async def zabbix_lld_host_prototype_get(
    hostids: Annotated[list[str] | None, Field(description="Return only host prototypes with these IDs.")] = None,
    discoveryids: Annotated[list[str] | None, Field(description="Return host prototypes for these LLD rule IDs.")] = None,
    groupids: Annotated[list[str] | None, Field(description="Return host prototypes in these group IDs.")] = None,
    name: Annotated[str | None, Field(description="Search by prototype name (substring match).")] = None,
    limit: Annotated[int, Field(description="Maximum number of results.", ge=1, le=1000)] = 100,
    output: Annotated[list[str], Field(description="Fields to return.")] = [
        "hostid", "host", "name", "status",
    ],
) -> list[dict[str, Any]]:
    """Return host prototypes for Zabbix LLD rules."""
    params = compact({
        "output": output,
        "limit": limit,
        "hostids": hostids,
        "discoveryids": discoveryids,
        "groupids": groupids,
    })
    params.update(search_params(name=name))
    async with ZabbixClient() as client:
        return await client.call("hostprototype.get", params)


@mcp.tool(
    name="zabbix_lld_rule_create",
    description=(
        "Create a new Zabbix LLD (Low-Level Discovery) rule on a host. "
        "type: 0=Zabbix agent, 2=Zabbix trapper, 3=Simple check, 5=Zabbix internal, "
        "7=Zabbix agent (active), 10=External check, 11=Database monitor, 12=IPMI, "
        "13=SSH, 14=Telnet, 16=JMX, 18=Dependent, 19=HTTP agent, 20=SNMP, 21=Script. "
        "Returns the new LLD rule ID."
    ),
    annotations=WRITE,
)
async def zabbix_lld_rule_create(
    hostid: Annotated[str, Field(description="ID of the host to add the LLD rule to.")],
    name: Annotated[str, Field(description="LLD rule name.")],
    key_: Annotated[str, Field(description="LLD rule key. Example: 'net.if.discovery'.")],
    type: Annotated[int, Field(description="Item type (0=Zabbix agent, 7=active agent, etc.).", ge=0, le=21)] = 0,
    delay: Annotated[str, Field(description="Update interval. Example: '1m', '30s'.")] = "1m",
    lifetime: Annotated[str, Field(description="Days to keep lost resources before deletion.")] = "30d",
    status: Annotated[int, Field(description="0=enabled (default), 1=disabled.", ge=0, le=1)] = 0,
    filter: Annotated[dict[str, Any] | None, Field(description="LLD filter conditions.")] = None,
    preprocessing: Annotated[list[dict[str, Any]] | None, Field(description="Preprocessing steps.")] = None,
    lld_macro_paths: Annotated[list[dict[str, Any]] | None, Field(description="LLD macro paths.")] = None,
    description: Annotated[str | None, Field(description="Rule description.")] = None,
) -> dict[str, Any]:
    """Create a Zabbix LLD discovery rule."""
    params = compact({
        "hostid": hostid,
        "name": name,
        "key_": key_,
        "type": type,
        "delay": delay,
        "lifetime": lifetime,
        "status": status,
        "filter": filter,
        "preprocessing": preprocessing,
        "lld_macro_paths": lld_macro_paths,
        "description": description,
    })
    async with ZabbixClient() as client:
        return await client.call("discoveryrule.create", params)


@mcp.tool(
    name="zabbix_lld_rule_update",
    description="Update an existing Zabbix LLD rule. Only provided fields are changed. Returns the updated rule ID.",
    annotations=WRITE_IDEMPOTENT,
)
async def zabbix_lld_rule_update(
    itemid: Annotated[str, Field(description="ID of the LLD rule to update.")],
    name: Annotated[str | None, Field(description="New rule name.")] = None,
    key_: Annotated[str | None, Field(description="New rule key.")] = None,
    delay: Annotated[str | None, Field(description="New update interval.")] = None,
    lifetime: Annotated[str | None, Field(description="New lost resource lifetime.")] = None,
    status: Annotated[int | None, Field(description="0=enabled, 1=disabled.", ge=0, le=1)] = None,
    filter: Annotated[dict[str, Any] | None, Field(description="Replace LLD filter conditions.")] = None,
    preprocessing: Annotated[list[dict[str, Any]] | None, Field(description="Replace preprocessing steps.")] = None,
    lld_macro_paths: Annotated[list[dict[str, Any]] | None, Field(description="Replace LLD macro paths.")] = None,
    description: Annotated[str | None, Field(description="New description.")] = None,
) -> dict[str, Any]:
    """Update a Zabbix LLD discovery rule."""
    params = compact({
        "itemid": itemid,
        "name": name,
        "key_": key_,
        "delay": delay,
        "lifetime": lifetime,
        "status": status,
        "filter": filter,
        "preprocessing": preprocessing,
        "lld_macro_paths": lld_macro_paths,
        "description": description,
    })
    async with ZabbixClient() as client:
        return await client.call("discoveryrule.update", params)


@mcp.tool(
    name="zabbix_lld_item_prototype_create",
    description=(
        "Create an item prototype for a Zabbix LLD rule. "
        "Item prototypes use LLD macros (e.g., {#FSNAME}) in their key and name. "
        "value_type: 0=float, 1=char, 2=log, 3=unsigned int, 4=text. "
        "Returns the new item prototype ID."
    ),
    annotations=WRITE,
)
async def zabbix_lld_item_prototype_create(
    hostid: Annotated[str, Field(description="ID of the host owning this prototype.")],
    ruleid: Annotated[str, Field(description="ID of the parent LLD rule.")],
    name: Annotated[str, Field(description="Prototype name. May contain LLD macros.")],
    key_: Annotated[str, Field(description="Prototype key.")],
    type: Annotated[int, Field(description="Item type.", ge=0, le=21)] = 0,
    value_type: Annotated[int, Field(description="0=float, 1=char, 2=log, 3=unsigned int, 4=text.", ge=0, le=4)] = 3,
    delay: Annotated[str, Field(description="Collection interval.")] = "1m",
    history: Annotated[str, Field(description="History retention.")] = "7d",
    trends: Annotated[str, Field(description="Trends retention.")] = "365d",
    units: Annotated[str | None, Field(description="Value units.")] = None,
    tags: Annotated[list[dict[str, Any]] | None, Field(description="Item prototype tags.")] = None,
    preprocessing: Annotated[list[dict[str, Any]] | None, Field(description="Preprocessing steps.")] = None,
    description: Annotated[str | None, Field(description="Prototype description.")] = None,
) -> dict[str, Any]:
    """Create an item prototype for a Zabbix LLD rule."""
    params = compact({
        "hostid": hostid,
        "ruleid": ruleid,
        "name": name,
        "key_": key_,
        "type": type,
        "value_type": value_type,
        "delay": delay,
        "history": history,
        "trends": trends,
        "units": units,
        "tags": tags,
        "preprocessing": preprocessing,
        "description": description,
    })
    async with ZabbixClient() as client:
        return await client.call("itemprototype.create", params)


@mcp.tool(
    name="zabbix_lld_item_prototype_update",
    description="Update an existing LLD item prototype. Only provided fields are changed. Returns the updated prototype ID.",
    annotations=WRITE_IDEMPOTENT,
)
async def zabbix_lld_item_prototype_update(
    itemid: Annotated[str, Field(description="ID of the item prototype to update.")],
    name: Annotated[str | None, Field(description="New prototype name.")] = None,
    key_: Annotated[str | None, Field(description="New prototype key.")] = None,
    delay: Annotated[str | None, Field(description="New collection interval.")] = None,
    history: Annotated[str | None, Field(description="New history retention.")] = None,
    trends: Annotated[str | None, Field(description="New trends retention.")] = None,
    units: Annotated[str | None, Field(description="New value units.")] = None,
    status: Annotated[int | None, Field(description="0=enabled, 1=disabled.", ge=0, le=1)] = None,
    tags: Annotated[list[dict[str, Any]] | None, Field(description="Replace tags.")] = None,
    preprocessing: Annotated[list[dict[str, Any]] | None, Field(description="Replace preprocessing steps.")] = None,
    description: Annotated[str | None, Field(description="New description.")] = None,
) -> dict[str, Any]:
    """Update a Zabbix LLD item prototype."""
    params = compact({
        "itemid": itemid,
        "name": name,
        "key_": key_,
        "delay": delay,
        "history": history,
        "trends": trends,
        "units": units,
        "status": status,
        "tags": tags,
        "preprocessing": preprocessing,
        "description": description,
    })
    async with ZabbixClient() as client:
        return await client.call("itemprototype.update", params)


@mcp.tool(
    name="zabbix_lld_trigger_prototype_create",
    description=(
        "Create a trigger prototype for a Zabbix LLD rule. "
        "The expression must reference item prototypes using LLD macros. "
        "Returns the new trigger prototype ID."
    ),
    annotations=WRITE,
)
async def zabbix_lld_trigger_prototype_create(
    description: Annotated[str, Field(description="Trigger prototype description. May contain LLD macros.")],
    expression: Annotated[str, Field(description="Trigger expression using item prototype keys with LLD macros.")],
    ruleid: Annotated[str, Field(description="ID of the parent LLD rule.")],
    priority: Annotated[int, Field(description="0=not classified, 1=info, 2=warning, 3=average, 4=high, 5=disaster.", ge=0, le=5)] = 2,
    status: Annotated[int, Field(description="0=enabled (default), 1=disabled.", ge=0, le=1)] = 0,
    tags: Annotated[list[dict[str, Any]] | None, Field(description="Trigger prototype tags.")] = None,
    comments: Annotated[str | None, Field(description="Extended description / runbook notes.")] = None,
    url: Annotated[str | None, Field(description="URL associated with this trigger prototype.")] = None,
    recovery_mode: Annotated[int | None, Field(description="0=expression, 1=recovery expression, 2=none.", ge=0, le=2)] = None,
    recovery_expression: Annotated[str | None, Field(description="Recovery expression (required if recovery_mode=1).")] = None,
) -> dict[str, Any]:
    """Create a trigger prototype for a Zabbix LLD rule."""
    params = compact({
        "description": description,
        "expression": expression,
        "ruleid": ruleid,
        "priority": priority,
        "status": status,
        "tags": tags,
        "comments": comments,
        "url": url,
        "recovery_mode": recovery_mode,
        "recovery_expression": recovery_expression,
    })
    async with ZabbixClient() as client:
        return await client.call("triggerprototype.create", params)


@mcp.tool(
    name="zabbix_lld_trigger_prototype_update",
    description="Update an existing LLD trigger prototype. Only provided fields are changed. Returns the updated prototype ID.",
    annotations=WRITE_IDEMPOTENT,
)
async def zabbix_lld_trigger_prototype_update(
    triggerid: Annotated[str, Field(description="ID of the trigger prototype to update.")],
    description: Annotated[str | None, Field(description="New prototype description.")] = None,
    expression: Annotated[str | None, Field(description="New trigger expression.")] = None,
    priority: Annotated[int | None, Field(description="New severity: 0=not classified ... 5=disaster.", ge=0, le=5)] = None,
    status: Annotated[int | None, Field(description="0=enabled, 1=disabled.", ge=0, le=1)] = None,
    tags: Annotated[list[dict[str, Any]] | None, Field(description="Replace tags.")] = None,
    comments: Annotated[str | None, Field(description="New extended description.")] = None,
    url: Annotated[str | None, Field(description="New URL.")] = None,
) -> dict[str, Any]:
    """Update a Zabbix LLD trigger prototype."""
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
        return await client.call("triggerprototype.update", params)


@mcp.tool(
    name="zabbix_lld_graph_prototype_create",
    description=(
        "Create a graph prototype for a Zabbix LLD rule. "
        "gitems must reference item prototypes. "
        "Returns the new graph prototype ID."
    ),
    annotations=WRITE,
)
async def zabbix_lld_graph_prototype_create(
    name: Annotated[str, Field(description="Graph prototype name. May contain LLD macros.")],
    gitems: Annotated[list[dict[str, Any]], Field(description="Item prototypes to plot.")],
    width: Annotated[int, Field(description="Graph width in pixels.", ge=20)] = 900,
    height: Annotated[int, Field(description="Graph height in pixels.", ge=20)] = 200,
    type: Annotated[int, Field(description="0=normal, 1=stacked, 2=pie, 3=exploded.", ge=0, le=3)] = 0,
    show_legend: Annotated[int, Field(description="1=show legend (default), 0=hide.", ge=0, le=1)] = 1,
) -> dict[str, Any]:
    """Create a graph prototype for a Zabbix LLD rule."""
    params = {
        "name": name,
        "gitems": gitems,
        "width": width,
        "height": height,
        "graphtype": type,
        "show_legend": show_legend,
    }
    async with ZabbixClient() as client:
        return await client.call("graphprototype.create", params)


@mcp.tool(
    name="zabbix_lld_graph_prototype_update",
    description="Update an existing LLD graph prototype. Only provided fields are changed. Returns the updated prototype ID.",
    annotations=WRITE_IDEMPOTENT,
)
async def zabbix_lld_graph_prototype_update(
    graphid: Annotated[str, Field(description="ID of the graph prototype to update.")],
    name: Annotated[str | None, Field(description="New prototype name.")] = None,
    gitems: Annotated[list[dict[str, Any]] | None, Field(description="Replace graph items.")] = None,
    width: Annotated[int | None, Field(description="New width in pixels.", ge=20)] = None,
    height: Annotated[int | None, Field(description="New height in pixels.", ge=20)] = None,
    type: Annotated[int | None, Field(description="New graph type: 0=normal, 1=stacked, 2=pie, 3=exploded.", ge=0, le=3)] = None,
) -> dict[str, Any]:
    """Update a Zabbix LLD graph prototype."""
    params = compact({
        "graphid": graphid,
        "name": name,
        "gitems": gitems,
        "width": width,
        "height": height,
        "graphtype": type,
    })
    async with ZabbixClient() as client:
        return await client.call("graphprototype.update", params)


@mcp.tool(
    name="zabbix_lld_host_prototype_create",
    description=(
        "Create a host prototype for a Zabbix LLD rule. "
        "Host prototypes define hosts that are automatically created for each discovered entity. "
        "The host field may contain LLD macros. "
        "Returns the new host prototype ID."
    ),
    annotations=WRITE,
)
async def zabbix_lld_host_prototype_create(
    ruleid: Annotated[str, Field(description="ID of the parent LLD rule.")],
    host: Annotated[str, Field(description="Technical host name. May contain LLD macros.")],
    name: Annotated[str | None, Field(description="Visible host name. Defaults to host if omitted.")] = None,
    groupLinks: Annotated[list[dict[str, Any]] | None, Field(description="Host groups to add discovered hosts to.")] = None,
    groupPrototypes: Annotated[list[dict[str, Any]] | None, Field(description="Group prototypes.")] = None,
    templates: Annotated[list[dict[str, Any]] | None, Field(description="Templates to link.")] = None,
    status: Annotated[int, Field(description="0=enabled (default), 1=disabled.", ge=0, le=1)] = 0,
    inventory_mode: Annotated[int | None, Field(description="-1=disabled, 0=manual, 1=automatic.", ge=-1, le=1)] = None,
) -> dict[str, Any]:
    """Create a host prototype for a Zabbix LLD rule."""
    params = compact({
        "ruleid": ruleid,
        "host": host,
        "status": status,
        "name": name,
        "groupLinks": groupLinks,
        "groupPrototypes": groupPrototypes,
        "templates": templates,
        "inventory_mode": inventory_mode,
    })
    async with ZabbixClient() as client:
        return await client.call("hostprototype.create", params)


@mcp.tool(
    name="zabbix_lld_host_prototype_update",
    description="Update an existing LLD host prototype. Only provided fields are changed. Returns the updated prototype ID.",
    annotations=WRITE_IDEMPOTENT,
)
async def zabbix_lld_host_prototype_update(
    hostid: Annotated[str, Field(description="ID of the host prototype to update.")],
    host: Annotated[str | None, Field(description="New technical host name.")] = None,
    name: Annotated[str | None, Field(description="New visible host name.")] = None,
    groupLinks: Annotated[list[dict[str, Any]] | None, Field(description="Replace host group links.")] = None,
    groupPrototypes: Annotated[list[dict[str, Any]] | None, Field(description="Replace group prototypes.")] = None,
    templates: Annotated[list[dict[str, Any]] | None, Field(description="Replace linked templates.")] = None,
    status: Annotated[int | None, Field(description="0=enabled, 1=disabled.", ge=0, le=1)] = None,
    inventory_mode: Annotated[int | None, Field(description="-1=disabled, 0=manual, 1=automatic.", ge=-1, le=1)] = None,
) -> dict[str, Any]:
    """Update a Zabbix LLD host prototype."""
    params = compact({
        "hostid": hostid,
        "host": host,
        "name": name,
        "groupLinks": groupLinks,
        "groupPrototypes": groupPrototypes,
        "templates": templates,
        "status": status,
        "inventory_mode": inventory_mode,
    })
    async with ZabbixClient() as client:
        return await client.call("hostprototype.update", params)


@mcp.tool(
    name="zabbix_lld_rule_delete",
    description=(
        "DESTRUCTIVE — Permanently delete Zabbix LLD rules and all their discovered items, triggers, and graphs. "
        "This action cannot be undone. Returns the deleted rule IDs."
    ),
    annotations=DELETE,
)
async def zabbix_lld_rule_delete(
    itemids: Annotated[list[str], Field(description="IDs of LLD rules to delete.")],
) -> dict[str, Any]:
    """Permanently delete Zabbix LLD rules."""
    async with ZabbixClient() as client:
        return await client.call("discoveryrule.delete", itemids)


@mcp.tool(
    name="zabbix_lld_item_prototype_delete",
    description=(
        "DESTRUCTIVE — Permanently delete LLD item prototypes and all items created from them. "
        "This action cannot be undone. Returns the deleted prototype IDs."
    ),
    annotations=DELETE,
)
async def zabbix_lld_item_prototype_delete(
    itemids: Annotated[list[str], Field(description="IDs of item prototypes to delete.")],
) -> dict[str, Any]:
    """Permanently delete LLD item prototypes."""
    async with ZabbixClient() as client:
        return await client.call("itemprototype.delete", itemids)


@mcp.tool(
    name="zabbix_lld_trigger_prototype_delete",
    description=(
        "DESTRUCTIVE — Permanently delete LLD trigger prototypes and all triggers created from them. "
        "This action cannot be undone. Returns the deleted prototype IDs."
    ),
    annotations=DELETE,
)
async def zabbix_lld_trigger_prototype_delete(
    triggerids: Annotated[list[str], Field(description="IDs of trigger prototypes to delete.")],
) -> dict[str, Any]:
    """Permanently delete LLD trigger prototypes."""
    async with ZabbixClient() as client:
        return await client.call("triggerprototype.delete", triggerids)


@mcp.tool(
    name="zabbix_lld_graph_prototype_delete",
    description=(
        "DESTRUCTIVE — Permanently delete LLD graph prototypes and all graphs created from them. "
        "This action cannot be undone. Returns the deleted prototype IDs."
    ),
    annotations=DELETE,
)
async def zabbix_lld_graph_prototype_delete(
    graphids: Annotated[list[str], Field(description="IDs of graph prototypes to delete.")],
) -> dict[str, Any]:
    """Permanently delete LLD graph prototypes."""
    async with ZabbixClient() as client:
        return await client.call("graphprototype.delete", graphids)


@mcp.tool(
    name="zabbix_lld_host_prototype_delete",
    description=(
        "DESTRUCTIVE — Permanently delete LLD host prototypes and all hosts created from them. "
        "This action cannot be undone. Returns the deleted prototype IDs."
    ),
    annotations=DELETE,
)
async def zabbix_lld_host_prototype_delete(
    hostids: Annotated[list[str], Field(description="IDs of host prototypes to delete.")],
) -> dict[str, Any]:
    """Permanently delete LLD host prototypes."""
    async with ZabbixClient() as client:
        return await client.call("hostprototype.delete", hostids)
