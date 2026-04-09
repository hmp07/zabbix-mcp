"""Zabbix MCP server entry point.

Transport is controlled by the MCP_TRANSPORT environment variable:
- stdio (default): local subprocess, no network exposure
- http: streamable-http for remote/multi-client use (MCP_HOST, MCP_PORT)
- sse: Server-Sent Events legacy transport (MCP_HOST, MCP_PORT)

Read-only mode is controlled by ZABBIX_READ_ONLY=true.
Tools are registered by importing each tools module.
"""

import logging

from .app import mcp
from .auth import get_transport_config, has_credentials, is_read_only_mode

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# Tool modules are imported after mcp is defined so that @mcp.tool() decorators
# can reference this instance. Import order follows the implementation phases.
from .tools import (  # noqa: E402, F401
    dashboard,
    graph,
    host,
    hostgroup,
    item,
    lld,
    macro,
    maintenance,
    monitoring,
    template,
    trigger,
    workflow,
)


def _apply_read_only_mode() -> int:
    """Remove write/delete tools from the FastMCP instance.

    Uses FastMCP's internal tool registry. Only call this once at startup,
    before mcp.run(). The removal is permanent for the process lifetime.

    Returns:
        Number of tools removed.
    """
    to_remove = [
        name
        for name, tool in list(mcp._tool_manager._tools.items())
        if not (tool.annotations and tool.annotations.readOnlyHint)
    ]
    for name in to_remove:
        del mcp._tool_manager._tools[name]
    return len(to_remove)


def main() -> None:
    if not has_credentials():
        logger.error(
            "No Zabbix credentials configured. "
            "Set ZABBIX_API_TOKEN or ZABBIX_USER + ZABBIX_PASSWORD."
        )
        raise SystemExit(1)

    if is_read_only_mode():
        removed = _apply_read_only_mode()
        logger.info("Read-only mode enabled: %d write/delete tools disabled.", removed)

    config = get_transport_config()
    transport = config["transport"]

    if transport == "stdio":
        logger.info("Starting Zabbix MCP server (stdio)")
        mcp.run(transport="stdio")
    else:
        host = str(config["host"])
        port = int(config["port"])
        # "http" maps to FastMCP's "streamable-http" transport
        mcp_transport = "streamable-http" if transport == "http" else transport
        logger.info(
            "Starting Zabbix MCP server (%s on %s:%d)",
            mcp_transport, host, port,
        )
        mcp.run(transport=mcp_transport, host=host, port=port)


if __name__ == "__main__":
    main()
