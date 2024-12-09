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
from monday.exceptions import MondayAPIError
from monday.services.boards import Boards
from monday.services.groups import Groups
from monday.services.items import Items


@pytest.fixture(scope='module')
def mock_client():
    return MagicMock(spec=MondayClient)


@pytest.fixture(scope='module')
def mock_boards():
    boards = MagicMock(spec=Boards)
    boards.query = AsyncMock()
    return boards


@pytest.fixture(scope='module')
def mock_items():
    return MagicMock(spec=Items)


@pytest.fixture(scope='module')
def groups_instance(mock_client, mock_boards):
    return Groups(mock_client, mock_boards)


@pytest.mark.asyncio
async def test_query(groups_instance, mock_boards):
    mock_boards.query.return_value = [
        {
            'id': 1,
            'groups': [
                {'id': 'group1', 'title': 'Group 1'},
                {'id': 'group2', 'title': 'Group 2'}
            ]
        }
    ]

    result = await groups_instance.query(board_ids=1)
    assert result == [{'id': 1, 'groups': [{'id': 'group1', 'title': 'Group 1'}, {'id': 'group2', 'title': 'Group 2'}]}]


@pytest.mark.asyncio
async def test_query_with_group_filter(groups_instance, mock_boards):
    mock_boards.query.return_value = [
        {
            'id': 1,
            'groups': [
                {'id': 'group1', 'title': 'Group 1'},
            ]
        }
    ]

    result = await groups_instance.query(board_ids=1, group_ids='group1')
    assert result == [{'id': 1, 'groups': [{'id': 'group1', 'title': 'Group 1'}]}]


@pytest.mark.asyncio
async def test_query_with_name_filter(groups_instance, mock_boards):
    mock_boards.query.return_value = [
        {
            'id': 1,
            'groups': [
                {'id': 'group1', 'title': 'Group 1'},
                {'id': 'group2', 'title': 'Group 2'}
            ]
        }
    ]

    result = await groups_instance.query(board_ids=1, group_name='Group 1')
    assert result == [{'id': 1, 'groups': [{'id': 'group1'}]}]


@pytest.mark.asyncio
async def test_query_with_name_filter_and_title(groups_instance, mock_boards):
    mock_boards.query.return_value = [
        {
            'id': 1,
            'groups': [
                {'id': 'group1', 'title': 'Group 1'},
                {'id': 'group2', 'title': 'Group 2'}
            ]
        }
    ]

    result = await groups_instance.query(board_ids=1, group_name='Group 1', fields='id title')
    assert result == [{'id': 1, 'groups': [{'id': 'group1', 'title': 'Group 1'}]}]


@pytest.mark.asyncio
async def test_query_with_api_error(groups_instance, mock_boards):
    """Test handling of API errors in query method."""
    error_response = {
        'errors': [{
            'message': 'API Error',
            'extensions': {'code': 'SomeError'}
        }]
    }

    mock_boards.query.side_effect = MondayAPIError('API Error', json=error_response)

    with pytest.raises(MondayAPIError) as exc_info:
        await groups_instance.query(board_ids=1)
    assert exc_info.value.json == error_response
