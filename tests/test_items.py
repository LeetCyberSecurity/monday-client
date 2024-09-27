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

# pylint: disable=redefined-outer-name

from unittest.mock import AsyncMock, MagicMock

import pytest

from monday.client import MondayClient
from monday.services.items import Items


@pytest.fixture(scope="module")
def mock_client():
    return MagicMock(spec=MondayClient)


@pytest.fixture(scope="module")
def items_instance(mock_client):
    return Items(mock_client)


@pytest.mark.asyncio
async def test_query(items_instance):
    mock_responses = [
        {'data': {'items': [{'id': 1, 'name': 'Item 1'}, {'id': 2, 'name': 'Item 2'}]}},
        {'data': {'items': []}}
    ]

    items_instance.client.post_request = AsyncMock(side_effect=mock_responses)
    result = await items_instance.query(item_ids=[1, 2])

    assert result == [{'id': 1, 'name': 'Item 1'}, {'id': 2, 'name': 'Item 2'}]
    assert items_instance.client.post_request.await_count == 2


@pytest.mark.asyncio
async def test_create(items_instance):
    mock_response = {
        'data': {
            'create_item': {'id': 1, 'name': 'New Item'}
        }
    }

    items_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await items_instance.create(board_id=1, item_name="New Item")

    assert result == {'id': 1, 'name': 'New Item'}
    items_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_duplicate(items_instance):
    mock_response = {
        'data': {
            'duplicate_item': {'id': 2, 'name': 'Item 1 (copy)'}
        }
    }

    items_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await items_instance.duplicate(item_id=1, board_id=1)

    assert result == {'id': 2, 'name': 'Item 1 (copy)'}
    items_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_move_to_group(items_instance):
    mock_response = {
        'data': {
            'move_item_to_group': {'id': 1, 'group': {'id': 'new_group'}}
        }
    }

    items_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await items_instance.move_to_group(item_id=1, group_id='new_group')

    assert result == {'id': 1, 'group': {'id': 'new_group'}}
    items_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_move_to_board(items_instance):
    mock_response = {
        'data': {
            'move_item_to_board': {'id': 1, 'board': {'id': 2}}
        }
    }

    items_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await items_instance.move_to_board(
        item_id=1,
        board_id=2,
        group_id='new_group',
        columns_mapping=None,
        subitems_columns_mapping=None
    )

    assert result == {'id': 1, 'board': {'id': 2}}
    items_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_archive(items_instance):
    mock_response = {
        'data': {
            'archive_item': {'id': 1, 'state': 'archived'}
        }
    }

    items_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await items_instance.archive(item_id=1)

    assert result == {'id': 1, 'state': 'archived'}
    items_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete(items_instance):
    mock_response = {
        'data': {
            'delete_item': {'id': 1, 'state': 'deleted'}
        }
    }

    items_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await items_instance.delete(item_id=1)

    assert result == {'id': 1, 'state': 'deleted'}
    items_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_clear_updates(items_instance):
    mock_response = {
        'data': {
            'clear_item_updates': {'id': 1, 'updates_cleared': True}
        }
    }

    items_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await items_instance.clear_updates(item_id=1)

    assert result == {'id': 1, 'updates_cleared': True}
    items_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_items_page_by_column_values(items_instance):
    mock_responses = [{
        'data': {
            'items_page_by_column_values': {
                'cursor': None,
                'items': [
                    {'id': 1, 'name': 'Item 1'},
                    {'id': 2, 'name': 'Item 2'}
                ]
            }
        }
    }]

    items_instance.client.post_request = AsyncMock(side_effect=mock_responses)
    result = await items_instance.items_page_by_column_values(
        board_id=1,
        columns=[{'column_id': 'status', 'column_values': ['Done']}],
        limit=2
    )

    assert result == {'items': [{'id': 1, 'name': 'Item 1'}, {'id': 2, 'name': 'Item 2'}]}
    items_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_items_page(items_instance):
    mock_response = {
        'data': {
            'boards': [
                {
                    'id': 1,
                    'items_page': {
                        'cursor': None,
                        'items': [
                            {'id': 1, 'name': 'Item 1'},
                            {'id': 2, 'name': 'Item 2'}
                        ]
                    }
                }
            ]
        }
    }

    items_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await items_instance.items_page(board_ids=1, limit=2)

    assert result == [{'board_id': 1, 'items': [{'id': 1, 'name': 'Item 1'}, {'id': 2, 'name': 'Item 2'}]}]
    items_instance.client.post_request.assert_awaited_once()