..
   This file is part of monday-client.

   Copyright (C) 2024 Leet Cyber Security <https://leetcybersecurity.com/>

   monday-client is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   monday-client is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with monday-client. If not, see <https://www.gnu.org/licenses/>.

Synchronous Usage
====================================

This page documents the optional synchronous API provided by :class:`SyncMondayClient <monday.sync_client.SyncMondayClient>` and the top-level helpers :func:`sync() <monday.sync>`, :func:`run_sync() <monday.run_sync>`, and :func:`to_sync() <monday.to_sync>`.

When to use
-----------

- You are not using ``asyncio`` but want to call the async Monday API client.
- You prefer a blocking API surface while preserving the same service design.

What it provides
----------------

- :class:`SyncMondayClient <monday.sync_client.SyncMondayClient>`: mirrors :class:`MondayClient <monday.client.MondayClient>` services but executes coroutine-returning methods on a dedicated background event loop.
- :func:`sync() <monday.sync>`: convenience factory that returns a :class:`SyncMondayClient <monday.sync_client.SyncMondayClient>`.
- :func:`run_sync() <monday.run_sync>`: run a single coroutine to completion without managing an event loop.
- :func:`to_sync() <monday.to_sync>`: wrap an ``async def`` function so you can call it synchronously.

Quick start
-----------

.. code-block:: python

    from monday import sync

    client = sync(api_key='your_api_key')
    items = client.items.query(item_ids=[123])  # blocking call
    with client.use_api_key('another_token'):
        board = client.boards.query(board_ids=[456])
    client.close()

Header override contexts
------------------------

- :func:`use_headers() <monday.sync_client.SyncMondayClient.use_headers>`: Synchronous context manager that applies temporary headers to awaited calls made inside the ``with`` block.
- :func:`use_api_key() <monday.sync_client.SyncMondayClient.use_api_key>`: Synchronous shorthand for overriding the ``Authorization`` header.
- Contexts are stackable; later (inner) overrides take precedence on key conflicts.

.. code-block:: python

    with client.use_headers({'X-Trace': 'outer', 'Authorization': 'Bearer A'}):
        # headers include X-Trace=outer, Authorization=Bearer A
        with client.use_api_key('B'):
            # headers include X-Trace=outer, Authorization=Bearer B
            ...
        # back to Authorization=Bearer A

Performance and threading notes
--------------------------------

- Each :class:`SyncMondayClient <monday.sync_client.SyncMondayClient>` instance owns a dedicated background event loop running in a daemon thread.
- Prefer reusing a single instance rather than repeatedly constructing/destroying clients.
- The facade is intended for non-async callers. Avoid calling it from within an event loop running on the same thread.

Top-level helpers
-----------------

.. code-block:: python

    from monday import run_sync, to_sync

    async def compute(x):
        return x * 2

    assert run_sync(compute(21)) == 42

    compute_sync = to_sync(compute)
    assert compute_sync(21) == 42

Testing guidance
----------------

- When writing tests for code using :class:`SyncMondayClient <monday.sync_client.SyncMondayClient>`, mock or stub :meth:`AiohttpAdapter.post <monday.http_adapters.AiohttpAdapter.post>` (or :meth:`HttpxAdapter.post <monday.http_adapters.HttpxAdapter.post>`) to avoid real network calls.
- Use nested :func:`use_headers() <monday.sync_client.SyncMondayClient.use_headers>` contexts to test header propagation and override precedence.

API reference
-------------

.. autoclass:: monday.sync_client.SyncMondayClient
   :members: post_request, use_api_key, use_headers, close
   :show-inheritance:

.. autofunction:: monday.sync

.. autofunction:: monday.run_sync

.. autofunction:: monday.to_sync
