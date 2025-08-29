"""
Synchronous facade for the async Monday client.

Overview:
    The :class:`SyncMondayClient` mirrors the public surface of
    :class:`monday.client.MondayClient` and executes coroutine-returning
    methods on a background event loop so callers can use a blocking style
    without managing asyncio.

Key properties:
    - Background loop: A dedicated event loop is created in a daemon thread
      and re-used for all calls on the facade instance.
    - Services parity: The same services are exposed (``boards``, ``items``,
      ``subitems``, ``groups``, ``users``, ``webhooks``) via lightweight
      proxies that run awaitables transparently.
    - Header overrides: Sync context managers ``use_headers`` and
      ``use_api_key`` mirror their async counterparts and support nested
      stacking. The most recent context layer wins. Overrides apply to all
      awaited calls executed within the ``with`` block.

Usage:
    >>> from monday.sync_client import SyncMondayClient
    >>> client = SyncMondayClient(api_key='token')
    >>> items = client.items.query(item_ids=[123])  # blocking
    >>> with client.use_api_key('other'):
    ...     client.boards.query(board_ids=[456])
    >>> client.close()

Caveats:
    - Do not call sync methods from within an event loop that you control in
      the same thread (e.g., inside an async test without running it in a
      thread). The facade is intended for non-async callers and runs its own
      loop in a separate thread.
    - For high-throughput usage, prefer reusing a single facade instance to
      avoid repeatedly creating event loops.
"""

from __future__ import annotations

import asyncio
import inspect
import threading
from contextlib import contextmanager, suppress
from typing import TYPE_CHECKING, Any, Self

from monday.client import MondayClient

if TYPE_CHECKING:
    from collections.abc import Awaitable, Coroutine, Generator
    from concurrent.futures._base import Future

    from monday.config import Config


class _BackgroundLoopRunner:
    """
    Owns a dedicated asyncio event loop in a background thread and exposes
    a `run(coro)` API that blocks until completion and returns the result
    (or raises the original exception).
    """

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._started = threading.Event()
        self._thread.start()
        self._started.wait()

    def _run(self) -> None:
        asyncio.set_event_loop(loop=self._loop)
        self._started.set()
        self._loop.run_forever()

    def run(self, coro: Coroutine[Any, Any, Any]) -> Any:
        future: Future[Any] = asyncio.run_coroutine_threadsafe(coro, loop=self._loop)
        return future.result()

    def shutdown(self) -> None:
        try:
            self._loop.call_soon_threadsafe(callback=self._loop.stop)
            self._thread.join(timeout=2)
        finally:
            with suppress(Exception):
                self._loop.close()


class _SyncProxy:
    """
    Proxy around service instances so attribute access and method calls are
    transparently executed, and coroutine-returning methods are run via the
    background loop.
    """

    def __init__(self, facade: SyncMondayClient, target: object) -> None:
        self._facade = facade
        self._target = target

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._target, name)
        if callable(attr):

            def _wrapped(*args: Any, **kwargs: Any) -> Any:
                result: object = attr(*args, **kwargs)
                # If the result is a coroutine, execute it on the background loop
                if inspect.iscoroutine(object=result):
                    return self._facade._run_with_headers(coro=result)  # noqa: SLF001
                return result

            return _wrapped
        return attr


class SyncMondayClient:
    """
    Synchronous facade for `MondayClient`.

    This class constructs an underlying async `MondayClient` and exposes the
    same services, but methods can be called synchronously. Internally, calls
    are executed on a background asyncio event loop.
    """

    def __init__(  # noqa: PLR0913
        self,
        config: Config | None = None,
        *,
        api_key: str | None = None,
        url: str = 'https://api.monday.com/v2',
        version: str | None = None,
        headers: dict[str, Any] | None = None,
        max_retries: int = 4,
        transport: str = 'aiohttp',
    ) -> None:
        self._runner = _BackgroundLoopRunner()
        # Build the underlying async client
        if config is not None:
            self._async_client = MondayClient(config, transport=transport)
        else:
            self._async_client = MondayClient(
                api_key=api_key,
                url=url,
                version=version,
                headers=headers,
                max_retries=max_retries,
                transport=transport,
            )

        # Thread-local stack for header overrides used by sync context managers
        self._local = threading.local()

        # Expose service proxies
        self.boards = _SyncProxy(facade=self, target=self._async_client.boards)
        self.items = _SyncProxy(facade=self, target=self._async_client.items)
        self.subitems = _SyncProxy(facade=self, target=self._async_client.subitems)
        self.groups = _SyncProxy(facade=self, target=self._async_client.groups)
        self.users = _SyncProxy(facade=self, target=self._async_client.users)
        self.webhooks = _SyncProxy(facade=self, target=self._async_client.webhooks)

    # Basic properties passthrough
    @property
    def api_key(self) -> str:
        """Current API key used for Authorization."""
        return self._async_client.api_key

    @property
    def url(self) -> str:
        """Base URL for the Monday GraphQL API."""
        return self._async_client.url

    @property
    def version(self) -> str | None:
        """Pinned API version (e.g., '2024-10'), if configured."""
        return self._async_client.version

    @property
    def headers(self) -> dict[str, Any]:
        """Default HTTP headers applied to requests."""
        return self._async_client.headers

    @property
    def max_retries(self) -> int:
        """Maximum retry attempts for failed requests."""
        return self._async_client.max_retries

    # Core request API (sync)
    def post_request(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Execute a GraphQL request synchronously and return the response."""
        return self._run_with_headers(self._async_client.post_request(query, variables))

    # Sync context managers for per-call header overrides
    @contextmanager
    def use_api_key(self, api_key: str) -> Generator[Self, Any, None]:
        """
        Synchronous context manager to temporarily override Authorization header
        for calls inside the `with` block.
        """
        with self.use_headers(headers={'Authorization': api_key}):
            yield self

    @contextmanager
    def use_headers(self, headers: dict[str, Any]) -> Generator[Self, Any, None]:
        """
        Synchronous context manager to temporarily override headers for calls
        inside the `with` block.
        """
        stack: list[dict[str, Any]] = list(getattr(self._local, 'headers_stack', []))
        stack.append(dict(headers))
        self._local.headers_stack = stack
        try:
            yield self
        finally:
            try:
                stack.pop()
            finally:
                self._local.headers_stack = stack

    def close(self) -> None:
        """Shut down the background event loop and release resources."""
        self._runner.shutdown()

    def __enter__(self) -> Self:
        """Support `with SyncMondayClient(...) as c:`; returns `self`."""
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Close the client when leaving a context manager block."""
        self.close()

    def _current_headers_override(self) -> dict[str, Any] | None:
        stack: list[dict[str, Any]] = getattr(self._local, 'headers_stack', [])
        if not stack:
            return None
        merged: dict[str, Any] = {}
        for layer in stack:
            merged.update(layer)
        return merged

    def _wrap_with_headers_coro(
        self, coro: Awaitable[Any], override_headers: dict[str, Any] | None
    ) -> Coroutine[Any, Any, Any]:
        async def _runner() -> Any:
            if override_headers:
                async with self._async_client.use_headers(headers=override_headers):
                    return await coro
            return await coro

        return _runner()

    def _run_with_headers(self, coro: Awaitable[Any]) -> Any:
        # Capture headers override on calling thread, then use inside loop thread
        override = self._current_headers_override()
        return self._runner.run(coro=self._wrap_with_headers_coro(coro, override))
