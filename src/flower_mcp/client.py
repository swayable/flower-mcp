import logging
import os

import httpx

logger = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        base_url = os.environ.get("FLOWER_URL", "http://localhost:5555")
        auth = None
        auth_str = os.environ.get("FLOWER_AUTH")
        if auth_str:
            if ":" not in auth_str:
                logger.warning(
                    "FLOWER_AUTH is set but missing ':' separator "
                    "(expected 'user:password') — requests will be unauthenticated"
                )
            else:
                username, password = auth_str.split(":", 1)
                auth = httpx.BasicAuth(username, password)
        _client = httpx.AsyncClient(base_url=base_url, auth=auth, timeout=30.0)
    return _client


def reset_client() -> None:
    global _client
    _client = None


async def flower_request(method: str, path: str, **kwargs) -> dict | list | str:
    try:
        client = get_client()
        response = await client.request(method, path, **kwargs)
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            return response.text
    except httpx.HTTPStatusError as e:
        return f"HTTP {e.response.status_code}: {e.response.text}"
    except httpx.ConnectError:
        return f"Connection error: could not connect to Flower at {get_client().base_url}"
    except httpx.TimeoutException:
        return "Timeout: request to Flower timed out"
    except Exception as e:
        return f"Error: {e}"
