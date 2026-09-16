"""Zabbix MCP tools — Workflow (multi-step convenience tools)."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from ..client import ZabbixClient
from ..app import mcp
from ._annotations import DELETE, READ_ONLY, WRITE, WRITE_IDEMPOTENT


@mcp.tool(
    name="zabbix_host_problems_summary",
    description=(
        "Return a summary of active problems for one or more hosts, grouped by severity. "
        "Each entry includes the host name, host ID, and problem counts per severity level "
        "(disaster, high, average, warning, info, not_classified). "
        "Useful for a quick health overview without needing two separate tool calls."
    ),
    annotations=READ_ONLY,
)
async def zabbix_host_problems_summary(
    hostids: Annotated[list[str] | None, Field(description="Summarise problems for these host IDs. Omit to summarise all hosts with active problems.")] = None,
    groupids: Annotated[list[str] | None, Field(description="Restrict to hosts in these group IDs.")] = None,
    min_severity: Annotated[int, Field(description="Minimum severity to include: 0=not classified, 1=info, 2=warning, 3=average, 4=high, 5=disaster.", ge=0, le=5)] = 0,
) -> list[dict[str, Any]]:
    """Summarise active problems per host, grouped by severity."""
    async with ZabbixClient() as client:
        # 1. Resolve hosts
        host_params: dict[str, Any] = {
            "output": ["hostid", "host", "name"],
            "limit": 1000,
        }
        if hostids is not None:
            host_params["hostids"] = hostids
        if groupids is not None:
            host_params["groupids"] = groupids
        hosts = await client.call("host.get", host_params)

        if not hosts:
            return []

        resolved_hostids = [h["hostid"] for h in hosts]
        hosts_by_id = {h["hostid"]: h for h in hosts}

        # 2. Fetch active problems for those hosts
        problem_params: dict[str, Any] = {
            "output": ["eventid", "objectid", "name", "severity"],
            "hostids": resolved_hostids,
            "limit": 10000,
        }
        if min_severity > 0:
            problem_params["severities"] = list(range(min_severity, 6))
        problems = await client.call("problem.get", problem_params)

        # 3. Fetch trigger->host mapping to associate problems with hosts
        trigger_ids = list({p["objectid"] for p in problems})
        host_by_trigger: dict[str, str] = {}
        if trigger_ids:
            trigger_params: dict[str, Any] = {
                "output": ["triggerid"],
                "selectHosts": ["hostid"],
                "triggerids": trigger_ids,
            }
            triggers = await client.call("trigger.get", trigger_params)
            for t in triggers:
                for h in t.get("hosts", []):
                    host_by_trigger[t["triggerid"]] = h["hostid"]

        # 4. Aggregate per host
        severity_keys = ["not_classified", "info", "warning", "average", "high", "disaster"]
        counts: dict[str, dict[str, int]] = {
            hid: {k: 0 for k in severity_keys} for hid in resolved_hostids
        }
        for p in problems:
            hid = host_by_trigger.get(p["objectid"])
            if hid and hid in counts:
                sev = int(p["severity"])
                counts[hid][severity_keys[sev]] += 1

        # 5. Build result
        result = []
        for hid in resolved_hostids:
            host_counts = counts[hid]
            total = sum(host_counts.values())
            if total == 0 and hostids is None:
                continue
            host_info = hosts_by_id[hid]
            result.append({
                "hostid": hid,
                "host": host_info["host"],
                "name": host_info["name"],
                "problems": host_counts,
                "total": total,
            })

        result.sort(key=lambda x: -x["total"])
        return result


@mcp.tool(
    name="zabbix_lld_scaffold",
    description=(
        "Create a complete LLD (Low-Level Discovery) setup in a single call: "
        "one discovery rule + one item prototype + one trigger prototype. "
        "Returns the IDs of all created objects."
    ),
    annotations=WRITE,
)
async def zabbix_lld_scaffold(
    hostid: Annotated[str, Field(description="ID of the host to add the LLD setup to.")],
    rule_name: Annotated[str, Field(description="LLD rule name.")],
    rule_key: Annotated[str, Field(description="LLD rule key.")],
    item_name: Annotated[str, Field(description="Item prototype name. May contain LLD macros.")],
    item_key: Annotated[str, Field(description="Item prototype key. May contain LLD macros.")],
    trigger_description: Annotated[str, Field(description="Trigger prototype description. May contain LLD macros.")],
    trigger_expression: Annotated[str, Field(description="Trigger prototype expression referencing the item prototype key.")],
    rule_type: Annotated[int, Field(description="LLD rule type: 0=Zabbix agent, 7=active agent, etc.", ge=0, le=21)] = 0,
    rule_delay: Annotated[str, Field(description="LLD rule polling interval.")] = "1h",
    item_type: Annotated[int, Field(description="Item prototype type.", ge=0, le=21)] = 0,
    item_value_type: Annotated[int, Field(description="Item value type: 0=float, 1=char, 2=log, 3=unsigned int, 4=text.", ge=0, le=4)] = 3,
    item_delay: Annotated[str, Field(description="Item prototype polling interval.")] = "1m",
    item_units: Annotated[str | None, Field(description="Item units.")] = None,
    trigger_priority: Annotated[int, Field(description="Trigger severity: 0=not classified ... 5=disaster.", ge=0, le=5)] = 2,
) -> dict[str, Any]:
    """Create a complete LLD rule + item prototype + trigger prototype in one call."""
    async with ZabbixClient() as client:
        rule_params: dict[str, Any] = {
            "hostid": hostid,
            "name": rule_name,
            "key_": rule_key,
            "type": rule_type,
            "delay": rule_delay,
            "lifetime": "30d",
            "status": 0,
        }
        rule_result = await client.call("discoveryrule.create", rule_params)
        ruleid = rule_result["itemids"][0]

        item_params: dict[str, Any] = {
            "hostid": hostid,
            "ruleid": ruleid,
            "name": item_name,
            "key_": item_key,
            "type": item_type,
            "value_type": item_value_type,
            "delay": item_delay,
            "history": "7d",
            "trends": "365d",
        }
        if item_units is not None:
            item_params["units"] = item_units
        item_result = await client.call("itemprototype.create", item_params)
        item_prototype_id = item_result["itemids"][0]

        trigger_params: dict[str, Any] = {
            "description": trigger_description,
            "expression": trigger_expression,
            "ruleid": ruleid,
            "priority": trigger_priority,
            "status": 0,
        }
        trigger_result = await client.call("triggerprototype.create", trigger_params)
        trigger_prototype_id = trigger_result["triggerids"][0]

        return {
            "ruleid": ruleid,
            "item_prototypeid": item_prototype_id,
            "trigger_prototypeid": trigger_prototype_id,
        }


@mcp.tool(
    name="zabbix_template_link",
    description=(
        "Link one or more templates to one or more hosts. "
        "Merges the given templates with any templates already linked to each host "
        "(does not unlink existing templates). "
        "Returns the updated host IDs."
    ),
    annotations=WRITE_IDEMPOTENT,
)
async def zabbix_template_link(
    hostids: Annotated[list[str], Field(description="IDs of hosts to link templates to.")],
    templateids: Annotated[list[str], Field(description="IDs of templates to link.")],
) -> dict[str, Any]:
    """Link templates to hosts, preserving existing template links."""
    async with ZabbixClient() as client:
        host_params: dict[str, Any] = {
            "output": ["hostid"],
            "selectParentTemplates": ["templateid"],
            "hostids": hostids,
        }
        hosts = await client.call("host.get", host_params)

        updated_hostids = []
        for host in hosts:
            existing = {t["templateid"] for t in host.get("parentTemplates", [])}
            merged = list(existing | set(templateids))
            update_params: dict[str, Any] = {
                "hostid": host["hostid"],
                "templates": [{"templateid": tid} for tid in merged],
            }
            result = await client.call("host.update", update_params)
            updated_hostids.extend(result.get("hostids", []))

        return {"hostids": updated_hostids}
