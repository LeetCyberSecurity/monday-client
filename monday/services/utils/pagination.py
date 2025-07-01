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
Module for handling pagination in monday.com API requests.

This module provides utilities and types for handling paginated requests and extracting
pagination-related data from API responses.
"""

import json
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional, Union

from monday.exceptions import PaginationError
from monday.services.utils import check_query_result

if TYPE_CHECKING:
    from monday import MondayClient

logger: logging.Logger = logging.getLogger(__name__)


@dataclass
class ItemsPage:
    """
    Represents a paginated page of Monday.com items with cursor for navigation.

    This dataclass maps to the Monday.com API items page structure, containing
    a list of items and a cursor for retrieving the next page.

    See also:
        https://developer.monday.com/api-reference/reference/items#fields
    """

    items: list[Any] | None = None
    """List of items"""

    cursor: str = ''
    """cursor for retrieving the next page of items"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        result = {}

        if self.items:
            result['items'] = [item.to_dict() if hasattr(item, 'to_dict') else item for item in self.items]
        if self.cursor:
            result['cursor'] = self.cursor

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'ItemsPage':
        """Create from dictionary."""
        from monday.types.item import Item

        return cls(
            items=[Item.from_dict(item) if hasattr(Item, 'from_dict') else item for item in data.get('items', [])] if data.get('items') else None,
            cursor=str(data.get('cursor', ''))
        )


@dataclass
class PaginatedResult:
    """
    Type definition for paginated request results.

    This structure is used by pagination utilities to return structured
    results from paginated API requests.
    """

    items: list[Any]
    """The list of items retrieved from the paginated request"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {
            'items': [item.to_dict() if hasattr(item, 'to_dict') else item for item in self.items]
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'PaginatedResult':
        """Create from dictionary."""
        return cls(
            items=data.get('items', [])
        )


def extract_items_page_value(
    data: Union[dict[str, Any], list]
) -> Optional[Any]:
    """
    Recursively extract the 'items_page' value from a nested dictionary or list.

    Args:
        data: The dictionary or list to search.

    Returns:
        The 'items_page' value if found; otherwise, None.
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


def extract_cursor_from_response(
    response_data: dict[str, Any]
) -> Optional[str]:
    """
    Recursively extract the 'cursor' value from the response data.

    Args:
        response_data: The response data containing the cursor information.

    Returns:
        The extracted cursor value, or None if not found.
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


def extract_items_from_response(
    data: Any
) -> list[dict[str, Any]]:
    """
    Recursively extract items from the response data.

    Args:
        data: The response data containing the items.

    Returns:
        A list of extracted items.
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


def extract_items_from_query(
    query: str
) -> Optional[str]:
    """
    Extract the items block from the query string.

    Args:
        query: The GraphQL query string containing the items block.

    Returns:
        The items block as a string, or None if not found.
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
    cursor: Optional[str] = None
) -> PaginatedResult:
    """
    Executes a paginated request to retrieve items from monday.com.

    Args:
        client: The MondayClient instance to execute the request.
        query: The GraphQL query string.
        limit: Maximum items per page.
        cursor: Starting cursor for pagination.

    Returns:
        PaginatedResult dataclass instance containing the list of retrieved items.

    Raises:
        PaginationError: If item extraction fails.
    """
    combined_items = []
    cursor = cursor or 'start'

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
            return PaginatedResult(items=[])
        data = check_query_result(response_data)

        if 'boards' in data['data']:
            for board in data['data']['boards']:
                if board['items_page'] is None:
                    logger.error('Failed to extract items from response')
                    raise PaginationError('Item pagination failed', json=data)
                board_data = {
                    'board_id': board['id'],
                    'items': board['items_page']['items']
                }
                existing_board = next((b for b in combined_items if b['board_id'] == board['id']), None)
                if existing_board:
                    existing_board['items'].extend(board_data['items'])
                else:
                    combined_items.append(board_data)
        else:
            items = extract_items_from_response(data)
            if not items:
                if 'data' not in data:
                    logger.error('Failed to extract items from response')
                    logger.error(json.dumps(response_data))
                    raise PaginationError('Item pagination failed')
            else:
                combined_items.extend(items)

        cursor = extract_cursor_from_response(data)
        if not cursor:
            break

    return PaginatedResult(items=combined_items)
