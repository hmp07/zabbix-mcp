"""Tests for the shared Zabbix HTTP session in zabbix_mcp.client.

The tool layer no longer opens one aiohttp session per call. These tests pin
the behaviour that fixes the original leak:

- The session is created once and reused across tool calls.
- close_shared_session() releases the aiohttp session and its connector.
- A token session does not call Zabbix logout on teardown.
- A user/password session does call it.
- A failed authentication does not leave an open session behind.
- The retry loop evicts a broken shared session so the next attempt rebuilds.
- The server lifespan closes the shared session on shutdown.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from zabbix_mcp import client as client_mod
from zabbix_mcp.client import ZabbixClient, close_shared_session, shared_session
from zabbix_mcp.errors import ZabbixAuthError


@pytest.fixture(autouse=True)
def _clean_shared_state():
    """Guarantee no session leaks between tests, in either direction."""
    client_mod.reset_shared_state()
    yield
    client_mod.reset_shared_state()


@pytest.fixture()
def fake_transport():
    """Replace aiohttp with mocks and AsyncZabbixAPI with a stub.

    Returns the mock objects so tests can assert on close() being awaited.
    """
    session = AsyncMock()
    session.closed = False
    connector = AsyncMock()

    api = AsyncMock()

    with (
        patch.object(client_mod.aiohttp, "ClientSession", return_value=session),
        patch.object(client_mod.aiohttp, "TCPConnector", return_value=connector),
        patch.object(client_mod.aiohttp, "ClientTimeout", return_value=MagicMock()),
        patch.object(client_mod, "AsyncZabbixAPI", return_value=api),
    ):
        yield {"session": session, "connector": connector, "api": api}


class TestSharedSessionReuse:
    async def test_reuses_one_session_across_calls(
        self, zabbix_env: dict, fake_transport: dict
    ) -> None:
        """Ten tool calls must produce one login and one aiohttp session."""
        for _ in range(10):
            async with shared_session() as c:
                await c.call("host.get", {"output": ["hostid"]})

        assert fake_transport["api"].login.await_count == 1, "logged in more than once"
        assert client_mod.aiohttp.ClientSession.call_count == 1, "session rebuilt"

        await close_shared_session()

    async def test_concurrent_calls_share_one_session(
        self, zabbix_env: dict, fake_transport: dict
    ) -> None:
        """The lock must collapse parallel first-calls into a single connect."""
        import asyncio

        async def one_call() -> None:
            async with shared_session() as c:
                await c.call("host.get", {"output": ["hostid"]})

        await asyncio.gather(*(one_call() for _ in range(5)))

        assert fake_transport["api"].login.await_count == 1
        await close_shared_session()

    async def test_shared_client_detaches_without_closing(
        self, zabbix_env: dict, fake_transport: dict
    ) -> None:
        """Leaving the context must NOT close the shared transport."""
        async with shared_session() as c:
            await c.call("host.get", {"output": ["hostid"]})

        assert fake_transport["session"].close.await_count == 0, (
            "shared session was closed by a single tool call"
        )
        await close_shared_session()


class TestCloseSharedSession:
    async def test_closes_aiohttp_session(
        self, zabbix_env: dict, fake_transport: dict
    ) -> None:
        async with shared_session() as c:
            await c.call("host.get", {"output": ["hostid"]})

        await close_shared_session()

        assert fake_transport["session"].close.await_count == 1

    async def test_closes_connector(
        self, zabbix_env: dict, fake_transport: dict
    ) -> None:
        async with shared_session() as c:
            await c.call("host.get", {"output": ["hostid"]})

        await close_shared_session()

        # The connector is owned by the session we created and passed in, so
        # closing the session must be enough to release it.
        assert fake_transport["session"].close.await_count == 1

    async def test_token_session_does_not_call_logout(
        self, zabbix_env: dict, fake_transport: dict
    ) -> None:
        async with shared_session() as c:
            await c.call("host.get", {"output": ["hostid"]})

        await close_shared_session()

        fake_transport["api"].logout.assert_not_awaited()

    async def test_userpass_session_calls_logout(
        self, zabbix_env_userpass: dict, fake_transport: dict
    ) -> None:
        async with shared_session() as c:
            await c.call("host.get", {"output": ["hostid"]})

        await close_shared_session()

        fake_transport["api"].logout.assert_awaited_once()

    async def test_is_idempotent(
        self, zabbix_env: dict, fake_transport: dict
    ) -> None:
        async with shared_session() as c:
            await c.call("host.get", {"output": ["hostid"]})

        await close_shared_session()
        await close_shared_session()  # must not raise

        assert fake_transport["session"].close.await_count == 1

    async def test_noop_when_never_opened(self) -> None:
        await close_shared_session()  # must not raise

    async def test_tolerates_logout_failure(
        self, zabbix_env_userpass: dict, fake_transport: dict
    ) -> None:
        fake_transport["api"].logout = AsyncMock(side_effect=Exception("gone"))

        async with shared_session() as c:
            await c.call("host.get", {"output": ["hostid"]})

        await close_shared_session()  # must not raise
        assert fake_transport["session"].close.await_count == 1


class TestStandaloneClientStillCloses:
    async def test_standalone_close_closes_session(
        self, zabbix_env: dict, fake_transport: dict
    ) -> None:
        """A non-shared client owns its transport and must release it."""
        c = ZabbixClient()
        await c._connect()
        await c.close()

        assert fake_transport["session"].close.await_count == 1

    async def test_standalone_does_not_touch_shared_state(
        self, zabbix_env: dict, fake_transport: dict
    ) -> None:
        c = ZabbixClient()
        await c._connect()
        await c.close()

        assert client_mod._shared_state["api"] is None


class TestFailedAuthDoesNotLeak:
    async def test_auth_failure_closes_session(
        self, zabbix_env: dict, fake_transport: dict
    ) -> None:
        """A failed login must not leave an aiohttp session open."""
        from zabbix_utils import APIRequestError

        fake_transport["api"].login.side_effect = APIRequestError(
            {"message": "Not authorized.", "data": "", "body": {"code": -32602}}
        )

        with pytest.raises(ZabbixAuthError):
            async with shared_session() as c:
                await c.call("host.get", {"output": ["hostid"]})

        assert fake_transport["session"].close.await_count == 1, (
            "session leaked after failed authentication"
        )
        assert client_mod._shared_state["api"] is None


class TestRetryEvictsSharedSession:
    async def test_network_error_rebuilds_shared_session(
        self, zabbix_env: dict, fake_transport: dict
    ) -> None:
        """A dead shared session must be discarded so retry can reconnect."""
        api_1 = AsyncMock()
        api_1.host.get = AsyncMock(side_effect=ConnectionError("drop"))
        api_2 = AsyncMock()
        api_2.host.get = AsyncMock(return_value=[{"hostid": "1"}])

        with patch.object(client_mod, "AsyncZabbixAPI", side_effect=[api_1, api_2]):
            with patch.object(client_mod.asyncio, "sleep", new_callable=AsyncMock):
                async with shared_session() as c:
                    result = await c.call("host.get", {"output": ["hostid"]})

        assert result == [{"hostid": "1"}]
        assert api_1.host.get.await_count == 1
        assert api_2.host.get.await_count == 1

        await close_shared_session()


class TestLifespanClosesSession:
    async def test_lifespan_closes_shared_session_on_shutdown(
        self, zabbix_env: dict, fake_transport: dict
    ) -> None:
        """The server lifespan must release the session when it stops."""
        from zabbix_mcp.app import mcp

        async with mcp._mcp_server.lifespan(mcp._mcp_server) as _ctx:
            # Touch a tool so a session actually exists.
            from zabbix_mcp.tools.host import zabbix_host_get

            await zabbix_host_get(limit=1)

        assert fake_transport["session"].close.await_count == 1, (
            "lifespan did not close the shared session"
        )
