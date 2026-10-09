"""Shared FastMCP application instance.

Defined in a dedicated module so that both server.py (entry point)
and all tool modules import the *same* object, regardless of whether
server.py is loaded as __main__ or as zabbix_mcp.server.

The lifespan below owns the process-wide Zabbix HTTP session. Tools share one
connection instead of opening (and leaking) one per call; it is closed on
shutdown so no aiohttp session or TCP connector outlives the server.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(_server: FastMCP) -> AsyncIterator[dict[str, object]]:
    """Open the shared Zabbix session on startup, close it on shutdown."""
    from .client import close_shared_session

    logger.debug("zabbix-mcp lifespan: starting")
    try:
        yield {}
    finally:
        # Runs on normal shutdown and on cancellation/teardown alike.
        await close_shared_session()
        logger.debug("zabbix-mcp lifespan: stopped")


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
    lifespan=_lifespan,
)
