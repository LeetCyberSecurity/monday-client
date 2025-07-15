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
        items_page = await monday_client.items.query(item_ids=[123456789, 123456780])

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

        # Get filtered items from a board
        item_lists = await monday_client.boards.get_items(
            board_ids=987654321,
            query_params=query_params,
            fields='id name status'
        )

        for item_list in item_lists:
            print(f"Board {item_list.board_id}:")
            for item in item_list.items:
                print(f"  - {item.name} ({item.status})")

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

The client uses a logger named ``monday`` for all logging operations. By default, a ``NullHandler`` is added to suppress logging output. To enable logging, you can configure the logger in your application:

.. code-block:: python

    import logging
    from monday import MondayClient

    # Remove the default NullHandler and add a real handler
    monday_logger = logging.getLogger('monday')
    for handler in monday_logger.handlers[:]:
        if isinstance(handler, logging.NullHandler):
            monday_logger.removeHandler(handler)

    if not monday_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        monday_logger.addHandler(handler)

    client = MondayClient('your_api_key')
