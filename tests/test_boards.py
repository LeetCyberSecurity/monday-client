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

"""Comprehensive tests for Boards methods"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from monday.client import MondayClient
from monday.exceptions import MondayAPIError
from monday.services.boards import Boards


@pytest.fixture(scope='module')
def mock_client():
    """Create a mock MondayClient instance"""
    return MagicMock(spec=MondayClient)


@pytest.fixture(scope='module')
def boards_instance(mock_client):
    """Create a mock Boards instance"""
    return Boards(mock_client)


@pytest.mark.asyncio
async def test_query(boards_instance: Boards):
    """Test basic board query functionality."""
    mock_responses = [
        {'data': {'boards': [{'id': 1, 'name': 'Board 1'}, {'id': 2, 'name': 'Board 2'}]}},
        {'data': {'boards': [{'id': 3, 'name': 'Board 3'}]}},
        {'data': {'boards': []}}
    ]

    boards_instance.client.post_request = AsyncMock(side_effect=mock_responses)
    result = await boards_instance.query(board_ids=[1, 2, 3], boards_limit=2)

    assert result == [{'id': 1, 'name': 'Board 1'}, {'id': 2, 'name': 'Board 2'}, {'id': 3, 'name': 'Board 3'}]
    assert boards_instance.client.post_request.await_count == 3


@pytest.mark.asyncio
async def test_query_with_api_error(boards_instance: Boards):
    """Test handling of API errors in query method."""
    error_response = {
        'errors': [{
            'message': 'API Error',
            'extensions': {'code': 'SomeError'}
        }]
    }

    boards_instance.client.post_request = AsyncMock(return_value=error_response)
    with pytest.raises(MondayAPIError) as exc_info:
        await boards_instance.query(board_ids=[1])
    assert exc_info.value.json == error_response


@pytest.mark.asyncio
async def test_get_items(boards_instance: Boards):
    """Test retrieving items from multiple boards."""
    mock_response = {
        'data': {
            'boards': [
                {
                    'id': 1,
                    'items_page': {
                        'cursor': None,  # Add cursor to prevent pagination
                        'items': [
                            {'id': '101', 'name': 'Item 1'},
                            {'id': '102', 'name': 'Item 2'}
                        ]
                    }
                },
                {
                    'id': 2,
                    'items_page': {
                        'cursor': None,  # Add cursor to prevent pagination
                        'items': [
                            {'id': '201', 'name': 'Item 3'}
                        ]
                    }
                }
            ]
        }
    }

    # Mock the query method to return empty boards after first call
    mock_empty_response = {'data': {'boards': []}}
    boards_instance.client.post_request = AsyncMock(side_effect=[mock_response, mock_empty_response])

    result = await boards_instance.get_items(
        board_ids=[1, 2],
        fields='id name'
    )

    expected = [
        {
            'id': 1,
            'items': [
                {'id': '101', 'name': 'Item 1'},
                {'id': '102', 'name': 'Item 2'}
            ]
        },
        {
            'id': 2,
            'items': [
                {'id': '201', 'name': 'Item 3'}
            ]
        }
    ]

    assert result == expected
    assert boards_instance.client.post_request.await_count == 2


@pytest.mark.asyncio
async def test_get_items_with_group(boards_instance: Boards):
    """Test retrieving items from a specific board group."""
    mock_response = {
        'data': {
            'boards': [
                {
                    'id': 1,
                    'groups': [
                        {
                            'items_page': {
                                'cursor': None,  # Add cursor to prevent pagination
                                'items': [
                                    {'id': '101', 'name': 'Item 1'},
                                    {'id': '102', 'name': 'Item 2'}
                                ]
                            }
                        }
                    ]
                }
            ]
        }
    }

    # Mock the query method to return empty boards after first call
    mock_empty_response = {'data': {'boards': []}}
    boards_instance.client.post_request = AsyncMock(side_effect=[mock_response, mock_empty_response])

    result = await boards_instance.get_items(
        board_ids=1,
        group_id='group1',
        fields='id name'
    )

    expected = [
        {
            'id': 1,
            'items': [
                {'id': '101', 'name': 'Item 1'},
                {'id': '102', 'name': 'Item 2'}
            ]
        }
    ]

    assert result == expected
    assert boards_instance.client.post_request.await_count == 2


@pytest.mark.asyncio
async def test_get_items_with_empty_group(boards_instance: Boards):
    """Test retrieving items from an empty board group."""
    mock_response = {
        'data': {
            'boards': [
                {
                    'id': 1,
                    'groups': []
                }
            ]
        }
    }

    # Mock the query method to return empty boards after first call
    mock_empty_response = {'data': {'boards': []}}
    boards_instance.client.post_request = AsyncMock(side_effect=[mock_response, mock_empty_response])

    result = await boards_instance.get_items(
        board_ids=1,
        group_id='group1',
        fields='id name'
    )

    expected = [
        {
            'id': 1,
            'items': []
        }
    ]

    assert result == expected
    assert boards_instance.client.post_request.await_count == 2


@pytest.mark.asyncio
async def test_get_items_with_query_params(boards_instance: Boards):
    """Test retrieving items with query parameter filtering."""
    mock_response = {
        'data': {
            'boards': [
                {
                    'id': 1,
                    'items_page': {
                        'cursor': None,  # Add cursor to prevent pagination
                        'items': [
                            {'id': '101', 'status': 'Done'}
                        ]
                    }
                }
            ]
        }
    }

    query_params = {
        'rules': [
            {
                'column_id': 'status',
                'compare_value': ['Done'],
                'operator': 'contains_terms'
            }
        ]
    }

    # Mock the query method to return empty boards after first call
    mock_empty_response = {'data': {'boards': []}}
    boards_instance.client.post_request = AsyncMock(side_effect=[mock_response, mock_empty_response])

    result = await boards_instance.get_items(
        board_ids=1,
        query_params=query_params,
        fields='id status'
    )

    expected = [
        {
            'id': 1,
            'items': [
                {'id': '101', 'status': 'Done'}
            ]
        }
    ]

    assert result == expected
    assert boards_instance.client.post_request.await_count == 2


@pytest.mark.asyncio
async def test_get_items_by_column_values(boards_instance: Boards):
    """Test retrieving items filtered by column values."""
    mock_response = {
        'data': {
            'items_page_by_column_values': {
                'cursor': None,
                'items': [
                    {
                        'id': '101',
                        'name': 'Item 1',
                        'column_values': [
                            {'id': 'status', 'text': 'Done'},
                            {'id': 'priority', 'text': 'High'}
                        ]
                    },
                    {
                        'id': '102',
                        'name': 'Item 2',
                        'column_values': [
                            {'id': 'status', 'text': 'Done'},
                            {'id': 'priority', 'text': 'Low'}
                        ]
                    }
                ]
            }
        }
    }

    boards_instance.client.post_request = AsyncMock(return_value=mock_response)

    result = await boards_instance.get_items_by_column_values(
        board_id=1,
        columns=[
            {
                'column_id': 'status',
                'column_values': ['Done']
            },
            {
                'column_id': 'priority',
                'column_values': ['High', 'Low']
            }
        ],
        fields='id name column_values { id text }'
    )

    expected = mock_response['data']['items_page_by_column_values']['items']
    assert result == expected
    boards_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_items_by_column_values_with_pagination(boards_instance: Boards):
    """Test paginated retrieval of items filtered by column values."""
    mock_responses = [
        {
            'data': {
                'items_page_by_column_values': {
                    'cursor': 'next_page',
                    'items': [{'id': '101', 'name': 'Item 1'}]
                }
            }
        },
        {
            'data': {
                'items_page_by_column_values': {
                    'cursor': None,
                    'items': [{'id': '102', 'name': 'Item 2'}]
                }
            }
        }
    ]

    boards_instance.client.post_request = AsyncMock(side_effect=mock_responses)

    result = await boards_instance.get_items_by_column_values(
        board_id=1,
        columns=[{'column_id': 'status', 'column_values': ['Done']}],
        paginate_items=True
    )

    expected = [
        {'id': '101', 'name': 'Item 1'},
        {'id': '102', 'name': 'Item 2'}
    ]
    assert result == expected
    assert boards_instance.client.post_request.await_count == 2


@pytest.mark.asyncio
async def test_get_column_values(boards_instance: Boards):
    """Test retrieving column values for board items."""
    mock_response = [
        {
            'id': 1,
            'items': [
                {
                    'id': '101',
                    'name': 'Item 1',
                    'column_values': [
                        {'id': 'status', 'text': 'Done'},
                        {'id': 'priority', 'text': 'High'}
                    ]
                },
                {
                    'id': '102',
                    'name': 'Item 2',
                    'column_values': [
                        {'id': 'status', 'text': 'In Progress'},
                        {'id': 'priority', 'text': 'Low'}
                    ]
                }
            ]
        }
    ]

    boards_instance.get_items = AsyncMock(return_value=mock_response)

    result = await boards_instance.get_column_values(
        board_id=1,
        column_ids=['status', 'priority'],
        column_fields='id text',
        item_fields='id name'
    )

    expected = mock_response[0]['items']
    assert result == expected
    boards_instance.get_items.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_column_values_with_existing_column_values(boards_instance: Boards):
    """Test get_column_values with pre-existing column_values field."""
    mock_response = [
        {
            'id': 1,
            'items': [
                {
                    'id': '101',
                    'name': 'Item 1',
                    'column_values': [
                        {'id': 'status', 'text': 'Done'}
                    ]
                }
            ]
        }
    ]

    boards_instance.get_items = AsyncMock(return_value=mock_response)

    result = await boards_instance.get_column_values(
        board_id=1,
        column_ids=['status'],
        item_fields='id name column_values { id text }'
    )

    expected = mock_response[0]['items']
    assert result == expected
    boards_instance.get_items.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_column_values_error_handling(boards_instance: Boards):
    """Test error handling in get_column_values method."""
    error_response = {
        'errors': [{
            'message': 'Column not found',
            'extensions': {'code': 'InvalidColumnId'}
        }]
    }

    boards_instance.get_items = AsyncMock(return_value=error_response)

    with pytest.raises(MondayAPIError) as exc_info:
        await boards_instance.get_column_values(
            board_id=1,
            column_ids=['invalid_column']
        )
    assert exc_info.value.json == error_response


@pytest.mark.asyncio
async def test_create(boards_instance: Boards):
    """Test board creation."""
    mock_response = {
        'data': {
            'create_board': {'id': 1, 'name': 'New Board'}
        }
    }

    boards_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await boards_instance.create(name='New Board')

    assert result == {'id': 1, 'name': 'New Board'}
    boards_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_duplicate(boards_instance: Boards):
    """Test board duplication."""
    mock_response = {
        'data': {
            'duplicate_board': {'board': {'id': 2}}
        }
    }

    boards_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await boards_instance.duplicate(board_id=1)

    assert result == {'id': 2}
    boards_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_update(boards_instance: Boards):
    """Test board attribute updates."""
    mock_response = {
        'data': {
            'update_board': '{"id": 1, "name": "Updated Board"}'
        }
    }

    boards_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await boards_instance.update(board_id=1, board_attribute='name', new_value='Updated Board')

    assert result == {'id': 1, 'name': 'Updated Board'}
    boards_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_archive(boards_instance: Boards):
    """Test board archival."""
    mock_response = {
        'data': {
            'archive_board': {'id': 1, 'state': 'archived'}
        }
    }

    boards_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await boards_instance.archive(board_id=1)

    assert result == {'id': 1, 'state': 'archived'}
    boards_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete(boards_instance: Boards):
    """Test board deletion."""
    mock_response = {
        'data': {
            'delete_board': {'id': 1, 'state': 'deleted'}
        }
    }

    boards_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await boards_instance.delete(board_id=1)

    assert result == {'id': 1, 'state': 'deleted'}
    boards_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_query_with_items_pagination(boards_instance: Boards):
    """Test query method with items pagination."""
    mock_responses = [
        # First response - initial board query
        {
            'data': {
                'boards': [{
                    'id': 1,
                    'items_page': {
                        'cursor': 'next_page',
                        'items': [{'id': '101'}]
                    }
                }]
            }
        },
        # Second response - next_items_page query
        {
            'data': {
                'next_items_page': {
                    'cursor': None,  # No more pages
                    'items': [{'id': '102'}]
                }
            }
        },
        # Third response - final empty boards query to end pagination
        {
            'data': {
                'boards': []
            }
        }
    ]

    boards_instance.client.post_request = AsyncMock(side_effect=mock_responses)
    result = await boards_instance.query(
        board_ids=1,
        paginate_items=True,
        fields='id items_page { items { id } }'
    )

    assert len(result) == 1
    assert result[0]['id'] == 1
    assert len(result[0]['items_page']['items']) == 2
    assert result[0]['items_page']['items'][0]['id'] == '101'
    assert result[0]['items_page']['items'][1]['id'] == '102'
    assert boards_instance.client.post_request.await_count == 3


@pytest.mark.asyncio
async def test_query_with_workspace_ids(boards_instance: Boards):
    """Test query method with workspace filtering."""
    mock_responses = [
        {
            'data': {
                'boards': [{
                    'id': 1,
                    'workspace_id': 100
                }]
            }
        },
        {
            'data': {
                'boards': []  # Empty response to end pagination
            }
        }
    ]

    boards_instance.client.post_request = AsyncMock(side_effect=mock_responses)
    result = await boards_instance.query(workspace_ids=100)

    assert result[0]['workspace_id'] == 100
    assert boards_instance.client.post_request.await_count == 2


@pytest.mark.asyncio
async def test_create_with_all_parameters(boards_instance: Boards):
    """Test board creation with all optional parameters."""
    mock_response = {
        'data': {
            'create_board': {
                'id': 1,
                'name': 'New Board',
                'board_kind': 'private',
                'description': 'Test board',
                'workspace_id': 100
            }
        }
    }

    boards_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await boards_instance.create(
        name='New Board',
        board_kind='private',
        owner_ids=[1, 2],
        subscriber_ids=[3, 4],
        subscriber_teams_ids=[5, 6],
        description='Test board',
        folder_id=200,
        template_id=300,
        workspace_id=100
    )

    assert result['board_kind'] == 'private'
    assert result['description'] == 'Test board'
    assert result['workspace_id'] == 100
    boards_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_duplicate_with_all_parameters(boards_instance: Boards):
    """Test board duplication with all optional parameters."""
    mock_response = {
        'data': {
            'duplicate_board': {
                'board': {
                    'id': 2,
                    'name': 'Duplicated Board',
                    'workspace_id': 100
                }
            }
        }
    }

    boards_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await boards_instance.duplicate(
        board_id=1,
        board_name='Duplicated Board',
        duplicate_type='with_pulses_and_updates',
        folder_id=200,
        keep_subscribers=True,
        workspace_id=100
    )

    assert result['name'] == 'Duplicated Board'
    assert result['workspace_id'] == 100
    boards_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_with_non_json_response(boards_instance: Boards):
    """Test update method with non-JSON response."""
    mock_response = {
        'data': {
            'update_board': {'id': 1, 'name': 'Updated Board'}  # Direct dict instead of JSON string
        }
    }

    boards_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await boards_instance.update(
        board_id=1,
        board_attribute='name',
        new_value='Updated Board'
    )

    assert result['name'] == 'Updated Board'
    boards_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_items_by_column_values_without_pagination(boards_instance: Boards):
    """Test retrieving items by column values without pagination."""
    mock_response = {
        'data': {
            'items_page_by_column_values': {
                'items': [{'id': '101', 'name': 'Item 1'}]
            }
        }
    }

    boards_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await boards_instance.get_items_by_column_values(
        board_id=1,
        columns=[{'column_id': 'status', 'column_values': ['Done']}],
        paginate_items=False
    )

    assert len(result) == 1
    assert result[0]['id'] == '101'
    boards_instance.client.post_request.assert_awaited_once()
