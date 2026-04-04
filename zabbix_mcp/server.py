"""Zabbix MCP server entry point.

Transport: stdio (local subprocess, no network exposure).
Tools are registered by importing each tools module.
"""

import logging

from .app import mcp
from .auth import has_credentials

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


def main() -> None:
    if not has_credentials():
        logger.error(
            "No Zabbix credentials configured. "
            "Set ZABBIX_API_TOKEN or ZABBIX_USER + ZABBIX_PASSWORD."
        )
        raise SystemExit(1)

    logger.info("Starting Zabbix MCP server (stdio transport)")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
