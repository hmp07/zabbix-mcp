"""Shared FastMCP application instance.

Defined in a dedicated module so that both server.py (entry point)
and all tool modules import the *same* object, regardless of whether
server.py is loaded as __main__ or as zabbix_mcp.server.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "zabbix_mcp",
    instructions=(
        "MCP server for Zabbix 7.4. "
        "Provides tools for monitoring, host management, items, triggers, "
        "LLD rules, graphs, dashboards, templates, maintenances, and macros. "
        "All tools communicate with the Zabbix API via JSON-RPC 2.0. "
        "Credentials are configured via ZABBIX_URL and ZABBIX_API_TOKEN "
        "(or ZABBIX_USER / ZABBIX_PASSWORD) environment variables."
    ),
)
