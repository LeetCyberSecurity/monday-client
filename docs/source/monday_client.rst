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

.. index:: MondayClient

MondayClient
------------

.. autoclass:: monday.client.MondayClient
   :members: logger, post_request, use_api_key, use_headers, _adapter
   :show-inheritance:

Header overrides
~~~~~~~~~~~~~~~~

To use a different API token for a subset of calls (e.g., integration OAuth tokens for webhooks), use the async context managers. Overrides are applied per awaited call and are safe under concurrency:

.. code-block:: python

   import asyncio

   async def main():
      async with monday_client.use_api_key('integration_oauth_token'):
         await monday_client.webhooks.create(...)

   asyncio.run(main())

You can also override arbitrary headers:

.. code-block:: python

   import asyncio

   async def main():
      async with monday_client.use_headers({'Authorization': 'token2', 'API-Version': '2025-01'}):
         await monday_client.groups.create(...)

   asyncio.run(main())

Services
~~~~~~~~

The MondayClient provides access to various services for interacting with different aspects of the Monday.com API:

.. py:attribute:: MondayClient.boards
   :no-index:

   Service for board-related operations.

   Type: :ref:`Boards <services_section_boards>`

.. py:attribute:: MondayClient.items
   :no-index:

   Service for item-related operations.

   Type: :ref:`Items <services_section_items>`

.. py:attribute:: MondayClient.subitems
   :no-index:

   Service for subitem-related operations.

   Type: :ref:`Subitems <services_section_subitems>`

.. py:attribute:: MondayClient.groups
   :no-index:

   Service for group-related operations.

   Type: :ref:`Groups <services_section_groups>`

.. py:attribute:: MondayClient.users
   :no-index:

   Service for user-related operations.

   Type: :ref:`Users <services_section_users>`

.. py:attribute:: MondayClient.webhooks
   :no-index:

   Service for webhook-related operations.

   Type: :ref:`Webhooks <services_section_webhooks>`
