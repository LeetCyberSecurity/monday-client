from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

if TYPE_CHECKING:
    from ...client import MondayClient

import json
import logging
import re

from ...exceptions import PaginationError

logger = logging.getLogger(__name__)

def extract_cursor_from_response(response_data: str) -> Optional[str]:
    cursor_pattern = re.compile(r'"cursor":\s*(?:"([^"]+)"|null)')
    match = cursor_pattern.search(response_data)
    if match:
        return match.group(1)
    else:
        return None

def extract_items_from_response(response_data: str) -> List[Dict[str, Any]]:
    items_pattern = re.compile(r'"items"\s*:\s*(\[(?:[^[\]]*|\[(?:[^[\]]*|\[[^[\]]*\])*\])*\])')
    matches = items_pattern.findall(response_data)
    all_items = []
    for match in matches:
        try:
            items = json.loads(match)
            all_items.extend(items)
        except json.JSONDecodeError:
            pass
    return all_items

def extract_items_from_query(query: str) -> Optional[str]:
    items_query_pattern = re.compile(r'items\s*{(?:[^{}]|{(?:[^{}]|{(?:[^{}]|{[^{}]*})*})*})*}')
    match = items_query_pattern.search(query)
    if match:
        items_value = match.group(0)
        items_value = re.sub(r'\s*cursor\s*(?=})', '', items_value)
        return items_value
    else:
        return None

def paginated_item_request(
        client: 'MondayClient',
        query: str,
        limit: int = 25,
        _cursor: Optional[str] = None
    ) -> Dict[str, Union[bool, List[Dict[str, Any]], Optional[str]]]:
    """
    Executes a paginated request to retrieve items from Monday.com.

    This method handles the pagination logic to retrieve all items from a board
    by repeatedly querying the API until all items are fetched.

    Args:
        client (Any): The client instance to execute the request.
        query (str): The GraphQL query string to be executed.
        limit (int, optional): The maximum number of items to retrieve per page. Defaults to 25.
        _cursor (str, optional): Specify a cursor to begin the paginated search with. Defaults to None.

    Returns:
        Dict[str, Union[bool, List[Dict[str, Any]], Optional[str]]]: A dictionary containing the combined items retrieved,
        a completion status, and optionally the query string if an error occurs. The dictionary has the following structure:
            
            - 'items': A list of dictionaries representing the items retrieved.
            - 'completed': A boolean indicating whether the pagination was completed successfully.
            - 'query' (optional): The query string if an error occurs.
    """
    combined_items = []
    cursor = _cursor or 'start'

    while True:
        if cursor == 'start':
            paginated_query = query
        else:
            items_value = extract_items_from_query(query)
            if not items_value:
                logger.error('Failed to extract items from query')
                logger.error(items_value)
                raise PaginationError('Item pagination failed')
            paginated_query = f'query {{ next_items_page (limit: {limit}, cursor: "{cursor}") {{ cursor {items_value} }} }}'
        
        response_data = client._execute_post_request(paginated_query)
        if 'error' in response_data:
            return response_data
        
        items = extract_items_from_response(json.dumps(response_data))
        if not items and not isinstance(items, list):
            logger.error('Failed to extract items from response')
            logger.error(json.dumps(response_data))
            raise PaginationError('Item pagination failed')
        combined_items.extend(items)

        cursor = extract_cursor_from_response(json.dumps(response_data))
        if not cursor:
            break

    return {'items': combined_items, 'completed': True}