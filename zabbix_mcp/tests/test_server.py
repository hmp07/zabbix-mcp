"""Tests for zabbix_mcp.server — entry point, read-only pruning, transport selection.

Verifies that:
- main() exits with code 1 when no credentials are configured.
- main() runs the stdio transport when MCP_TRANSPORT=stdio.
- main() maps "http" -> "streamable-http" and passes host/port.
- main() passes "sse" through unchanged.
- main() prunes write/delete tools when ZABBIX_READ_ONLY=true.
- main() leaves the full tool set intact when read-only mode is off.
- _apply_read_only_mode() removes exactly the non-read-only tools and is
  idempotent (a second call removes nothing).

The read-only pruning tests mutate the shared FastMCP tool registry, so a
``restore_tool_registry`` fixture snapshots and restores it around each test.
Without it, pruning in one test would silently break every other test file
that asserts on the registered tool set.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from zabbix_mcp.app import mcp
from zabbix_mcp.server import _apply_read_only_mode, main


# ── fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def restore_tool_registry():
    """Snapshot and restore the FastMCP tool registry around a test.

    _apply_read_only_mode() deletes entries from mcp._tool_manager._tools
    permanently for the process lifetime. Tests must not leak that state.
    """
    saved = dict(mcp._tool_manager._tools)
    try:
        yield
    finally:
        mcp._tool_manager._tools.clear()
        mcp._tool_manager._tools.update(saved)


def _tool_names() -> set[str]:
    return set(mcp._tool_manager._tools.keys())


# ── _apply_read_only_mode() ──────────────────────────────────────────────────

class TestApplyReadOnlyMode:
    def test_removes_non_read_only_tools(self, restore_tool_registry: None) -> None:
        """Write and delete tools are removed from the registry."""
        before = _tool_names()
        removed = _apply_read_only_mode()

        assert removed > 0, "expected read-only mode to remove at least one tool"
        assert _tool_names() < before, "tool set should shrink after pruning"

    def test_keeps_exactly_the_read_only_tools(self, restore_tool_registry: None) -> None:
        """Every surviving tool must still carry readOnlyHint=True."""
        before = {n: t for n, t in mcp._tool_manager._tools.items()}
        expected_read_only = {
            n for n, t in before.items()
            if t.annotations and t.annotations.readOnlyHint
        }

        _apply_read_only_mode()

        assert _tool_names() == expected_read_only

    def test_return_value_matches_actual_removal_count(
        self, restore_tool_registry: None
    ) -> None:
        """The returned count must equal the number of tools actually removed."""
        before_count = len(_tool_names())
        removed = _apply_read_only_mode()
        assert removed == before_count - len(_tool_names())

    def test_does_not_remove_read_only_tools(self, restore_tool_registry: None) -> None:
        """Read-only tools are never removed, even if their name looks like a write."""
        read_only_before = {
            n for n, t in mcp._tool_manager._tools.items()
            if t.annotations and t.annotations.readOnlyHint
        }
        _apply_read_only_mode()
        assert read_only_before <= _tool_names()

    def test_no_delete_tools_survive(self, restore_tool_registry: None) -> None:
        """No destructive tool may remain after pruning."""
        _apply_read_only_mode()
        survivors = mcp._tool_manager._tools
        for name, tool in survivors.items():
            assert not name.endswith("_delete"), (
                f"destructive tool '{name}' survived read-only pruning"
            )
            assert tool.annotations.readOnlyHint is True, (
                f"'{name}' survived pruning but is not read-only"
            )

    def test_is_idempotent(self, restore_tool_registry: None) -> None:
        """A second call removes nothing more and keeps the first result."""
        _apply_read_only_mode()
        after_first = _tool_names()
        second = _apply_read_only_mode()
        assert second == 0
        assert _tool_names() == after_first

    def test_returns_positive_count_covering_writes_and_deletes(
        self, restore_tool_registry: None
    ) -> None:
        """Pruning removes both delete tools and non-delete write tools."""
        before = _tool_manager_snapshot()
        removed = _apply_read_only_mode()
        removed_names = {
            n for n, t in before.items()
            if not (t.annotations and t.annotations.readOnlyHint)
        }
        assert removed == len(removed_names)
        assert any(n.endswith("_delete") for n in removed_names)
        assert any(not n.endswith("_delete") for n in removed_names)


def _tool_manager_snapshot() -> dict:
    return dict(mcp._tool_manager._tools)


# ── main() credential gate ───────────────────────────────────────────────────

class TestMainCredentialGate:
    def test_exits_when_no_credentials(
        self, no_zabbix_env: None, restore_tool_registry: None
    ) -> None:
        """No credentials -> SystemExit(1) and the server never starts."""
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1

    def test_does_not_start_transport_without_credentials(
        self, no_zabbix_env: None, restore_tool_registry: None
    ) -> None:
        with patch.object(mcp, "run") as mock_run:
            with pytest.raises(SystemExit):
                main()
        mock_run.assert_not_called()


# ── main() transport selection ───────────────────────────────────────────────

class TestMainTransportSelection:
    def test_stdio_by_default(
        self, zabbix_env: dict, restore_tool_registry: None
    ) -> None:
        with patch.object(mcp, "run") as mock_run:
            main()
        mock_run.assert_called_once_with(transport="stdio")

    def test_http_maps_to_streamable_http(
        self, zabbix_env: dict, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MCP_TRANSPORT", "http")
        monkeypatch.setenv("MCP_HOST", "127.0.0.1")
        monkeypatch.setenv("MCP_PORT", "8001")
        with patch.object(mcp, "run") as mock_run:
            main()
        mock_run.assert_called_once_with(
            transport="streamable-http", host="127.0.0.1", port=8001
        )

    def test_sse_passes_through(
        self, zabbix_env: dict, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MCP_TRANSPORT", "sse")
        monkeypatch.setenv("MCP_PORT", "9000")
        with patch.object(mcp, "run") as mock_run:
            main()
        mock_run.assert_called_once_with(
            transport="sse", host="127.0.0.1", port=9000
        )

    def test_unknown_transport_falls_back_to_stdio(
        self, zabbix_env: dict, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MCP_TRANSPORT", "grpc")
        with patch.object(mcp, "run") as mock_run:
            main()
        assert mock_run.call_args.kwargs["transport"] == "stdio"


# ── main() read-only integration ─────────────────────────────────────────────

    def test_pruned_count_matches_readme(
        self, zabbix_env: dict, monkeypatch: pytest.MonkeyPatch,
        restore_tool_registry: None,
    ) -> None:
        """README states: 60 write/delete tools removed, 26 read-only tools remain.

        Keep this in sync with the "In read-only mode" paragraph in README.md.
        """
        monkeypatch.setenv("ZABBIX_READ_ONLY", "true")
        with patch.object(mcp, "run"):
            main()
        assert len(_tool_names()) == 26

    def test_removed_count_is_sixty(
        self, restore_tool_registry: None
    ) -> None:
        total_before = len(_tool_names())
        removed = _apply_read_only_mode()
        assert removed == 60
        assert total_before - removed == 26


class TestMainReadOnlyIntegration:
    def test_prunes_tools_when_read_only_enabled(
        self, zabbix_env: dict, monkeypatch: pytest.MonkeyPatch,
        restore_tool_registry: None,
    ) -> None:
        """ZABBIX_READ_ONLY=true -> the server exposes only read-only tools."""
        before = _tool_names()
        monkeypatch.setenv("ZABBIX_READ_ONLY", "true")
        with patch.object(mcp, "run"):
            main()

        after = _tool_names()
        assert after < before, "read-only mode should prune write/delete tools"
        for name, tool in mcp._tool_manager._tools.items():
            assert tool.annotations.readOnlyHint is True, (
                f"'{name}' is exposed in read-only mode but is not read-only"
            )

    def test_prunes_before_transport_starts(
        self, zabbix_env: dict, monkeypatch: pytest.MonkeyPatch,
        restore_tool_registry: None,
    ) -> None:
        """Pruning must happen before mcp.run(), not after."""
        monkeypatch.setenv("ZABBIX_READ_ONLY", "true")
        seen_at_run_time: set[str] = set()

        def _capture(**_kwargs: object) -> None:
            seen_at_run_time.update(_tool_names())

        with patch.object(mcp, "run", side_effect=_capture):
            main()

        assert seen_at_run_time
        for name in seen_at_run_time:
            assert not name.endswith("_delete"), (
                f"'{name}' was still registered when the transport started"
            )

    def test_keeps_all_tools_when_read_only_disabled(
        self, zabbix_env: dict, monkeypatch: pytest.MonkeyPatch,
        restore_tool_registry: None,
    ) -> None:
        """Read-only off (default) -> nothing is pruned."""
        monkeypatch.delenv("ZABBIX_READ_ONLY", raising=False)
        before = _tool_names()
        with patch.object(mcp, "run"):
            main()
        assert _tool_names() == before

    def test_falsy_read_only_value_does_not_prune(
        self, zabbix_env: dict, monkeypatch: pytest.MonkeyPatch,
        restore_tool_registry: None,
    ) -> None:
        """ZABBIX_READ_ONLY=false must not trigger pruning."""
        monkeypatch.setenv("ZABBIX_READ_ONLY", "false")
        before = _tool_names()
        with patch.object(mcp, "run"):
            main()
        assert _tool_names() == before
