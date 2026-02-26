import json

from mcp.server.fastmcp import FastMCP

from flower_mcp.client import flower_request

mcp = FastMCP("Flower")


def _format(result: dict | list | str) -> str:
    if isinstance(result, str):
        return result
    return json.dumps(result, indent=2)


# --- Read-only tools ---


@mcp.tool()
async def list_workers(refresh: bool = False, status: bool = False) -> str:
    """List all Celery workers and their info.

    Args:
        refresh: Refresh worker stats before returning.
        status: Include worker status (active/offline).
    """
    params = {}
    if refresh:
        params["refresh"] = "true"
    if status:
        params["status"] = "true"
    return _format(await flower_request("GET", "/api/workers", params=params))


@mcp.tool()
async def list_tasks(
    state: str | None = None,
    worker: str | None = None,
    taskname: str | None = None,
    limit: int = 100,
    sort_by: str | None = None,
) -> str:
    """List Celery tasks with optional filtering and sorting.

    Returns up to `limit` tasks (default 100) to avoid flooding context.

    Args:
        state: Filter by task state (e.g. SUCCESS, FAILURE, PENDING, STARTED, REVOKED).
        worker: Filter by worker name.
        taskname: Filter by task type name.
        limit: Maximum number of tasks to return (default 100).
        sort_by: Sort field name.
    """
    params: dict = {"limit": limit}
    if state:
        params["state"] = state
    if worker:
        params["workername"] = worker
    if taskname:
        params["taskname"] = taskname
    if sort_by:
        params["sort_by"] = sort_by
    return _format(await flower_request("GET", "/api/tasks", params=params))


@mcp.tool()
async def get_task_info(task_id: str) -> str:
    """Get detailed information about a specific task.

    Args:
        task_id: The task UUID.
    """
    return _format(await flower_request("GET", f"/api/task/info/{task_id}"))


@mcp.tool()
async def get_task_result(task_id: str) -> str:
    """Get the result of a completed task.

    Args:
        task_id: The task UUID.
    """
    return _format(await flower_request("GET", f"/api/task/result/{task_id}"))


@mcp.tool()
async def get_task_types() -> str:
    """List all registered task type names across all workers."""
    return _format(await flower_request("GET", "/api/task/types"))


@mcp.tool()
async def get_queue_lengths() -> str:
    """Get the current length of all active queues."""
    return _format(await flower_request("GET", "/api/queues/length"))


# --- Action tools ---


@mcp.tool()
async def apply_task(
    task_name: str, args: list | None = None, kwargs: dict | None = None
) -> str:
    """Execute a task synchronously and wait for the result.

    WARNING: This blocks until the task completes. For long-running tasks,
    use async_apply_task instead.

    Args:
        task_name: Fully qualified task name (e.g. 'myapp.tasks.add').
        args: Positional arguments for the task.
        kwargs: Keyword arguments for the task.
    """
    body: dict = {}
    if args:
        body["args"] = args
    if kwargs:
        body["kwargs"] = kwargs
    return _format(await flower_request("POST", f"/api/task/apply/{task_name}", json=body))


@mcp.tool()
async def async_apply_task(
    task_name: str, args: list | None = None, kwargs: dict | None = None
) -> str:
    """Submit a task for asynchronous execution. Returns immediately with a task ID.

    Args:
        task_name: Fully qualified task name (e.g. 'myapp.tasks.add').
        args: Positional arguments for the task.
        kwargs: Keyword arguments for the task.
    """
    body: dict = {}
    if args:
        body["args"] = args
    if kwargs:
        body["kwargs"] = kwargs
    return _format(
        await flower_request("POST", f"/api/task/async-apply/{task_name}", json=body)
    )


@mcp.tool()
async def abort_task(task_id: str) -> str:
    """Abort a currently executing task.

    Args:
        task_id: The task UUID to abort.
    """
    return _format(await flower_request("POST", f"/api/task/abort/{task_id}"))


@mcp.tool()
async def revoke_task(task_id: str, terminate: bool = False) -> str:
    """Revoke a pending or active task.

    WARNING: With terminate=True, this sends SIGTERM to the worker process
    executing the task. Only use terminate=True if the task is stuck and you
    understand the consequences.

    Args:
        task_id: The task UUID to revoke.
        terminate: If True, terminate the worker process running the task.
    """
    return _format(
        await flower_request(
            "POST", f"/api/task/revoke/{task_id}", json={"terminate": terminate}
        )
    )


@mcp.tool()
async def shutdown_worker(worker_name: str) -> str:
    """Shut down a Celery worker.

    WARNING: This will stop the worker process. The worker will not restart
    automatically unless managed by a process supervisor. Use with caution
    in production.

    Args:
        worker_name: The worker hostname to shut down.
    """
    return _format(
        await flower_request("POST", f"/api/worker/shutdown/{worker_name}")
    )


@mcp.tool()
async def pool_grow(worker_name: str, n: int = 1) -> str:
    """Grow the worker's execution pool by n processes.

    Args:
        worker_name: The worker hostname.
        n: Number of processes to add (default 1).
    """
    return _format(
        await flower_request(
            "POST", f"/api/worker/pool/grow/{worker_name}", json={"n": n}
        )
    )


@mcp.tool()
async def pool_shrink(worker_name: str, n: int = 1) -> str:
    """Shrink the worker's execution pool by n processes.

    Args:
        worker_name: The worker hostname.
        n: Number of processes to remove (default 1).
    """
    return _format(
        await flower_request(
            "POST", f"/api/worker/pool/shrink/{worker_name}", json={"n": n}
        )
    )


@mcp.tool()
async def pool_restart(worker_name: str) -> str:
    """Restart the worker's execution pool.

    WARNING: This will restart all pool processes. In-flight tasks may be affected.

    Args:
        worker_name: The worker hostname.
    """
    return _format(
        await flower_request("POST", f"/api/worker/pool/restart/{worker_name}")
    )


@mcp.tool()
async def pool_autoscale(worker_name: str, min_processes: int, max_processes: int) -> str:
    """Configure autoscaling for the worker's execution pool.

    Args:
        worker_name: The worker hostname.
        min_processes: Minimum number of pool processes.
        max_processes: Maximum number of pool processes.
    """
    return _format(
        await flower_request(
            "POST",
            f"/api/worker/pool/autoscale/{worker_name}",
            json={"min": min_processes, "max": max_processes},
        )
    )


@mcp.tool()
async def add_consumer(worker_name: str, queue: str) -> str:
    """Add a queue consumer to a worker.

    Args:
        worker_name: The worker hostname.
        queue: The queue name to start consuming from.
    """
    return _format(
        await flower_request(
            "POST",
            f"/api/worker/queue/add-consumer/{worker_name}",
            json={"queue": queue},
        )
    )


@mcp.tool()
async def cancel_consumer(worker_name: str, queue: str) -> str:
    """Cancel a queue consumer from a worker.

    Args:
        worker_name: The worker hostname.
        queue: The queue name to stop consuming from.
    """
    return _format(
        await flower_request(
            "POST",
            f"/api/worker/queue/cancel-consumer/{worker_name}",
            json={"queue": queue},
        )
    )


@mcp.tool()
async def rate_limit_task(task_name: str, rate: str) -> str:
    """Set a rate limit for a task type.

    Args:
        task_name: Fully qualified task name.
        rate: Rate limit string (e.g. '10/m' for 10 per minute, '100/h' for 100 per hour).
    """
    return _format(
        await flower_request(
            "POST", f"/api/task/rate-limit/{task_name}", json={"rate": rate}
        )
    )


@mcp.tool()
async def set_task_timeout(
    task_name: str, soft: float | None = None, hard: float | None = None
) -> str:
    """Set soft and/or hard time limits for a task type.

    Args:
        task_name: Fully qualified task name.
        soft: Soft time limit in seconds (raises SoftTimeLimitExceeded).
        hard: Hard time limit in seconds (kills the task).
    """
    body: dict = {}
    if soft is not None:
        body["soft"] = soft
    if hard is not None:
        body["hard"] = hard
    return _format(
        await flower_request("POST", f"/api/task/timeout/{task_name}", json=body)
    )


def main():
    mcp.run()
