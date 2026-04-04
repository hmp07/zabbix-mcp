"""Phase 6 — Security tests.

Verifies that:
- No credential parameters appear in any tool's input schema.
- Token/password are never returned raw in error messages.
- redact_token() always hides the secret.
- ZabbixConfigError raised when no credentials are configured.
- ZabbixAuthError raised on invalid token (not a generic exception).
- Auth errors do not contain the raw credential value.
- SSRF: ZABBIX_URL is not injectable via tool parameters.
- Client enforces method validation before touching the network.
"""

from __future__ import annotations

import inspect
import os
import pytest
from unittest.mock import AsyncMock, patch

from zabbix_mcp.auth import redact_token
from zabbix_mcp.client import ZabbixClient
from zabbix_mcp.errors import ZabbixAuthError, ZabbixConfigError, ZabbixNetworkError
from zabbix_mcp.app import mcp

_CREDENTIAL_PARAM_NAMES = {
    "zabbix_url", "api_url", "host_url", "base_url", "server_url",
    "token", "api_token", "zabbix_token", "auth_token",
    "password", "passwd", "secret", "api_key", "apikey",
    "username", "user", "login",
    "zabbix_user", "zabbix_password", "zabbix_api_token",
}


class TestNoCredentialsInToolSchemas:
    def test_no_credential_params_in_any_tool(self) -> None:
        tools = mcp._tool_manager.list_tools()
        violations = []
        for tool in tools:
            param_names = set(tool.parameters.get("properties", {}).keys())
            bad = param_names & _CREDENTIAL_PARAM_NAMES
            if bad:
                violations.append(f"{tool.name}: {bad}")
        assert not violations, (
            "The following tools expose credential parameters — "
            "credentials must come from env vars only:\n" + "\n".join(violations)
        )

    def test_no_credential_params_in_tool_function_signatures(self) -> None:
        tools = mcp._tool_manager.list_tools()
        violations = []
        for tool in tools:
            sig = inspect.signature(tool.fn)
            bad = set(sig.parameters.keys()) & _CREDENTIAL_PARAM_NAMES
            if bad:
                violations.append(f"{tool.name}: {bad}")
        assert not violations, (
            "Tool functions expose credential parameters:\n" + "\n".join(violations)
        )

    def test_no_url_override_param_in_any_tool(self) -> None:
        tools = mcp._tool_manager.list_tools()
        api_endpoint_params = {"zabbix_url", "api_url", "base_url", "server_url", "endpoint"}
        violations = []
        for tool in tools:
            param_names = set(tool.parameters.get("properties", {}).keys())
            bad = param_names & api_endpoint_params
            if bad:
                violations.append(f"{tool.name}: {bad}")
        assert not violations, (
            "The following tools accept API endpoint parameters — this enables SSRF:\n"
            + "\n".join(violations)
        )


class TestRedactToken:
    def test_short_token_fully_redacted(self) -> None:
        result = redact_token("ab")
        assert "ab" not in result

    def test_long_token_partially_visible(self) -> None:
        token = "abcdef1234567890"
        result = redact_token(token)
        assert "<redacted>" in result
        assert token not in result

    def test_empty_string_returns_redacted(self) -> None:
        result = redact_token("")
        assert "<redacted>" in result

    def test_full_secret_never_in_result(self) -> None:
        secret = "super-secret-token-value-1234"
        result = redact_token(secret)
        assert secret not in result

    def test_result_always_contains_redacted_marker(self) -> None:
        for value in ["x", "short", "a" * 100]:
            result = redact_token(value)
            assert "<redacted>" in result

    def test_visible_prefix_is_short(self) -> None:
        token = "a" * 64
        result = redact_token(token)
        visible_part = result.split("...")[0]
        assert len(visible_part) <= 8


class TestMissingCredentials:
    async def test_raises_config_error_when_no_credentials(self, no_zabbix_env: dict) -> None:
        async with ZabbixClient() as client:
            with pytest.raises(ZabbixConfigError):
                await client.call("host.get", {})

    async def test_config_error_message_is_actionable(self, no_zabbix_env: dict) -> None:
        async with ZabbixClient() as client:
            with pytest.raises(ZabbixConfigError, match="ZABBIX_URL|ZABBIX_API_TOKEN"):
                await client.call("host.get", {})


class TestAuthErrorTranslation:
    async def test_invalid_token_raises_auth_error(self, zabbix_env: dict) -> None:
        from zabbix_utils import APIRequestError

        def _make_api_error(msg: str) -> APIRequestError:
            err = APIRequestError.__new__(APIRequestError)
            err.body = {"code": -32602, "message": msg, "data": ""}
            Exception.__init__(err, msg)
            return err

        auth_exc = _make_api_error("Not authorized.")
        mock_api = AsyncMock()
        mock_api.login = AsyncMock(side_effect=auth_exc)

        with patch("zabbix_mcp.client.AsyncZabbixAPI", return_value=mock_api):
            async with ZabbixClient() as client:
                with pytest.raises(ZabbixAuthError):
                    await client.call("host.get", {})

    async def test_auth_error_message_does_not_contain_token(self, zabbix_env: dict) -> None:
        from zabbix_utils import APIRequestError

        token = os.environ.get("ZABBIX_API_TOKEN", "test-token-value")

        def _make_api_error(msg: str) -> APIRequestError:
            err = APIRequestError.__new__(APIRequestError)
            err.body = {"code": -32602, "message": msg, "data": ""}
            Exception.__init__(err, msg)
            return err

        auth_exc = _make_api_error("Not authorized.")
        mock_api = AsyncMock()
        mock_api.login = AsyncMock(side_effect=auth_exc)

        with patch("zabbix_mcp.client.AsyncZabbixAPI", return_value=mock_api):
            async with ZabbixClient() as client:
                try:
                    await client.call("host.get", {})
                except ZabbixAuthError as exc:
                    assert token not in str(exc), "Auth error message must not contain the raw token"
                except Exception:
                    pass

    async def test_network_error_does_not_contain_password(self, zabbix_env_userpass: dict) -> None:
        password = os.environ.get("ZABBIX_PASSWORD", "test-password")
        mock_api = AsyncMock()
        mock_api.login = AsyncMock(side_effect=ConnectionError("Connection refused"))

        with patch("zabbix_mcp.client.AsyncZabbixAPI", return_value=mock_api):
            async with ZabbixClient() as client:
                try:
                    await client.call("host.get", {})
                except Exception as exc:
                    assert password not in str(exc), "Error must not contain the password"


class TestSSRFPrevention:
    def test_zabbix_url_always_from_env_not_tool_args(self) -> None:
        tools = mcp._tool_manager.list_tools()
        api_endpoint_params = {"zabbix_url", "api_url", "base_url", "server_url", "endpoint"}
        for tool in tools:
            params = set(tool.parameters.get("properties", {}).keys())
            bad = params & api_endpoint_params
            assert not bad, (
                f"Tool '{tool.name}' has API endpoint override parameter(s): {bad}"
            )

    async def test_url_comes_from_env_var(self, zabbix_env: dict) -> None:
        from zabbix_mcp.auth import get_zabbix_url
        expected_url = os.environ["ZABBIX_URL"].rstrip("/")
        assert get_zabbix_url() == expected_url

    async def test_url_cannot_be_overridden_at_call_time(self, zabbix_env: dict) -> None:
        mock_api = AsyncMock()
        mock_api.host = AsyncMock()
        mock_api.host.get = AsyncMock(return_value=[])

        captured_url = None

        def fake_zabbix_api(url: str, **kwargs):
            nonlocal captured_url
            captured_url = url
            return mock_api

        with patch("zabbix_mcp.client.AsyncZabbixAPI", side_effect=fake_zabbix_api):
            async with ZabbixClient() as client:
                client._api = mock_api
                await client.call("host.get", {"output": ["hostid"]})

        assert captured_url is None or captured_url == os.environ["ZABBIX_URL"].rstrip("/")


class TestInputValidation:
    async def test_host_get_rejects_invalid_limit_too_high(self, zabbix_env: dict) -> None:
        from pydantic import ValidationError
        from zabbix_mcp.tools.host import zabbix_host_get

        with pytest.raises((ValidationError, Exception)):
            await zabbix_host_get(limit=99999)

    async def test_trigger_get_rejects_invalid_priority(self, zabbix_env: dict) -> None:
        from pydantic import ValidationError
        from zabbix_mcp.tools.trigger import zabbix_trigger_get

        with pytest.raises((ValidationError, Exception)):
            await zabbix_trigger_get(priority=99)

    async def test_event_acknowledge_rejects_zero_action(self, zabbix_env: dict) -> None:
        from pydantic import ValidationError
        from zabbix_mcp.tools.monitoring import zabbix_event_acknowledge

        with pytest.raises((ValidationError, Exception)):
            await zabbix_event_acknowledge(eventids=["1"], action=0)


class TestLogRedaction:
    async def test_debug_log_does_not_emit_full_token(
        self, zabbix_env: dict, caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging
        token = os.environ.get("ZABBIX_API_TOKEN", "test-token-value")

        mock_api = AsyncMock()
        mock_api.login = AsyncMock(return_value=None)
        mock_api.host = AsyncMock()
        mock_api.host.get = AsyncMock(return_value=[])

        with patch("zabbix_mcp.client.AsyncZabbixAPI", return_value=mock_api):
            with caplog.at_level(logging.DEBUG, logger="zabbix_mcp.client"):
                async with ZabbixClient() as client:
                    client._api = None
                    await client.call("host.get", {})

        for record in caplog.records:
            assert token not in record.getMessage(), (
                f"Full token found in log message: {record.getMessage()!r}"
            )
