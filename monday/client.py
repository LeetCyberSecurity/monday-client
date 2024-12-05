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
Client module for interacting with the monday.com API.

This module provides a comprehensive client for interacting with the monday.com GraphQL API.
It includes the MondayClient class, which handles authentication, rate limiting, pagination,
and various API operations.
"""

import asyncio
import logging
import math
import re
from typing import Any, Optional

import aiohttp

from monday.exceptions import (ComplexityLimitExceeded, MondayAPIError,
                               MutationLimitExceeded, QueryFormatError)
from monday.services import Boards, Groups, Items, Users


class MondayClient:
    """
    Client for interacting with the monday.com API.
    This client handles API requests, rate limiting, and pagination for monday.com's GraphQL API.

    It uses a class-level logger named ``monday_client`` for all logging operations.

    Usage:
        .. code-block:: python

            >>> from monday import MondayClient
            >>> monday_client = MondayClient('your_api_key')
            >>> monday_client.boards.query(board_ids=987654321)

    Args:
        api_key: The API key for authenticating with the monday.com API.
        url: The endpoint URL for the monday.com API.
        headers: Additional HTTP headers used for API requests.
        max_retries: Maximum amount of retry attempts before raising an error.

    """

    logger: logging.Logger = logging.getLogger(__name__)
    """
    Class-level logger named ``monday_client`` for all logging operations.

    Note:
        Logging can be controlled by configuring this logger.
        By default, a ``NullHandler`` is added to the logger, which suppresses all output.
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
        headers: Optional[dict[str, Any]] = None,
        max_retries: int = 4
    ):
        """
        Initialize the MondayClient with the provided API key.

        Args:
            api_key: The API key for authenticating with the monday.com API.
            url: The endpoint URL for the monday.com API.
            headers: Additional HTTP headers used for API requests.
            max_retries: Maximum amount of retry attempts before raising an error.
        """
        self.url = url
        self.headers = {'Content-Type': 'application/json', 'Authorization': f'{api_key}', **(headers or {})}
        self.max_retries = int(max_retries)
        self.boards = Boards(self)
        """
        Service for board-related operations

        Type: `Boards <services.html#boards>`_
        """
        self.items = Items(self, self.boards)
        """
        Service for item-related operations

        Type: `Items <services.html#items>`_
        """
        self.groups = Groups(self, self.boards)
        """
        Service for group-related operations

        Type: `Groups <services.html#groups>`_
        """
        self.users = Users(self)
        """
        Service for user-related operations

        Type: `Users <services.html#users>`_
        """
        self._rate_limit_seconds = 60
        self._query_errors = {
            'argumentLiteralsIncompatible'
        }

    async def post_request(
        self,
        query: str
    ) -> dict[str, Any]:
        """
        Executes an asynchronous post request to the monday.com API with rate limiting and retry logic.

        Args:
            query: The GraphQL query string to be executed.

        Returns:
            A dictionary containing the response data from the API.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            MutationLimitExceeded: When the API rate limit is exceeded.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> await monday_client.post_request(
                ...      query='query { boards (ids: 987654321) { id name } }'
                ... )
                {
                    "data": {
                        "boards": [
                            {
                                "id": "987654321",
                                "name": "Board 1"
                            }
                        ]
                    },
                    "account_id": 1234567
                }

        Note:
            This is a low-level method that directly executes GraphQL queries. In most cases, you should use the higher-level
            methods provided by the :ref:`service classes <services_section>` instead, as they handle query construction
            and provide a more user-friendly interface.
        """
        for attempt in range(self.max_retries):
            try:
                response_data = await self._execute_request(query)

                if any('error' in key.lower() for key in response_data.keys()):
                    response_data['query'] = ' '.join(query.split())
                    if 'error_code' in response_data and response_data['error_code'] == 'ComplexityException':
                        reset_in_search = re.search(r'(\d+(?:\.\d+)?) seconds', response_data['error_message'])
                        if reset_in_search:
                            reset_in = math.ceil(float(reset_in_search.group(1)))
                        else:
                            self.logger.error('error getting reset_in_x_seconds: %s', response_data)
                            raise MondayAPIError('Error getting reset_in_x_seconds', json=response_data)
                        raise ComplexityLimitExceeded(f'Complexity limit exceeded, retrying after {reset_in} seconds...', reset_in, json=response_data)
                    if 'status_code' in response_data:
                        if int(response_data['status_code']) == 429:
                            raise MutationLimitExceeded(f'Rate limit exceeded, retrying after {self._rate_limit_seconds} seconds...', self._rate_limit_seconds, json=response_data)
                        else:
                            if 'mapping is not in the expected format' in response_data['error_message'] and 'move_item_to_board' in query:
                                raise QueryFormatError('Columns mapping is not in the expected format. Verify all of your columns are mapped and you do not have formula columns mapped.', json=response_data)
                            raise MondayAPIError(f'Received status code {response_data["status_code"]}: {response_data["error_message"]}', json=response_data)
                    if any('Parse error on' in e['message'] for e in response_data['errors']):
                        raise QueryFormatError('Invalid monday.com GraphQL query', json=response_data)
                    if any(c in self._query_errors for c in [e['extensions']['code'] for e in response_data['errors']]):
                        raise QueryFormatError('Invalid monday.com GraphQL query', json=response_data)
                    raise MondayAPIError('Unhandled monday.com API error', json=response_data)

                return response_data

            except (ComplexityLimitExceeded, MutationLimitExceeded) as e:
                if attempt < self.max_retries - 1:
                    self.logger.warning('Attempt %d failed: %s. Retrying...', attempt + 1, str(e))
                    await asyncio.sleep(e.reset_in)
                else:
                    self.logger.error('Max retries reached. Last error: %s', str(e), exc_info=True)
                    e.args = (f'Max retries ({self.max_retries}) reached',)
                    raise
            except (MondayAPIError, QueryFormatError) as e:
                self.logger.error('Attempt %d failed: %s', attempt + 1, str(e), exc_info=True)
                raise
            except aiohttp.ClientError as e:
                if attempt < self.max_retries - 1:
                    self.logger.warning('Attempt %d failed due to aiohttp.ClientError: %s. Retrying after %d seconds...', attempt + 1, str(e), self._rate_limit_seconds)
                    await asyncio.sleep(self._rate_limit_seconds)
                else:
                    self.logger.error('Max retries reached. Last error (aiohttp.ClientError): %s', str(e), exc_info=True)
                    e.args = (f'Max retries ({self.max_retries}) reached',)
                    raise

        return {'error': f'Max retries reached: {response_data}'}

    async def _execute_request(
        self,
        query: str
    ) -> dict[str, Any]:
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
