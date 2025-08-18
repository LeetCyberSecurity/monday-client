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

"""Tests for monday-client HTTP adapters."""

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from monday.http_adapters import AiohttpAdapter


@pytest.mark.asyncio
@pytest.mark.unit
async def test_aiohttp_adapter_post_non_json_response():
    """Test AiohttpAdapter.post falls back to text on non-JSON response."""
    adapter = AiohttpAdapter(
        proxy_url=None,
        proxy_auth=None,
        proxy_auth_type='basic',
        proxy_trust_env=False,
        proxy_ssl_verify=True,
        timeout_seconds=1,
    )

    # Mock response that raises ContentTypeError on .json(), falls back to .text()
    response = AsyncMock()
    response.headers = {'X-Test': '1'}
    response.json.side_effect = aiohttp.ContentTypeError(
        MagicMock(), (), message='not json'
    )
    response.text = AsyncMock(return_value='oops')

    # Mock the nested context managers used by ClientSession and session.post
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    post_cm = MagicMock()
    post_cm.__aenter__ = AsyncMock(return_value=response)
    post_cm.__aexit__ = AsyncMock(return_value=None)
    # session.post should return an async-context-manager object (not a coroutine)
    mock_session.post = MagicMock(return_value=post_cm)

    with patch('aiohttp.ClientSession', return_value=mock_session):
        data, headers = await adapter.post(
            url='https://example.com', json={'q': 1}, headers={'H': 'V'}
        )

    assert 'Non-JSON response' in data.get('error', '')
    assert headers.get('X-Test') == '1'


@pytest.mark.unit
def test_aiohttp_adapter_proxy_kwargs_basic_auth():
    """Test proxy kwargs include proxy and aiohttp.BasicAuth for basic auth."""
    adapter = AiohttpAdapter(
        proxy_url='http://proxy.local:8080',
        proxy_auth=('user', 'pass'),
        proxy_auth_type='basic',
        proxy_trust_env=False,
        proxy_ssl_verify=True,
        timeout_seconds=1,
    )

    kwargs = adapter._build_request_proxy_kwargs()
    assert kwargs['proxy'] == 'http://proxy.local:8080'
    # aiohttp.BasicAuth is used for proxy_auth
    assert isinstance(kwargs['proxy_auth'], aiohttp.BasicAuth)
