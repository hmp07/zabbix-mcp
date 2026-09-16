"""Zabbix MCP tools — User Macros (read, write, delete)."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from ..client import ZabbixClient
from ..app import mcp
from ._annotations import DELETE, READ_ONLY, WRITE, WRITE_IDEMPOTENT


@mcp.tool(
    name="zabbix_usermacro_get",
    description=(
        "List Zabbix user macros. Filter by host, template, or macro name. "
        "User macros are reusable variables ({$MACRO}) used in items, triggers, and LLD rules. "
        "Set globalmacro=true to return global macros instead of host-level ones."
    ),
    annotations=READ_ONLY,
)
async def zabbix_usermacro_get(
    hostmacroids: Annotated[list[str] | None, Field(description="Return only macros with these IDs.")] = None,
    hostids: Annotated[list[str] | None, Field(description="Return macros defined on these host IDs.")] = None,
    templateids: Annotated[list[str] | None, Field(description="Return macros defined on these template IDs.")] = None,
    macro: Annotated[str | None, Field(description="Search by macro name (substring match).")] = None,
    globalmacro: Annotated[bool, Field(description="If true, return global macros instead of host macros.")] = False,
    limit: Annotated[int, Field(description="Maximum number of results.", ge=1, le=1000)] = 100,
    output: Annotated[list[str], Field(description="Fields to return.")] = [
        "hostmacroid", "hostid", "macro", "value", "type", "description",
    ],
) -> list[dict[str, Any]]:
    """Return Zabbix user macros matching the given filters."""
    params: dict[str, Any] = {
        "output": output,
        "limit": limit,
        "globalmacro": globalmacro,
    }
    if hostmacroids is not None:
        params["hostmacroids"] = hostmacroids
    if hostids is not None:
        params["hostids"] = hostids
    if templateids is not None:
        params["templateids"] = templateids
    if macro is not None:
        params["search"] = {"macro": macro}
    async with ZabbixClient() as client:
        return await client.call("usermacro.get", params)


@mcp.tool(
    name="zabbix_usermacro_create",
    description=(
        "Create a user macro on a host or template. "
        "Macros use the {$MACRO_NAME} format and can be referenced in items, triggers, and LLD rules. "
        "type: 0=text (default), 1=secret (value redacted in UI), 2=vault secret. "
        "Returns the new macro ID."
    ),
    annotations=WRITE,
)
async def zabbix_usermacro_create(
    hostid: Annotated[str, Field(description="ID of the host or template to add the macro to.")],
    macro: Annotated[str, Field(description="Macro name in {$NAME} format.")],
    value: Annotated[str, Field(description="Macro value.")],
    type: Annotated[int, Field(description="0=text (default), 1=secret (hidden in UI), 2=vault secret.", ge=0, le=2)] = 0,
    description: Annotated[str | None, Field(description="Macro description.")] = None,
) -> dict[str, Any]:
    """Create a user macro on a host or template."""
    params: dict[str, Any] = {
        "hostid": hostid,
        "macro": macro,
        "value": value,
        "type": type,
    }
    if description is not None:
        params["description"] = description
    async with ZabbixClient() as client:
        return await client.call("usermacro.create", params)


@mcp.tool(
    name="zabbix_usermacro_update",
    description="Update an existing user macro. Only provided fields are changed. Returns the updated macro ID.",
    annotations=WRITE_IDEMPOTENT,
)
async def zabbix_usermacro_update(
    hostmacroid: Annotated[str, Field(description="ID of the macro to update.")],
    value: Annotated[str | None, Field(description="New macro value.")] = None,
    type: Annotated[int | None, Field(description="0=text, 1=secret, 2=vault secret.", ge=0, le=2)] = None,
    description: Annotated[str | None, Field(description="New description.")] = None,
) -> dict[str, Any]:
    """Update a user macro."""
    params: dict[str, Any] = {"hostmacroid": hostmacroid}
    if value is not None:
        params["value"] = value
    if type is not None:
        params["type"] = type
    if description is not None:
        params["description"] = description
    async with ZabbixClient() as client:
        return await client.call("usermacro.update", params)


@mcp.tool(
    name="zabbix_usermacro_delete",
    description=(
        "DESTRUCTIVE — Permanently delete Zabbix user macros. "
        "Items and triggers referencing these macros will use unresolved macro names. "
        "Returns the deleted macro IDs."
    ),
    annotations=DELETE,
)
async def zabbix_usermacro_delete(
    hostmacroids: Annotated[list[str], Field(description="IDs of user macros to delete.")],
) -> dict[str, Any]:
    """Permanently delete Zabbix user macros."""
    async with ZabbixClient() as client:
        return await client.call("usermacro.delete", hostmacroids)
