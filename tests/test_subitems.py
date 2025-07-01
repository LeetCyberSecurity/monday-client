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

"""Comprehensive tests for Subitems methods"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from monday.client import MondayClient
from monday.exceptions import MondayAPIError
from monday.services.boards import Boards
from monday.services.items import Items
from monday.services.subitems import Subitems
from monday.types.item import Item
from monday.types.subitem import Subitem, SubitemList


@pytest.fixture(scope='module')
def mock_client():
    """Create mock MondayClient instance"""
    return MagicMock(spec=MondayClient)


@pytest.fixture(scope='module')
def mock_items():
    """Create mock Items instance"""
    items = MagicMock(spec=Items)
    items.query = AsyncMock()
    return items


@pytest.fixture(scope='module')
def mock_boards():
    """Create mock Boards instance"""
    boards = MagicMock(spec=Boards)
    boards.get_items = AsyncMock()
    return boards


@pytest.fixture(scope='module')
def subitems_instance(mock_client, mock_items, mock_boards):
    """Create Subitems instance with mocked dependencies"""
    return Subitems(mock_client, mock_items, mock_boards)


@pytest.mark.asyncio
async def test_query_without_subitem_ids(subitems_instance):
    """Test querying subitems without specific subitem IDs."""
    mock_items = [
        Item(id='1', subitems=[
            Subitem(id='11', name='Subitem 1'),
            Subitem(id='12', name='Subitem 2')
        ])
    ]

    subitems_instance.items.query = AsyncMock(return_value=mock_items)
    result = await subitems_instance.query(item_ids=1)

    assert isinstance(result[0], SubitemList)
    assert result[0].item_id == '1'
    assert result[0].subitems[0].id == '11'
    assert result[0].subitems[0].name == 'Subitem 1'
    assert result[0].subitems[1].id == '12'
    assert result[0].subitems[1].name == 'Subitem 2'
    subitems_instance.items.query.assert_awaited_once()


@pytest.mark.asyncio
async def test_query_with_subitem_ids(subitems_instance):
    """Test querying specific subitems by their IDs."""
    mock_items = [
        Item(id='1', subitems=[
            Subitem(id='11', name='Subitem 1', board=None),
            Subitem(id='12', name='Subitem 2', board=None)
        ])
    ]
    mock_board_response = [
        Item(id='11', name='Subitem 1'),
        Item(id='12', name='Subitem 2')
    ]

    subitems_instance.items.query = AsyncMock(return_value=mock_items)
    subitems_instance.boards.get_items = AsyncMock(return_value=[MagicMock(items=mock_board_response)])

    result = await subitems_instance.query(
        item_ids=1,
        subitem_ids=['11', '12']
    )

    assert isinstance(result[0], SubitemList)
    assert result[0].item_id == '1'
    assert len(result[0].subitems) == 2
    assert result[0].subitems[0].id == '11'
    assert result[0].subitems[1].id == '12'
    assert result[0].subitems[0].name == 'Subitem 1'
    assert result[0].subitems[1].name == 'Subitem 2'
    assert subitems_instance.items.query.await_count == 1
    assert subitems_instance.boards.get_items.await_count == 1


@pytest.mark.asyncio
async def test_query_multiple_items(subitems_instance):
    """Test querying subitems for multiple parent items."""
    mock_items = [
        Item(id='1', subitems=[
            Subitem(id='11', name='Subitem 1'),
            Subitem(id='12', name='Subitem 2')
        ]),
        Item(id='2', subitems=[
            Subitem(id='21', name='Subitem 3')
        ])
    ]

    subitems_instance.items.query = AsyncMock(return_value=mock_items)
    result = await subitems_instance.query(item_ids=[1, 2])

    assert len(result) == 2
    assert result[0].item_id == '1'
    assert result[1].item_id == '2'
    assert len(result[0].subitems) == 2
    assert len(result[1].subitems) == 1
    subitems_instance.items.query.assert_awaited_once()


@pytest.mark.asyncio
async def test_query_with_custom_fields(subitems_instance):
    """Test querying subitems with custom fields."""
    mock_items = [
        Item(id='1', subitems=[
            Subitem(id='11', name='Subitem 1')
        ])
    ]

    subitems_instance.items.query = AsyncMock(return_value=mock_items)
    result = await subitems_instance.query(
        item_ids=1,
        fields='id name column_values { id text }'
    )

    assert result[0].subitems[0].id == '11'
    assert result[0].subitems[0].name == 'Subitem 1'
    subitems_instance.items.query.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_subitem(subitems_instance):
    """Test creating a new subitem."""
    mock_response = {
        'data': {
            'create_subitem': {
                'id': '11',
                'name': 'New Subitem',
            }
        }
    }

    subitems_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await subitems_instance.create(item_id='1', subitem_name='New Subitem')

    assert isinstance(result, Subitem)
    assert result.id == '11'
    assert result.name == 'New Subitem'
    subitems_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_subitem_with_labels(subitems_instance):
    """Test creating a subitem with create_labels_if_missing enabled."""
    mock_response = {
        'data': {
            'create_subitem': {
                'id': '11',
                'name': 'New Subitem',
            }
        }
    }

    subitems_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await subitems_instance.create(
        item_id='1',
        subitem_name='New Subitem',
        create_labels_if_missing=True
    )

    assert isinstance(result, Subitem)
    assert result.id == '11'
    assert result.name == 'New Subitem'
    subitems_instance.client.post_request.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_subitem_with_api_error(subitems_instance):
    """Test handling of API errors in create method."""
    error_response = {
        'errors': [{
            'message': 'Invalid input',
            'extensions': {'code': 'InvalidInput'}
        }]
    }

    subitems_instance.client.post_request = AsyncMock(return_value=error_response)
    with pytest.raises(MondayAPIError) as exc_info:
        await subitems_instance.create(
            item_id='1',
            subitem_name='New Subitem'
        )
    assert exc_info.value.json == error_response
