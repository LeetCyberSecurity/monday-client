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

"""Comprehensive tests for Groups methods"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from monday.client import MondayClient
from monday.exceptions import MondayAPIError
from monday.services.boards import Boards
from monday.services.groups import Groups
from monday.services.items import Items
from monday.types.board import Board
from monday.types.group import Group, GroupList


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
def mock_items():
    """Create mock Items instance"""
    return MagicMock(spec=Items)


@pytest.fixture(scope='module')
def groups_instance(mock_client, mock_boards):
    """Create mock Groups instance"""
    return Groups(mock_client, mock_boards)


@pytest.mark.asyncio
async def test_query(groups_instance, mock_boards):
    """Test basic group query functionality."""
    mock_boards.query.return_value = [
        Board(
            id='1',
            groups=[
                Group(id='group1', title='Group 1'),
                Group(id='group2', title='Group 2')
            ]
        )
    ]
    result = await groups_instance.query(board_ids=1)
    assert len(result) == 1
    assert result[0].board_id == '1'
    assert result[0].groups[0].id == 'group1'
    assert result[0].groups[0].title == 'Group 1'
    assert result[0].groups[1].id == 'group2'
    assert result[0].groups[1].title == 'Group 2'


@pytest.mark.asyncio
async def test_query_with_group_filter(groups_instance, mock_boards):
    """Test group query with group ID filter."""
    mock_boards.query.return_value = [
        Board(
            id='1',
            groups=[
                Group(id='group1', title='Group 1'),
            ]
        )
    ]

    result = await groups_instance.query(board_ids=1, group_ids='group1')
    assert len(result) == 1
    assert result[0].board_id == '1'
    assert result[0].groups[0].id == 'group1'
    assert result[0].groups[0].title == 'Group 1'


@pytest.mark.asyncio
async def test_query_with_name_filter(groups_instance, mock_boards):
    """Test group query with name filter."""
    mock_boards.query.return_value = [
        Board(
            id='1',
            groups=[
                Group(id='group1', title='Group 1'),
                Group(id='group2', title='Group 2')
            ]
        )
    ]

    result = await groups_instance.query(board_ids=1, group_name='Group 1', fields='id')
    assert len(result) == 1
    assert result[0].board_id == '1'
    assert len(result[0].groups) == 1
    assert result[0].groups[0].id == 'group1'


@pytest.mark.asyncio
async def test_query_with_name_filter_and_title(groups_instance, mock_boards):
    """Test group query with name filter and title field."""
    mock_boards.query.return_value = [
        Board(
            id='1',
            groups=[
                Group(id='group1', title='Group 1'),
                Group(id='group2', title='Group 2')
            ]
        )
    ]

    result = await groups_instance.query(board_ids=1, group_name='Group 1', fields='id title')
    assert len(result) == 1
    assert result[0].board_id == '1'
    assert len(result[0].groups) == 1
    assert result[0].groups[0].id == 'group1'
    assert result[0].groups[0].title == 'Group 1'


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


@pytest.mark.asyncio
async def test_create_group(groups_instance, mock_client):
    """Test group creation functionality."""
    mock_client.post_request.return_value = {
        'data': {
            'create_group': {
                'id': 'new_group',
                'title': 'New Group',
                'color': '#0086c0'
            }
        }
    }

    result = await groups_instance.create(
        board_id=1,
        group_name='New Group',
        group_color='#0086c0',
        fields='id title color'
    )

    assert result.id == 'new_group'
    assert result.title == 'New Group'
    assert result.color == '#0086c0'


@pytest.mark.asyncio
async def test_update_group(groups_instance, mock_client):
    """Test group update functionality."""
    mock_client.post_request.return_value = {
        'data': {
            'update_group': {
                'id': 'group1',
                'title': 'Updated Group',
                'color': '#7F5347'
            }
        }
    }

    result = await groups_instance.update(
        board_id=1,
        group_id='group1',
        attribute='color',
        new_value='#7f5347',
        fields='id title color'
    )

    assert result.id == 'group1'
    assert result.title == 'Updated Group'
    assert result.color == '#7F5347'


@pytest.mark.asyncio
async def test_duplicate_group(groups_instance, mock_client):
    """Test group duplication functionality."""
    mock_client.post_request.return_value = {
        'data': {
            'duplicate_group': {
                'id': 'group2',
                'title': 'Duplicate of Group 1'
            }
        }
    }

    result = await groups_instance.duplicate(
        board_id=1,
        group_id='group1',
        fields='id title'
    )

    assert result.id == 'group2'
    assert result.title == 'Duplicate of Group 1'


@pytest.mark.asyncio
async def test_archive_group(groups_instance, mock_client):
    """Test group archival functionality."""
    mock_client.post_request.return_value = {
        'data': {
            'archive_group': {
                'id': 'group1',
                'title': 'Group 1',
                'archived': True
            }
        }
    }

    result = await groups_instance.archive(
        board_id=1,
        group_id='group1',
        fields='id title archived'
    )

    assert result.id == 'group1'
    assert result.title == 'Group 1'
    assert result.archived is True


@pytest.mark.asyncio
async def test_delete_group(groups_instance, mock_client):
    """Test group deletion functionality."""
    mock_client.post_request.return_value = {
        'data': {
            'delete_group': {
                'id': 'group1',
                'title': 'Group 1',
                'deleted': True
            }
        }
    }

    result = await groups_instance.delete(
        board_id=1,
        group_id='group1',
        fields='id title deleted'
    )

    assert result.id == 'group1'
    assert result.title == 'Group 1'
    assert result.deleted is True


@pytest.mark.asyncio
async def test_get_items_by_name(groups_instance, mock_client):
    """Test retrieving items by name within a group."""
    mock_client.post_request.return_value = {
        'data': {
            'boards': [{
                'groups': [{
                    'items_page': {
                        'items': [
                            {'id': '123', 'name': 'Test Item'},
                            {'id': '456', 'name': 'Test Item'}
                        ]
                    }
                }]
            }]
        }
    }

    result = await groups_instance.get_items_by_name(
        board_id=1,
        group_id='group1',
        item_name='Test Item',
        item_fields='id name'
    )

    assert len(result) == 2
    assert result[0].id == '123'
    assert result[0].name == 'Test Item'
    assert result[1].id == '456'
    assert result[1].name == 'Test Item'


@pytest.mark.asyncio
async def test_create_group_with_position(groups_instance, mock_client):
    """Test group creation with position specification."""
    mock_client.post_request.return_value = {
        'data': {
            'create_group': {
                'id': 'new_group',
                'title': 'New Group'
            }
        }
    }

    result = await groups_instance.create(
        board_id=1,
        group_name='New Group',
        relative_to=2,
        position_relative_method='before',
        fields='id title'
    )

    assert result.id == 'new_group'
    assert result.title == 'New Group'


@pytest.mark.asyncio
async def test_update_group_relative_position(groups_instance, mock_client):
    """Test updating group's relative position."""
    mock_client.post_request.return_value = {
        'data': {
            'update_group': {
                'id': 'group1',
                'title': 'Group 1'
            }
        }
    }

    result = await groups_instance.update(
        board_id=1,
        group_id='group1',
        attribute='relative_position_after',
        new_value='group2',
        fields='id title'
    )

    assert result.id == 'group1'
    assert result.title == 'Group 1'


@pytest.mark.asyncio
async def test_duplicate_group_with_custom_title(groups_instance, mock_client):
    """Test group duplication with custom title."""
    mock_client.post_request.return_value = {
        'data': {
            'duplicate_group': {
                'id': 'group2',
                'title': 'Custom Title'
            }
        }
    }

    result = await groups_instance.duplicate(
        board_id=1,
        group_id='group1',
        group_title='Custom Title',
        add_to_top=True,
        fields='id title'
    )

    assert result.id == 'group2'
    assert result.title == 'Custom Title'


class TestGroupsService:
    def setup_method(self):
        self.client = Mock()
        self.boards = Mock()
        self.groups_service = Groups(self.client, self.boards)

    @pytest.mark.asyncio
    async def test_query_groups(self):
        # Mock response data
        mock_group1 = Group(id='group1', title='Group 1', color='#ff0000', position='1', archived=False)
        mock_group2 = Group(id='group2', title='Group 2', color='#00ff00', position='2', archived=True)
        mock_board = Board(id='123', groups=[mock_group1, mock_group2])

        # Mock the boards.query method
        self.boards.query = AsyncMock(return_value=[mock_board])

        # Call the method
        result = await self.groups_service.query(123)

        # Verify the boards.query was called correctly
        self.boards.query.assert_called_once()

        # Verify the result is a list of GroupList
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], GroupList)
        assert result[0].board_id == '123'
        assert len(result[0].groups) == 2

        # Verify first group
        group1 = result[0].groups[0]
        assert group1.id == 'group1'
        assert group1.title == 'Group 1'
        assert group1.color == '#ff0000'
        assert group1.position == '1'
        assert group1.archived is False

        # Verify second group
        group2 = result[0].groups[1]
        assert group2.id == 'group2'
        assert group2.title == 'Group 2'
        assert group2.color == '#00ff00'
        assert group2.position == '2'
        assert group2.archived is True

    @pytest.mark.asyncio
    async def test_create_group(self):
        # Mock response data
        mock_response = {
            'data': {
                'create_group': {
                    'id': 'new_group_id',
                    'title': 'New Group',
                    'color': '#ff0000',
                    'position': '3',
                    'archived': False
                }
            }
        }

        # Mock the client's post_request method
        self.client.post_request = AsyncMock(return_value=mock_response)

        # Call the method
        result = await self.groups_service.create(123, 'New Group')

        # Verify the client was called correctly
        self.client.post_request.assert_called_once()

        # Verify the result is a Group
        assert isinstance(result, Group)
        assert result.id == 'new_group_id'
        assert result.title == 'New Group'
        assert result.color == '#ff0000'
        assert result.position == '3'
        assert result.archived is False

    @pytest.mark.asyncio
    async def test_update_group(self):
        # Mock response data
        mock_response = {
            'data': {
                'update_group': {
                    'id': 'group1',
                    'title': 'Updated Group',
                    'color': '#00ff00',
                    'position': '2',
                    'archived': True
                }
            }
        }

        # Mock the client's post_request method
        self.client.post_request = AsyncMock(return_value=mock_response)

        # Call the method
        result = await self.groups_service.update(123, 'group1', 'title', 'Updated Group')

        # Verify the client was called correctly
        self.client.post_request.assert_called_once()

        # Verify the result is a Group
        assert isinstance(result, Group)
        assert result.id == 'group1'
        assert result.title == 'Updated Group'
        assert result.color == '#00ff00'
        assert result.position == '2'
        assert result.archived is True

    @pytest.mark.asyncio
    async def test_delete_group(self):
        # Mock response data
        mock_response = {
            'data': {
                'delete_group': {
                    'id': 'deleted_group_id',
                    'title': 'Deleted Group',
                    'deleted': True
                }
            }
        }

        # Mock the client's post_request method
        self.client.post_request = AsyncMock(return_value=mock_response)

        # Call the method
        result = await self.groups_service.delete(123, 'group1')

        # Verify the client was called correctly
        self.client.post_request.assert_called_once()

        # Verify the result
        assert isinstance(result, Group)
        assert result.id == 'deleted_group_id'
        assert result.deleted is True

    @pytest.mark.asyncio
    async def test_duplicate_group(self):
        # Mock response data
        mock_response = {
            'data': {
                'duplicate_group': {
                    'id': 'duplicated_group_id',
                    'title': 'Group 1 (Copy)',
                    'color': '#ff0000',
                    'position': '4',
                    'archived': False
                }
            }
        }

        # Mock the client's post_request method
        self.client.post_request = AsyncMock(return_value=mock_response)

        # Call the method
        result = await self.groups_service.duplicate(123, 'group1', group_title='Group 1 (Copy)')

        # Verify the client was called correctly
        self.client.post_request.assert_called_once()

        # Verify the result is a Group
        assert isinstance(result, Group)
        assert result.id == 'duplicated_group_id'
        assert result.title == 'Group 1 (Copy)'
        assert result.color == '#ff0000'
        assert result.position == '4'
        assert result.archived is False

    @pytest.mark.asyncio
    async def test_archive_group(self):
        # Mock response data
        mock_response = {
            'data': {
                'archive_group': {
                    'id': 'group1',
                    'title': 'Group 1',
                    'color': '#ff0000',
                    'position': '1',
                    'archived': True
                }
            }
        }

        # Mock the client's post_request method
        self.client.post_request = AsyncMock(return_value=mock_response)

        # Call the method
        result = await self.groups_service.archive(123, 'group1')

        # Verify the client was called correctly
        self.client.post_request.assert_called_once()

        # Verify the result is a Group
        assert isinstance(result, Group)
        assert result.id == 'group1'
        assert result.title == 'Group 1'
        assert result.color == '#ff0000'
        assert result.position == '1'
        assert result.archived is True

    @pytest.mark.asyncio
    async def test_query_groups_empty_response(self):
        # Mock empty response
        mock_board = Board(id='123', groups=[])

        # Mock the boards.query method
        self.boards.query = AsyncMock(return_value=[mock_board])

        result = await self.groups_service.query(123)

        assert isinstance(result, list)
        assert len(result) == 0  # Empty groups list means no GroupList is created

    @pytest.mark.asyncio
    async def test_query_groups_with_filter(self):
        # Mock response data
        mock_group1 = Group(id='group1', title='Group 1', color='#ff0000', position='1', archived=False)
        mock_board = Board(id='123', groups=[mock_group1])

        # Mock the boards.query method
        self.boards.query = AsyncMock(return_value=[mock_board])

        # Call the method with group name filter
        result = await self.groups_service.query(123, group_name='Group 1')

        # Verify the boards.query was called correctly
        self.boards.query.assert_called_once()

        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 1
        assert len(result[0].groups) == 1
        assert result[0].groups[0].title == 'Group 1'

    @pytest.mark.asyncio
    async def test_query_groups_with_group_ids_filter(self):
        # Mock response data
        mock_group1 = Group(id='group1', title='Group 1', color='#ff0000', position='1', archived=False)
        mock_group2 = Group(id='group2', title='Group 2', color='#00ff00', position='2', archived=True)
        mock_board = Board(id='123', groups=[mock_group1, mock_group2])

        # Mock the boards.query method
        self.boards.query = AsyncMock(return_value=[mock_board])

        # Call the method with group IDs filter
        result = await self.groups_service.query(123, group_ids=['group1'])

        # Verify the boards.query was called correctly
        self.boards.query.assert_called_once()

        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 1
        assert len(result[0].groups) == 2  # Both groups are returned, filtering happens in the query
