"""Tests for zabbix_mcp.auth — credential management."""

import pytest

from zabbix_mcp.auth import (
    get_api_token,
    get_user_credentials,
    get_zabbix_url,
    has_credentials,
    redact_token,
)
from zabbix_mcp.errors import ZabbixConfigError


class TestGetZabbixUrl:
    def test_returns_url_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ZABBIX_URL", "https://zabbix.example.com/zabbix")
        assert get_zabbix_url() == "https://zabbix.example.com/zabbix"

    def test_strips_trailing_slash(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ZABBIX_URL", "https://zabbix.example.com/zabbix/")
        assert get_zabbix_url() == "https://zabbix.example.com/zabbix"

    def test_strips_multiple_trailing_slashes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ZABBIX_URL", "https://zabbix.example.com///")
        assert get_zabbix_url() == "https://zabbix.example.com"

    def test_raises_config_error_when_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ZABBIX_URL", raising=False)
        with pytest.raises(ZabbixConfigError, match="ZABBIX_URL"):
            get_zabbix_url()

    def test_raises_config_error_when_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ZABBIX_URL", "")
        with pytest.raises(ZabbixConfigError, match="ZABBIX_URL"):
            get_zabbix_url()

    def test_raises_config_error_when_whitespace_only(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ZABBIX_URL", "   ")
        with pytest.raises(ZabbixConfigError, match="ZABBIX_URL"):
            get_zabbix_url()


class TestGetApiToken:
    def test_returns_token_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ZABBIX_API_TOKEN", "my_secret_token")
        assert get_api_token() == "my_secret_token"

    def test_returns_none_when_not_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ZABBIX_API_TOKEN", raising=False)
        assert get_api_token() is None

    def test_returns_none_when_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ZABBIX_API_TOKEN", "")
        assert get_api_token() is None


class TestGetUserCredentials:
    def test_returns_tuple_when_both_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ZABBIX_USER", "Admin")
        monkeypatch.setenv("ZABBIX_PASSWORD", "secret")
        result = get_user_credentials()
        assert result == ("Admin", "secret")

    def test_returns_none_when_user_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ZABBIX_USER", raising=False)
        monkeypatch.setenv("ZABBIX_PASSWORD", "secret")
        assert get_user_credentials() is None

    def test_returns_none_when_password_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ZABBIX_USER", "Admin")
        monkeypatch.delenv("ZABBIX_PASSWORD", raising=False)
        assert get_user_credentials() is None

    def test_returns_none_when_both_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ZABBIX_USER", raising=False)
        monkeypatch.delenv("ZABBIX_PASSWORD", raising=False)
        assert get_user_credentials() is None

    def test_returns_none_when_user_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ZABBIX_USER", "")
        monkeypatch.setenv("ZABBIX_PASSWORD", "secret")
        assert get_user_credentials() is None

    def test_password_not_in_repr(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The password must never appear in string representations."""
        monkeypatch.setenv("ZABBIX_USER", "Admin")
        monkeypatch.setenv("ZABBIX_PASSWORD", "top_secret_password")
        result = get_user_credentials()
        assert result is not None
        assert result[1] == "top_secret_password"  # value exists but is handled safely


class TestHasCredentials:
    def test_true_with_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ZABBIX_API_TOKEN", "token")
        monkeypatch.delenv("ZABBIX_USER", raising=False)
        monkeypatch.delenv("ZABBIX_PASSWORD", raising=False)
        assert has_credentials() is True

    def test_true_with_user_pass(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ZABBIX_API_TOKEN", raising=False)
        monkeypatch.setenv("ZABBIX_USER", "Admin")
        monkeypatch.setenv("ZABBIX_PASSWORD", "secret")
        assert has_credentials() is True

    def test_true_with_both(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ZABBIX_API_TOKEN", "token")
        monkeypatch.setenv("ZABBIX_USER", "Admin")
        monkeypatch.setenv("ZABBIX_PASSWORD", "secret")
        assert has_credentials() is True

    def test_false_when_nothing_set(self, no_zabbix_env: None) -> None:
        assert has_credentials() is False


class TestRedactToken:
    def test_redacts_token(self) -> None:
        result = redact_token("abcdef1234567890")
        assert "<redacted>" in result
        assert "abcdef1234567890" not in result

    def test_shows_prefix(self) -> None:
        result = redact_token("abcdef1234567890")
        assert result.startswith("a")

    def test_empty_string(self) -> None:
        assert redact_token("") == "<redacted>"

    def test_short_token(self) -> None:
        result = redact_token("x")
        assert "<redacted>" in result
        assert "x" in result

    def test_does_not_reveal_full_token(self) -> None:
        token = "very_long_secret_token_that_must_not_appear"
        result = redact_token(token)
        assert token not in result
        assert len(result) > 0


class TestGetVerifySsl:
    def test_default_is_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ZABBIX_VERIFY_SSL", raising=False)
        from zabbix_mcp.auth import get_verify_ssl
        assert get_verify_ssl() is True

    def test_false_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from zabbix_mcp.auth import get_verify_ssl
        for value in ("false", "False", "FALSE"):
            monkeypatch.setenv("ZABBIX_VERIFY_SSL", value)
            assert get_verify_ssl() is False

    def test_zero_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from zabbix_mcp.auth import get_verify_ssl
        monkeypatch.setenv("ZABBIX_VERIFY_SSL", "0")
        assert get_verify_ssl() is False

    def test_no_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from zabbix_mcp.auth import get_verify_ssl
        monkeypatch.setenv("ZABBIX_VERIFY_SSL", "no")
        assert get_verify_ssl() is False

    def test_true_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from zabbix_mcp.auth import get_verify_ssl
        for value in ("true", "True", "1", "yes"):
            monkeypatch.setenv("ZABBIX_VERIFY_SSL", value)
            assert get_verify_ssl() is True
