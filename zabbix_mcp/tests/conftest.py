"""Shared pytest fixtures for Zabbix MCP tests."""

import pytest


@pytest.fixture()
def zabbix_env(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Set a baseline Zabbix environment with a token."""
    env = {
        "ZABBIX_URL": "https://zabbix.example.com/zabbix",
        "ZABBIX_API_TOKEN": "test_token_abc123",
    }
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    # Ensure user/pass vars are absent
    monkeypatch.delenv("ZABBIX_USER", raising=False)
    monkeypatch.delenv("ZABBIX_PASSWORD", raising=False)
    return env


@pytest.fixture()
def zabbix_env_userpass(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Set a baseline Zabbix environment with user/password credentials."""
    env = {
        "ZABBIX_URL": "https://zabbix.example.com/zabbix",
        "ZABBIX_USER": "Admin",
        "ZABBIX_PASSWORD": "secret_password",
    }
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("ZABBIX_API_TOKEN", raising=False)
    return env


@pytest.fixture()
def no_zabbix_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove all Zabbix environment variables."""
    for key in ("ZABBIX_URL", "ZABBIX_API_TOKEN", "ZABBIX_USER", "ZABBIX_PASSWORD"):
        monkeypatch.delenv(key, raising=False)
