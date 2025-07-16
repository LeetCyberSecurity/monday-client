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
from typing import Any

import aiohttp

from monday.exceptions import (
    ComplexityLimitExceeded,
    MondayAPIError,
    MutationLimitExceeded,
    QueryFormatError,
)
from monday.services.boards import Boards
from monday.services.groups import Groups
from monday.services.items import Items
from monday.services.subitems import Subitems
from monday.services.users import Users
from monday.services.utils.error_handlers import ErrorHandler, check_query_result


class MondayClient:
    """
    Client for interacting with the monday.com API.
    This client handles API requests, rate limiting, and pagination for monday.com's GraphQL API.

    It uses a class-level logger named ``monday`` for all logging operations.

    Usage:
        .. code-block:: python

            >>> from monday import MondayClient
            >>> monday_client = MondayClient('your_api_key')
            >>> monday_client.boards.query(board_ids=987654321)

    Args:
        api_key: The API key for authenticating with the monday.com API.
        url: The endpoint URL for the monday.com API.
        version: The monday.com API version to use. If None, will automatically fetch the current version.
        headers: Additional HTTP headers used for API requests.
        max_retries: Maximum amount of retry attempts before raising an error.

    """

    logger: logging.Logger = logging.getLogger(__name__)
    """
    Class-level logger named ``monday`` for all logging operations.

    Note:
        Logging can be controlled by configuring this logger.
        By default, a ``NullHandler`` is added to the logger, which suppresses all output.
        To enable logging, configure the logger in your application code. For example:

        .. code-block:: python

            import logging

            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.StreamHandler(),
                ]
            )
            logging.getLogger('monday').setLevel(logging.DEBUG)

            # Always remove the NullHandler that monday-client adds and add a real handler
            monday_logger = logging.getLogger('monday')
            for handler in monday_logger.handlers[:]:
                if isinstance(handler, logging.NullHandler):
                    monday_logger.removeHandler(handler)

            # Add a real handler to monday logger if it doesn't have one
            if not monday_logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                monday_logger.addHandler(handler)

        To disable all logging (including warnings and errors):

        .. code-block:: python

            import logging
            logging.getLogger('monday').disabled = True
    """

    def __init__(
        self,
        api_key: str,
        url: str = 'https://api.monday.com/v2',
        version: str | None = None,
        headers: dict[str, Any] | None = None,
        max_retries: int = 4,
    ):
        """
        Initialize the MondayClient with the provided API key.

        Args:
            api_key: The API key for authenticating with the monday.com API.
            url: The endpoint URL for the monday.com API.
            version: The monday.com API version to use. If None, will automatically fetch the current version.
            headers: Additional HTTP headers used for API requests.
            max_retries: Maximum amount of retry attempts before raising an error.

        """
        self.url = url
        self.api_key = api_key
        self.version = version
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': api_key,
            **(headers or {}),
        }
        self.max_retries = int(max_retries)

        # Initialize service instances
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
        self.subitems = Subitems(self, self.items, self.boards)
        """
        Service for subitem-related operations

        Type: `Subitems <services.html#subitems>`_
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
        self._query_errors = {'argumentLiteralsIncompatible'}
        self._error_handler = ErrorHandler(self._rate_limit_seconds)

    async def post_request(self, query: str) -> dict[str, Any]:
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
        # Ensure version is set before making any requests
        await self._ensure_version_set()

        response_data = None
        for attempt in range(self.max_retries):
            response_headers = {}

            try:
                response_data, response_headers = await self._execute_request(query)
                self._handle_api_errors(response_data, response_headers, query)
            except (ComplexityLimitExceeded, MutationLimitExceeded) as e:
                if attempt < self.max_retries - 1:
                    self.logger.warning(
                        'Attempt %d failed: %s. Retrying...', attempt + 1, str(e)
                    )
                    await asyncio.sleep(e.reset_in)
                else:
                    self.logger.exception('Max retries reached. Last error: ')
                    e.args = (f'Max retries ({self.max_retries}) reached',)
                    raise
            except (MondayAPIError, QueryFormatError):
                self.logger.exception('Attempt %d failed', attempt + 1)
                raise
            except aiohttp.ClientError as e:
                if attempt < self.max_retries - 1:
                    # Check for Retry-After header even for client errors
                    retry_seconds = self._error_handler.get_retry_after_seconds(
                        response_headers, self._rate_limit_seconds
                    )
                    self.logger.warning(
                        'Attempt %d failed due to aiohttp.ClientError: %s. Retrying after %d seconds...',
                        attempt + 1,
                        str(e),
                        retry_seconds,
                    )
                    await asyncio.sleep(retry_seconds)
                else:
                    self.logger.exception(
                        'Max retries reached. Last error (aiohttp.ClientError)'
                    )
                    e.args = (f'Max retries ({self.max_retries}) reached',)
                    raise
            else:
                # Always check for legacy errors before returning
                check_query_result(response_data)
                return response_data

        return {'error': f'Max retries reached: {response_data}'}

    def _handle_api_errors(
        self,
        response_data: dict[str, Any],
        response_headers: dict[str, str],
        query: str,
    ) -> None:
        """
        Handle API errors and raise appropriate exceptions.

        Args:
            response_data: The response data from the API.
            response_headers: HTTP response headers from the API.
            query: The original GraphQL query.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds complexity limits.
            MutationLimitExceeded: When the API rate limit is exceeded.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.

        """
        # Handle GraphQL-compliant error format (2025-01+)
        if response_data.get('errors'):
            self._error_handler.handle_graphql_errors(
                response_data, response_headers, query
            )

    async def _ensure_version_set(self) -> None:
        """
        Ensure the API version is set, fetching the current version if needed.
        """
        if self.version is None:
            self.version = await self._get_current_version()
            self.headers['API-Version'] = self.version

    async def _get_current_version(self) -> str:
        """
        Fetch the current monday.com API version.

        Returns:
            The current API version string.

        Raises:
            MondayAPIError: If unable to fetch the current version.

        """
        # Use a temporary session without version header to query versions
        temp_headers = {
            'Content-Type': 'application/json',
            'Authorization': self.api_key,
        }

        query = """
        query {
            versions {
                kind
                value
                display_name
            }
        }
        """

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    self.url, json={'query': query}, headers=temp_headers
                ) as response,
            ):
                data = await response.json()

                if 'errors' in data:
                    raise MondayAPIError(
                        message=f'Failed to fetch API versions: {data["errors"]}',
                        json=data,
                    )

                versions = data.get('data', {}).get('versions', [])
                current_version = next(
                    (v['value'] for v in versions if v['kind'] == 'current'), None
                )

                if not current_version:
                    raise MondayAPIError(
                        message='No current version found in API response', json=data
                    )

                self.logger.info(
                    'Using current monday.com API version: %s', current_version
                )
                return current_version

        except aiohttp.ClientError as e:
            raise MondayAPIError(
                message=f'Network error while fetching API version: {e}'
            ) from e

    async def _execute_request(
        self, query: str
    ) -> tuple[dict[str, Any], dict[str, str]]:
        """
        Executes a single API request.

        Args:
            query: The GraphQL query to be executed.

        Returns:
            A tuple containing (JSON response from the API, HTTP response headers).

        Raises:
            aiohttp.ClientError: If there's a client-side error during the request.

        """
        async with (
            aiohttp.ClientSession() as session,
            session.post(
                self.url, json={'query': query}, headers=self.headers
            ) as response,
        ):
            response_headers = dict(response.headers)
            try:
                response_data = await response.json()
            except aiohttp.ContentTypeError:
                # Handle non-JSON responses
                text_response = await response.text()
                return {
                    'error': f'Non-JSON response: {text_response[:200]}'
                }, response_headers
            else:
                return response_data, response_headers


logging.getLogger('monday').addHandler(logging.NullHandler())
