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


.. _usage:

Usage
=====

.. contents:: Table of Contents
    :depth: 2
    :local:

Installation
------------

.. code-block:: bash

    pip install monday-client

Quick Start
-----------

.. code-block:: python

    import asyncio

    from monday import MondayClient

    async def main():
        monday_client = MondayClient(api_key='your_api_key_here')
        boards = await monday_client.boards.query(board_ids=[987654321, 876543210])
        items = await monday_client.items.query(item_ids=[123456789, 123456780])

    asyncio.run(main())

Using multiple tokens safely
----------------------------

When you need to use a different token for a specific operation (e.g., creating a webhook with an integration OAuth token), use the client's async context managers to apply a per-request header override without mutating shared state:

.. code-block:: python

    import asyncio

    async def main():
        async with monday_client.use_api_key('integration_oauth_token'):
            await monday_client.webhooks.create(board_id=1234567890, url='https://example.com/webhooks/monday', event='create_item')

    asyncio.run(main())

You can also override arbitrary headers:

.. code-block:: python

    import asyncio

    async def main():
        async with monday_client.use_headers({'Authorization': 'other_token', 'API-Version': '2025-01'}):
            await monday_client.users.query()

    asyncio.run(main())

.. _usage_filtering_and_querying_items:

Filtering and Querying Items
----------------------------

The client provides powerful filtering capabilities for retrieving items based on specific criteria. Use :class:`~monday.types.item.QueryParams` and :class:`~monday.types.item.QueryRule` to build complex queries:

.. code-block:: python

    import asyncio
    from monday import MondayClient, QueryParams, QueryRule

    async def main():
        monday_client = MondayClient(api_key='your_api_key_here')

        # Filter items with status "Done" or "In Progress"
        query_params = QueryParams(
            rules=[
                QueryRule(
                    column_id='status',
                    compare_value=['Done', 'In Progress'],
                    operator='any_of'
                )
            ],
            operator='and'
        )

        # Get filtered items from a board, including status column text
        item_lists = await monday_client.boards.get_items(
            board_ids=987654321,
            query_params=query_params,
            fields='id name column_values (ids: ["status"]) { id text }'
        )

        for item_list in item_lists:
            print(f"Board {item_list.board_id}:")
            for item in item_list.items:
                status_text = next((cv.text for cv in (item.column_values or []) if cv.id == 'status'), '')
                print(f"  - {item.name} (status: {status_text})")

    asyncio.run(main())

For more advanced querying options, see :ref:`Query Types <query_types>` in the Types documentation. The :meth:`boards.get_items() <monday.services.boards.Boards.get_items>` method is the primary way to use these query parameters.

Error Handling
--------------

Custom exceptions are defined for handling specific error cases:

    * :exc:`~monday.exceptions.MondayAPIError`: Raised when an error occurs during API communication with Monday.com.
    * :exc:`~monday.exceptions.PaginationError`: Raised when item pagination fails during a request.
    * :exc:`~monday.exceptions.QueryFormatError`: Raised when there is a query formatting error.
    * :exc:`~monday.exceptions.ComplexityLimitExceeded`: Raised when the complexity limit is exceeded.
    * :exc:`~monday.exceptions.MutationLimitExceeded`: Raised when the mutation limit is exceeded.

Logging
-------

Library modules log under the ``monday.*`` hierarchy (e.g., ``monday.client``) which propagate to the root ``monday`` logger. By default, a ``NullHandler`` is attached to ``monday`` to suppress output. Enable logging by configuring the ``monday`` logger or by using the helpers:

.. code-block:: python

    import logging
    from monday import MondayClient

    from monday import enable_logging, configure_for_external_logging

    # Simple enable with defaults
    enable_logging(level='INFO')

    # Or integrate with your logging config
    configure_for_external_logging()
    logging.config.dictConfig({
        'version': 1,
        'handlers': {'console': {'class': 'logging.StreamHandler'}},
        'loggers': {'monday': {'level': 'INFO', 'handlers': ['console']}},
    })

    client = MondayClient(api_key='your_api_key')
