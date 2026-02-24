import json

import httpx
import pytest
import respx

from flower_mcp.client import flower_request, get_client, reset_client


class TestGetClient:
    def test_default_base_url(self, monkeypatch):
        monkeypatch.setenv("FLOWER_URL", "http://custom:1234")
        reset_client()
        client = get_client()
        assert str(client.base_url) == "http://custom:1234"

    def test_auth_from_env(self, monkeypatch):
        monkeypatch.setenv("FLOWER_AUTH", "admin:secret")
        reset_client()
        client = get_client()
        assert client.auth is not None

    def test_no_auth_by_default(self):
        client = get_client()
        assert client.auth is None

    def test_singleton(self):
        assert get_client() is get_client()

    def test_reset_creates_new_client(self):
        first = get_client()
        reset_client()
        second = get_client()
        assert first is not second


class TestFlowerRequest:
    @respx.mock
    async def test_success_json(self):
        respx.get("http://flower-test:5555/api/workers").mock(
            return_value=httpx.Response(200, json={"worker1": {}})
        )
        result = await flower_request("GET", "/api/workers")
        assert result == {"worker1": {}}

    @respx.mock
    async def test_success_post(self):
        respx.post("http://flower-test:5555/api/task/abort/abc123").mock(
            return_value=httpx.Response(200, json={"message": "ok"})
        )
        result = await flower_request("POST", "/api/task/abort/abc123")
        assert result == {"message": "ok"}

    @respx.mock
    async def test_http_error(self):
        respx.get("http://flower-test:5555/api/workers").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        result = await flower_request("GET", "/api/workers")
        assert "HTTP 500" in result
        assert "Internal Server Error" in result

    @respx.mock
    async def test_connection_error(self):
        respx.get("http://flower-test:5555/api/workers").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        result = await flower_request("GET", "/api/workers")
        assert "Connection error" in result

    @respx.mock
    async def test_timeout(self):
        respx.get("http://flower-test:5555/api/workers").mock(
            side_effect=httpx.ReadTimeout("timed out")
        )
        result = await flower_request("GET", "/api/workers")
        assert "Timeout" in result

    @respx.mock
    async def test_non_json_response(self):
        respx.get("http://flower-test:5555/api/workers").mock(
            return_value=httpx.Response(200, text="OK")
        )
        result = await flower_request("GET", "/api/workers")
        assert result == "OK"

    @respx.mock
    async def test_passes_query_params(self):
        route = respx.get("http://flower-test:5555/api/tasks").mock(
            return_value=httpx.Response(200, json={})
        )
        await flower_request("GET", "/api/tasks", params={"limit": 10})
        assert route.called
        assert "limit=10" in str(route.calls[0].request.url)

    @respx.mock
    async def test_passes_json_body(self):
        route = respx.post("http://flower-test:5555/api/task/apply/add").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        await flower_request("POST", "/api/task/apply/add", json={"args": [1, 2]})
        assert route.called
        assert json.loads(route.calls[0].request.content) == {"args": [1, 2]}
