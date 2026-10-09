"""Tests for zabbix_mcp.client — Zabbix API wrapper.

AsyncZabbixAPI is mocked at the class level to avoid real network calls.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from zabbix_mcp.client import ZabbixClient
from zabbix_mcp.errors import (
    ZabbixAPIError,
    ZabbixAuthError,
    ZabbixConfigError,
    ZabbixNetworkError,
    ZabbixNotFoundError,
    ZabbixPermissionError,
)


def _make_api_exception(message: str, code: int = -32602) -> Exception:
    """Create an APIRequestError with a structured body."""
    from zabbix_utils import APIRequestError

    return APIRequestError({"message": message, "data": "", "body": {"code": code}})


def _patch_transport():
    """Patch the aiohttp session and connector used to build the transport.

    _build_shared_transport() now creates the ClientSession explicitly and
    hands it to AsyncZabbixAPI, so the real aiohttp objects must be replaced
    or a test would open genuine sockets.
    """
    return patch.multiple(
        "zabbix_mcp.client.aiohttp",
        ClientSession=AsyncMock,
        TCPConnector=AsyncMock,
        ClientTimeout=AsyncMock,
    )


class TestZabbixClientConnect:
    @pytest.fixture(autouse=True)
    def _no_real_sockets(self):
        with _patch_transport():
            yield

    async def test_connects_with_token(self, zabbix_env: dict[str, str]) -> None:
        with patch("zabbix_mcp.client.AsyncZabbixAPI") as MockAPI:
            mock_api = AsyncMock()
            MockAPI.return_value = mock_api

            client = ZabbixClient()
            await client._connect()

            _, kwargs = MockAPI.call_args
            assert kwargs["url"] == "https://zabbix.example.com/zabbix"
            assert kwargs["timeout"] == 30
            assert kwargs["validate_certs"] is True
            # The transport is created here and passed in, so zabbix-utils does
            # not create (and leak) an internal session of its own.
            assert "client_session" in kwargs
            mock_api.login.assert_awaited_once_with(token="test_token_abc123")

    async def test_connects_with_user_password(
        self, zabbix_env_userpass: dict[str, str]
    ) -> None:
        with patch("zabbix_mcp.client.AsyncZabbixAPI") as MockAPI:
            mock_api = AsyncMock()
            MockAPI.return_value = mock_api

            client = ZabbixClient()
            await client._connect()

            mock_api.login.assert_awaited_once_with(user="Admin", password="secret_password")

    async def test_raises_config_error_when_no_url(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ZABBIX_API_TOKEN", "tok")
        monkeypatch.delenv("ZABBIX_URL", raising=False)

        client = ZabbixClient()
        with pytest.raises(ZabbixConfigError, match="ZABBIX_URL"):
            await client._connect()

    async def test_raises_config_error_when_no_credentials(
        self, no_zabbix_env: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ZABBIX_URL", "https://zabbix.example.com/zabbix")

        client = ZabbixClient()
        with pytest.raises(ZabbixConfigError, match="credentials"):
            await client._connect()

    async def test_raises_network_error_on_connection_failure(
        self, zabbix_env: dict[str, str]
    ) -> None:
        with patch("zabbix_mcp.client.AsyncZabbixAPI") as MockAPI:
            mock_api = AsyncMock()
            mock_api.login.side_effect = ConnectionRefusedError("refused")
            MockAPI.return_value = mock_api

            client = ZabbixClient()
            with pytest.raises(ZabbixNetworkError, match="Cannot connect"):
                await client._connect()

    async def test_raises_auth_error_on_bad_token(
        self, zabbix_env: dict[str, str]
    ) -> None:
        with patch("zabbix_mcp.client.AsyncZabbixAPI") as MockAPI:
            mock_api = AsyncMock()
            mock_api.login.side_effect = _make_api_exception("Not authorized.")
            MockAPI.return_value = mock_api

            client = ZabbixClient()
            with pytest.raises(ZabbixAuthError):
                await client._connect()

    async def test_token_auth_sets_flag(self, zabbix_env: dict[str, str]) -> None:
        with patch("zabbix_mcp.client.AsyncZabbixAPI") as MockAPI:
            mock_api = AsyncMock()
            MockAPI.return_value = mock_api

            client = ZabbixClient()
            await client._connect()
            assert client._authenticated_with_token is True

    async def test_userpass_auth_clears_flag(
        self, zabbix_env_userpass: dict[str, str]
    ) -> None:
        with patch("zabbix_mcp.client.AsyncZabbixAPI") as MockAPI:
            mock_api = AsyncMock()
            MockAPI.return_value = mock_api

            client = ZabbixClient()
            await client._connect()
            assert client._authenticated_with_token is False

    async def test_custom_timeout_passed_to_api(
        self, zabbix_env: dict[str, str]
    ) -> None:
        with patch("zabbix_mcp.client.AsyncZabbixAPI") as MockAPI:
            mock_api = AsyncMock()
            MockAPI.return_value = mock_api

            client = ZabbixClient(timeout=60)
            await client._connect()

            _, kwargs = MockAPI.call_args
            assert kwargs["timeout"] == 60


class TestZabbixClientCall:
    async def test_call_success(self, zabbix_env: dict[str, str]) -> None:
        with patch("zabbix_mcp.client.AsyncZabbixAPI"):
            client = ZabbixClient()
            mock_api = AsyncMock()
            mock_api.host.get = AsyncMock(return_value=[{"hostid": "1", "host": "server1"}])
            client._api = mock_api
            client._authenticated_with_token = True

            result = await client.call("host.get", {"output": ["hostid", "host"]})
            assert result == [{"hostid": "1", "host": "server1"}]
            mock_api.host.get.assert_awaited_once_with(output=["hostid", "host"])

    async def test_call_empty_params(self, zabbix_env: dict[str, str]) -> None:
        with patch("zabbix_mcp.client.AsyncZabbixAPI"):
            client = ZabbixClient()
            mock_api = AsyncMock()
            mock_api.host.get = AsyncMock(return_value=[])
            client._api = mock_api

            result = await client.call("host.get")
            assert result == []

    async def test_call_invalid_method_format(
        self, zabbix_env: dict[str, str]
    ) -> None:
        client = ZabbixClient()
        with pytest.raises(ValueError, match="Invalid Zabbix method"):
            await client.call("hostget")

    async def test_call_translates_auth_error(
        self, zabbix_env: dict[str, str]
    ) -> None:
        with patch("zabbix_mcp.client.AsyncZabbixAPI"):
            client = ZabbixClient()
            mock_api = AsyncMock()
            mock_api.host.get = AsyncMock(
                side_effect=_make_api_exception("Not authorized.")
            )
            client._api = mock_api

            with pytest.raises(ZabbixAuthError):
                await client.call("host.get")

    async def test_call_translates_permission_error(
        self, zabbix_env: dict[str, str]
    ) -> None:
        with patch("zabbix_mcp.client.AsyncZabbixAPI"):
            client = ZabbixClient()
            mock_api = AsyncMock()
            mock_api.host.get = AsyncMock(
                side_effect=_make_api_exception("No permissions to referred object.")
            )
            client._api = mock_api

            with pytest.raises(ZabbixPermissionError):
                await client.call("host.get")

    async def test_call_translates_not_found_error(
        self, zabbix_env: dict[str, str]
    ) -> None:
        with patch("zabbix_mcp.client.AsyncZabbixAPI"):
            client = ZabbixClient()
            mock_api = AsyncMock()
            mock_api.host.get = AsyncMock(
                side_effect=_make_api_exception("Host does not exist.")
            )
            client._api = mock_api

            with pytest.raises(ZabbixNotFoundError):
                await client.call("host.get")

    async def test_call_translates_generic_api_error(
        self, zabbix_env: dict[str, str]
    ) -> None:
        with patch("zabbix_mcp.client.AsyncZabbixAPI"):
            client = ZabbixClient()
            mock_api = AsyncMock()
            mock_api.host.get = AsyncMock(
                side_effect=_make_api_exception("Invalid parameter.")
            )
            client._api = mock_api

            with pytest.raises(ZabbixAPIError):
                await client.call("host.get")

    async def test_call_does_not_retry_api_exceptions(
        self, zabbix_env: dict[str, str]
    ) -> None:
        with patch("zabbix_mcp.client.AsyncZabbixAPI"):
            client = ZabbixClient()
            mock_api = AsyncMock()
            mock_api.host.get = AsyncMock(
                side_effect=_make_api_exception("Invalid parameter.")
            )
            client._api = mock_api

            with pytest.raises(ZabbixAPIError):
                await client.call("host.get")

            assert mock_api.host.get.call_count == 1

    async def test_call_retries_on_network_error(
        self, zabbix_env: dict[str, str]
    ) -> None:
        with patch("zabbix_mcp.client.AsyncZabbixAPI") as MockAPI:
            with patch("zabbix_mcp.client.asyncio.sleep", new_callable=AsyncMock):
                mock_api = AsyncMock()
                mock_api.host.get = AsyncMock(
                    side_effect=[
                        ConnectionError("timeout"),
                        ConnectionError("timeout"),
                        [{"hostid": "1"}],
                    ]
                )
                MockAPI.return_value = mock_api

                client = ZabbixClient()
                client._api = mock_api

                result = await client.call("host.get")
                assert result == [{"hostid": "1"}]
                assert mock_api.host.get.call_count == 3

    async def test_call_raises_network_error_after_max_retries(
        self, zabbix_env: dict[str, str]
    ) -> None:
        with patch("zabbix_mcp.client.AsyncZabbixAPI") as MockAPI:
            with patch("zabbix_mcp.client.asyncio.sleep", new_callable=AsyncMock):
                mock_api = AsyncMock()
                mock_api.host.get = AsyncMock(
                    side_effect=ConnectionError("unreachable")
                )
                MockAPI.return_value = mock_api

                client = ZabbixClient()
                client._api = mock_api

                with pytest.raises(ZabbixNetworkError, match="3 attempts"):
                    await client.call("host.get")

                assert mock_api.host.get.call_count == 3

    async def test_call_resets_api_on_retry(self, zabbix_env: dict[str, str]) -> None:
        with patch("zabbix_mcp.client.AsyncZabbixAPI") as MockAPI:
            with patch("zabbix_mcp.client.asyncio.sleep", new_callable=AsyncMock):
                mock_api_1 = AsyncMock()
                mock_api_2 = AsyncMock()
                mock_api_1.host.get = AsyncMock(side_effect=ConnectionError("drop"))
                mock_api_2.host.get = AsyncMock(return_value=[])
                MockAPI.side_effect = [mock_api_1, mock_api_2]

                client = ZabbixClient()
                client._api = mock_api_1

                result = await client.call("host.get")
                assert result == []


class TestZabbixClientClose:
    async def test_close_calls_logout_for_user_pass(
        self, zabbix_env_userpass: dict[str, str]
    ) -> None:
        with patch("zabbix_mcp.client.AsyncZabbixAPI"):
            client = ZabbixClient()
            mock_api = AsyncMock()
            client._api = mock_api
            client._authenticated_with_token = False

            await client.close()
            mock_api.logout.assert_awaited_once()
            assert client._api is None

    async def test_close_does_not_logout_for_token(
        self, zabbix_env: dict[str, str]
    ) -> None:
        with patch("zabbix_mcp.client.AsyncZabbixAPI"):
            client = ZabbixClient()
            mock_api = AsyncMock()
            client._api = mock_api
            client._authenticated_with_token = True

            await client.close()
            mock_api.logout.assert_not_awaited()
            assert client._api is None

    async def test_close_tolerates_logout_failure(
        self, zabbix_env_userpass: dict[str, str]
    ) -> None:
        with patch("zabbix_mcp.client.AsyncZabbixAPI"):
            client = ZabbixClient()
            mock_api = AsyncMock()
            mock_api.logout = AsyncMock(side_effect=Exception("gone"))
            client._api = mock_api
            client._authenticated_with_token = False

            await client.close()
            assert client._api is None

    async def test_close_noop_when_not_connected(
        self, zabbix_env: dict[str, str]
    ) -> None:
        client = ZabbixClient()
        await client.close()

    async def test_context_manager(self, zabbix_env: dict[str, str]) -> None:
        with patch("zabbix_mcp.client.AsyncZabbixAPI") as MockAPI:
            mock_api = AsyncMock()
            MockAPI.return_value = mock_api

            # A standalone client owns its transport; shared_session() is the
            # process-wide path exercised in test_session.py.
            async with ZabbixClient() as client:
                client._api = mock_api
                client._authenticated_with_token = True
                assert client._api is not None

            assert client._api is None


class TestCredentialSafetyInLogs:
    async def test_password_not_logged(
        self, zabbix_env_userpass: dict[str, str], caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging

        with patch("zabbix_mcp.client.AsyncZabbixAPI") as MockAPI:
            mock_api = AsyncMock()
            MockAPI.return_value = mock_api

            with caplog.at_level(logging.DEBUG, logger="zabbix_mcp"):
                client = ZabbixClient()
                await client._connect()

            assert "secret_password" not in caplog.text

    async def test_full_token_not_logged(
        self, zabbix_env: dict[str, str], caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging

        with patch("zabbix_mcp.client.AsyncZabbixAPI") as MockAPI:
            mock_api = AsyncMock()
            MockAPI.return_value = mock_api

            with caplog.at_level(logging.DEBUG, logger="zabbix_mcp"):
                client = ZabbixClient()
                await client._connect()

            assert "test_token_abc123" not in caplog.text
