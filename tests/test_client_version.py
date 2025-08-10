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

"""Tests for monday version gathering."""

from unittest.mock import AsyncMock, patch

import pytest

from monday.client import MondayClient
from monday.exceptions import MondayAPIError


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_current_version_happy_path():
    """Test that _get_current_version returns the current version on success."""
    client = MondayClient(api_key='k')
    mock_post = AsyncMock(
        return_value=(
            {
                'data': {
                    'versions': [
                        {'kind': 'previous', 'value': '2023-01'},
                        {'kind': 'current', 'value': '2024-10'},
                    ]
                }
            },
            {},
        )
    )
    with patch.object(client, '_adapter') as adapter:
        adapter.post = mock_post
        v = await client._get_current_version()
    assert v == '2024-10'


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_current_version_errors_key():
    """Test that _get_current_version raises on API error response."""
    client = MondayClient(api_key='k')
    mock_post = AsyncMock(return_value=({'errors': [{'message': 'x'}]}, {}))
    with patch.object(client, '_adapter') as adapter:
        adapter.post = mock_post
        with pytest.raises(MondayAPIError):
            await client._get_current_version()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_current_version_missing_current():
    """Test that _get_current_version raises when no current version is present."""
    client = MondayClient(api_key='k')
    mock_post = AsyncMock(return_value=({'data': {'versions': []}}, {}))
    with patch.object(client, '_adapter') as adapter:
        adapter.post = mock_post
        with pytest.raises(MondayAPIError) as exc:
            await client._get_current_version()
    assert 'No current version' in str(exc.value)
