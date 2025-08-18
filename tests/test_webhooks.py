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

"""Unit tests for the Webhooks service."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from monday.client import MondayClient
from monday.exceptions import MondayAPIError
from monday.services.webhooks import Webhooks
from monday.types.webhook import Webhook


@pytest.fixture
def mock_client() -> MondayClient:
    """Create a mock MondayClient instance."""
    return MagicMock(spec=MondayClient)


@pytest.fixture
def webhooks_instance(mock_client: MondayClient) -> Webhooks:
    """Create a Webhooks instance with a mocked client."""
    return Webhooks(mock_client)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_query_returns_webhooks(webhooks_instance: Webhooks):
    """Test that query returns a list of Webhook dataclasses and parses config."""
    mock_response = {
        'data': {
            'webhooks': [
                {
                    'id': '10',
                    'event': 'create_item',
                    'board_id': '123',
                    'config': '{"foo": "bar"}',
                },
                {
                    'id': 11,
                    'event': 'item_deleted',
                    'board_id': 123,
                    'config': {'a': 1},
                },
            ]
        }
    }

    webhooks_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await webhooks_instance.query(board_id=123, app_webhooks_only=True)

    assert isinstance(result, list)
    assert len(result) == 2
    assert isinstance(result[0], Webhook)
    assert result[0].id == '10'
    assert result[0].event == 'create_item'
    assert result[0].board_id == '123'
    assert isinstance(result[0].config, dict)
    assert result[0].config == {'foo': 'bar'}

    assert result[1].id == '11'
    assert result[1].event == 'item_deleted'
    assert result[1].board_id == '123'
    assert isinstance(result[1].config, dict)
    assert result[1].config == {'a': 1}

    # Ensure a query was sent with expected structure (non-brittle substring checks)
    called_args = webhooks_instance.client.post_request.call_args.args
    assert isinstance(called_args[0], str)
    assert 'query' in called_args[0]
    assert 'webhooks' in called_args[0]
    assert 'app_webhooks_only: true' in called_args[0]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_query_handles_empty_response(webhooks_instance: Webhooks):
    """Test that query returns an empty list when no webhooks are returned."""
    mock_response = {'data': {'webhooks': []}}
    webhooks_instance.client.post_request = AsyncMock(return_value=mock_response)

    result = await webhooks_instance.query(board_id='456')
    assert result == []
    webhooks_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_query_with_api_error(webhooks_instance: Webhooks):
    """Test that API errors bubble up as MondayAPIError via check_query_result."""
    error_response = {
        'errors': [{'message': 'API Error', 'extensions': {'code': 'SomeError'}}]
    }
    webhooks_instance.client.post_request = AsyncMock(return_value=error_response)

    with pytest.raises(MondayAPIError) as exc_info:
        await webhooks_instance.query(board_id=1)
    assert exc_info.value.json == error_response


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_with_config_serializes_json(webhooks_instance: Webhooks):
    """Test that create serializes config to JSON variables and returns Webhook."""
    mock_response = {
        'data': {
            'create_webhook': {
                'id': '999',
                'event': 'create_item',
                'board_id': '321',
                'config': {'x': 1},
            }
        }
    }
    webhooks_instance.client.post_request = AsyncMock(return_value=mock_response)

    config = {'x': 1}
    result = await webhooks_instance.create(
        board_id=321,
        url='https://example.com/hook',
        event='create_item',
        config=config,
    )

    assert isinstance(result, Webhook)
    assert result.id == '999'
    assert result.event == 'create_item'
    assert result.board_id == '321'
    assert result.config == {'x': 1}

    # Validate variables passed to post_request
    called_args = webhooks_instance.client.post_request.call_args.args
    assert isinstance(called_args[0], str)
    assert 'create_webhook' in called_args[0]
    assert len(called_args) == 2  # operation, variables
    variables = called_args[1]
    assert isinstance(variables, dict)
    assert variables['boardId'] == '321'
    assert variables['url'] == 'https://example.com/hook'
    assert variables['event'] == 'create_item'
    # config is json-dumped string
    assert isinstance(variables['config'], str)
    assert json.loads(variables['config']) == config


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_without_config_excludes_variable(webhooks_instance: Webhooks):
    """Test that create does not include config when not provided."""
    mock_response = {
        'data': {
            'create_webhook': {
                'id': '1',
                'event': 'create_item',
                'board_id': '100',
                'config': None,
            }
        }
    }
    webhooks_instance.client.post_request = AsyncMock(return_value=mock_response)

    await webhooks_instance.create(
        board_id=100,
        url='https://example.com/hook',
        event='create_item',
    )

    called_args = webhooks_instance.client.post_request.call_args.args
    variables = called_args[1]
    assert 'config' not in variables


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_with_api_error(webhooks_instance: Webhooks):
    """Test that create propagates MondayAPIError on error responses."""
    error_response = {
        'errors': [{'message': 'API Error', 'extensions': {'code': 'SomeError'}}]
    }
    webhooks_instance.client.post_request = AsyncMock(return_value=error_response)

    with pytest.raises(MondayAPIError):
        await webhooks_instance.create(
            board_id=1, url='https://example.com', event='create_item'
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_delete_returns_webhook(webhooks_instance: Webhooks):
    """Test that delete returns a Webhook dataclass."""
    mock_response = {
        'data': {
            'delete_webhook': {
                'id': '5',
                'event': 'create_item',
                'board_id': '200',
                'config': None,
            }
        }
    }
    webhooks_instance.client.post_request = AsyncMock(return_value=mock_response)

    result = await webhooks_instance.delete(webhook_id='5')
    assert isinstance(result, Webhook)
    assert result.id == '5'
    assert result.board_id == '200'

    called_args = webhooks_instance.client.post_request.call_args.args
    assert 'delete_webhook' in called_args[0]
    variables = called_args[1]
    assert variables == {'webhookId': '5'}


@pytest.mark.asyncio
@pytest.mark.unit
async def test_delete_with_api_error(webhooks_instance: Webhooks):
    """Test that delete propagates MondayAPIError on error responses."""
    error_response = {
        'errors': [{'message': 'API Error', 'extensions': {'code': 'SomeError'}}]
    }
    webhooks_instance.client.post_request = AsyncMock(return_value=error_response)

    with pytest.raises(MondayAPIError):
        await webhooks_instance.delete(webhook_id='5')


@pytest.mark.unit
def test_webhook_from_dict_parses_config_string_dict():
    """Test that Webhook.from_dict parses config when it is a JSON string dict."""
    data = {
        'id': 1,
        'event': 'create_item',
        'board_id': 2,
        'config': '{"alpha": 42}',
    }
    wh = Webhook.from_dict(data)
    assert wh.id == '1'
    assert wh.event == 'create_item'
    assert wh.board_id == '2'
    assert isinstance(wh.config, dict)
    assert wh.config == {'alpha': 42}


@pytest.mark.unit
def test_webhook_from_dict_handles_invalid_config_string():
    """Test that invalid JSON config strings result in config=None."""
    data = {
        'id': '1',
        'event': 'create_item',
        'board_id': '2',
        'config': '{not json',
    }
    wh = Webhook.from_dict(data)
    assert wh.config is None
