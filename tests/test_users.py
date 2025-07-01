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

"""Comprehensive tests for Users methods"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from monday.client import MondayClient
from monday.exceptions import MondayAPIError
from monday.services.users import Users
from monday.services.utils.fields import Fields
from monday.types.user import User


@pytest.fixture(scope='module')
def mock_client():
    """Create mock MondayClient instance"""
    return MagicMock(spec=MondayClient)


@pytest.fixture(scope='module')
def users_instance(mock_client):
    """Create mock Users instance"""
    return Users(mock_client)


@pytest.mark.asyncio
async def test_query(users_instance):
    """Test basic user query functionality."""
    mock_responses = [
        {'data': {'users': [
            {'id': '1', 'name': 'User 1'},
            {'id': '2', 'name': 'User 2'}
        ]}},
        {'data': {'users': []}}
    ]

    users_instance.client.post_request = AsyncMock(side_effect=mock_responses)
    result = await users_instance.query(limit=2)

    assert isinstance(result[0], User)
    assert result[0].id == '1'
    assert result[0].name == 'User 1'
    assert result[1].id == '2'
    assert result[1].name == 'User 2'
    assert users_instance.client.post_request.await_count == 2


@pytest.mark.asyncio
async def test_query_with_api_error(users_instance):
    """Test handling of API errors in query method."""
    error_response = {
        'errors': [{
            'message': 'API Error',
            'extensions': {'code': 'SomeError'}
        }]
    }

    users_instance.client.post_request = AsyncMock(return_value=error_response)
    with pytest.raises(MondayAPIError) as exc_info:
        await users_instance.query()
    assert exc_info.value.json == error_response


@pytest.mark.asyncio
async def test_query_with_filters(users_instance):
    """Test query with email, id, name and kind filters."""
    mock_responses = [
        {'data': {'users': [
            {'id': '1', 'email': 'test@example.com'}
        ]}}
    ]

    users_instance.client.post_request = AsyncMock(side_effect=mock_responses)
    result = await users_instance.query(
        emails='test@example.com',
        ids=1,
        name='Test User',
        kind='non_guests'
    )

    assert isinstance(result[0], User)
    assert result[0].id == '1'
    assert result[0].email == 'test@example.com'
    assert users_instance.client.post_request.await_count == 1


@pytest.mark.asyncio
async def test_query_pagination(users_instance):
    """Test pagination behavior of query method."""
    mock_responses = [
        {'data': {'users': [{'id': '1'}, {'id': '2'}]}},  # First page
        {'data': {'users': [{'id': '3'}, {'id': '4'}]}},  # Second page
        {'data': {'users': []}}  # Empty last page
    ]

    users_instance.client.post_request = AsyncMock(side_effect=mock_responses)
    result = await users_instance.query(limit=2, paginate=True)

    assert len(result) == 4
    assert [user.id for user in result] == ['1', '2', '3', '4']
    assert users_instance.client.post_request.await_count == 3


@pytest.mark.asyncio
async def test_query_no_pagination(users_instance):
    """Test query behavior when pagination is disabled."""
    mock_response = {'data': {'users': [{'id': '1'}, {'id': '2'}]}}

    users_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await users_instance.query(limit=2, paginate=False)

    assert len(result) == 2
    assert users_instance.client.post_request.await_count == 1


@pytest.mark.asyncio
async def test_query_duplicate_handling(users_instance):
    """Test handling of duplicate users in response."""
    mock_responses = [
        {'data': {'users': [{'id': '1'}, {'id': '2'}]}},
        {'data': {'users': [{'id': '2'}, {'id': '3'}]}},  # Note duplicate id '2'
        {'data': {'users': []}}  # Empty response to stop pagination
    ]

    users_instance.client.post_request = AsyncMock(side_effect=mock_responses)
    result = await users_instance.query(limit=2)

    ids = [user.id for user in result]
    assert len(set(ids)) == 3
    assert sorted(ids) == ['1', '2', '3']
    assert users_instance.client.post_request.await_count == 3  # Verify all pages were requested


@pytest.mark.asyncio
async def test_query_empty_response(users_instance):
    """Test handling of empty response."""
    mock_response = {'data': {'users': []}}

    users_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await users_instance.query()

    assert result == []
    assert users_instance.client.post_request.await_count == 1


@pytest.mark.asyncio
async def test_query_custom_fields(users_instance):
    """Test querying with custom fields."""
    mock_response = {
        'data': {
            'users': [{
                'id': '1',
                'name': 'Test User',
                'email': 'test@example.com',
                'title': 'Developer'
            }]
        }
    }

    users_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await users_instance.query(
        fields='id name email title',
        limit=1
    )

    assert len(result) == 1
    assert isinstance(result[0], User)
    assert result[0].id == '1'
    assert result[0].name == 'Test User'
    assert result[0].email == 'test@example.com'
    assert result[0].title == 'Developer'


@pytest.mark.asyncio
async def test_query_pagination_with_full_pages(users_instance):
    """Test pagination when all pages are full."""
    mock_responses = [
        {'data': {'users': [{'id': '1'}, {'id': '2'}]}},  # Full page
        {'data': {'users': [{'id': '3'}, {'id': '4'}]}},  # Full page
        {'data': {'users': [{'id': '5'}]}}  # Partial page to end pagination
    ]

    users_instance.client.post_request = AsyncMock(side_effect=mock_responses)
    result = await users_instance.query(limit=2, paginate=True)

    assert len(result) == 5
    assert [user.id for user in result] == ['1', '2', '3', '4', '5']
    assert users_instance.client.post_request.await_count == 3


@pytest.mark.asyncio
async def test_temp_fields_management(users_instance):
    """Test temporary fields are properly added and removed."""
    mock_response = {
        'data': {
            'users': [
                {'id': '1', 'name': 'Test User', 'temp_field': 'value'}
            ]
        }
    }

    users_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await users_instance.query(fields='name')  # Note: not requesting 'id'

    assert len(result) == 1
    assert hasattr(result[0], 'name')
    assert getattr(result[0], 'name') == 'Test User'
    # id should not be present unless requested
    assert not getattr(result[0], 'id', None)


@pytest.mark.asyncio
async def test_query_with_duplicate_users_across_pages(users_instance):
    """Test deduplication of users when duplicates appear across different pages."""
    mock_responses = [
        {'data': {'users': [{'id': '1', 'name': 'User 1'}, {'id': '2', 'name': 'User 2'}]}},
        {'data': {'users': [{'id': '2', 'name': 'User 2'}, {'id': '3', 'name': 'User 3'}]}},
        {'data': {'users': []}}
    ]

    users_instance.client.post_request = AsyncMock(side_effect=mock_responses)
    result = await users_instance.query(limit=2)

    assert len(result) == 3  # Should only have 3 unique users
    assert sorted([user.id for user in result]) == ['1', '2', '3']
    assert users_instance.client.post_request.await_count == 3


@pytest.mark.asyncio
async def test_query_with_fields_object_and_temp_fields(users_instance):
    """Test query using Fields object with temporary fields."""
    mock_response = {
        'data': {
            'users': [{'id': '1', 'name': 'Test User', 'email': 'test@example.com'}]
        }
    }

    users_instance.client.post_request = AsyncMock(return_value=mock_response)
    fields = Fields('name email')  # Not requesting 'id'
    result = await users_instance.query(fields=fields)

    assert len(result) == 1
    user = result[0]
    assert hasattr(user, 'name')
    assert hasattr(user, 'email')
    assert getattr(user, 'name') == 'Test User'
    assert getattr(user, 'email') == 'test@example.com'
    # id should not be present unless requested
    assert not getattr(user, 'id', None)


@pytest.mark.asyncio
async def test_query_identical_responses_stops_pagination(users_instance):
    """Test that pagination stops when receiving identical responses."""
    mock_responses = [
        {'data': {'users': [{'id': '1'}, {'id': '2'}]}},
        {'data': {'users': [{'id': '1'}, {'id': '2'}]}}  # Identical response
    ]

    users_instance.client.post_request = AsyncMock(side_effect=mock_responses)
    result = await users_instance.query(limit=2)

    assert len(result) == 2
    assert [user.id for user in result] == ['1', '2']
    assert users_instance.client.post_request.await_count == 2


@pytest.mark.asyncio
async def test_query_empty_response_handling(users_instance):
    """Test handling of empty response from the API."""
    mock_response = {'data': {'users': []}}

    users_instance.client.post_request = AsyncMock(return_value=mock_response)
    result = await users_instance.query()

    assert result == []
    assert users_instance.client.post_request.await_count == 1
