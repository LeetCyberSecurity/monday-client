# This file is part of monday-client.
#
# Copyright (C) 2024 Leet Cyber Security <https://leetcybersecurity.com/>
#
# monday-client is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# monday-client is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with monday-client. If not, see <https://www.gnu.org/licenses/>.

"""
Module for handling monday.com webhook operations.

This module provides a set of operations for reading, creating, and deleting
webhooks via the monday.com GraphQL API.

References:
    Webhooks API: https://developer.monday.com/api-reference/reference/webhooks

Usage requires an initialized :class:`~monday.client.MondayClient` instance.

"""

import json
import logging
from typing import Any, Literal

from monday.fields.webhook_fields import WebhookFields
from monday.protocols import MondayClientProtocol
from monday.services.utils.error_handlers import check_query_result
from monday.services.utils.fields import Fields
from monday.services.utils.query_builder import (
    build_graphql_query,
    build_operation_with_variables,
)
from monday.types.webhook import Webhook

# Align with monday.com documented events
WebhookEventType = Literal[
    'change_column_value',
    'change_status_column_value',
    'change_subitem_column_value',
    'change_specific_column_value',
    'change_name',
    'create_item',
    'item_archived',
    'item_deleted',
    'item_moved_to_any_group',
    'item_moved_to_specific_group',
    'item_restored',
    'create_subitem',
    'change_subitem_name',
    'move_subitem',
    'subitem_archived',
    'subitem_deleted',
    'create_column',
    'create_update',
    'edit_update',
    'delete_update',
    'create_subitem_update',
]


class Webhooks:
    """
    Service class for handling monday.com webhook operations.
    """

    _logger: logging.Logger = logging.getLogger(__name__)

    def __init__(self, client: MondayClientProtocol):
        """
        Initialize a Webhooks service instance.

        Args:
            client: A client implementing MondayClientProtocol for API requests.

        """
        self.client = client

    async def query(
        self,
        board_id: int | str,
        *,
        app_webhooks_only: bool | None = None,
        fields: str | Fields = WebhookFields.BASIC,
    ) -> list[Webhook]:
        """
        Query webhooks configured for a specific board.

        Args:
            board_id: The unique identifier of the board to query webhooks for.
            app_webhooks_only: Returns only webhooks created by the app initiating the request.
            fields: Fields to return from the webhook objects.

        Returns:
            A list of :class:`~monday.types.webhook.Webhook` instances.

        """
        fields = Fields(fields)

        args = {
            'board_id': board_id,
            'app_webhooks_only': app_webhooks_only,
            'fields': fields,
        }

        query_string = build_graphql_query('webhooks', 'query', args)

        query_result = await self.client.post_request(query_string)
        data = check_query_result(query_result)

        webhooks = data['data'].get('webhooks', [])
        return [Webhook.from_dict(w) for w in webhooks]

    async def create(
        self,
        board_id: int | str,
        url: str,
        event: WebhookEventType | str,
        *,
        config: dict[str, Any] | None = None,
        fields: str | Fields = WebhookFields.BASIC,
    ) -> Webhook:
        """
        Create a webhook subscription on a board.

        Args:
            board_id: The board's unique identifier.
            url: The webhook target URL. Max length 255 characters.
            event: The event to listen to (WebhookEventType).
            config: Optional configuration JSON for supported events.
            fields: Fields to return from the created webhook.

        Returns:
            A :class:`~monday.types.webhook.Webhook` instance for the created webhook.

        """
        fields = Fields(fields)

        variable_types: dict[str, str] = {
            'boardId': 'ID!',
            'url': 'String!',
            'event': 'WebhookEventType!',
        }
        variables: dict[str, Any] = {
            'boardId': str(board_id),
            'url': url,
            'event': event,
        }
        arg_var_mapping: dict[str, str] = {
            'board_id': 'boardId',
            'url': 'url',
            'event': 'event',
        }

        if config is not None:
            variable_types['config'] = 'JSON'
            variables['config'] = json.dumps(config)
            arg_var_mapping['config'] = 'config'

        operation = build_operation_with_variables(
            'create_webhook', 'mutation', variable_types, arg_var_mapping, fields
        )

        self._logger.debug('create_webhook operation: %s', operation)

        query_result = await self.client.post_request(operation, variables)
        data = check_query_result(query_result)

        return Webhook.from_dict(data['data']['create_webhook'])

    async def delete(
        self,
        webhook_id: int | str,
        *,
        fields: str | Fields = WebhookFields.BASIC,
    ) -> Webhook:
        """
        Delete a webhook subscription by its ID.

        Args:
            webhook_id: The webhook's unique identifier.
            fields: Fields to return from the deleted webhook.

        Returns:
            A :class:`~monday.types.webhook.Webhook` instance for the deleted webhook.

        """
        fields = Fields(fields)

        variable_types = {'webhookId': 'ID!'}
        variables = {'webhookId': str(webhook_id)}
        # GraphQL arg is `id`, bind it to variable $webhookId
        arg_var_mapping = {'id': 'webhookId'}

        operation = build_operation_with_variables(
            'delete_webhook', 'mutation', variable_types, arg_var_mapping, fields
        )

        self._logger.debug('delete_webhook operation: %s', operation)

        query_result = await self.client.post_request(operation, variables)
        data = check_query_result(query_result)

        return Webhook.from_dict(data['data']['delete_webhook'])
