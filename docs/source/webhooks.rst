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

Webhooks
========

This guide explains how to work with monday.com Webhooks using monday-client and how to implement URL verification on your server endpoint.

References: `monday.com Webhooks API <https://developer.monday.com/api-reference/reference/webhooks>`_.

.. contents::
   :depth: 2
   :local:

Overview
--------

monday-client provides a ``Webhooks`` service with helpers to query, create, and delete webhooks for a board. After you create a webhook, monday.com will send a verification POST to your webhook URL with a JSON body containing a ``challenge`` token. Your endpoint must echo that token back to verify the URL.

.. note::

   For standard webhooks, a personal API key is sufficient to create them. To receive webhooks that include a JWT ``Authorization`` header, or to prevent end-users from disabling integration webhooks, you must create the webhook using an integration app OAuth token.

URL Verification
----------------

When you create a webhook, monday.com verifies that you control the target URL by POSTing a JSON body containing a randomly generated token:

.. code-block:: python

   { 'challenge': 'challenge_text_here' }

Your server must respond with HTTP 200 and the same JSON body:

.. code-block:: python

   { 'challenge': 'challenge_text_here' }

Minimal endpoint examples
~~~~~~~~~~~~~~~~~~~~~~~~~

FastAPI:

.. code-block:: python

   from fastapi import FastAPI, Request
   from fastapi.responses import JSONResponse

   app = FastAPI()

   @app.post('/webhooks/monday')
   async def monday_webhook(request: Request):
      body = await request.json()
      if isinstance(body, dict) and 'challenge' in body:
         return JSONResponse(content={'challenge': body['challenge']}, status_code=200)
      # Handle normal webhook delivery here
      return JSONResponse(content={'ok': True}, status_code=200)

Flask:

.. code-block:: python

   from flask import Flask, request, jsonify

   app = Flask(__name__)

   @app.post('/webhooks/monday')
   def monday_webhook():
      data = request.get_json(silent=True) or {}
      if 'challenge' in data:
         return jsonify({'challenge': data['challenge']}), 200
      # Handle normal webhook delivery here
      return jsonify({'ok': True}), 200

Notes:

- Return quickly with 200; monday will retry once per minute for 30 minutes if not acknowledged.
- If the request includes an Authorization header with a JWT (when created with an integration app token), verify it against your app's signing secret before processing events.
- Always use HTTPS and return JSON that exactly matches the received ``challenge`` object.
- The webhook URL must be <= 255 characters, and must be reachable from monday.com's servers.
- See monday's URL verification docs for full details: https://developer.monday.com/api-reference/reference/webhooks#url-verification

Creating and managing webhooks with monday-client
-------------------------------------------------

Create a webhook
~~~~~~~~~~~~~~~~

.. code-block:: python

   import asyncio
   from monday import MondayClient

   async def main():
      monday_client = MondayClient(api_key='your_api_key')
      webhook = await monday_client.webhooks.create(
         board_id=1234567890,
         url='https://example.com/webhooks/monday',
         event='create_item',  # see supported events below
         # Optional config for supported events, e.g.:
         # config={'columnId': 'status'}
      )
      print(webhook)

   asyncio.run(main())

.. tip::

   If you need to call the webhooks API with a different token (for example, an integration app OAuth token to enable JWT-authenticated deliveries), use the :py:meth:`monday.client.MondayClient.use_api_key` context manager (inside an async function):

   .. code-block:: python

      import asyncio
      from monday import MondayClient

      async def main():
         monday_client = MondayClient(api_key='your_api_key')
         async with monday_client.use_api_key('integration_oauth_token'):
            await monday_client.webhooks.create(
               board_id=1234567890,
               url='https://example.com/webhooks/monday',
               event='create_item',
            )

      asyncio.run(main())

Query webhooks
~~~~~~~~~~~~~~

.. code-block:: python

   import asyncio
   from monday import MondayClient

   async def main():
      monday_client = MondayClient(api_key='your_api_key')
      hooks = await monday_client.webhooks.query(board_id=1234567890)
      print(hooks)

   asyncio.run(main())

Delete a webhook
~~~~~~~~~~~~~~~~

.. code-block:: python

   import asyncio
   from monday import MondayClient

   async def main():
      monday_client = MondayClient(api_key='your_api_key')
      deleted = await monday_client.webhooks.delete(webhook_id='123')
      print(deleted)

   asyncio.run(main())

Supported events
----------------

The API supports these event types (see monday docs for details):

- ``change_column_value``
- ``change_status_column_value``
- ``change_subitem_column_value``
- ``change_specific_column_value``
- ``change_name``
- ``create_item``
- ``item_archived``
- ``item_deleted``
- ``item_moved_to_any_group``
- ``item_moved_to_specific_group``
- ``item_restored``
- ``create_subitem``
- ``change_subitem_name``
- ``move_subitem``
- ``subitem_archived``
- ``subitem_deleted``
- ``create_column``
- ``create_update``
- ``edit_update``
- ``delete_update``
- ``create_subitem_update``

Event configuration (``config``)
--------------------------------

Some events accept a ``config`` JSON argument when creating the webhook. Examples:

- ``change_specific_column_value``: ``{'columnId': '<column_id>'}``
- ``change_status_column_value``: ``{'columnValue': {'index': <index>}, 'columnId': '<column_id>'}``
- ``item_moved_to_specific_group``: ``{'groupId': '<group_id>'}``

Retry policy
------------

monday retries failed webhook deliveries once per minute for 30 minutes.

Testing notes
-------------

When running integration/mutation tests in this repository, configure a target URL that responds to monday's URL verification by echoing the ``challenge`` JSON back. Provide this via ``tests/integrations/config.yml`` as ``monday.webhook_target_url`` or the ``MONDAY_WEBHOOK_TARGET_URL`` environment variable.

Further reading
---------------

- monday.com Webhooks reference: https://developer.monday.com/api-reference/reference/webhooks
