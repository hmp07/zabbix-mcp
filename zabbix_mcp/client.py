"""Zabbix API client with authentication, retry, and error translation.

Design principles:
- Credentials come from env vars only (auth.py). Never from call parameters.
- APIRequestError (application errors) are never retried.
- Network/timeout errors are retried up to _MAX_RETRIES with exponential backoff.
- No credentials appear in logs or exception messages.
"""

import asyncio
import logging
import os
from typing import Any

from zabbix_utils import APIRequestError, AsyncZabbixAPI

from .auth import get_api_token, get_user_credentials, get_verify_ssl, get_zabbix_url, redact_token
from .errors import (
    ZabbixAPIError,
    ZabbixAuthError,
    ZabbixConfigError,
    ZabbixMCPError,
    ZabbixNetworkError,
    ZabbixNotFoundError,
    ZabbixPermissionError,
)

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_BASE_BACKOFF = 1.0  # seconds, doubled on each retry


def _translate_api_error(exc: APIRequestError) -> ZabbixMCPError:
    """Convert an APIRequestError into a typed, actionable MCP error."""
    # Code lives in exc.body["code"] when the API returns a structured error.
    body = getattr(exc, "body", None)
    code: int | None = body.get("code") if isinstance(body, dict) else None
    message = str(exc)
    msg_lower = message.lower()

    if "not authorized" in msg_lower or "session terminated" in msg_lower:
        return ZabbixAuthError(
            f"Authentication failed: {message}. "
            "Verify ZABBIX_API_TOKEN or ZABBIX_USER/ZABBIX_PASSWORD."
        )
    if "no permissions" in msg_lower or "permission denied" in msg_lower:
        return ZabbixPermissionError(f"Permission denied: {message}")
    if "does not exist" in msg_lower or "no such" in msg_lower:
        return ZabbixNotFoundError(f"Resource not found: {message}")

    return ZabbixAPIError(message, code=code)


class ZabbixClient:
    """Async Zabbix API client.

    Usage:
        client = ZabbixClient()
        result = await client.call("host.get", {"output": ["hostid", "host"]})
        await client.close()

    Or as a context manager:
        async with ZabbixClient() as client:
            result = await client.call("host.get", {"output": "extend"})
    """

    def __init__(self, timeout: int | None = None) -> None:
        self._api: AsyncZabbixAPI | None = None
        self._timeout = timeout or int(os.environ.get("ZABBIX_TIMEOUT", "30"))
        self._authenticated_with_token = False

    async def _connect(self) -> AsyncZabbixAPI:
        """Initialize and authenticate the Zabbix API session."""
        url = get_zabbix_url()
        token = get_api_token()
        creds = get_user_credentials()

        if not token and not creds:
            raise ZabbixConfigError(
                "No Zabbix credentials configured. "
                "Set ZABBIX_API_TOKEN or both ZABBIX_USER and ZABBIX_PASSWORD."
            )

        verify_ssl = get_verify_ssl()
        if not verify_ssl:
            logger.warning("SSL certificate verification is DISABLED (ZABBIX_VERIFY_SSL=false)")
        api = AsyncZabbixAPI(url=url, timeout=self._timeout, validate_certs=verify_ssl)

        try:
            if token:
                logger.debug(
                    "Connecting to Zabbix at %s using API token %s",
                    url,
                    redact_token(token),
                )
                await api.login(token=token)
                self._authenticated_with_token = True
            else:
                user, password = creds  # type: ignore[misc]
                logger.debug("Connecting to Zabbix at %s as user=%s", url, user)
                await api.login(user=user, password=password)
                self._authenticated_with_token = False
        except APIRequestError as exc:
            raise _translate_api_error(exc) from exc
        except Exception as exc:
            raise ZabbixNetworkError(
                f"Cannot connect to Zabbix at {url}: {type(exc).__name__}. "
                "Verify ZABBIX_URL and network connectivity."
            ) from exc

        return api

    async def _get_api(self) -> AsyncZabbixAPI:
        if self._api is None:
            self._api = await self._connect()
        return self._api

    async def call(self, method: str, params: dict[str, Any] | None = None) -> Any:
        """Call a Zabbix API method with automatic retry on transient failures.

        Args:
            method: Zabbix API method in dot notation, e.g. "host.get".
            params: Method parameters. Must never contain credentials.

        Returns:
            The Zabbix API result (list or dict depending on the method).

        Raises:
            ZabbixAuthError: Authentication or session failure.
            ZabbixPermissionError: Insufficient permissions.
            ZabbixNotFoundError: Resource does not exist.
            ZabbixAPIError: Other application-level Zabbix error.
            ZabbixNetworkError: Network or timeout failure after all retries.
            ZabbixConfigError: Missing credentials or URL.
        """
        params = params or {}

        if "." not in method:
            raise ValueError(f"Invalid Zabbix method format: {method!r}. Expected 'resource.action'.")

        resource_name, action_name = method.split(".", 1)
        last_exc: Exception | None = None

        for attempt in range(_MAX_RETRIES):
            try:
                api = await self._get_api()
                resource = getattr(api, resource_name)
                func = getattr(resource, action_name)
                result = await func(**params)
                logger.debug("Zabbix API call %s succeeded", method)
                return result

            except APIRequestError as exc:
                # Application-level error — do not retry.
                raise _translate_api_error(exc) from exc

            except (ZabbixConfigError, ZabbixAuthError):
                raise

            except Exception as exc:
                last_exc = exc
                if attempt < _MAX_RETRIES - 1:
                    delay = _BASE_BACKOFF * (2**attempt)
                    logger.warning(
                        "Zabbix API call %s failed (attempt %d/%d), retrying in %.1fs: %s",
                        method,
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                        type(exc).__name__,
                    )
                    await asyncio.sleep(delay)
                    self._api = None  # force reconnect on next attempt

        raise ZabbixNetworkError(
            f"Zabbix API call '{method}' failed after {_MAX_RETRIES} attempts "
            f"({type(last_exc).__name__}). "
            "Check ZABBIX_URL and network connectivity."
        ) from last_exc

    async def close(self) -> None:
        """Log out and release the API session.

        Only logs out when authenticated with user/password. Token-based sessions
        do not require an explicit logout.
        """
        if self._api is not None:
            if not self._authenticated_with_token:
                try:
                    await self._api.logout()
                    logger.debug("Zabbix API session closed")
                except Exception as exc:
                    logger.debug("Zabbix logout failed (ignored): %s", exc)
            self._api = None

    async def __aenter__(self) -> "ZabbixClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()
