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
from monday.exceptions import MondayAPIError, QueryFormatError
from monday.services.boards import Boards


@pytest.fixture(scope='module')
def mock_client():
    return MagicMock(spec=MondayClient)


@pytest.fixture(scope='module')
def boards_instance(mock_client):
    return Boards(mock_client)


@pytest.mark.asyncio
async def test_query(boards_instance):
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
async def test_query_with_invalid_pagination(boards_instance):
    """Test query with invalid pagination parameters."""
    with pytest.raises(QueryFormatError) as exc_info:
        await boards_instance.query(fields='items_page { items { id } }', paginate_items=True)
    assert 'Pagination requires a cursor' in str(exc_info.value)


@pytest.mark.asyncio
async def test_query_with_api_error(boards_instance):
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
async def test_create(boards_instance):
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
async def test_duplicate(boards_instance):
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
async def test_update(boards_instance):
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
async def test_archive(boards_instance):
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
async def test_delete(boards_instance):
    mock_response = {
        'data': {
            'delete_board': {'id': 1, 'state': 'deleted'}
        }
    }

    boards_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await boards_instance.delete(board_id=1)

    assert result == {'id': 1, 'state': 'deleted'}
    boards_instance.client.post_request.assert_awaited_once()
