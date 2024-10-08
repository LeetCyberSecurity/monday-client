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
        client = MondayClient(api_key='your_api_key_here')
        boards = await client.boards.query(board_ids=[1234567890, 1234567891])
        items_page = await client.items.items_page(board_ids=[1234567890, 1234567891])

    asyncio.run(main())

Error Handling
--------------

Custom exceptions are defined for handling specific error cases:

    * :exc:`~monday.exceptions.MondayAPIError`: Raised when an error occurs during API communication with Monday.com.
    * :exc:`~monday.exceptions.PaginationError`: Raised when item pagination fails during a request.
    * :exc:`~monday.exceptions.QueryFormatError`: Raised when there is a query formatting error.

These exceptions are handled internally by the client during retries. If the maximum number of retries is exceeded, the client will return an error response.

    * :exc:`~monday.exceptions.ComplexityLimitExceeded`: Raised when the complexity limit is exceeded.
    * :exc:`~monday.exceptions.MutationLimitExceeded`: Raised when the mutation limit is exceeded.

Logging
-------

The client uses a logger named ``monday_client`` for all logging operations. By default, a NullHandler is added to suppress logging output. To enable logging, you can configure the logger in your application:

.. code-block:: python

    import logging

    logger = logging.getLogger('monday_client')
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)