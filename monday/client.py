"""Client module for interacting with the Monday.com API."""

import asyncio
import logging
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
            headers (dict): HTTP headers used for API requests, including authentication.

    Args:
            api_key (str): The API key for authenticating with the Monday.com API.

    Note:
            Logging can be controlled by configuring the 'monday_client' logger.
            By default, a NullHandler is added to the logger, which suppresses all output.
            To enable logging, configure the logger in your application code. For example:

            ```python
            import logging
            logger = logging.getLogger('monday_client')
            logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
            ```

            To disable all logging (including warnings and errors):

            ```python
            import logging
            logging.getLogger('monday_client').disabled = True
            ```

    Example:
            ```python
            from monday_client import MondayClient
            client = MondayClient(api_key='your_api_key')
            ```
    """

    logger = logging.getLogger(__name__)

    def __init__(
        self,
        api_key: str,
        url: str = 'https://api.monday.com/v2',
        headers: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the MondayClient with the provided API key.

        Args:
            api_key (str): The API key for authenticating with the Monday.com API.
            url (str): The endpoint URL for the Monday.com API. Defaults to 'https://api.monday.com/v2'.
            headers ([Dict[str, Any]]): Additional HTTP headers used for API requests. Defaults to None.
        """
        self.url = url
        self.headers = {'Content-Type': 'application/json', 'Authorization': f'{api_key}', **(headers or {})}
        self.rate_limit_seconds = 60
        self.max_retries = 4
        self.boards = Boards(self)
        self.items = Items(self)

    @board_action('query')
    async def query_board(self, **kwargs) -> Dict[str, Any]:
        """
        Query boards to return metadata about one or multiple boards.

        This method is a wrapper for the Boards.query() method.
        For detailed information on parameters and usage, refer to the Boards.query() method documentation.

        Returns:
            List[Dict[str, Any]]: List of dictionaries containing queried board data.

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

        This method is a wrapper for the Boards.create() method.
        For detailed information on parameters and usage, refer to the Boards.create() method documentation.

        Returns:
            Dict[str, Any]: Dictionary containing info for the new board.

        Raises:
            MondayAPIError: If API request fails or returns unexpected format.
            ValueError: If input parameters are invalid.
        """

    @board_action('duplicate')
    async def duplicate_board(self, **kwargs) -> Dict[str, Any]:
        """
        Duplicate a board.

        This method is a wrapper for the Boards.duplicate() method.
        For detailed information on parameters and usage, refer to the Boards.duplicate() method documentation.

        Returns:
            Dict[str, Any]: Dictionary containing info for the new board.

        Raises:
            ValueError: If input parameters are invalid.
            MondayAPIError: If API request fails or returns unexpected format.
        """

    @board_action('update')
    async def update_board(self, **kwargs) -> Dict[str, Any]:
        """
        Update a board.

        This method is a wrapper for the Boards.update() method.
        For detailed information on parameters and usage, refer to the Boards.update() method documentation.

        Returns:
            Dict[str, Any]: Dictionary containing updated board info.

        Raises:
            ValueError: If input parameters are invalid.
            MondayAPIError: If API request fails or returns unexpected format.
        """

    @board_action('archive')
    async def archive_board(self, **kwargs) -> Dict[str, Any]:
        """
        Archive a board.

        This method is a wrapper for the Boards.archive() method.
        For detailed information on parameters and usage, refer to the Boards.archive() method documentation.

        Returns:
            Dict[str, Any]: Dictionary containing archived board info.

        Raises:
            ValueError: If board_id is not a positive integer.
            MondayAPIError: If API request fails or returns unexpected format.
        """

    @board_action('delete')
    async def delete_board(self, **kwargs) -> Dict[str, Any]:
        """
        Delete a board.

        This method is a wrapper for the Boards.delete() method.
        For detailed information on parameters and usage, refer to the Boards.delete() method documentation.

        Returns:
            Dict[str, Any]: Dictionary containing deleted board info.

        Raises:
            ValueError: If board_id is not a positive integer.
            MondayAPIError: If API request fails or returns unexpected format.
        """

    @item_action('items_page_by_column_values')
    async def items_page_by_column_values(self, **kwargs) -> Dict[str, Any]:
        """
        Query paginated items by their column values.

        This method is a wrapper for the Items.items_page_by_column_values() method.
        For detailed information on parameters and usage, refer to the Items.items_page_by_column_values() method documentation.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing the combined items retrieved.

        Raises:
            ValueError: If board_id is not a positive integer.
            MondayAPIError: If API request fails or returns unexpected format.
        """

    async def post_request(self, query: str) -> Dict[str, Any]:
        """
        Executes an asynchronous post request to the Monday.com API with rate limiting and retry logic.

        Args:
                query (str): The GraphQL query string to be executed.

        Returns:
                Dict[str, Any]: The response data from the API.
        """
        for attempt in range(self.max_retries):
            try:
                response_data = await self._execute_request(query)

                if any('error' in key.lower() for key in response_data.keys()):
                    if 'error_code' in response_data and response_data['error_code'] == 'ComplexityException':
                        reset_in_search = re.search(r'reset in (\d+) seconds', response_data['error_message'])
                        if reset_in_search:
                            reset_in = int(reset_in_search.group(1))
                        else:
                            self.logger.error('error getting reset_in_x_seconds: %s', response_data)
                            return {'error': response_data}
                        raise ComplexityLimitExceeded(f'Complexity limit exceeded, retrying after {reset_in} seconds...', reset_in)
                    if 'status_code' in response_data and int(response_data['status_code']) == 429:
                        reset_in = self.rate_limit_seconds
                        raise MutationLimitExceeded(f'Rate limit exceeded, retrying after {reset_in} seconds...', reset_in)
                    return {'error': response_data}

                return response_data

            except (ComplexityLimitExceeded, MutationLimitExceeded, aiohttp.ClientError) as e:
                if attempt < self.max_retries - 1:
                    self.logger.warning("Attempt %d failed: %s. Retrying...", attempt + 1, str(e))
                    await asyncio.sleep(e.reset_in)
                else:
                    self.logger.error("Max retries reached. Last error: %s", str(e))
                    return {'error': str(e)}

        return {'error': f'Max retries reached: {response_data}'}

    async def _execute_request(self, query: Dict[str, Any]) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, json={'query': query}, headers=self.headers) as response:
                return await response.json()


logging.getLogger('monday_client').addHandler(logging.NullHandler())