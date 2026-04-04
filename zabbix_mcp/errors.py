"""Typed errors with actionable messages for Zabbix MCP."""


class ZabbixMCPError(Exception):
    """Base error for all Zabbix MCP errors."""


class ZabbixConfigError(ZabbixMCPError):
    """Missing or invalid server configuration.

    Fix: set ZABBIX_URL and either ZABBIX_API_TOKEN or ZABBIX_USER/ZABBIX_PASSWORD.
    """


class ZabbixAuthError(ZabbixMCPError):
    """Authentication failure.

    Causes: invalid token, expired session, wrong credentials.
    Fix: verify ZABBIX_API_TOKEN or ZABBIX_USER/ZABBIX_PASSWORD env vars.
    """


class ZabbixPermissionError(ZabbixMCPError):
    """Authenticated user lacks permission for this operation."""


class ZabbixNotFoundError(ZabbixMCPError):
    """Requested resource does not exist in Zabbix."""


class ZabbixAPIError(ZabbixMCPError):
    """Zabbix API returned an application-level error."""

    def __init__(self, message: str, code: int | None = None) -> None:
        super().__init__(message)
        self.code = code


class ZabbixNetworkError(ZabbixMCPError):
    """Network-level failure reaching the Zabbix API.

    Causes: unreachable host, TLS error, timeout.
    Fix: verify ZABBIX_URL and network connectivity.
    """


class ZabbixValidationError(ZabbixMCPError):
    """Input validation failed before calling the Zabbix API."""
