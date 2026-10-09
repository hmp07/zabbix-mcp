"""Zabbix API client with authentication, retry, and error translation.

Design principles:
- Credentials come from env vars only (auth.py). Never from call parameters.
- APIRequestError (application errors) are never retried.
- Network/timeout errors are retried up to _MAX_RETRIES with exponential backoff.
- No credentials appear in logs or exception messages.

Connection lifecycle
--------------------
Every tool used to open its own ``ZabbixClient``, which built a fresh
``aiohttp.ClientSession`` + ``TCPConnector`` on each call and abandoned it
afterwards. That leaked an unclosed session and a TCP connection per tool
invocation ("Unclosed client session" / "Unclosed connector" on stderr), and
re-authenticated on every call.

Tools now share one process-wide session via :func:`shared_session`, opened
lazily and closed by the server lifespan (see server.py). Per-call
``ZabbixClient()`` instances remain available and still own their transport;
``close()`` now releases it properly in every path.
"""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import aiohttp
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

# Bound on simultaneous outbound connections to the Zabbix API. The default
# aiohttp limit is 100, which a burst of parallel tool calls can exhaust and
# then queue on. Kept modest because one session now serves every tool.
_MAX_CONNECTIONS = 20

# Reference to the process-wide session, or None when not yet opened.
_shared_state: dict[str, Any] = {"api": None, "session": None, "lock": None, "token": False}


def reset_shared_state() -> None:
    """Drop cached shared-session references without closing anything.

    For tests: clears module state so one test cannot leak a session into the
    next. Does not perform I/O, so it is safe to call outside a loop.
    """
    _shared_state["api"] = None
    _shared_state["session"] = None
    _shared_state["token"] = False


def _get_lock() -> asyncio.Lock:
    """Return the shared session lock, creating it on first use.

    Created lazily so the module stays importable outside a running event
    loop (asyncio.Lock() binds to the loop that is current at construction).
    """
    lock = _shared_state["lock"]
    if lock is None:
        lock = asyncio.Lock()
        _shared_state["lock"] = lock
    return lock


async def close_shared_session() -> None:
    """Log out and close the process-wide session. Safe to call repeatedly.

    Called from the server lifespan on shutdown, and directly by tests.
    """
    async with _get_lock():
        api: AsyncZabbixAPI | None = _shared_state["api"]
        session: aiohttp.ClientSession | None = _shared_state["session"]
        used_token = bool(_shared_state["token"])
        _shared_state["api"] = None
        _shared_state["session"] = None
        _shared_state["token"] = False

    if api is not None and not used_token:
        # Token sessions have no server-side session to end; logging out would
        # only cost a round trip.
        try:
            await api.logout()
        except Exception as exc:  # noqa: BLE001 - best effort teardown
            logger.debug("Zabbix logout failed during shared close (ignored): %s", exc)
    if session is not None and not session.closed:
        await session.close()
        logger.debug("Shared aiohttp session closed")


@asynccontextmanager
async def shared_session() -> AsyncIterator["ZabbixClient"]:
    """Yield a :class:`ZabbixClient` bound to the process-wide HTTP session.

    The underlying ``aiohttp.ClientSession`` is opened on first use and reused
    for the lifetime of the process, so authentication and TCP handshakes are
    paid once instead of once per tool call. Release it with
    :func:`close_shared_session` on shutdown.
    """
    client = ZabbixClient(shared=True)
    try:
        yield client
    finally:
        # Detach this client without touching the shared transport: the
        # session outlives individual calls and is closed by the lifespan.
        client._detach()


def _build_shared_transport(timeout: int) -> tuple[aiohttp.ClientSession, AsyncZabbixAPI]:
    """Create the shared aiohttp session and an API object bound to it.

    Passing ``client_session`` explicitly is what stops zabbix-utils from
    creating (and leaking) its own internal session.
    """
    # Validate config before allocating any socket: AsyncZabbixAPI performs a
    # version check on construction, so a missing-credentials error must be
    # raised first or it would surface as a confusing network failure.
    if not (get_api_token() or get_user_credentials()):
        raise ZabbixConfigError(
            "No Zabbix credentials configured. "
            "Set ZABBIX_API_TOKEN or both ZABBIX_USER and ZABBIX_PASSWORD."
        )
    get_zabbix_url()  # raises ZabbixConfigError when unset

    verify_ssl = get_verify_ssl()
    if not verify_ssl:
        logger.warning("SSL certificate verification is DISABLED (ZABBIX_VERIFY_SSL=false)")

    session = aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=verify_ssl, limit=_MAX_CONNECTIONS),
        timeout=aiohttp.ClientTimeout(total=timeout),
    )
    api = AsyncZabbixAPI(
        url=get_zabbix_url(),
        timeout=timeout,
        validate_certs=verify_ssl,
        client_session=session,
    )
    return session, api


async def authenticate(api: AsyncZabbixAPI) -> bool:
    """Log in to an already-constructed API object.

    Returns True when authenticated with an API token, False with user/password.
    Raises the usual typed errors on failure.
    """
    token = get_api_token()
    creds = get_user_credentials()

    if not token and not creds:
        raise ZabbixConfigError(
            "No Zabbix credentials configured. "
            "Set ZABBIX_API_TOKEN or both ZABBIX_USER and ZABBIX_PASSWORD."
        )

    url = get_zabbix_url()
    try:
        if token:
            logger.debug(
                "Connecting to Zabbix at %s using API token %s", url, redact_token(token)
            )
            await api.login(token=token)
            return True
        user, password = creds  # type: ignore[misc]
        logger.debug("Connecting to Zabbix at %s as user=%s", url, user)
        await api.login(user=user, password=password)
        return False
    except APIRequestError as exc:
        raise _translate_api_error(exc) from exc
    except Exception as exc:
        raise ZabbixNetworkError(
            f"Cannot connect to Zabbix at {url}: {type(exc).__name__}. "
            "Verify ZABBIX_URL and network connectivity."
        ) from exc


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

    Standalone usage (owns and releases its own transport):
        client = ZabbixClient()
        result = await client.call("host.get", {"output": ["hostid", "host"]})
        await client.close()

    Shared usage (tools): the process-wide session is reused and is *not*
    closed when this client is closed.
        async with shared_session() as client:
            result = await client.call("host.get", {"output": "extend"})
    """

    def __init__(self, timeout: int | None = None, shared: bool = False) -> None:
        self._api: AsyncZabbixAPI | None = None
        self._timeout = timeout or int(os.environ.get("ZABBIX_TIMEOUT", "30"))
        self._authenticated_with_token = False
        self._shared = shared
        # Session this client must close on teardown. None in shared mode,
        # where the transport is owned by the process, not by this instance.
        self._owned_session: aiohttp.ClientSession | None = None

    async def _connect(self) -> AsyncZabbixAPI:
        """Initialize and authenticate the Zabbix API session.

        In shared mode this joins (or creates) the process-wide session; in
        standalone mode it builds a private one. Either way the aiohttp
        session is tracked so it can be released.
        """
        if self._shared:
            return await self._connect_shared()

        verify_ssl = get_verify_ssl()
        if not verify_ssl:
            logger.warning("SSL certificate verification is DISABLED (ZABBIX_VERIFY_SSL=false)")

        session, api = _build_shared_transport(self._timeout)
        self._owned_session = session
        try:
            self._authenticated_with_token = await authenticate(api)
        except Exception:
            # Never leak a session that failed to authenticate.
            await session.close()
            self._owned_session = None
            raise
        return api

    async def _connect_shared(self) -> AsyncZabbixAPI:
        """Return the process-wide authenticated API, creating it if needed."""
        async with _get_lock():
            api = _shared_state["api"]
            if api is not None:
                self._authenticated_with_token = bool(_shared_state["token"])
                return api

            timeout = int(os.environ.get("ZABBIX_TIMEOUT", "30"))
            session, new_api = _build_shared_transport(timeout)
            try:
                used_token = await authenticate(new_api)
            except Exception:
                await session.close()
                raise
            _shared_state["api"] = new_api
            _shared_state["session"] = session
            _shared_state["token"] = used_token
            self._authenticated_with_token = used_token
            logger.info("Opened shared Zabbix API session")
            return new_api

    def _drop_shared_api(self) -> None:
        """Discard the cached shared API so the next call reconnects.

        Called when a shared session turns out to be dead, so the existing
        retry loop can rebuild it instead of reusing a broken connection.
        """
        if self._shared:
            _shared_state["api"] = None

    def _detach(self) -> None:
        """Forget this client's API without closing the shared transport."""
        self._api = None
        self._owned_session = None

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
                    # Force a fresh connection on the next attempt. In shared
                    # mode this also evicts the cached API, so the shared
                    # session is rebuilt rather than reused while broken.
                    self._api = None
                    self._drop_shared_api()

        raise ZabbixNetworkError(
            f"Zabbix API call '{method}' failed after {_MAX_RETRIES} attempts "
            f"({type(last_exc).__name__}). "
            "Check ZABBIX_URL and network connectivity."
        ) from last_exc

    async def close(self) -> None:
        """Log out and release the transport.

        Token-based sessions skip the Zabbix-side logout (tokens need none) but
        the HTTP session is still closed -- previously it was abandoned, which
        leaked an aiohttp session and TCP connector per call.

        In shared mode the transport belongs to the process, so this only
        detaches; use close_shared_session() to tear it down.
        """
        api = self._api
        session = self._owned_session
        self._api = None
        self._owned_session = None

        if api is not None and not self._authenticated_with_token:
            try:
                await api.logout()
                logger.debug("Zabbix API session closed")
            except Exception as exc:
                logger.debug("Zabbix logout failed (ignored): %s", exc)
        elif api is not None:
            # Token sessions need no Zabbix logout. logout() would also close
            # the underlying HTTP session, so it is skipped deliberately.
            logger.debug("Token session released (no Zabbix logout needed)")

        if self._shared:
            return

        if session is not None and not session.closed:
            await session.close()

    async def __aenter__(self) -> "ZabbixClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()
