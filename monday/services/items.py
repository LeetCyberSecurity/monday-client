import json
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from .utils.pagination import paginated_item_request

if TYPE_CHECKING:
    from ..client import MondayClient

class Items:
	logger = logging.getLogger(__name__)

	def __init__(self, client: 'MondayClient'):
		self.client = client

	def items_page(
		self,
		board_id: int,
		query_params: str = '',
		limit: int = 25,
		fields: str = 'id name column_values { id text value column { title } }'
	) -> Dict[str, Union[bool, List[Dict[str, Any]], Optional[str]]]:
		"""
		Retrieves a paginated list of items from a specified board on Monday.com.

		Args:
			board_id (int): The ID of the board from which to retrieve items.
			query_params (str, optional): Additional query parameters to filter the items. Defaults to ''.
			limit (int, optional): The maximum number of items to retrieve per page. Defaults to 25.
			fields (str, optional): The fields to include in the response. Defaults to 'id name column_values { id text value column { title } }'.

		Returns:
			Dict[str, Union[bool, List[Dict[str, Any]], Optional[str]]]: A dictionary containing the combined items retrieved
			and a completion status. 
			The dictionary has the following structure:
				
				- 'items': A list of dictionaries representing the items retrieved.
				- 'completed': A boolean indicating whether the pagination was completed successfully.
		"""
		query = f'query {{ boards (ids: {board_id}) {{ items_page (limit: {limit}{", query_params: " + query_params if query_params else ""}) {{ cursor items {{ {fields} }} }} }} }}'
		return paginated_item_request(self.client, query, limit=limit)
	