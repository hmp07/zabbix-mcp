"""Tests for zabbix_mcp.tools._params — Zabbix API parameter assembly helpers.

These helpers replaced a per-field ``if x is not None: params["x"] = x`` pattern
repeated across every tool. Zabbix rejects explicit ``None`` and rejects an empty
``filter``/``search``, so the exact drop/keep semantics matter.

Verifies that:
- compact() drops only None, and keeps False / 0 / "" / [] / {}.
- filter_params()/search_params() omit the key entirely when empty.
- filter_params()/search_params() merge multiple fields into one nested dict.
- as_int_flag() maps True/False/None to 1/0/None.
"""

from __future__ import annotations

from typing import Any

import pytest

from zabbix_mcp.tools._params import as_int_flag, compact, filter_params, search_params


class TestCompact:
    def test_drops_none_values(self) -> None:
        assert compact({"a": 1, "b": None}) == {"a": 1}

    def test_keeps_false(self) -> None:
        """False is a meaningful Zabbix value and must survive."""
        assert compact({"flag": False}) == {"flag": False}

    def test_keeps_zero(self) -> None:
        """status=0 means 'enabled' in Zabbix -- must not be dropped."""
        assert compact({"status": 0}) == {"status": 0}

    def test_keeps_empty_string(self) -> None:
        assert compact({"name": ""}) == {"name": ""}

    def test_keeps_empty_list(self) -> None:
        """An explicitly empty list is a deliberate request, not an absent filter."""
        assert compact({"hostids": []}) == {"hostids": []}

    def test_keeps_empty_dict(self) -> None:
        assert compact({"filter": {}}) == {"filter": {}}

    def test_empty_input(self) -> None:
        assert compact({}) == {}

    def test_all_none_becomes_empty(self) -> None:
        assert compact({"a": None, "b": None}) == {}

    def test_preserves_order(self) -> None:
        assert list(compact({"z": 1, "a": 2, "m": 3})) == ["z", "a", "m"]

    def test_does_not_mutate_input(self) -> None:
        source: dict[str, Any] = {"a": 1, "b": None}
        compact(source)
        assert source == {"a": 1, "b": None}


class TestFilterParams:
    def test_wraps_single_field(self) -> None:
        assert filter_params(status=1) == {"filter": {"status": 1}}

    def test_merges_multiple_fields(self) -> None:
        result = filter_params(status=1, value=0, priority=4)
        assert result == {"filter": {"status": 1, "value": 0, "priority": 4}}

    def test_omits_key_when_all_none(self) -> None:
        """Zabbix rejects an empty filter object, so the key must be absent."""
        assert filter_params(status=None) == {}

    def test_drops_none_members_but_keeps_set_ones(self) -> None:
        result = filter_params(status=1, value=None)
        assert result == {"filter": {"status": 1}}

    def test_no_args(self) -> None:
        assert filter_params() == {}

    def test_keeps_zero_member(self) -> None:
        assert filter_params(priority=0) == {"filter": {"priority": 0}}


class TestSearchParams:
    def test_wraps_single_field(self) -> None:
        assert search_params(name="web") == {"search": {"name": "web"}}

    def test_merges_multiple_fields(self) -> None:
        result = search_params(name="web", key_="cpu")
        assert result == {"search": {"name": "web", "key_": "cpu"}}

    def test_omits_key_when_all_none(self) -> None:
        assert search_params(name=None) == {}

    def test_no_args(self) -> None:
        assert search_params() == {}

    def test_drops_none_members(self) -> None:
        assert search_params(name="web", key_=None) == {"search": {"name": "web"}}


class TestFilterAndSearchCombined:
    def test_merges_into_existing_params(self) -> None:
        """Both helpers can be applied to the same flat params dict."""
        params = compact({"output": ["hostid"], "hostids": None})
        params.update(filter_params(status=1))
        params.update(search_params(name="web"))
        assert params == {
            "output": ["hostid"],
            "filter": {"status": 1},
            "search": {"name": "web"},
        }

    def test_no_filters_leaves_only_flat_keys(self) -> None:
        params = compact({"output": ["hostid"], "limit": 100})
        params.update(filter_params(status=None))
        params.update(search_params(name=None))
        assert params == {"output": ["hostid"], "limit": 100}


class TestAsIntFlag:
    def test_true_becomes_one(self) -> None:
        assert as_int_flag(True) == 1

    def test_false_becomes_zero(self) -> None:
        """An explicit False must become 0, not be dropped -- the caller asked
        for 'not only true', which is different from omitting the filter."""
        assert as_int_flag(False) == 0

    def test_none_stays_none(self) -> None:
        assert as_int_flag(None) is None

    def test_false_survives_compact(self) -> None:
        """The point of as_int_flag: 0 is falsy but must not be dropped."""
        assert compact({"only_true": as_int_flag(False)}) == {"only_true": 0}

    def test_none_is_dropped_by_compact(self) -> None:
        assert compact({"only_true": as_int_flag(None)}) == {}
