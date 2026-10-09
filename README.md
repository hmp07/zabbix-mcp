# zabbix-mcp

[![Tests](https://img.shields.io/badge/tests-1045%20passed-brightgreen)](#running-tests)
[![Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen)](#running-tests)
[![Methodology](https://img.shields.io/badge/methodology-TDD-blue)](#running-tests)
[![Security](https://img.shields.io/badge/security-hardened-blue)](#security)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

A complete [MCP](https://modelcontextprotocol.io/) server for **Zabbix 7.4**, enabling any MCP-compatible AI assistant to interact with your Zabbix infrastructure using natural language.

## Features

- **86 tools** covering the full Zabbix API surface
- One shared, reused HTTP session for the whole server (no per-call connections)
- Read-only, write, and destructive operations with explicit annotations
- Hosts, host groups, items, triggers, LLD rules, graphs, dashboards, templates, maintenances, macros and more
- 3 workflow tools for common multi-step operations
- Automatic retry with exponential backoff on network failures
- Credentials exclusively from environment variables, never in tool arguments or logs
- SSL verification configurable (for self-signed certificates)
- Read-only mode to restrict the server to monitoring operations only
- HTTP and SSE transports for remote or multi-client deployments

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- A Zabbix 7.4 instance with API access
- A Zabbix API token (*User settings > API tokens > Create token*)
- An MCP-compatible client (e.g. [Claude Desktop](https://claude.ai/download), [Cursor](https://www.cursor.com/), [Continue](https://www.continue.dev/))

## Installation

```bash
git clone https://github.com/Alysko/zabbix-mcp.git
cd zabbix-mcp
uv sync
```

## Configuration

### MCP client (stdio)

Add the following to your MCP client's configuration file:

```json
{
  "mcpServers": {
    "zabbix": {
      "command": "uv",
      "args": [
        "--directory", "/absolute/path/to/zabbix-mcp",
        "run", "zabbix-mcp"
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

### HTTP transport

To expose the server over HTTP (useful for remote clients, Cursor, Copilot, Gemini, etc.):

```bash
ZABBIX_URL=https://your-zabbix-instance/zabbix \
ZABBIX_API_TOKEN=<your-api-token> \
MCP_TRANSPORT=http \
MCP_PORT=8000 \
uv run zabbix-mcp
```

The server listens on `http://127.0.0.1:8000/mcp` by default.

To bind to all interfaces (e.g. for Docker or a remote host), set `MCP_HOST=0.0.0.0`. In that case, place the server behind a reverse proxy with authentication.

For SSE transport (legacy), use `MCP_TRANSPORT=sse`. The endpoint is then `/sse`.

Client configuration example for HTTP:

```json
{
  "mcpServers": {
    "zabbix": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

### Read-only mode

Set `ZABBIX_READ_ONLY=true` to start the server with only read-only tools exposed. All write and delete tools are removed at startup. This is useful for monitoring-only deployments where write access would be undesirable.

```json
{
  "mcpServers": {
    "zabbix": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/zabbix-mcp", "run", "zabbix-mcp"],
      "env": {
        "ZABBIX_URL": "https://your-zabbix-instance/zabbix",
        "ZABBIX_API_TOKEN": "<your-api-token>",
        "ZABBIX_READ_ONLY": "true"
      }
    }
  }
}
```

In read-only mode, 60 write/delete tools are removed, leaving 26 read-only tools.

### Environment variables

#### Zabbix connection

| Variable | Required | Description |
|---|---|---|
| `ZABBIX_URL` | yes | Zabbix frontend URL (e.g. `https://zabbix.example.com/zabbix`) |
| `ZABBIX_API_TOKEN` | yes* | API token (preferred) |
| `ZABBIX_USER` | yes* | Username (alternative to token) |
| `ZABBIX_PASSWORD` | yes* | Password (alternative to token) |
| `ZABBIX_VERIFY_SSL` | no | Set to `false` to disable SSL verification. Default: `true` |
| `ZABBIX_TIMEOUT` | no | API request timeout in seconds. Default: `30` |
| `ZABBIX_READ_ONLY` | no | Set to `true` to expose only read-only tools. Default: `false` |

*Either `ZABBIX_API_TOKEN` or `ZABBIX_USER` + `ZABBIX_PASSWORD` is required.

#### Transport

| Variable | Default | Description |
|---|---|---|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio`, `http`, or `sse` |
| `MCP_HOST` | `127.0.0.1` | Bind address for http/sse transport |
| `MCP_PORT` | `8000` | Listen port for http/sse transport |

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
| Hosts & groups | `zabbix_host_*`, `zabbix_hostgroup_*`, `zabbix_host_interface_*` |
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

All tools follow the `zabbix_<resource>_<action>` naming convention and declare annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`) so the client can make informed decisions about safety.

### Result limits and pagination

Read tools accept a `limit` parameter (default 100, max 1000) and do **not** paginate. A
query that matches more records than `limit` is silently truncated -- the response carries no
total count, so the caller cannot tell a complete result from a clipped one.

When working on large instances, raise `limit` deliberately and narrow the filter (for example
by `hostids` or `groupids`) rather than assuming the default returned everything.

## Connection handling

All tools share a single HTTP session for the life of the server process. It is opened on the
first tool call and closed when the server shuts down, so repeated calls reuse one
authenticated connection instead of opening a new one each time. Outbound connections are
capped at 20; concurrent calls beyond that queue rather than exhausting sockets.

A network failure evicts the shared session so the next attempt reconnects cleanly.

## Running tests

```bash
uv sync
uv run pytest --cov=zabbix_mcp -q
```

Coverage: **96%** -- 1045 tests.

## Architecture

```
zabbix_mcp/
├── app.py              # MCP application instance + shared-session lifespan
├── server.py           # Entry point, transport selection, read-only mode
├── client.py           # Zabbix API wrapper (auth, retry, shared session)
├── auth.py             # Credential and transport config from env vars
├── errors.py           # Typed errors with actionable messages
└── tools/
    ├── _annotations.py # Shared annotation dicts (READ_ONLY, WRITE, DELETE)
    ├── _params.py      # Zabbix param assembly helpers (None-drop, filter/search)
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
- No generic passthrough (`zabbix_raw_call`) -- all tools are endpoint-aligned
- SSL verification enabled by default
- HTTP transport warns at startup when bound to `0.0.0.0`

## Zabbix API compatibility

Targets **Zabbix 7.4**. Uses JSON-RPC 2.0 via [`zabbix-utils`](https://github.com/zabbix/python-zabbix-utils).

The deprecated `host.massupdate`, `host.massadd`, and `host.massremove` methods are intentionally not implemented (scheduled for removal in a future Zabbix version).

## License

MIT
