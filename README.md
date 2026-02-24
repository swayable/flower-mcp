# flower-mcp

MCP server for [Celery Flower](https://flower.readthedocs.io/) monitoring and management.

Exposes Flower's REST API as MCP tools, enabling Claude Code and other MCP clients to monitor and manage Celery workers and tasks conversationally.

## Installation

```bash
uvx flower-mcp
```

Or install with pip:

```bash
pip install flower-mcp
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `FLOWER_URL` | Base URL of the Flower instance | `http://localhost:5555` |
| `FLOWER_AUTH` | Basic auth credentials (`user:password`) | None |

### Claude Code

Add to your MCP settings (`.claude/settings.json`):

```json
{
  "mcpServers": {
    "flower": {
      "command": "uvx",
      "args": ["flower-mcp"],
      "env": {
        "FLOWER_URL": "http://localhost:5555"
      }
    }
  }
}
```

## Tools

### Read-only

| Tool | Description |
|------|-------------|
| `list_workers` | List all Celery workers and their info |
| `list_tasks` | List tasks with filtering by state, worker, task name (default limit: 100) |
| `get_task_info` | Get detailed information about a specific task |
| `get_task_result` | Get the result of a completed task |
| `get_task_types` | List all registered task type names |
| `get_queue_lengths` | Get current length of all active queues |

### Actions

| Tool | Description |
|------|-------------|
| `apply_task` | Execute a task synchronously (blocks until complete) |
| `async_apply_task` | Submit a task for async execution (returns task ID) |
| `abort_task` | Abort a currently executing task |
| `revoke_task` | Revoke a pending or active task (optional terminate) |
| `shutdown_worker` | Shut down a Celery worker |
| `pool_grow` | Grow a worker's execution pool |
| `pool_shrink` | Shrink a worker's execution pool |
| `pool_restart` | Restart a worker's execution pool |
| `pool_autoscale` | Configure pool autoscaling (min/max) |
| `add_consumer` | Add a queue consumer to a worker |
| `cancel_consumer` | Cancel a queue consumer from a worker |
| `rate_limit_task` | Set a rate limit for a task type |
| `set_task_timeout` | Set soft/hard time limits for a task type |

## Development

```bash
uv venv && source .venv/bin/activate
uv pip install -e . pytest pytest-asyncio respx
pytest
```

## License

MIT
