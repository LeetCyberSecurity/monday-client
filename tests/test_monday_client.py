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

from unittest.mock import AsyncMock, patch

import aiohttp
import pytest

from monday.client import MondayClient


@pytest.fixture(scope='module')
def client_instance():
    client = MondayClient('test_api_key')
    client.max_retries = 2
    client._rate_limit_seconds = 1
    return client


@pytest.mark.asyncio
async def test_init():
    client = MondayClient('test_api_key')
    assert client.url == 'https://api.monday.com/v2'
    assert client.headers == {
        'Content-Type': 'application/json',
        'Authorization': 'test_api_key'
    }
    assert client._rate_limit_seconds == 60
    assert client.max_retries == 4


@pytest.mark.asyncio
async def test_post_request_success(client_instance):
    mock_response = {'data': {'some': 'data'}}

    with patch.object(client_instance, '_execute_request', new_callable=AsyncMock, return_value=mock_response):
        result = await client_instance.post_request('test_query')

    assert result == mock_response


@pytest.mark.asyncio
async def test_post_request_complexity_limit_exceeded(client_instance):
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
    mock_response = AsyncMock()
    mock_json = AsyncMock(return_value={'data': {'some': 'data'}})
    mock_response.__aenter__.return_value.json = mock_json

    with patch('aiohttp.ClientSession.post', return_value=mock_response) as mock_post:
        result = await client_instance._execute_request('test_query')

    assert result == {'data': {'some': 'data'}}
    mock_post.assert_called_once_with(
        'https://api.monday.com/v2',
        json={'query': 'test_query'},
        headers={'Content-Type': 'application/json', 'Authorization': 'test_api_key'}
    )
