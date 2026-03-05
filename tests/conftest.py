import os

import pytest

from flower_mcp.client import reset_client


@pytest.fixture(autouse=True)
def _flower_env(monkeypatch):
    monkeypatch.setenv("FLOWER_URL", "http://flower-test:5555")
    monkeypatch.delenv("FLOWER_AUTH", raising=False)
    reset_client()
    yield
    reset_client()
