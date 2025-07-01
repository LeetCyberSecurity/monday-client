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

"""Tests for pagination utilities."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from monday.exceptions import PaginationError
from monday.services.utils.pagination import (extract_cursor_from_response,
                                              extract_items_from_query,
                                              extract_items_from_response,
                                              extract_items_page_value,
                                              paginated_item_request)


def test_extract_items_page_value_dict():
    """Test extracting items_page from dictionary."""
    data = {
        'boards': {
            'items_page': {'items': [1, 2, 3]}
        }
    }
    result = extract_items_page_value(data)
    assert result == {'items': [1, 2, 3]}


def test_extract_items_page_value_nested_dict():
    """Test extracting items_page from nested dictionary."""
    data = {
        'data': {
            'boards': {
                'some_key': {
                    'items_page': {'items': [1, 2, 3]}
                }
            }
        }
    }
    result = extract_items_page_value(data)
    assert result == {'items': [1, 2, 3]}


def test_extract_items_page_value_list():
    """Test extracting items_page from list."""
    data = [
        {'other': 'value'},
        {'items_page': {'items': [1, 2, 3]}},
        {'more': 'data'}
    ]
    result = extract_items_page_value(data)
    assert result == {'items': [1, 2, 3]}


def test_extract_items_page_value_not_found():
    """Test when items_page is not found."""
    data = {'some': 'data', 'nested': {'more': 'data'}}
    result = extract_items_page_value(data)
    assert result is None


def test_extract_cursor_from_response_dict():
    """Test extracting cursor from dictionary."""
    data = {
        'next_items_page': {
            'cursor': 'abc123'
        }
    }
    result = extract_cursor_from_response(data)
    assert result == 'abc123'


def test_extract_cursor_from_response_nested():
    """Test extracting cursor from nested structure."""
    data = {
        'data': {
            'boards': [
                {
                    'items_page': {
                        'cursor': 'abc123'
                    }
                }
            ]
        }
    }
    result = extract_cursor_from_response(data)
    assert result == 'abc123'


def test_extract_cursor_from_response_not_found():
    """Test when cursor is not found."""
    data = {'some': 'data', 'nested': {'more': 'data'}}
    result = extract_cursor_from_response(data)
    assert result is None


def test_extract_items_from_response_direct_items():
    """Test extracting items from direct items key."""
    data = {
        'items': [
            {'id': 1, 'name': 'Item 1'},
            {'id': 2, 'name': 'Item 2'}
        ]
    }
    result = extract_items_from_response(data)
    assert result == [{'id': 1, 'name': 'Item 1'}, {'id': 2, 'name': 'Item 2'}]


def test_extract_items_from_response_nested():
    """Test extracting items from nested structure."""
    data = {
        'data': {
            'boards': {
                'items': [
                    {'id': 1, 'name': 'Item 1'},
                    {'id': 2, 'name': 'Item 2'}
                ]
            }
        }
    }
    result = extract_items_from_response(data)
    assert result == [{'id': 1, 'name': 'Item 1'}, {'id': 2, 'name': 'Item 2'}]


def test_extract_items_from_response_multiple_items():
    """Test extracting items from multiple items arrays."""
    data = {
        'board1': {
            'items': [{'id': 1}]
        },
        'board2': {
            'items': [{'id': 2}]
        }
    }
    result = extract_items_from_response(data)
    assert result == [{'id': 1}, {'id': 2}]


def test_extract_items_from_response_empty():
    """Test extracting items when no items are present."""
    data = {'some': 'data', 'nested': {'more': 'data'}}
    result = extract_items_from_response(data)
    assert result == []


def test_extract_items_from_query_simple():
    """Test extracting items block from simple query."""
    query = '''
    query {
        items {
            id
            name
        }
    }
    '''
    result = extract_items_from_query(query)
    assert result is not None
    assert 'items {' in result
    assert 'id' in result
    assert 'name' in result


def test_extract_items_from_query_complex():
    """Test extracting items block from complex query."""
    query = '''
    query {
        boards {
            items {
                id
                name
                column_values {
                    id
                    value
                }
            }
        }
    }
    '''
    result = extract_items_from_query(query)
    assert result is not None
    assert 'items {' in result
    assert 'column_values' in result


def test_extract_items_from_query_no_items():
    """Test when no items block is present."""
    query = '''
    query {
        boards {
            id
            name
        }
    }
    '''
    result = extract_items_from_query(query)
    assert result is None


def test_extract_items_from_query_unbalanced_braces():
    """Test with unbalanced braces in query."""
    query = '''
    query {
        items {
            id
            name
    '''
    result = extract_items_from_query(query)
    assert result is None


@pytest.mark.asyncio
async def test_paginated_item_request_single_page():
    """Test paginated request with single page of results."""
    mock_client = MagicMock()
    mock_client.post_request = AsyncMock(return_value={
        'data': {
            'boards': [{
                'id': '1',
                'items_page': {
                    'items': [{'id': 1}, {'id': 2}],
                    'cursor': None
                }
            }]
        }
    })

    result = await paginated_item_request(
        client=mock_client,
        query='query { boards { id items_page { items { id } } } }',
        limit=25
    )

    assert len(result.items) == 1
    assert result.items[0]['board_id'] == '1'
    assert len(result.items[0]['items']) == 2
    assert result.items[0]['items'][0]['id'] == 1
    assert result.items[0]['items'][1]['id'] == 2
    assert mock_client.post_request.await_count == 1


@pytest.mark.asyncio
async def test_paginated_item_request_multiple_pages():
    """Test paginated request with multiple pages."""
    mock_client = MagicMock()
    mock_client.post_request = AsyncMock(side_effect=[
        {
            'data': {
                'boards': [{
                    'id': '1',
                    'items_page': {
                        'items': [{'id': 1}],
                        'cursor': 'next_page'
                    }
                }]
            }
        },
        {
            'data': {
                'boards': [{
                    'id': '1',
                    'items_page': {
                        'items': [{'id': 2}],
                        'cursor': None
                    }
                }]
            }
        }
    ])

    result = await paginated_item_request(
        client=mock_client,
        query='query { boards { id items_page { items { id } } } }',
        limit=25
    )

    assert len(result.items) == 1
    assert result.items[0]['board_id'] == '1'
    assert len(result.items[0]['items']) == 2
    assert result.items[0]['items'][0]['id'] == 1
    assert result.items[0]['items'][1]['id'] == 2
    assert mock_client.post_request.await_count == 2


@pytest.mark.asyncio
async def test_paginated_item_request_error():
    """Test handling of errors in paginated request."""
    mock_client = MagicMock()
    mock_client.post_request = AsyncMock(return_value={
        'error': 'Some error occurred'
    })

    result = await paginated_item_request(
        client=mock_client,
        query='query { items { id } }',
        limit=25
    )

    assert len(result.items) == 0
    assert mock_client.post_request.await_count == 1


@pytest.mark.asyncio
async def test_paginated_item_request_extraction_failure():
    """Test handling of item extraction failure."""
    mock_client = MagicMock()
    mock_client.post_request = AsyncMock(return_value={
        'data': {
            'boards': [{
                'id': '1',
                'items_page': None  # This will cause extraction failure
            }]
        }
    })

    with pytest.raises(PaginationError) as exc_info:
        await paginated_item_request(
            client=mock_client,
            query='query { boards { id items_page { items { id } } } }',  # Match the expected query format
            limit=25,
            cursor='some_cursor'
        )

    assert str(exc_info.value) == 'Item pagination failed'
    assert mock_client.post_request.await_count == 1


@pytest.mark.asyncio
async def test_paginated_item_request_with_custom_cursor():
    """Test paginated request with custom starting cursor."""
    mock_client = MagicMock()
    mock_client.post_request = AsyncMock(return_value={
        'data': {
            'next_items_page': {
                'items': [{'id': 1}],
                'cursor': None
            }
        }
    })

    result = await paginated_item_request(
        client=mock_client,
        query='query { items { id } }',
        limit=25,
        cursor='custom_cursor'
    )

    assert len(result.items) == 1
    assert result.items[0]['id'] == 1
    assert mock_client.post_request.await_count == 1


@pytest.mark.asyncio
async def test_paginated_item_request_with_logging():
    """Test logging behavior during pagination errors."""
    mock_client = MagicMock()
    mock_client.post_request = AsyncMock(return_value={
        'data': {
            'boards': [{
                'id': '1',
                'items_page': None  # This will cause extraction failure
            }]
        }
    })

    with patch('monday.services.utils.pagination.logger') as mock_logger:
        with pytest.raises(PaginationError):
            await paginated_item_request(
                client=mock_client,
                query='query { boards { id items_page { items { id } } } }',  # Match the expected query format
                limit=25
            )

        mock_logger.error.assert_called_with('Failed to extract items from response')
