"""Helpers for assembling Zabbix API parameter dicts.

Every tool builds a params dict and calls ``client.call("resource.action", params)``.
Two rules hold across the whole tool layer:

1. Zabbix treats an absent parameter and an explicit ``None`` differently -- ``None``
   is rejected by most endpoints, so ``None`` values must be dropped entirely.
2. ``filter`` / ``search`` are nested dicts, and must be omitted (not sent as ``{}``)
   when no member is set.

These helpers encode both rules in one place so tool bodies stay declarative.
"""

from __future__ import annotations

from typing import Any


def compact(values: dict[str, Any]) -> dict[str, Any]:
    """Drop keys whose value is ``None``.

    Use for the flat top-level params of a ``.get`` call. Keys mapped to
    ``False`` or ``0`` are kept -- only ``None`` is dropped.
    """
    return {k: v for k, v in values.items() if v is not None}


def filter_params(**fields: Any) -> dict[str, dict[str, Any]]:
    """Build a ``{"filter": {...}}`` entry, or ``{}`` when no field is set.

    Pass a single value for Zabbix's exact-match ``filter``, e.g.::

        params.update(filter_params(status=status))
    """
    kept = compact(fields)
    return {"filter": kept} if kept else {}


def search_params(**fields: Any) -> dict[str, dict[str, str]]:
    """Build a ``{"search": {...}}`` entry, or ``{}`` when no field is set.

    Zabbix's ``search`` performs substring matching on string fields, so
    members are grouped into a single ``search`` dict.
    """
    kept = compact(fields)
    return {"search": kept} if kept else {}


def as_int_flag(value: bool | None) -> int | None:
    """Convert a tri-state boolean to Zabbix's ``1``/``0`` convention.

    ``True`` -> ``1``, ``False`` -> ``0``, ``None`` -> ``None`` (dropped).
    Used for parameters such as ``real_hosts`` and ``only_true`` where the
    caller must be able to send an explicit zero, not just omit the key.
    """
    if value is None:
        return None
    return 1 if value else 0
