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
from monday.services.users import Users


@pytest.fixture(scope='module')
def mock_client():
    return MagicMock(spec=MondayClient)


@pytest.fixture(scope='module')
def users_instance(mock_client):
    return Users(mock_client)


@pytest.mark.asyncio
async def test_query(users_instance):
    mock_responses = [
        {'data': {'users': [{'id': 1, 'name': 'User 1'}, {'id': 2, 'name': 'User 2'}]}},
        {'data': {'users': []}}
    ]

    users_instance.client.post_request = AsyncMock(side_effect=mock_responses)
    result = await users_instance.query(limit=2)

    assert result == [{'id': 1, 'name': 'User 1'}, {'id': 2, 'name': 'User 2'}]
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
    mock_responses = [
        {
            'data': {
                'users': [{'id': 1, 'email': 'test@example.com'}]
            }
        }
    ]

    users_instance.client.post_request = AsyncMock(side_effect=mock_responses)
    result = await users_instance.query(
        emails='test@example.com',
        ids=1,
        name='Test User',
        kind='non_guests'
    )

    assert result == [{'id': 1, 'email': 'test@example.com'}]
    assert users_instance.client.post_request.await_count == 1
