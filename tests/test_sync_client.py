"""Tests for synchronous helpers and `SyncMondayClient` facade behaviors."""

from contextlib import nullcontext
from typing import Any

import pytest

from monday import run_sync, sync, to_sync
from monday.config import Config
from monday.sync_client import SyncMondayClient


class DummyAdapter:
    """Minimal test adapter that records calls and returns canned responses."""

    def __init__(self, responses: list[dict[str, Any]] | None = None) -> None:
        """Initialize the adapter with optional canned responses."""
        self._responses = responses or []
        self.calls: list[dict[str, Any]] = []

    async def post(
        self,
        *,
        url: str,
        json: dict[str, Any],
        headers: dict[str, str],
        timeout_seconds: int,
    ) -> tuple[dict[str, Any], dict[str, str]]:
        """Record the request and return a canned or default response and headers."""
        self.calls.append(
            {'url': url, 'json': json, 'headers': headers, 'timeout': timeout_seconds}
        )
        if self._responses:
            return self._responses.pop(0), {'x-test': '1'}
        # default: basic versions response or empty data shape
        if 'versions' in json.get('query', ''):
            return {
                'data': {
                    'versions': [
                        {
                            'kind': 'current',
                            'value': '2024-10',
                            'display_name': '2024-10',
                        }
                    ]
                }
            }, {}
        return {'data': {}}, {}


def make_client_with_dummy(config: Config | None = None) -> SyncMondayClient:
    """Create a `SyncMondayClient` with `DummyAdapter` injected for testing."""
    cfg = config or Config(api_key='token')
    client = SyncMondayClient(cfg)
    # Inject dummy adapter on the underlying async client
    client._async_client._adapter = DummyAdapter()  # type: ignore[attr-defined]
    return client


@pytest.mark.sync
def test_sync_factory_basic():
    """Create a `SyncMondayClient` via the `sync` convenience factory."""
    c = sync(api_key='token')
    assert isinstance(c, SyncMondayClient)
    c.close()


@pytest.mark.sync
def test_run_sync_one_off():
    """`run_sync` executes a coroutine and returns its result."""

    async def add(a: int, b: int) -> int:
        return a + b

    assert run_sync(add(2, 3)) == 5


@pytest.mark.sync
def test_to_sync_wrapper():
    """`to_sync` wraps an async function into a blocking callable."""

    async def mul(a: int, b: int) -> int:
        return a * b

    mul_sync = to_sync(mul)
    assert mul_sync(3, 7) == 21


@pytest.mark.sync
def test_post_request_executes_and_records_headers(monkeypatch):  # noqa: ARG001
    """`post_request` sends and records headers on the adapter."""
    cfg = Config(api_key='token', version='2024-10')
    c = make_client_with_dummy(cfg)
    dummy: DummyAdapter = c._async_client._adapter  # type: ignore[attr-defined]
    out = c.post_request('query { me { id } }')
    assert isinstance(out, dict)
    assert dummy.calls[0]['headers']['Authorization'] == 'token'
    c.close()


@pytest.mark.sync
def test_use_headers_context_applies_and_restores():
    """`use_headers` overlays headers and restores prior values on exit."""
    c = make_client_with_dummy()
    dummy: DummyAdapter = c._async_client._adapter  # type: ignore[attr-defined]

    with c.use_headers({'Authorization': 'A', 'X-Trace': 'outer'}):
        c.post_request('query { me { id } }')
        assert dummy.calls[-1]['headers']['Authorization'] == 'A'
        assert dummy.calls[-1]['headers']['X-Trace'] == 'outer'
        with c.use_headers({'Authorization': 'B'}):
            c.post_request('query { me { id } }')
            assert dummy.calls[-1]['headers']['Authorization'] == 'B'
            assert dummy.calls[-1]['headers']['X-Trace'] == 'outer'

    c.post_request('query { me { id } }')
    assert dummy.calls[-1]['headers'].get('X-Trace') is None
    assert dummy.calls[-1]['headers']['Authorization'] == 'token'
    c.close()


@pytest.mark.sync
def test_use_api_key_shorthand():
    """`use_api_key` temporarily overrides the Authorization header."""
    c = make_client_with_dummy()
    dummy: DummyAdapter = c._async_client._adapter  # type: ignore[attr-defined]

    with c.use_api_key('alt'):
        c.post_request('query { me { id } }')
        assert dummy.calls[-1]['headers']['Authorization'] == 'alt'

    c.post_request('query { me { id } }')
    assert dummy.calls[-1]['headers']['Authorization'] == 'token'
    c.close()


@pytest.mark.sync
@pytest.mark.parametrize('ctx', [nullcontext(), pytest.param(None, id='noctx')])
def test_services_proxy_runs_methods(ctx):
    """Services proxy forwards calls correctly with or without a context manager."""
    # We will stub adapter to return a minimal items response
    cfg = Config(api_key='token', version='2024-10')
    c = SyncMondayClient(cfg)
    c._async_client._adapter = DummyAdapter(responses=[{'data': {'items': []}}])  # type: ignore[attr-defined]

    if ctx is None:
        c.items.query(item_ids=[1])
    else:
        with ctx:
            c.items.query(item_ids=[1])

    c.close()


@pytest.mark.sync
def test_context_is_thread_local():
    """Header context is thread-local and restored after context exit."""
    c = make_client_with_dummy()
    dummy: DummyAdapter = c._async_client._adapter  # type: ignore[attr-defined]

    with c.use_headers({'Authorization': 'outer'}):
        # Call from a different thread via the runner loop (already what facade does)
        c.post_request('query { me { id } }')
        assert dummy.calls[-1]['headers']['Authorization'] == 'outer'

    # Outside context, back to default
    c.post_request('query { me { id } }')
    assert dummy.calls[-1]['headers']['Authorization'] == 'token'
    c.close()
