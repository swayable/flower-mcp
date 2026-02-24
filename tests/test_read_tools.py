import json

import httpx
import respx

from flower_mcp.server import (
    get_queue_lengths,
    get_task_info,
    get_task_result,
    get_task_types,
    list_tasks,
    list_workers,
)

BASE = "http://flower-test:5555"


class TestListWorkers:
    @respx.mock
    async def test_returns_workers(self):
        data = {"worker1@host": {"active": 2, "processed": 100}}
        respx.get(f"{BASE}/api/workers").mock(
            return_value=httpx.Response(200, json=data)
        )
        result = json.loads(await list_workers())
        assert "worker1@host" in result

    @respx.mock
    async def test_refresh_param(self):
        route = respx.get(f"{BASE}/api/workers").mock(
            return_value=httpx.Response(200, json={})
        )
        await list_workers(refresh=True)
        assert "refresh=true" in str(route.calls[0].request.url)

    @respx.mock
    async def test_status_param(self):
        route = respx.get(f"{BASE}/api/workers").mock(
            return_value=httpx.Response(200, json={})
        )
        await list_workers(status=True)
        assert "status=true" in str(route.calls[0].request.url)


class TestListTasks:
    @respx.mock
    async def test_returns_tasks(self):
        data = {"task-id-1": {"state": "SUCCESS"}}
        respx.get(f"{BASE}/api/tasks").mock(
            return_value=httpx.Response(200, json=data)
        )
        result = json.loads(await list_tasks())
        assert "task-id-1" in result

    @respx.mock
    async def test_default_limit(self):
        route = respx.get(f"{BASE}/api/tasks").mock(
            return_value=httpx.Response(200, json={})
        )
        await list_tasks()
        assert "limit=100" in str(route.calls[0].request.url)

    @respx.mock
    async def test_filter_params(self):
        route = respx.get(f"{BASE}/api/tasks").mock(
            return_value=httpx.Response(200, json={})
        )
        await list_tasks(state="FAILURE", worker="w1", taskname="myapp.add", sort_by="name")
        url = str(route.calls[0].request.url)
        assert "state=FAILURE" in url
        assert "workername=w1" in url
        assert "taskname=myapp.add" in url
        assert "sort_by=name" in url


class TestGetTaskInfo:
    @respx.mock
    async def test_returns_task_info(self):
        data = {"task-id": "abc", "state": "SUCCESS", "result": 42}
        respx.get(f"{BASE}/api/task/info/abc").mock(
            return_value=httpx.Response(200, json=data)
        )
        result = json.loads(await get_task_info("abc"))
        assert result["state"] == "SUCCESS"

    @respx.mock
    async def test_not_found(self):
        respx.get(f"{BASE}/api/task/info/missing").mock(
            return_value=httpx.Response(404, text="Not Found")
        )
        result = await get_task_info("missing")
        assert "404" in result


class TestGetTaskResult:
    @respx.mock
    async def test_returns_result(self):
        data = {"result": 42, "state": "SUCCESS"}
        respx.get(f"{BASE}/api/task/result/abc").mock(
            return_value=httpx.Response(200, json=data)
        )
        result = json.loads(await get_task_result("abc"))
        assert result["result"] == 42


class TestGetTaskTypes:
    @respx.mock
    async def test_returns_types(self):
        data = {"worker1": ["myapp.tasks.add", "myapp.tasks.multiply"]}
        respx.get(f"{BASE}/api/task/types").mock(
            return_value=httpx.Response(200, json=data)
        )
        result = json.loads(await get_task_types())
        assert "myapp.tasks.add" in result["worker1"]


class TestGetQueueLengths:
    @respx.mock
    async def test_returns_lengths(self):
        data = {"active_queues": [{"name": "celery", "messages": 5}]}
        respx.get(f"{BASE}/api/queues/length").mock(
            return_value=httpx.Response(200, json=data)
        )
        result = json.loads(await get_queue_lengths())
        assert result["active_queues"][0]["messages"] == 5
