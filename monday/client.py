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

"""
Client module for interacting with the Monday.com API.

This module provides a comprehensive client for interacting with the Monday.com GraphQL API.
It includes the MondayClient class, which handles authentication, rate limiting, pagination,
and various API operations for boards and items.

Key features:
- Asynchronous API requests using aiohttp
- Rate limiting and automatic retries
- Error handling for API-specific exceptions
- Convenient methods for common board and item operations
- Logging support for debugging and monitoring

Classes:
    MondayClient: The main client class for interacting with the Monday.com API.

Usage:
    from monday.client import MondayClient

    client = MondayClient(api_key='your_api_key')
    # Use client methods to interact with the Monday.com API
"""

import asyncio
import logging
import math
import re
from typing import Any, Dict, Optional

import aiohttp

from .exceptions import (ComplexityLimitExceeded, MondayAPIError,
                         MutationLimitExceeded)
from .services.boards import Boards
from .services.groups import Groups
from .services.items import Items
from .services.users import Users


class MondayClient:
    """
    Client for interacting with the Monday.com API.
    This client handles API requests, rate limiting, and pagination for Monday.com's GraphQL API.

    It uses a class-level logger named 'monday_client' for all logging operations.

    Attributes:
        url (str): The endpoint URL for the Monday.com API.
        headers (Dict[str, str]): HTTP headers used for API requests, including authentication.
        max_retries (int): Maximum number of retry attempts for API requests.
        boards (Boards): Service for board-related operations.
        items (Items): Service for item-related operations.
        _rate_limit_seconds (int): Rate limit in seconds for API requests.
    """

    logger = logging.getLogger(__name__)
    """
    Class-level logger named 'monday_client' for all logging operations.

    Note:
        Logging can be controlled by configuring this logger.
        By default, a NullHandler is added to the logger, which suppresses all output.
        To enable logging, configure the logger in your application code. For example:

        .. code-block:: python

            import logging
            logger = logging.getLogger('monday_client')
            logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)

        To disable all logging (including warnings and errors):

        .. code-block:: python

            import logging
            logging.getLogger('monday_client').disabled = True
    """

    def __init__(
        self,
        api_key: str,
        url: str = 'https://api.monday.com/v2',
        headers: Optional[Dict[str, Any]] = None,
        max_retries: int = 4
    ):
        """
        Initialize the MondayClient with the provided API key.

        Args:
            api_key: The API key for authenticating with the Monday.com API.
            url: The endpoint URL for the Monday.com API. Defaults to 'https://api.monday.com/v2'.
            headers: Additional HTTP headers used for API requests. Defaults to None.
            max_retries: Maximum amount of retry attempts before raising an error. Defaults to 4.
        """
        self.url = url
        self.headers = {'Content-Type': 'application/json', 'Authorization': f'{api_key}', **(headers or {})}
        self.max_retries = int(max_retries)
        self.boards = Boards(self)
        self.groups = Groups(self, self.boards)
        self.items = Items(self)
        self.users = Users(self)
        self._rate_limit_seconds = 60

    async def post_request(self, query: str) -> Dict[str, Any]:
        """
        Executes an asynchronous post request to the Monday.com API with rate limiting and retry logic.

        Args:
            query: The GraphQL query string to be executed.

        Returns:
            A dictionary containing either the successful response data from the API or error information.
            In case of errors, the dictionary will include an 'error' key with a description of the error,
            and potentially a 'data' key with additional error details.

        Note:
            This method handles ComplexityLimitExceeded, MutationLimitExceeded, MondayAPIError, and
            aiohttp.ClientError internally. Instead of raising these exceptions, it returns error
            information in the response dictionary after max retries are exhausted.
        """
        for attempt in range(self.max_retries):
            try:
                response_data = await self._execute_request(query)

                if any('error' in key.lower() for key in response_data.keys()):
                    if 'error_code' in response_data and response_data['error_code'] == 'ComplexityException':
                        reset_in_search = re.search(r'(\d+(?:\.\d+)?) seconds', response_data['error_message'])
                        if reset_in_search:
                            reset_in = math.ceil(float(reset_in_search.group(1)))
                        else:
                            self.logger.error('error getting reset_in_x_seconds: %s', response_data)
                            return {'error': response_data}
                        raise ComplexityLimitExceeded(f'Complexity limit exceeded, retrying after {reset_in} seconds...', reset_in, json_data=response_data)
                    if 'status_code' in response_data and int(response_data['status_code']) == 429:
                        reset_in = self._rate_limit_seconds
                        raise MutationLimitExceeded(f'Rate limit exceeded, retrying after {reset_in} seconds...', reset_in, json_data=response_data)
                    response_data['query'] = query
                    raise MondayAPIError('Unhandled monday.com API error', json_data=response_data)

                return response_data

            except (ComplexityLimitExceeded, MutationLimitExceeded) as e:
                if attempt < self.max_retries - 1:
                    self.logger.warning("Attempt %d failed: %s. Retrying...", attempt + 1, str(e))
                    await asyncio.sleep(e.reset_in)
                else:
                    self.logger.error("Max retries reached. Last error: %s", str(e))
                    return {'error': f"Max retries reached. Last error: {str(e)}", 'data': e.json}
            except MondayAPIError as e:
                self.logger.error("Attempt %d failed: %s", attempt + 1, str(e))
                return {'data': e.json}
            except aiohttp.ClientError as e:
                if attempt < self.max_retries - 1:
                    self.logger.warning("Attempt %d failed due to aiohttp.ClientError: %s. Retrying after 60 seconds...", attempt + 1, str(e))
                    await asyncio.sleep(self._rate_limit_seconds)
                else:
                    self.logger.error("Max retries reached. Last error (aiohttp.ClientError): %s", str(e))
                    return {'error': f"Max retries reached. Last error (aiohttp.ClientError): {str(e)}"}

        return {'error': f'Max retries reached: {response_data}'}

    async def _execute_request(self, query: str) -> Dict[str, Any]:
        """
        Executes a single API request.

        Args:
            query: The GraphQL query to be executed.

        Returns:
            The JSON response from the API.

        Raises:
            aiohttp.ClientError: If there's a client-side error during the request.
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, json={'query': query}, headers=self.headers) as response:
                return await response.json()


logging.getLogger('monday_client').addHandler(logging.NullHandler())
