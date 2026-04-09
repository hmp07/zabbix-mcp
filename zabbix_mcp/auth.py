"""Credential management for Zabbix MCP.

Credentials are read from environment variables only.
Secrets are never passed through tool arguments, never logged in full.
"""

import logging
import os

from .errors import ZabbixConfigError

logger = logging.getLogger(__name__)

_REDACTED = "<redacted>"


def get_zabbix_url() -> str:
    """Return the Zabbix URL from ZABBIX_URL env var.

    Raises:
        ZabbixConfigError: if ZABBIX_URL is not set.
    """
    url = os.environ.get("ZABBIX_URL", "").strip().rstrip("/")
    if not url:
        raise ZabbixConfigError(
            "ZABBIX_URL is not set. "
            "Set ZABBIX_URL to your Zabbix frontend URL "
            "(e.g. https://zabbix.example.com/zabbix)."
        )
    return url


def get_api_token() -> str | None:
    """Return the API token from ZABBIX_API_TOKEN, or None if not set."""
    return os.environ.get("ZABBIX_API_TOKEN") or None


def get_user_credentials() -> tuple[str, str] | None:
    """Return (user, password) from ZABBIX_USER/ZABBIX_PASSWORD, or None.

    The password is never logged.
    """
    user = os.environ.get("ZABBIX_USER", "")
    password = os.environ.get("ZABBIX_PASSWORD", "")
    if user and password:
        logger.debug("Credential source: ZABBIX_USER (user=%s)", user)
        return user, password
    return None


def has_credentials() -> bool:
    """Return True if any usable auth credentials are configured."""
    return bool(get_api_token() or get_user_credentials())


def get_verify_ssl() -> bool:
    """Return whether SSL certificates should be verified.

    Reads ZABBIX_VERIFY_SSL env var. Defaults to True.
    Set to 'false', '0', or 'no' to disable (e.g. self-signed certs in dev/lab).
    """
    value = os.environ.get("ZABBIX_VERIFY_SSL", "true").strip().lower()
    return value not in ("false", "0", "no")


def is_read_only_mode() -> bool:
    """Return True if ZABBIX_READ_ONLY is set to a truthy value.

    When active, the server only exposes read-only tools (_get and read workflow tools).
    Set ZABBIX_READ_ONLY=true to enable (also accepts '1' or 'yes').
    """
    value = os.environ.get("ZABBIX_READ_ONLY", "false").strip().lower()
    return value in ("true", "1", "yes")


def get_transport_config() -> dict[str, str | int]:
    """Return transport configuration from environment variables.

    Supported transports:
    - stdio (default): local subprocess, no network exposure
    - http: streamable-http, suitable for remote/multi-client use
    - sse: Server-Sent Events, legacy HTTP transport

    Environment variables:
    - MCP_TRANSPORT: stdio | http | sse (default: stdio)
    - MCP_HOST: bind address for http/sse (default: 127.0.0.1)
    - MCP_PORT: listen port for http/sse (default: 8000)
    """
    transport = os.environ.get("MCP_TRANSPORT", "stdio").strip().lower()
    if transport not in ("stdio", "http", "sse"):
        logger.warning(
            "Unknown MCP_TRANSPORT value '%s', falling back to stdio. "
            "Valid values: stdio, http, sse.",
            transport,
        )
        transport = "stdio"

    host = os.environ.get("MCP_HOST", "127.0.0.1").strip()

    try:
        port = int(os.environ.get("MCP_PORT", "8000"))
    except ValueError:
        logger.warning("Invalid MCP_PORT value, falling back to 8000.")
        port = 8000

    if transport != "stdio" and host == "0.0.0.0":
        logger.warning(
            "MCP server is bound to all interfaces (0.0.0.0). "
            "Ensure this is on a trusted network or behind a reverse proxy with auth. "
            "Set MCP_HOST=127.0.0.1 to restrict to local access only."
        )

    return {"transport": transport, "host": host, "port": port}


def redact_token(value: str) -> str:
    """Return a redacted representation safe for logging.

    Shows only the first few characters followed by '...<redacted>'.
    """
    if not value:
        return _REDACTED
    visible = min(4, max(1, len(value) // 8))
    return value[:visible] + "..." + _REDACTED
