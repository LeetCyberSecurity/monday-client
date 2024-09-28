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

from .exceptions import ComplexityLimitExceeded, MutationLimitExceeded
from .services.boards import Boards
from .services.items import Items
from .services.utils.decorators import board_action, item_action


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
        self.items = Items(self)
        self._rate_limit_seconds = 60

    @board_action('query')
    async def query_board(self, **kwargs) -> Dict[str, Any]:
        """
        Query boards to return metadata about one or multiple boards.

        This method is a wrapper for the :meth:`Boards.query() <monday.Boards.query>` method.
        For detailed information on parameters and usage, refer to the :meth:`Boards.query() <monday.Boards.query>` method documentation.

        Returns:
            Dictionary containing queried board data.

        Raises:
            QueryFormatError: If 'items_page' is in fields but 'cursor' is not, when paginate_items is True.
            MondayAPIError: If API request fails or returns unexpected format.
            ValueError: If input parameters are invalid.
            PaginationError: If item pagination fails during the request.
        """

    @board_action('create')
    async def create_board(self, **kwargs) -> Dict[str, Any]:
        """
        Create a new board.

        This method is a wrapper for the :meth:`Boards.create() <monday.Boards.create>` method.
        For detailed information on parameters and usage, refer to the :meth:`Boards.create() <monday.Boards.create>` method documentation.

        Returns:
            Dictionary containing info for the new board.

        Raises:
            MondayAPIError: If API request fails or returns unexpected format.
            ValueError: If input parameters are invalid.
        """

    @board_action('duplicate')
    async def duplicate_board(self, **kwargs) -> Dict[str, Any]:
        """
        Duplicate a board.

        This method is a wrapper for the :meth:`Boards.duplicate() <monday.Boards.duplicate>` method.
        For detailed information on parameters and usage, refer to the :meth:`Boards.duplicate() <monday.Boards.duplicate>` method documentation.

        Returns:
            Dictionary containing info for the new board.

        Raises:
            ValueError: If input parameters are invalid.
            MondayAPIError: If API request fails or returns unexpected format.
        """

    @board_action('update')
    async def update_board(self, **kwargs) -> Dict[str, Any]:
        """
        Update a board.

        This method is a wrapper for the :meth:`Boards.update() <monday.Boards.update>` method.
        For detailed information on parameters and usage, refer to the :meth:`Boards.update() <monday.Boards.update>` method documentation.

        Returns:
            Dictionary containing updated board info.

        Raises:
            ValueError: If input parameters are invalid.
            MondayAPIError: If API request fails or returns unexpected format.
        """

    @board_action('archive')
    async def archive_board(self, **kwargs) -> Dict[str, Any]:
        """
        Archive a board.

        This method is a wrapper for the :meth:`Boards.archive() <monday.Boards.archive>` method.
        For detailed information on parameters and usage, refer to the :meth:`Boards.archive() <monday.Boards.archive>` method documentation.

        Returns:
            Dictionary containing archived board info.

        Raises:
            ValueError: If board_id is not a positive integer.
            MondayAPIError: If API request fails or returns unexpected format.
        """

    @board_action('delete')
    async def delete_board(self, **kwargs) -> Dict[str, Any]:
        """
        Delete a board.

        This method is a wrapper for the :meth:`Boards.delete() <monday.Boards.delete>` method.
        For detailed information on parameters and usage, refer to the :meth:`Boards.delete() <monday.Boards.delete>` method documentation.

        Returns:
            Dictionary containing deleted board info.

        Raises:
            ValueError: If board_id is not a positive integer.
            MondayAPIError: If API request fails or returns unexpected format.
        """

    @item_action('items_page_by_column_values')
    async def items_page_by_column_values(self, **kwargs) -> Dict[str, Any]:
        """
        Query paginated items by their column values.

        This method is a wrapper for the :meth:`Items.items_page_by_column_values() <monday.Items.items_page_by_column_values>` method.
        For detailed information on parameters and usage, refer to the :meth:`Items.items_page_by_column_values() <monday.Items.items_page_by_column_values>` method documentation.

        Returns:
            Dictionary containing the items retrieved.

        Raises:
            ValueError: If board_id is not a positive integer.
            MondayAPIError: If API request fails or returns unexpected format.
        """

    async def post_request(self, query: str) -> Dict[str, Any]:
        """
        Executes an asynchronous post request to the Monday.com API with rate limiting and retry logic.

        Args:
            query: The GraphQL query string to be executed.

        Returns:
            The response data from the API.

        Raises:
            ComplexityLimitExceeded: If the complexity limit is exceeded.
            MutationLimitExceeded: If the mutation limit is exceeded.
            aiohttp.ClientError: If there's a client-side error during the request.
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
                    raise aiohttp.ClientError

                return response_data

            except (ComplexityLimitExceeded, MutationLimitExceeded) as e:
                if attempt < self.max_retries - 1:
                    self.logger.warning("Attempt %d failed: %s. Retrying...", attempt + 1, str(e))
                    await asyncio.sleep(e.reset_in)
                else:
                    self.logger.error("Max retries reached. Last error: %s", str(e))
                    return {'error': f"Max retries reached. Last error: {str(e)}", 'data': e.json}
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
