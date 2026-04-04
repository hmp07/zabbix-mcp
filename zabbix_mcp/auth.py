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


def redact_token(value: str) -> str:
    """Return a redacted representation safe for logging.

    Shows only the first few characters followed by '...<redacted>'.
    """
    if not value:
        return _REDACTED
    visible = min(4, max(1, len(value) // 8))
    return value[:visible] + "..." + _REDACTED
