"""Base Pydantic models shared across all Zabbix MCP tools.

Tool-specific input/output models are defined in each tools/*.py module.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ZabbixBaseModel(BaseModel):
    """Base model for all Zabbix MCP inputs and outputs.

    Strict by default: extra fields are forbidden, strings are stripped.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ZabbixObject(BaseModel):
    """Permissive model for raw Zabbix API response objects.

    Used when returning arbitrary Zabbix objects whose schema varies by context.
    Extra fields are allowed to accommodate Zabbix's flexible output parameter.
    """

    model_config = ConfigDict(extra="allow")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard pagination envelope returned by list/search tools."""

    items: list[T]
    total: int | None = None
    has_more: bool = False
    next_offset: int | None = None


class DeleteResponse(BaseModel):
    """Standard response for destructive operations."""

    deleted_ids: list[str]
    count: int


class ErrorDetail(BaseModel):
    """Structured error detail for actionable MCP error responses."""

    error: str
    code: int | None = None
    suggestion: str | None = None
