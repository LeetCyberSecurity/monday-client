"""Utility functions and classes for handling pagination."""

import json
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ...exceptions import PaginationError

if TYPE_CHECKING:
    from ...client import MondayClient

logger = logging.getLogger(__name__)


def extract_items_page_value(data):
    """
    Recursively extract the 'items_page' value from a nested dictionary or list.

    Args:
        data (dict or list): The dictionary or list to search.

    Returns:
        dict or None: The 'items_page' value if found; otherwise, None.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'items_page':
                return value
            else:
                result = extract_items_page_value(value)
                if result is not None:
                    return result
    elif isinstance(data, list):
        for item in data:
            result = extract_items_page_value(item)
            if result is not None:
                return result
    return None


def extract_cursor_from_response(response_data: Dict[str, Any]) -> Optional[str]:
    """
    Recursively extract the 'cursor' value from the response data.

    Args:
        response_data (Dict[str, Any]): The response data containing the cursor information.

    Returns:
        Optional[str]: The extracted cursor value, or None if not found.
    """
    if isinstance(response_data, dict):
        for key, value in response_data.items():
            if key == 'cursor':
                return value
            else:
                result = extract_cursor_from_response(value)
                if result is not None:
                    return result
    elif isinstance(response_data, list):
        for item in response_data:
            result = extract_cursor_from_response(item)
            if result is not None:
                return result
    return None


def extract_items_from_response(data: Any) -> List[Dict[str, Any]]:
    """
    Recursively extract items from the response data.

    Args:
        data (Any): The response data containing the items.

    Returns:
        List[Dict[str, Any]]: A list of extracted items.
    """
    items = []

    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'items' and isinstance(value, list):
                items.extend(value)
            else:
                items.extend(extract_items_from_response(value))
    elif isinstance(data, list):
        for item in data:
            items.extend(extract_items_from_response(item))

    return items


def extract_items_from_query(query: str) -> Optional[str]:
    """
    Extract the items block from the query string.

    Args:
        query (str): The GraphQL query string containing the items block.

    Returns:
        Optional[str]: The items block as a string, or None if not found.
    """
    # Find the starting index of 'items {'
    start_index = query.find('items {')
    if start_index == -1:
        return None

    # Initialize brace counters
    brace_count = 0
    end_index = start_index

    # Iterate over the query string starting from 'items {'
    for i in range(start_index, len(query)):
        if query[i] == '{':
            brace_count += 1
        elif query[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end_index = i + 1
                break

    # If braces are unbalanced
    if brace_count != 0:
        return None

    # Extract the 'items' block
    items_block = query[start_index:end_index]

    # Remove any 'cursor' occurrences within the items block, if needed
    items_block = items_block.replace('cursor', '').strip()

    return items_block


async def paginated_item_request(
    client: 'MondayClient',
    query: str,
    limit: int = 25,
    _cursor: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes a paginated request to retrieve items from Monday.com.

    Args:
        client (MondayClient): The MondayClient instance to execute the request.
        query (str): The GraphQL query string.
        limit (int, optional): Maximum items per page. Defaults to 25.
        _cursor (str, optional): Starting cursor for pagination. Defaults to None.

    Returns:
        Dict[str, Any]: A dictionary containing:
        - 'items': List of retrieved items.

    Raises:
        PaginationError: If item extraction fails.
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
            paginated_query = f"""
                query {{
                    next_items_page (
                        limit: {limit},
                        cursor: "{cursor}"
                    ) {{
                        cursor {items_value}
                    }}
                }}
            """

        response_data = await client.post_request(paginated_query)
        if 'error' in response_data:
            return response_data

        items = extract_items_from_response(response_data)
        if not items:
            logger.error('Failed to extract items from response')
            logger.error(json.dumps(response_data))
            raise PaginationError('Item pagination failed')
        combined_items.extend(items)

        cursor = extract_cursor_from_response(response_data)
        if not cursor:
            break

    return {'items': combined_items}
