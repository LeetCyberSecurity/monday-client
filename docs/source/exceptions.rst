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

.. _exceptions:

Exception Handling
==================

The monday-client library provides comprehensive error handling through custom exceptions that help you understand and respond to different types of API errors. This page covers all available exceptions, when they occur, and how to handle them effectively.

.. contents:: Table of Contents
   :depth: 3
   :local:

Exception Overview
------------------

All custom exceptions in monday-client inherit from Python's base ``Exception`` class and provide additional context about API errors. They are designed to give you actionable information for debugging and error recovery.

.. list-table:: Exception Summary
   :header-rows: 1
   :widths: 25 25 50

   * - Exception
     - Trigger Condition
     - Key Attributes
   * - :exc:`MondayAPIError`
     - General API communication errors
     - ``json`` (API response data)
   * - :exc:`ComplexityLimitExceeded`
     - GraphQL query too complex
     - ``reset_in``, ``json``
   * - :exc:`MutationLimitExceeded`
     - Too many mutations per minute
     - ``reset_in``, ``json``
   * - :exc:`PaginationError`
     - Item pagination failures
     - ``json`` (pagination context)
   * - :exc:`QueryFormatError`
     - Malformed GraphQL queries
     - ``json`` (format details)

Exception Details
-----------------

MondayAPIError
~~~~~~~~~~~~~~

.. autoclass:: monday.exceptions.MondayAPIError
   :members:
   :show-inheritance:
   :exclude-members: json

**When it occurs:**
- Network connectivity issues
- Invalid API keys or authentication failures
- Server-side errors (5xx responses)
- Malformed requests that don't fit other specific categories

**Example usage:**

.. code-block:: python

   import asyncio
   from monday import MondayClient, MondayAPIError

   async def handle_api_errors():
      client = MondayClient(api_key='your_api_key')

      try:
         boards = await client.boards.query(board_ids=[123456789])
      except MondayAPIError as e:
         print(f'API Error: {e}')

         # Access additional error context
         if e.json:
            print(f'Error details: {e.json}')

            # Check for specific error types
            if 'errors' in e.json:
               for error in e.json['errors']:
                  print(f'- {error.get("message", "Unknown error")}')

   asyncio.run(handle_api_errors())

ComplexityLimitExceeded
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: monday.exceptions.ComplexityLimitExceeded
   :members:
   :show-inheritance:
   :exclude-members: json, reset_in

**When it occurs:**
- GraphQL query requests too much data in a single call
- Deeply nested queries with many relationships
- Queries that would consume excessive server resources

**Understanding complexity limits:**
Monday.com limits the computational complexity of GraphQL queries to ensure fair usage. Complex queries with many nested fields or large result sets can exceed these limits.

**Example usage:**

.. code-block:: python

   import asyncio
   from monday import MondayClient, ComplexityLimitExceeded

   async def handle_complexity_limits():
      client = MondayClient(api_key='your_api_key')

      try:
         # This might be too complex if requesting many boards with full details
         boards = await client.boards.query(
            board_ids=list(range(1000000, 1000100)),  # 100 boards
            fields='id name description owners { id name email } groups { id title color items { id name column_values { id text } } }'
         )
      except ComplexityLimitExceeded as e:
         print(f'Query too complex: {e}')
         print(f'Retry in {e.reset_in} seconds')

         # The client automatically handles retries, but you can implement custom logic
         await asyncio.sleep(e.reset_in)

         # Try a simpler query
         boards = await client.boards.query(
            board_ids=[1000000],  # Just one board
            fields='id name description'  # Fewer fields
         )

   asyncio.run(handle_complexity_limits())

MutationLimitExceeded
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: monday.exceptions.MutationLimitExceeded
   :members:
   :show-inheritance:
   :exclude-members: json, reset_in

**When it occurs:**
- Too many create, update, or delete operations per minute
- Exceeding monday.com's mutation rate limits
- Bulk operations that happen too quickly

**Rate limit details:**
Monday.com enforces rate limits on mutations (data-changing operations) to prevent abuse and ensure system stability. The exact limits depend on your plan and current usage.

**Example usage:**

.. code-block:: python

   import asyncio
   from monday import MondayClient, MutationLimitExceeded
   from monday.types import TextInput

   async def handle_mutation_limits():
      client = MondayClient(api_key='your_api_key')

      items_to_update = [123456789, 123456790, 123456791]

      for item_id in items_to_update:
         try:
            await client.items.change_column_values(
               item_id=item_id,
               column_values=[TextInput('text', f'Updated item {item_id}')]
            )
         except MutationLimitExceeded as e:
            print(f'Rate limit exceeded: {e}')
            print(f'Waiting {e.reset_in} seconds before retrying...')

            # Wait for rate limit to reset
            await asyncio.sleep(e.reset_in)

            # Retry the operation
            await client.items.change_column_values(
               item_id=item_id,
               column_values=[TextInput('text', f'Updated item {item_id}')]
            )

   asyncio.run(handle_mutation_limits())

PaginationError
~~~~~~~~~~~~~~~

.. autoclass:: monday.exceptions.PaginationError
   :members:
   :show-inheritance:
   :exclude-members: json

**When it occurs:**
- Invalid pagination cursors
- Attempting to paginate beyond available data
- Corrupted pagination state during large data retrievals

**Example usage:**

.. code-block:: python

   import asyncio
   from monday import MondayClient, PaginationError

   async def handle_pagination_errors():
      client = MondayClient(api_key='your_api_key')

      try:
         # Get items with pagination
         item_lists = await client.boards.get_items(
            board_ids=[123456789],
            limit=50
         )

         for item_list in item_lists:
            print(f'Board {item_list.board_id}: {len(item_list.items)} items')

      except PaginationError as e:
         print(f'Pagination failed: {e}')

         # Try without pagination for smaller datasets
         item_lists = await client.boards.get_items(
            board_ids=[123456789],
            limit=10  # Smaller limit
         )

   asyncio.run(handle_pagination_errors())

QueryFormatError
~~~~~~~~~~~~~~~~

.. autoclass:: monday.exceptions.QueryFormatError
   :members:
   :show-inheritance:
   :exclude-members: json

**When it occurs:**
- Malformed GraphQL query syntax
- Invalid field names or structures
- Incorrect query parameters or arguments

**Example usage:**

.. code-block:: python

   import asyncio
   from monday import MondayClient, QueryFormatError

   async def handle_query_format_errors():
      client = MondayClient(api_key='your_api_key')

      try:
         # This might cause a format error if fields are invalid
         boards = await client.boards.query(
            board_ids=[123456789],
            fields='invalid_field { also_invalid }'  # Bad field names
         )
      except QueryFormatError as e:
         print(f'Query format error: {e}')

         if e.json and 'errors' in e.json:
            for error in e.json['errors']:
               print(f'GraphQL Error: {error.get("message")}')

         # Use valid fields instead
         boards = await client.boards.query(
            board_ids=[123456789],
            fields='id name state'  # Valid fields
         )

   asyncio.run(handle_query_format_errors())

Best Practices
--------------

General Error Handling Strategy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. **Always use try-catch blocks** for API operations:

   .. code-block:: python

      from monday import MondayClient, MondayAPIError

      async def robust_api_call():
         client = MondayClient(api_key='your_api_key')

         try:
            result = await client.boards.query(board_ids=[123456789])
            return result
         except MondayAPIError as e:
            # Log the error for debugging
            print(f'API call failed: {e}')

            # Return None or empty list instead of crashing
            return []

#. **Handle specific exceptions differently**:

.. code-block:: python

   from monday import (
      MondayClient,
      MondayAPIError,
      ComplexityLimitExceeded,
      MutationLimitExceeded
   )

   async def comprehensive_error_handling():
      client = MondayClient(api_key='your_api_key')

      try:
         boards = await client.boards.query(board_ids=[123456789])
      except ComplexityLimitExceeded as e:
         # Simplify the query
         print(f'Query too complex, simplifying...')
         boards = await client.boards.query(
            board_ids=[123456789],
            fields='id name'
         )
      except MutationLimitExceeded as e:
         # Wait and retry
         print(f'Rate limited, waiting {e.reset_in} seconds...')
         await asyncio.sleep(e.reset_in)
         boards = await client.boards.query(board_ids=[123456789])
      except MondayAPIError as e:
         # General error handling
         print(f'API error: {e}')
         boards = []

Rate Limiting and Retries
~~~~~~~~~~~~~~~~~~~~~~~~~

The monday-client automatically handles rate limiting with built-in retry logic, but you can implement additional strategies:

.. code-block:: python

   import asyncio
   from monday import MondayClient, ComplexityLimitExceeded, MutationLimitExceeded

   async def retry_with_backoff(client, max_retries=3):
      """Retry an operation with exponential backoff."""
      for attempt in range(max_retries):
         try:
            return await client.items.create(
               board_id=123456789,
               item_name='New Item'
            )
         except (ComplexityLimitExceeded, MutationLimitExceeded) as e:
            if attempt == max_retries - 1:
               raise  # Re-raise on final attempt
            wait_time = e.reset_in if hasattr(e, 'reset_in') else (2 ** attempt)
            print(f'Attempt {attempt + 1} failed, waiting {wait_time} seconds...')
            await asyncio.sleep(wait_time)

   async def main():
      client = MondayClient(api_key='your_api_key')
      # Retry with backoff
      new_item = await retry_with_backoff(client)

   asyncio.run(main())

Query Optimization
~~~~~~~~~~~~~~~~~~

To avoid ``ComplexityLimitExceeded`` errors:

.. code-block:: python

   async def main():
      # Too complex - requests everything at once
      try:
         boards = await client.boards.query(
            board_ids=[987654321, 876543210, 765432109, 654321098, 543210987],
            fields='id name description owners { id name email } groups { id title color items { id name column_values { id text } subitems { id name } } }'
         )
      except ComplexityLimitExceeded:
         pass

      # Better - request fewer boards and simpler fields
      boards = await client.boards.query(
         board_ids=[987654321, 876543210, 765432109],  # Fewer boards
         fields='id name description'  # Essential fields only
      )

   main()

Logging and Debugging
~~~~~~~~~~~~~~~~~~~~~

Enable detailed logging to debug exceptions:

.. code-block:: python

   import logging
   from monday import MondayClient, MondayAPIError

   # Enable debug logging
   logging.basicConfig(level=logging.DEBUG)
   monday_logger = logging.getLogger('monday')
   monday_logger.setLevel(logging.DEBUG)

   # Add a handler if none exists
   if not monday_logger.handlers:
      handler = logging.StreamHandler()
      formatter = logging.Formatter(
         '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
      )
      handler.setFormatter(formatter)
      monday_logger.addHandler(handler)

   client = MondayClient(api_key='your_api_key')

   async def main():
      return await client.boards.query(board_ids=[123456789])

   try:
      boards = asyncio.run(main())
   except MondayAPIError as e:
      # Detailed error information will be logged automatically
      print(f'Operation failed: {e}')

Common Error Scenarios
----------------------

Authentication Issues
~~~~~~~~~~~~~~~~~~~~~

**Symptoms:**
- ``MondayAPIError`` with authentication-related messages
- HTTP 401 Unauthorized responses

**Solutions:**

.. code-block:: python

   from monday import MondayClient, MondayAPIError

   async def check_authentication():
      try:
         client = MondayClient(api_key='your_api_key')
         # Simple query to test authentication
         boards = await client.boards.query(board_ids=[123456789], fields='id')
      except MondayAPIError as e:
         if 'unauthorized' in str(e).lower():
            print('Authentication failed. Check your API key.')
            print('Get your API key from: https://monday.com/developers/api')
         else:
            print(f'Other API error: {e}')

Network Issues
~~~~~~~~~~~~~~

**Symptoms:**
- ``MondayAPIError`` with network-related messages
- Timeouts or connection errors

**Solutions:**

.. code-block:: python

   import aiohttp
   from monday import MondayClient, MondayAPIError, Config

   async def handle_network_issues():
      # Configure longer timeout for slow networks
      config = Config(
         api_key='your_api_key',
         timeout=60  # 60 second timeout instead of default 30
      )
      client = MondayClient(config)

      try:
         boards = await client.boards.query(board_ids=[123456789])
      except MondayAPIError as e:
         if 'timeout' in str(e).lower():
            print('Request timed out. Try again or check your network.')
         elif 'connection' in str(e).lower():
            print('Connection failed. Check your internet connection.')
         else:
            raise

Invalid Data Access
~~~~~~~~~~~~~~~~~~~

**Symptoms:**
- ``MondayAPIError`` when accessing non-existent boards/items
- Permission-related errors

**Solutions:**

.. code-block:: python

   from monday import MondayClient, MondayAPIError

   async def safe_data_access():
      client = MondayClient(api_key='your_api_key')

      try:
         boards = await client.boards.query(board_ids=[999999999])  # Non-existent board
      except MondayAPIError as e:
         if 'not found' in str(e).lower():
            print('Board not found or no access permission')
            return []
         elif 'permission' in str(e).lower():
            print('Insufficient permissions to access this board')
            return []
         else:
            raise

   # Alternative: Check if boards exist first
   async def check_board_access():
      client = MondayClient(api_key='your_api_key')

      try:
         # Get all accessible boards first
         all_boards = await client.boards.query(board_ids=[], fields='id name')
         accessible_ids = [board.id for board in all_boards]

         # Only query boards you have access to
         target_ids = [123456789, 987654321]
         valid_ids = [id for id in target_ids if str(id) in accessible_ids]

         if valid_ids:
            boards = await client.boards.query(board_ids=valid_ids)
            return boards
         else:
            print('No accessible boards found')
            return []

      except MondayAPIError as e:
         print(f'Error checking board access: {e}')
         return []

Troubleshooting Guide
---------------------

Exception Not Being Caught
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Exceptions are not being caught by your try-catch blocks.

**Solution:** Make sure you're importing the correct exceptions:

.. code-block:: python

   # Correct - import specific exceptions
   from monday.exceptions import MondayAPIError, ComplexityLimitExceeded

   async def example_function():
      # Incorrect - won't catch monday-client exceptions
      try:
         result = await client.boards.query(board_ids=[123])
      except Exception as e:  # Too generic
         pass

      # Correct - catch specific exceptions
      try:
         result = await client.boards.query(board_ids=[123])
      except MondayAPIError as e:
         print(f'Monday API error: {e}')
      except Exception as e:  # Catch-all for unexpected errors
         print(f'Unexpected error: {e}')

Unclear Error Messages
~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Error messages don't provide enough context.

**Solution:** Access the ``json`` attribute for detailed error information:

.. code-block:: python

   from monday import MondayClient, MondayAPIError
   import json

   async def debug_errors():
      try:
         boards = await client.boards.query(board_ids=[123456789])
      except MondayAPIError as e:
         print(f'Error message: {e}')

         if e.json:
            # Pretty print the full error context
            print('Full error details:')
            print(json.dumps(e.json, indent=2))

            # Extract specific error information
            if 'errors' in e.json:
               for error in e.json['errors']:
                  print(f'GraphQL Error: {error.get("message")}')
                  if 'path' in error:
                     print(f'Error path: {error["path"]}')

Frequent Rate Limiting
~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Constantly hitting rate limits.

**Solutions:**

#. **Reduce request frequency:**

   .. code-block:: python

      import asyncio
      from monday import MondayClient

      async def batch_operations_with_delay():
         client = MondayClient(api_key='your_api_key')

         items_to_update = [123, 456, 789, 101112]

         for i, item_id in enumerate(items_to_update):
            await client.items.change_column_values(
               item_id=item_id,
               column_values=[TextInput('text', f'Update {i}')]
            )

            # Add delay between operations
            if i < len(items_to_update) - 1:
               await asyncio.sleep(1)  # 1 second delay

#. **Batch operations when possible:**

.. code-block:: python

   async def batch_example():
      # Individual requests (more likely to hit limits)
      for item_id in [123, 456, 789]:
         await client.items.change_column_values(
            item_id=item_id,
            column_values=[TextInput('text', 'Updated')]
         )

      # Fewer, larger requests
      all_items = await client.items.query(
         item_ids=[123, 456, 789],
         fields='id name'
      )

.. seealso::

   - :doc:`usage` - Basic usage examples and patterns
   - :doc:`configuration` - Configuration options including timeouts and retries
   - :doc:`monday_client` - MondayClient API reference
