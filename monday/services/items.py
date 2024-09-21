import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from ..exceptions import QueryFormatError
from .utils.pagination import paginated_item_request

if TYPE_CHECKING:
    from ..client import MondayClient


class Items:
    logger = logging.getLogger(__name__)

    def __init__(self, client: 'MondayClient'):
        self.client = client

    def items_page_by_column_values(
            self,
            board_id: int,
            columns: str,
            limit: int = 25,
            fields: str = 'cursor items { id name }',
            paginate_items: bool = True
    ) -> Dict[str, Union[bool, List[Dict[str, Any]], Optional[str]]]:
        """
        Retrieves a paginated list of items from a specified board on Monday.com.

        Args:
                board_id (int): The ID of the board from which to retrieve items.
                columns (str): One or more columns and their values to search by.
                limit (int, optional): The maximum number of items to retrieve per page. Defaults to 25.
                fields (str, optional): The fields to include in the response. Defaults to 'cursor items { id name }'.
                paginate_items (bool, optional): Whether to paginate items. Defaults to True.

        Returns:
                Dict[str, Union[bool, List[Dict[str, Any]], Optional[str]]]: A dictionary containing the combined items retrieved
                and a completion status.
                The dictionary has the following structure:

                        - 'items': A list of dictionaries representing the items retrieved.
                        - 'completed': A boolean indicating whether the pagination was completed successfully.
        """
        if not isinstance(board_id, int):
            raise TypeError('board_id must be an int')
        if paginate_items and 'cursor' not in fields:
            raise QueryFormatError(
                'Pagination requires a cursor in the items_page_by_column_values field. '
                'Update your fields parameter to include cursor, e.g.: '
                '"cursor items { id name }"'
            )
        query = f'query {{ items_page_by_column_values (board_id: {board_id}, limit: {limit}, columns: {columns}) {{ {fields} }} }}'
        if paginate_items:
            return paginated_item_request(self.client, query, limit=limit)
        else:
            self.client.post_request(query)
