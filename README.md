# zabbix-mcp

[![Tests](https://img.shields.io/badge/tests-1017%20passed-brightgreen)](#running-tests)
[![Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen)](#running-tests)
[![Methodology](https://img.shields.io/badge/methodology-TDD-blue)](#running-tests)
[![Security](https://img.shields.io/badge/security-hardened-blue)](#security)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

A complete [MCP](https://modelcontextprotocol.io/) server for **Zabbix 7.4**, enabling any MCP-compatible AI assistant to interact with your Zabbix infrastructure using natural language.

## Features

- **86 tools** covering the full Zabbix API surface
- Read-only, write, and destructive operations with explicit annotations
- Hosts, host groups, items, triggers, LLD rules, graphs, dashboards, templates, maintenances, macros, monitoring, and more
- 3 workflow tools for common multi-step operations
- Automatic retry with exponential backoff on network failures
- Credentials exclusively from environment variables — never in tool arguments or logs
- SSL verification configurable (for self-signed certificates)

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- A Zabbix 7.4 instance with API access
- A Zabbix API token (*User settings → API tokens → Create token*)
- An MCP-compatible client (e.g. [Claude Desktop](https://claude.ai/download), [Cursor](https://www.cursor.com/), [Continue](https://www.continue.dev/))

## Installation

```bash
git clone https://github.com/Alysko/zabbix-mcp.git
cd zabbix-mcp
uv sync
```

## Configuration

### MCP client

Add the following to your MCP client's configuration file (exact path varies by client):

```json
{
  "mcpServers": {
    "zabbix": {
      "command": "uv",
      "args": [
        "--directory", "/absolute/path/to/zabbix-mcp",
        "run", "python", "-m", "zabbix_mcp.server"
      ],
      "env": {
        "ZABBIX_URL": "https://your-zabbix-instance/zabbix",
        "ZABBIX_API_TOKEN": "<your-api-token>"
      }
    }
  }
}
```

Restart your MCP client after saving the configuration.

### Environment variables

| Variable | Required | Description |
|---|---|---|
| `ZABBIX_URL` | Yes | Zabbix frontend URL (e.g. `https://zabbix.example.com/zabbix`) |
| `ZABBIX_API_TOKEN` | Yes* | API token (preferred) |
| `ZABBIX_USER` | Yes* | Username (alternative to token) |
| `ZABBIX_PASSWORD` | Yes* | Password (alternative to token) |
| `ZABBIX_VERIFY_SSL` | No | Set to `false` to disable SSL verification (self-signed certs). Default: `true` |
| `ZABBIX_TIMEOUT` | No | API request timeout in seconds. Default: `30` |

*Either `ZABBIX_API_TOKEN` or `ZABBIX_USER` + `ZABBIX_PASSWORD` is required.

## Usage examples

Once configured, interact with your Zabbix infrastructure naturally:

> "What hosts are currently in problem state?"

> "Create a maintenance window for web-01 tonight from 10pm to 11pm"

> "Show me all triggers with severity >= High on the Linux Servers group"

> "List items on host db-primary where the key contains 'cpu'"

> "Acknowledge all active problems on host app-server with message 'investigating'"

## Tool coverage

| Domain | Tools |
|---|---|
| Hosts & Groups | `zabbix_host_*`, `zabbix_hostgroup_*`, `zabbix_host_interface_*` |
| Items | `zabbix_item_*` |
| Triggers | `zabbix_trigger_*` |
| LLD | `zabbix_lld_rule_*`, `zabbix_lld_*_prototype_*` |
| Graphs | `zabbix_graph_*`, `zabbix_graph_item_get` |
| Dashboards | `zabbix_dashboard_*`, `zabbix_template_dashboard_*` |
| Value maps | `zabbix_valuemap_*` |
| Monitoring | `zabbix_problem_get`, `zabbix_event_*`, `zabbix_history_get`, `zabbix_trend_get`, `zabbix_alert_get` |
| Templates | `zabbix_template_*`, `zabbix_templategroup_*` |
| Maintenances | `zabbix_maintenance_*` |
| Macros | `zabbix_usermacro_*` |
| Reports | `zabbix_report_*` |
| Workflow | `zabbix_host_problems_summary`, `zabbix_lld_scaffold`, `zabbix_template_link` |

All tools follow the naming convention `zabbix_<resource>_<action>` and declare annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`) so the AI assistant can make informed decisions about safety.

## Running tests

```bash
uv sync
uv run pytest --cov=zabbix_mcp -q
```

Coverage: **96%** — 1017 tests.

## Architecture

```
zabbix_mcp/
├── app.py          # MCP application instance (shared across all modules)
├── server.py       # Entry point, tool module imports, main()
├── client.py       # Zabbix API wrapper (auth, retry, pagination)
├── auth.py         # Credential management from env vars
├── models.py       # Pydantic models
├── errors.py       # Typed errors with actionable messages
└── tools/
    ├── host.py
    ├── hostgroup.py
    ├── item.py
    ├── trigger.py
    ├── lld.py
    ├── graph.py
    ├── dashboard.py
    ├── monitoring.py
    ├── template.py
    ├── maintenance.py
    ├── macro.py
    └── workflow.py
```

## Security

- Credentials are read exclusively from environment variables
- No credential values ever appear in logs or error messages
- Destructive tools (`_delete`) are annotated with `destructiveHint=True`
- No generic passthrough (`zabbix_raw_call`) — all tools are endpoint-aligned
- SSL verification enabled by default

## Zabbix API compatibility

Targets **Zabbix 7.4**. Uses JSON-RPC 2.0 via [`zabbix-utils`](https://github.com/zabbix/python-zabbix-utils).

The deprecated `host.massupdate`, `host.massadd`, and `host.massremove` methods are intentionally not implemented (removed in a future Zabbix version).

## License

MIT
