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

"""Comprehensive tests for Items methods"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from monday.client import MondayClient
from monday.exceptions import MondayAPIError
from monday.services.boards import Boards
from monday.services.items import Items
from monday.types.column import ColumnValue
from monday.types.item import Item


@pytest.fixture(scope='module')
def mock_client():
    """Create mock MondayClient instance"""
    return MagicMock(spec=MondayClient)


@pytest.fixture(scope='module')
def mock_boards():
    """Create mock Boards instance"""
    boards = MagicMock(spec=Boards)
    boards.query = AsyncMock()
    return boards


@pytest.fixture(scope='module')
def items_instance(mock_client, mock_boards):
    """Create mock Items instance"""
    return Items(mock_client, mock_boards)


@pytest.mark.asyncio
async def test_query(items_instance):
    """Test basic item query functionality."""
    mock_responses = [
        {'data': {'items': [{'id': '1', 'name': 'Item 1'}, {'id': '2', 'name': 'Item 2'}]}},
        {'data': {'items': []}}
    ]

    items_instance.client.post_request = AsyncMock(side_effect=mock_responses)
    result = await items_instance.query(item_ids=['1', '2'])

    assert result[0].id == '1' and result[0].name == 'Item 1'
    assert result[1].id == '2' and result[1].name == 'Item 2'
    assert items_instance.client.post_request.await_count == 2


@pytest.mark.asyncio
async def test_query_with_api_error(items_instance):
    """Test handling of API errors in query method."""
    error_response = {
        'errors': [{
            'message': 'API Error',
            'extensions': {'code': 'SomeError'}
        }]
    }

    items_instance.client.post_request = AsyncMock(return_value=error_response)
    with pytest.raises(MondayAPIError) as exc_info:
        await items_instance.query(item_ids=['1'])
    assert exc_info.value.json == error_response


@pytest.mark.asyncio
async def test_query_with_complexity_error(items_instance):
    """Test handling of complexity limit errors."""
    error_response = {
        'error_code': 'ComplexityException',
        'error_message': 'Complexity limit exceeded. Please retry in 30.5 seconds',
        'status_code': 400
    }

    items_instance.client.post_request = AsyncMock(side_effect=[error_response, {'data': {'items': []}}])
    with pytest.raises(MondayAPIError) as exc_info:
        await items_instance.query(item_ids=['1'])
    assert exc_info.value.json == error_response


@pytest.mark.asyncio
async def test_query_with_rate_limit_error(items_instance):
    """Test handling of rate limit errors."""
    error_response = {
        'errors': [{
            'message': 'Rate limit exceeded'
        }],
        'status_code': 429
    }

    items_instance.client.post_request = AsyncMock(side_effect=[error_response, {'data': {'items': []}}])
    with pytest.raises(MondayAPIError) as exc_info:
        await items_instance.query(item_ids=['1'])
    assert exc_info.value.json == error_response


@pytest.mark.asyncio
async def test_create(items_instance):
    """Test creating a new item."""
    mock_response = {
        'data': {
            'create_item': {'id': '1', 'name': 'New Item'}
        }
    }

    items_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await items_instance.create(board_id='1', item_name='New Item')

    assert result.id == '1' and result.name == 'New Item'
    items_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_with_invalid_input(items_instance):
    """Test create method with invalid input."""
    error_response = {
        'errors': [{
            'message': 'Invalid input',
            'extensions': {'code': 'argumentLiteralsIncompatible'}
        }]
    }

    items_instance.client.post_request = AsyncMock(return_value=error_response)
    with pytest.raises(MondayAPIError) as exc_info:
        await items_instance.create(board_id='1', item_name='Test')
    assert exc_info.value.json == error_response


@pytest.mark.asyncio
async def test_duplicate(items_instance):
    """Test duplicating an existing item."""
    mock_response = {
        'data': {
            'duplicate_item': {'id': '2', 'name': 'Item 1 (copy)'}
        }
    }

    items_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await items_instance.duplicate(item_id='1', board_id='1')

    assert result.id == '2' and result.name == 'Item 1 (copy)'
    items_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_move_to_group(items_instance):
    """Test moving item to a different group."""
    mock_response = {
        'data': {
            'move_item_to_group': {'id': '1', 'group': {'id': 'new_group'}}
        }
    }

    items_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await items_instance.move_to_group(item_id='1', group_id='new_group')

    assert result.id == '1' and result.group.id == 'new_group'
    items_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_move_to_board(items_instance):
    """Test moving item to a different board."""
    mock_response = {
        'data': {
            'move_item_to_board': {'id': '1', 'board': {'id': '2'}}
        }
    }

    items_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await items_instance.move_to_board(
        item_id='1',
        board_id='2',
        group_id='new_group',
        columns_mapping=None,
        subitems_columns_mapping=None
    )

    assert result.id == '1' and result.board.id == '2'
    items_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_archive(items_instance):
    """Test archiving an item."""
    mock_response = {
        'data': {
            'archive_item': {'id': '1', 'state': 'archived'}
        }
    }

    items_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await items_instance.archive(item_id='1')

    assert result.id == '1' and result.state == 'archived'
    items_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete(items_instance):
    """Test deleting an item."""
    mock_response = {
        'data': {
            'delete_item': {'id': '1', 'state': 'deleted'}
        }
    }

    items_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await items_instance.delete(item_id='1')

    assert result.id == '1' and result.state == 'deleted'
    items_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_clear_updates(items_instance):
    """Test clearing item updates."""
    mock_response = {
        'data': {
            'clear_item_updates': {'id': '1'}
        }
    }
    items_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await items_instance.clear_updates(item_id='1')
    assert result.id == '1'
    items_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_column_values(items_instance):
    """Test retrieving column values for a specific item."""
    mock_response = {
        'data': {
            'items': [{
                'column_values': [
                    {'id': 'status', 'text': 'Done'},
                    {'id': 'text', 'text': 'Test content'}
                ]
            }]
        }
    }

    items_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await items_instance.get_column_values(
        item_id='1',
        column_ids=['status', 'text'],
        fields='id text'
    )

    assert result[0].id == 'status' and result[0].text == 'Done'
    assert result[1].id == 'text' and result[1].text == 'Test content'
    items_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_column_values_empty_response(items_instance):
    """Test handling empty response when getting column values."""
    mock_response = {
        'data': {
            'items': []
        }
    }

    items_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await items_instance.get_column_values(item_id='1')

    assert result == []
    items_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_change_column_values(items_instance):
    """Test changing column values for an item."""
    # First response is for the query to get board ID
    mock_query_response = {
        'data': {
            'items': [{
                'board': {'id': '123'}
            }]
        }
    }

    # Empty response to break the query loop
    mock_empty_response = {
        'data': {
            'items': []
        }
    }

    # Response for the actual column value change
    mock_change_response = {
        'data': {
            'change_multiple_column_values': {
                'id': '1',
                'text': 'Updated content',
                'additional_info': '',
                'title': '',
                'type': '',
                'value': ''
            }
        }
    }

    # Set up the mock to return all responses in sequence
    items_instance.client.post_request = AsyncMock(side_effect=[
        mock_query_response,  # First query response
        mock_empty_response,  # Empty response to break query loop
        mock_change_response  # Column value change response
    ])

    result = await items_instance.change_column_values(
        item_id='1',
        column_values={
            'status': 'In Progress',
            'text': 'Updated content'
        },
        fields='id text'
    )

    assert isinstance(result, ColumnValue)
    assert result.id == '1'
    assert result.text == 'Updated content'
    assert items_instance.client.post_request.await_count == 3


@pytest.mark.asyncio
async def test_get_name(items_instance):
    """Test retrieving item name by ID."""
    mock_response = {
        'data': {
            'items': [{
                'name': 'Test Item'
            }]
        }
    }

    items_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await items_instance.get_name(item_id='1')

    assert result == 'Test Item'
    items_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_id(items_instance):
    """Test retrieving item IDs by name."""
    mock_response = [Item(id='123'), Item(id='456')]
    items_instance.boards.get_items_by_column_values = AsyncMock(return_value=mock_response)
    result = await items_instance.get_id(board_id='1', item_name='Test Item')
    assert result == ['123', '456']
    items_instance.boards.get_items_by_column_values.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_id_no_matches(items_instance):
    """Test retrieving item IDs when no matches found."""
    mock_response = []

    items_instance.boards.get_items_by_column_values = AsyncMock(return_value=mock_response)
    result = await items_instance.get_id(board_id='1', item_name='Nonexistent Item')

    assert result == []
    items_instance.boards.get_items_by_column_values.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_with_column_values(items_instance):
    """Test creating an item with column values."""
    mock_response = {
        'data': {
            'create_item': {
                'id': '1',
                'name': 'New Item',
                'column_values': [
                    {'id': 'status', 'text': 'Done'},
                    {'id': 'text', 'text': 'Test content'}
                ]
            }
        }
    }

    items_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await items_instance.create(
        board_id='1',
        item_name='New Item',
        column_values={
            'status': 'Done',
            'text': 'Test content'
        },
        fields='id name column_values { id text }'
    )

    assert result.id == '1' and result.name == 'New Item'
    assert result.column_values[0].id == 'status' and result.column_values[0].text == 'Done'
    assert result.column_values[1].id == 'text' and result.column_values[1].text == 'Test content'
    items_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_duplicate_with_updates_and_new_name(items_instance):
    """Test duplicating an item with updates and new name."""
    mock_responses = [
        # First response for duplicate_item
        {
            'data': {
                'duplicate_item': {'id': '2'}
            }
        },
        # Second response for getting board ID (from change_column_values)
        {
            'data': {
                'items': [{
                    'board': {'id': '123'}
                }]
            }
        },
        # Empty response to break query loop (from change_column_values)
        {
            'data': {
                'items': []
            }
        },
        # Fourth response for change_multiple_column_values
        {
            'data': {
                'change_multiple_column_values': {
                    'id': '2',
                    'name': 'New Name',
                    'column_values': []
                }
            }
        },
        # Fifth response for final query to get complete item
        {
            'data': {
                'items': [{
                    'id': '2',
                    'name': 'New Name',
                    'column_values': []
                }]
            }
        },
        # Empty response to break final query loop
        {
            'data': {
                'items': []
            }
        }
    ]

    items_instance.client.post_request = AsyncMock(side_effect=mock_responses)
    result = await items_instance.duplicate(
        item_id='1',
        board_id='1',
        with_updates=True,
        new_item_name='New Name',
        fields='id name column_values { id text }'
    )

    assert result.name == 'New Name'
    assert items_instance.client.post_request.await_count == 6


@pytest.mark.asyncio
async def test_move_to_group_with_invalid_group(items_instance):
    """Test moving item to invalid group."""
    error_response = {
        'errors': [{
            'message': 'Group not found',
            'extensions': {'code': 'InvalidGroup'}
        }]
    }

    items_instance.client.post_request = AsyncMock(return_value=error_response)
    with pytest.raises(MondayAPIError) as exc_info:
        await items_instance.move_to_group(item_id='1', group_id='invalid_group')
    assert exc_info.value.json == error_response


@pytest.mark.asyncio
async def test_move_to_board_with_column_mapping(items_instance):
    """Test moving item to different board with column mapping."""
    mock_response = {
        'data': {
            'move_item_to_board': {
                'id': '1',
                'board': {'id': '2'},
                'column_values': [
                    {'id': 'new_status', 'text': 'Done'},
                    {'id': 'new_text', 'text': 'Mapped content'}
                ]
            }
        }
    }

    items_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await items_instance.move_to_board(
        item_id='1',
        board_id='2',
        group_id='new_group',
        columns_mapping=[
            {'from': 'old_status', 'to': 'new_status'},
            {'from': 'old_text', 'to': 'new_text'}
        ],
        fields='id board { id } column_values { id text }'
    )

    assert result.id == '1' and result.board.id == '2'
    assert result.column_values[0].id == 'new_status' and result.column_values[0].text == 'Done'
    assert result.column_values[1].id == 'new_text' and result.column_values[1].text == 'Mapped content'
    items_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_column_values_specific_columns(items_instance):
    """Test retrieving specific column values for an item."""
    mock_response = {
        'data': {
            'items': [{
                'column_values': [
                    {'id': 'status', 'text': 'Done'},
                    {'id': 'priority', 'text': 'High'}
                ]
            }]
        }
    }

    items_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await items_instance.get_column_values(
        item_id='1',
        column_ids=['status', 'priority'],
        fields='id text'
    )

    assert result[0].id == 'status' and result[0].text == 'Done'
    assert result[1].id == 'priority' and result[1].text == 'High'
    items_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_change_column_values_with_complex_values(items_instance):
    """Test changing column values with complex value types."""
    mock_responses = [
        # First response for getting board ID
        {
            'data': {
                'items': [{
                    'board': {'id': '123'}
                }]
            }
        },
        # Empty response to break query loop
        {
            'data': {
                'items': []
            }
        },
        # Third response for changing column values
        {
            'data': {
                'change_multiple_column_values': {
                    'id': '1',
                    'text': 'Done',
                    'additional_info': '',
                    'title': '',
                    'type': '',
                    'value': ''
                }
            }
        }
    ]

    items_instance.client.post_request = AsyncMock(side_effect=mock_responses)

    complex_values = {
        'status': {'label': 'Done'},
        'date': {'date': '2024-03-20'},
        'people': {'personsAndTeams': [{'id': 123, 'kind': 'person'}]}
    }

    result = await items_instance.change_column_values(
        item_id='1',
        column_values=complex_values,
        fields='id text'
    )

    assert isinstance(result, ColumnValue)
    assert result.id == '1'
    assert result.text == 'Done'
    assert items_instance.client.post_request.await_count == 3


@pytest.mark.asyncio
async def test_get_id_multiple_matches(items_instance):
    """Test getting IDs when multiple items match the name."""
    mock_items = [Item(id='123'), Item(id='456'), Item(id='789')]
    items_instance.boards.get_items_by_column_values = AsyncMock(return_value=mock_items)
    result = await items_instance.get_id(board_id='1', item_name='Duplicate Name')
    assert result == ['123', '456', '789']
