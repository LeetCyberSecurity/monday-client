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
Integration and mutation tests for webhook operations.

These tests make actual API calls and require:
1. A valid API key/token available via tests/conftest.py config loading
2. Network connectivity

Run:
    python -m pytest tests/integrations/test_webhooks_integrations.py -m integration -v
Skip by default with -m "not integration".
"""

from __future__ import annotations

import json
import logging

import pytest

from monday import MondayClient
from monday.fields.webhook_fields import WebhookFields
from monday.types.webhook import Webhook


@pytest.fixture(scope='module')
def client(monday_config):
    """Create a MondayClient instance with API key from config or skip."""
    api_key = monday_config.get('api_key')
    if api_key:
        return MondayClient(api_key=api_key)
    pytest.skip('MONDAY_API_KEY not found in config file or environment variable')


@pytest.fixture(scope='module')
def board_id(monday_config):
    """Return the test board ID from config or skip when absent."""
    value = monday_config.get('board_id')
    if value:
        return int(value)
    pytest.skip('MONDAY_BOARD_ID not found in config file or environment variable')


@pytest.fixture(scope='module')
def webhook_target_url(get_config):
    """Return a URL that responds to monday's creation challenge or skip."""
    full = get_config or {}
    url = (full.get('monday') or {}).get('webhook_target_url')
    if not url:
        # Fallback to environment variable for convenience in CI/local
        import os

        url = os.getenv('MONDAY_WEBHOOK_TARGET_URL')
    if url:
        return str(url)
    pytest.skip(
        'MONDAY_WEBHOOK_TARGET_URL not configured (set env var or tests/integrations/config.yml monday.webhook_target_url)'
    )


@pytest.mark.integration
class TestWebhookIntegrations:
    """Integration tests for webhook read operations."""

    @pytest.mark.asyncio
    async def test_query_webhooks(self, client: MondayClient, board_id: int):
        """Query and validate webhooks for the configured board."""
        webhooks = await client.webhooks.query(
            board_id=board_id, fields=WebhookFields.BASIC
        )
        assert isinstance(webhooks, list)
        for wh in webhooks:
            assert isinstance(wh, Webhook)
            assert hasattr(wh, 'id')
            assert hasattr(wh, 'event')
            assert hasattr(wh, 'board_id')


@pytest.mark.integration
@pytest.mark.mutation
class TestWebhookMutations:
    """Mutation tests for webhook create and delete operations."""

    @pytest.mark.asyncio
    async def test_create_and_delete_webhook(
        self, client: MondayClient, board_id: int, webhook_target_url: str
    ):
        """Create a webhook, ensure it lists, then delete and verify removal."""
        logger = logging.getLogger(__name__)
        # unique suffix not needed when target endpoint routes by path
        # Use configured target that responds to monday's verification challenge (no suffix)
        target_url = webhook_target_url.rstrip('/')

        # Create a simple webhook
        try:
            created = await client.webhooks.create(
                board_id=board_id,
                url=target_url,
                event='create_item',
                fields=WebhookFields.BASIC,
            )
        except Exception as exc:
            logger.exception('Webhook create failed')
            # If available, dump monday error JSON for diagnostics
            err_json = getattr(exc, 'json', None)
            if err_json is not None:
                try:
                    logger.exception(
                        'Webhook create error JSON: %s', json.dumps(err_json)[:2000]
                    )
                except Exception:
                    logger.exception('Webhook create error JSON (raw): %s', err_json)
            raise

        assert created is not None
        assert isinstance(created, Webhook)
        assert created.id
        assert created.board_id == str(board_id)

        # Verify it appears in query
        listed = await client.webhooks.query(board_id=board_id)
        ids = {w.id for w in listed}
        assert created.id in ids

        # Delete the webhook
        deleted = await client.webhooks.delete(created.id)
        assert deleted is not None
        assert deleted.id == created.id

        # Best-effort verify deletion by re-querying
        remaining = await client.webhooks.query(board_id=board_id)
        remaining_ids = {w.id for w in remaining}
        assert created.id not in remaining_ids
