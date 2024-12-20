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
# pylint: disable=protected-access

"""Comprehensive tests for MondayClient methods"""

from unittest.mock import AsyncMock, patch

import aiohttp
import pytest

from monday.client import MondayClient
from monday.exceptions import MondayAPIError, QueryFormatError


@pytest.fixture(scope='module')
def client_instance():
    """Create mock MondayClient instance"""
    client = MondayClient('test_api_key')
    client.max_retries = 2
    client._rate_limit_seconds = 1
    return client


@pytest.mark.asyncio
async def test_init():
    """Test MondayClient initialization and default values."""
    client = MondayClient('test_api_key')
    assert client.url == 'https://api.monday.com/v2'
    assert client.headers == {
        'Content-Type': 'application/json',
        'Authorization': 'test_api_key',
        'API-Version': '2024-10'
    }
    assert client._rate_limit_seconds == 60
    assert client.max_retries == 4


@pytest.mark.asyncio
async def test_post_request_success(client_instance):
    """Test successful POST request execution."""
    mock_response = {'data': {'some': 'data'}}

    with patch.object(client_instance, '_execute_request', new_callable=AsyncMock, return_value=mock_response):
        result = await client_instance.post_request('test_query')

    assert result == mock_response


@pytest.mark.asyncio
async def test_post_request_complexity_limit_exceeded(client_instance):
    """Test handling of complexity limit exceeded errors."""
    error_responses = [
        {'error': 'error', 'error_code': 'ComplexityException', 'error_message': 'Complexity limit exceeded reset in 0.1 seconds'},
        {'data': {'some': 'data'}}
    ]

    client_instance.max_retries = 2

    with patch.object(client_instance, '_execute_request', side_effect=error_responses):
        with patch('monday.client.asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            result = await client_instance.post_request('test_query')

    mock_sleep.assert_called_once_with(1)
    assert result == {'data': {'some': 'data'}}


@pytest.mark.asyncio
async def test_post_request_mutation_limit_exceeded(client_instance):
    """Test handling of mutation limit exceeded errors."""
    error_responses = [
        {'error': 'error', 'status_code': 429},
        {'data': {'some': 'data'}}
    ]

    with patch.object(client_instance, '_execute_request', side_effect=error_responses):
        with patch('monday.client.asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            result = await client_instance.post_request('test_query')

    mock_sleep.assert_called_once_with(1)
    assert result == {'data': {'some': 'data'}}


@pytest.mark.asyncio
async def test_post_request_max_retries_reached(client_instance):
    """Test behavior when maximum retry attempts are reached."""
    client_instance.max_retries = 1
    error_responses = [
        {'error': 'error', 'error_code': 'ComplexityException', 'error_message': 'Complexity limit exceeded reset in 0.1 seconds'},
        {'data': {'some': 'data'}}
    ]

    with patch.object(client_instance, '_execute_request', side_effect=error_responses):
        with patch('monday.client.asyncio.sleep', new_callable=AsyncMock):
            with pytest.raises(Exception) as exc_info:
                await client_instance.post_request('test_query')

    expected_error = f'Max retries ({client_instance.max_retries}) reached'
    assert str(exc_info.value) == expected_error


@pytest.mark.asyncio
async def test_post_request_client_error_retry(client_instance):
    """Test retry behavior on client errors."""
    error_responses = [
        aiohttp.ClientError('Client error occurred'),
        aiohttp.ClientError('Client error occurred'),
        {'data': {'some': 'data'}}
    ]
    client_instance.max_retries = 3

    with patch.object(client_instance, '_execute_request', side_effect=error_responses):
        with patch('monday.client.asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            result = await client_instance.post_request('test_query')

    assert mock_sleep.call_count == 2
    mock_sleep.assert_called_with(1)
    assert result == {'data': {'some': 'data'}}


@pytest.mark.asyncio
async def test_post_request_max_retries_client_error(client_instance):
    """Test max retries behavior with client errors."""
    client_instance.max_retries = 1
    client_error = aiohttp.ClientError('Client error occurred')

    with patch.object(client_instance, '_execute_request', side_effect=client_error):
        with patch('monday.client.asyncio.sleep', new_callable=AsyncMock):
            with pytest.raises(Exception) as exc_info:
                await client_instance.post_request('test_query')

    expected_error = f'Max retries ({client_instance.max_retries}) reached'
    assert str(exc_info.value) == expected_error


@pytest.mark.asyncio
async def test_execute_request(client_instance):
    """Test low-level request execution."""
    mock_response = AsyncMock()
    mock_json = AsyncMock(return_value={'data': {'some': 'data'}})
    mock_response.__aenter__.return_value.json = mock_json

    with patch('aiohttp.ClientSession.post', return_value=mock_response) as mock_post:
        result = await client_instance._execute_request('test_query')

    assert result == {'data': {'some': 'data'}}
    mock_post.assert_called_once_with(
        'https://api.monday.com/v2',
        json={'query': 'test_query'},
        headers={
            'Content-Type': 'application/json',
            'Authorization': 'test_api_key',
            'API-Version': '2024-10'
        }
    )


@pytest.mark.asyncio
async def test_query_format_error(client_instance):
    """Test handling of query format errors."""
    error_response = {
        'errors': [{'message': 'Parse error on line 2', 'extensions': {'code': 'argumentLiteralsIncompatible'}}]
    }

    with patch.object(client_instance, '_execute_request', return_value=error_response):
        with pytest.raises(QueryFormatError) as exc_info:
            await client_instance.post_request('invalid query')

    assert 'Invalid monday.com GraphQL query' in str(exc_info.value)


@pytest.mark.asyncio
async def test_move_item_mapping_error(client_instance):
    """Test handling of move_item_to_board mapping errors."""
    error_response = {
        'error': 'error',
        'status_code': 400,
        'error_message': 'mapping is not in the expected format',
    }

    with patch.object(client_instance, '_execute_request', return_value=error_response):
        with pytest.raises(QueryFormatError) as exc_info:
            await client_instance.post_request('mutation { move_item_to_board }')

    assert 'Columns mapping is not in the expected format' in str(exc_info.value)


@pytest.mark.asyncio
async def test_unhandled_monday_api_error(client_instance):
    """Test handling of unhandled Monday.com API errors."""
    error_response = {
        'errors': [{'message': 'Unknown error', 'extensions': {'code': 'UnknownError'}}]
    }

    with patch.object(client_instance, '_execute_request', return_value=error_response):
        with pytest.raises(MondayAPIError) as exc_info:
            await client_instance.post_request('test_query')

    assert 'Unhandled monday.com API error' in str(exc_info.value)


@pytest.mark.asyncio
async def test_service_initialization(client_instance):
    """Test that all services are properly initialized."""
    assert hasattr(client_instance, 'boards')
    assert hasattr(client_instance, 'items')
    assert hasattr(client_instance, 'subitems')
    assert hasattr(client_instance, 'groups')
    assert hasattr(client_instance, 'users')


@pytest.mark.asyncio
async def test_custom_headers():
    """Test initialization with custom headers."""
    custom_headers = {'Custom-Header': 'test_value'}
    client = MondayClient('test_api_key', headers=custom_headers)

    assert client.headers['Custom-Header'] == 'test_value'
    assert client.headers['Authorization'] == 'test_api_key'
    assert client.headers['Content-Type'] == 'application/json'


@pytest.mark.asyncio
async def test_invalid_max_retries():
    """Test initialization with invalid max_retries value."""
    client = MondayClient('test_api_key', max_retries='4')
    assert isinstance(client.max_retries, int)
    assert client.max_retries == 4


@pytest.mark.asyncio
async def test_complexity_limit_reset_time_parsing(client_instance):
    """Test parsing of reset time from complexity limit error."""
    error_response = {
        'error': 'error',
        'error_code': 'ComplexityException',
        'error_message': 'Complexity limit exceeded reset in 0.5 seconds'
    }
    success_response = {'data': {'some': 'data'}}

    # Set max_retries to 2 to allow one retry
    client_instance.max_retries = 2

    # Mock _execute_request to return error first, then success
    mock_execute = AsyncMock(side_effect=[error_response, success_response])

    with patch.object(client_instance, '_execute_request', new=mock_execute):
        with patch('monday.client.asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            result = await client_instance.post_request('test_query')

    mock_sleep.assert_called_once_with(1)  # Verify sleep was called with correct duration
    assert result == success_response  # Verify final result


@pytest.mark.asyncio
async def test_complexity_limit_invalid_reset_time(client_instance):
    """Test handling of invalid reset time format in complexity limit error."""
    error_response = {
        'error': 'error',
        'error_code': 'ComplexityException',
        'error_message': 'Complexity limit exceeded'  # Missing reset time
    }

    with patch.object(client_instance, '_execute_request', return_value=error_response):
        with pytest.raises(MondayAPIError) as exc_info:
            await client_instance.post_request('test_query')

    assert 'Error getting reset_in_x_seconds' in str(exc_info.value)
