import json

import httpx
import respx

from flower_mcp.server import (
    abort_task,
    add_consumer,
    apply_task,
    async_apply_task,
    cancel_consumer,
    pool_autoscale,
    pool_grow,
    pool_restart,
    pool_shrink,
    rate_limit_task,
    revoke_task,
    set_task_timeout,
    shutdown_worker,
)

BASE = "http://flower-test:5555"


class TestApplyTask:
    @respx.mock
    async def test_apply_with_args(self):
        route = respx.post(f"{BASE}/api/task/apply/myapp.add").mock(
            return_value=httpx.Response(200, json={"ok": True, "task-id": "t1"})
        )
        result = json.loads(await apply_task("myapp.add", args=[1, 2]))
        assert result["ok"] is True
        body = json.loads(route.calls[0].request.content)
        assert body["args"] == [1, 2]

    @respx.mock
    async def test_apply_with_kwargs(self):
        route = respx.post(f"{BASE}/api/task/apply/myapp.add").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        await apply_task("myapp.add", kwargs={"x": 1})
        body = json.loads(route.calls[0].request.content)
        assert body["kwargs"] == {"x": 1}

    @respx.mock
    async def test_apply_no_args(self):
        route = respx.post(f"{BASE}/api/task/apply/myapp.ping").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        await apply_task("myapp.ping")
        body = json.loads(route.calls[0].request.content)
        assert body == {}


class TestAsyncApplyTask:
    @respx.mock
    async def test_async_apply(self):
        respx.post(f"{BASE}/api/task/async-apply/myapp.add").mock(
            return_value=httpx.Response(200, json={"task-id": "t1", "state": "PENDING"})
        )
        result = json.loads(await async_apply_task("myapp.add", args=[1, 2]))
        assert result["task-id"] == "t1"


class TestAbortTask:
    @respx.mock
    async def test_abort(self):
        respx.post(f"{BASE}/api/task/abort/t1").mock(
            return_value=httpx.Response(200, json={"message": "ok"})
        )
        result = json.loads(await abort_task("t1"))
        assert result["message"] == "ok"


class TestRevokeTask:
    @respx.mock
    async def test_revoke_default(self):
        route = respx.post(f"{BASE}/api/task/revoke/t1").mock(
            return_value=httpx.Response(200, json={"message": "ok"})
        )
        await revoke_task("t1")
        body = json.loads(route.calls[0].request.content)
        assert body["terminate"] is False

    @respx.mock
    async def test_revoke_with_terminate(self):
        route = respx.post(f"{BASE}/api/task/revoke/t1").mock(
            return_value=httpx.Response(200, json={"message": "ok"})
        )
        await revoke_task("t1", terminate=True)
        body = json.loads(route.calls[0].request.content)
        assert body["terminate"] is True


class TestShutdownWorker:
    @respx.mock
    async def test_shutdown(self):
        respx.post(f"{BASE}/api/worker/shutdown/worker1").mock(
            return_value=httpx.Response(200, json={"message": "ok"})
        )
        result = json.loads(await shutdown_worker("worker1"))
        assert result["message"] == "ok"


class TestPoolGrow:
    @respx.mock
    async def test_grow_default(self):
        route = respx.post(f"{BASE}/api/worker/pool/grow/worker1").mock(
            return_value=httpx.Response(200, json={"message": "ok"})
        )
        await pool_grow("worker1")
        body = json.loads(route.calls[0].request.content)
        assert body["n"] == 1

    @respx.mock
    async def test_grow_by_n(self):
        route = respx.post(f"{BASE}/api/worker/pool/grow/worker1").mock(
            return_value=httpx.Response(200, json={"message": "ok"})
        )
        await pool_grow("worker1", n=5)
        body = json.loads(route.calls[0].request.content)
        assert body["n"] == 5


class TestPoolShrink:
    @respx.mock
    async def test_shrink(self):
        route = respx.post(f"{BASE}/api/worker/pool/shrink/worker1").mock(
            return_value=httpx.Response(200, json={"message": "ok"})
        )
        await pool_shrink("worker1", n=2)
        body = json.loads(route.calls[0].request.content)
        assert body["n"] == 2


class TestPoolRestart:
    @respx.mock
    async def test_restart(self):
        respx.post(f"{BASE}/api/worker/pool/restart/worker1").mock(
            return_value=httpx.Response(200, json={"message": "ok"})
        )
        result = json.loads(await pool_restart("worker1"))
        assert result["message"] == "ok"


class TestPoolAutoscale:
    @respx.mock
    async def test_autoscale(self):
        route = respx.post(f"{BASE}/api/worker/pool/autoscale/worker1").mock(
            return_value=httpx.Response(200, json={"message": "ok"})
        )
        await pool_autoscale("worker1", min=2, max=10)
        body = json.loads(route.calls[0].request.content)
        assert body["min"] == 2
        assert body["max"] == 10


class TestAddConsumer:
    @respx.mock
    async def test_add(self):
        route = respx.post(f"{BASE}/api/worker/queue/add-consumer/worker1").mock(
            return_value=httpx.Response(200, json={"message": "ok"})
        )
        await add_consumer("worker1", queue="priority")
        body = json.loads(route.calls[0].request.content)
        assert body["queue"] == "priority"


class TestCancelConsumer:
    @respx.mock
    async def test_cancel(self):
        route = respx.post(f"{BASE}/api/worker/queue/cancel-consumer/worker1").mock(
            return_value=httpx.Response(200, json={"message": "ok"})
        )
        await cancel_consumer("worker1", queue="priority")
        body = json.loads(route.calls[0].request.content)
        assert body["queue"] == "priority"


class TestRateLimitTask:
    @respx.mock
    async def test_rate_limit(self):
        route = respx.post(f"{BASE}/api/task/rate-limit/myapp.add").mock(
            return_value=httpx.Response(200, json={"message": "ok"})
        )
        await rate_limit_task("myapp.add", rate="10/m")
        body = json.loads(route.calls[0].request.content)
        assert body["rate"] == "10/m"


class TestSetTaskTimeout:
    @respx.mock
    async def test_soft_and_hard(self):
        route = respx.post(f"{BASE}/api/task/timeout/myapp.add").mock(
            return_value=httpx.Response(200, json={"message": "ok"})
        )
        await set_task_timeout("myapp.add", soft=30.0, hard=60.0)
        body = json.loads(route.calls[0].request.content)
        assert body["soft"] == 30.0
        assert body["hard"] == 60.0

    @respx.mock
    async def test_soft_only(self):
        route = respx.post(f"{BASE}/api/task/timeout/myapp.add").mock(
            return_value=httpx.Response(200, json={"message": "ok"})
        )
        await set_task_timeout("myapp.add", soft=30.0)
        body = json.loads(route.calls[0].request.content)
        assert body == {"soft": 30.0}

    @respx.mock
    async def test_hard_only(self):
        route = respx.post(f"{BASE}/api/task/timeout/myapp.add").mock(
            return_value=httpx.Response(200, json={"message": "ok"})
        )
        await set_task_timeout("myapp.add", hard=60.0)
        body = json.loads(route.calls[0].request.content)
        assert body == {"hard": 60.0}
