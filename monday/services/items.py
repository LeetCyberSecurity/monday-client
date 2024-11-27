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
Module for handling Monday.com item-related services.

This module provides a comprehensive set of operations for managing items in
Monday.com boards.

This module is part of the monday-client package and relies on the MondayClient
for making API requests. It also utilizes various utility functions to ensure proper 
data handling and error checking.

Usage of this module requires proper authentication and initialization of the
MondayClient instance.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Union

from monday.exceptions import MondayAPIError
from monday.services.utils import (GraphQLQueryBuilder, check_query_result,
                                   paginated_item_request)

if TYPE_CHECKING:
    from monday import MondayClient
    from monday.services import Boards


class Items:
    """
    Handles operations related to Monday.com items.

    This class provides a comprehensive set of methods for interacting with items
    on Monday.com boards.
    It encapsulates functionality for querying and managing items, always in the
    context of their parent boards.

    Note:
        This class requires an initialized MondayClient instance for making API requests.
    """

    logger: logging.Logger = logging.getLogger(__name__)

    def __init__(
        self,
        client: 'MondayClient',
        boards: 'Boards'
    ):
        """
        Initialize an Items instance with specified parameters.

        Args:
            client: The MondayClient instance to use for API requests.
            boards: The Boards instance to use for board-related operations.
        """
        self.client: 'MondayClient' = client
        self.boards: 'Boards' = boards

    async def query(
        self,
        item_ids: Union[int, List[int]],
        limit: int = 25,
        page: int = 1,
        exclude_nonactive: bool = False,
        newest_first: bool = False,
        fields: str = 'id'
    ) -> List[Dict[str, Any]]:
        """
        Query items to return metadata about one or multiple items.

        Args:
            item_ids: The ID or list of IDs of the specific items, subitems, or parent items to return. You can only return up to 100 IDs at a time.
            limit: The maximum number of items to retrieve per page.
            page: The page number at which to start.
            exclude_nonactive: Excludes items that are inactive, deleted, or belong to deleted items.
            newest_first: Lists the most recently created items at the top.
            fields: The fields to include in the response.

        Returns:
            A list of dictionaries containing the items retrieved.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Note:
            To return all items on a board, use :meth:`Items.page() <monday.Items.page>` or :meth:`Items.page_by_column_values() <monday.Items.page_by_column_values>` instead.
        """

        args = {
            'ids': item_ids,
            'limit': limit,
            'page': page,
            'exclude_nonactive': exclude_nonactive,
            'newest_first': newest_first,
            'fields': fields
        }

        items_data = []
        while True:

            query_string = GraphQLQueryBuilder.build_query(
                'items',
                'query',
                args
            )

            query_result = await self.client.post_request(query_string)

            data = check_query_result(query_result)

            if not data['data']['items']:
                break

            items_data.extend(data['data']['items'])

            args['page'] += 1

        return items_data

    async def create(
        self,
        board_id: int,
        item_name: str,
        column_values: Optional[Dict[str, Any]] = None,
        group_id: Optional[str] = None,
        create_labels_if_missing: bool = False,
        position_relative_method: Optional[Literal['before_at', 'after_at']] = None,
        relative_to: Optional[int] = None,
        fields: str = 'id'
    ) -> Dict[str, Any]:
        """
        Create a new item on a board.

        Args:
            board_id: The ID of the board where the item will be created.
            item_name: The name of the item.
            column_values: Column values for the item.
            group_id: The ID of the group where the item will be created.
            create_labels_if_missing: Creates status/dropdown labels if they are missing.
            position_relative_method: Specify whether you want to create the new item above or below the item given to relative_to.
            relative_to: The ID of the item you want to create the new one in relation to.
            fields: Fields to query back from the created item.

        Returns:
            Dictionary containing info for the new item.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
        """

        args = {
            'board_id': board_id,
            'item_name': item_name,
            'column_values': column_values,
            'group_id': group_id,
            'create_labels_if_missing': create_labels_if_missing,
            'position_relative_method': position_relative_method,
            'relative_to': relative_to,
            'fields': fields
        }

        query_string = GraphQLQueryBuilder.build_query(
            'create_item',
            'mutation',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['create_item']

    async def duplicate(
        self,
        item_id: int,
        board_id: int,
        with_updates: bool = False,
        fields: str = 'id'
    ) -> Dict[str, Any]:
        """
        Duplicate an item.

        Args:
            item_id: The ID of the item to be duplicated.
            board_id: The ID of the board where the item will be duplicated.
            with_updates: Duplicates the item with existing updates.
            fields: Fields to query back from the duplicated item.

        Returns:
            Dictionary containing info for the duplicated item.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
        """
        args = {
            'item_id': item_id,
            'board_id': board_id,
            'with_updates': with_updates,
            'fields': fields
        }

        query_string = GraphQLQueryBuilder.build_query(
            'duplicate_item',
            'mutation',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['duplicate_item']

    async def move_to_group(
        self,
        item_id: int,
        group_id: str,
        fields: str = 'id'
    ) -> Dict[str, Any]:
        """
        Move an item to a different group.

        Args:
            item_id: The ID of the item to be moved.
            group_id: The ID of the group to move the item to.
            fields: Fields to query back from the moved item.

        Returns:
            Dictionary containing info for the moved item.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
        """
        args = {
            'item_id': item_id,
            'group_id': group_id,
            'fields': fields
        }

        query_string = GraphQLQueryBuilder.build_query(
            'move_item_to_group',
            'mutation',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['move_item_to_group']

    async def move_to_board(
        self,
        item_id: int,
        board_id: int,
        group_id: str,
        columns_mapping: Optional[List[Dict[str, str]]] = None,
        subitems_columns_mapping: Optional[List[Dict[str, str]]] = None,
        fields: str = 'id'
    ) -> Dict[str, Any]:
        """
        Move an item to a different board.

        Args:
            item_id: The ID of the item to be moved.
            board_id: The ID of the board to move the item to.
            group_id: The ID of the group to move the item to.
            columns_mapping: Defines the column mapping between the original and target board.
            subitems_columns_mapping: Defines the subitems' column mapping between the original and target board.
            fields: Fields to query back from the moved item.

        Returns:
            Dictionary containing info for the moved item.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
        """
        args = {
            'item_id': item_id,
            'board_id': board_id,
            'group_id': group_id,
            'columns_mapping': columns_mapping,
            'subitems_columns_mapping': subitems_columns_mapping,
            'fields': fields
        }

        query_string = GraphQLQueryBuilder.build_query(
            'move_item_to_board',
            'mutation',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['move_item_to_board']

    async def archive(
        self,
        item_id: int,
        fields: str = 'id'
    ) -> Dict[str, Any]:
        """
        Archive an item.

        Args:
            item_id: The ID of the item to be archived.
            fields: Fields to query back from the archived item.

        Returns:
            Dictionary containing info for the archived item.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
        """
        args = {
            'item_id': item_id,
            'fields': fields
        }

        query_string = GraphQLQueryBuilder.build_query(
            'archive_item',
            'mutation',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['archive_item']

    async def delete(
        self,
        item_id: int,
        fields: str = 'id'
    ) -> Dict[str, Any]:
        """
        Delete an item.

        Args:
            item_id: The ID of the item to be deleted.
            fields: Fields to query back from the deleted item.

        Returns:
            Dictionary containing info for the deleted item.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
        """
        args = {
            'item_id': item_id,
            'fields': fields
        }

        query_string = GraphQLQueryBuilder.build_query(
            'delete_item',
            'mutation',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['delete_item']

    async def clear_updates(
        self,
        item_id: int,
        fields: str = 'id'
    ) -> Dict[str, Any]:
        """
        Clear an item's updates.

        Args:
            item_id: The ID of the item to be cleared.
            fields: Fields to query back from the cleared item.

        Returns:
            Dictionary containing info for the cleared item.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
        """
        args = {
            'item_id': item_id,
            'fields': fields
        }

        query_string = GraphQLQueryBuilder.build_query(
            'clear_item_updates',
            'mutation',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['clear_item_updates']

    async def page_by_column_values(
        self,
        board_id: int,
        columns: List[Dict[str, Any]],
        limit: int = 25,
        paginate_items: bool = True,
        fields: str = 'id'
    ) -> List[Dict[str, Any]]:
        """
        Retrieves a paginated list of items from a specified board on Monday.com.

        Args:
            board_id: The ID of the board from which to retrieve items.
            columns: One or more columns and their values to search by.
            limit: The maximum number of items to retrieve per page.
            paginate_items: Whether to paginate items.
            fields: The fields to include in the response.

        Returns:
            A list of dictionaries containing the combined items retrieved.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
            PaginationError: If pagination fails.
        """
        args = {
            'board_id': board_id,
            'columns': columns,
            'fields': f'cursor items {{ {fields} }}'
        }

        query_string = GraphQLQueryBuilder.build_query(
            'items_page_by_column_values',
            'query',
            args
        )

        if paginate_items:
            data = await paginated_item_request(
                self.client,
                query_string,
                limit=limit
            )
            if 'error' in data:
                check_query_result(data)
        else:
            query_result = await self.client.post_request(query_string)
            data = check_query_result(query_result)
            data = {'items': data['data']['items_page_by_column_values']['items']}

        return data

    async def page(
        self,
        board_ids: Union[int, List[int]],
        query_params: Optional[str] = None,
        limit: int = 25,
        group_id: Optional[str] = None,
        paginate_items: bool = True,
        fields: str = 'id'
    ) -> List[Dict[str, Any]]:
        """
        Retrieves a paginated list of items from specified boards.

        Args:
            board_ids: The ID or list of IDs of the boards from which to retrieve items.
            query_params: A set of parameters to filter, sort, and control the scope of the underlying boards query.
                          Use this to customize the results based on specific criteria.
            limit: The maximum number of items to retrieve per page.
            group_id: Only retrieve items from the specified group ID.
            paginate_items: Whether to paginate items.
            fields: The fields to include in the response.

        Returns:
            A list of dictionaries containing the board IDs and their combined items retrieved.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
        """

        group_query = f'groups (ids: "{group_id}") {{' if group_id else ''
        group_query_end = '}' if group_id else ''
        fields = f"""
            id 
            {group_query} 
            items_page (
                limit: {limit} 
                {f', query_params: {query_params}' if query_params else ''}
            ) {{
                cursor
                items {{ {fields} }}
            }}
            {group_query_end}
        """

        data = await self.boards.query(
            board_ids,
            fields=fields,
            paginate_items=paginate_items,
            items_page_limit=limit
        )

        return data

    async def get_column_values(
        self,
        item_id: int,
        column_ids: Optional[List[str]] = None,
        fields: str = 'id'
    ) -> List[Dict[str, Any]]:
        """
        Retrieves a list of column values for a specific item.

        Args:
            item_id: The ID of the item.
            column_ids: The specific column IDs to return. Will return all columns if no IDs specified.
            fields: Additional fields to query from the item column values.

        Returns:
            A list of dictionaries containing the item column values.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
        """

        column_ids = [f'"{i}"' for i in column_ids] if column_ids else None

        fields = f"""
            column_values {f"(ids: [{', '.join(column_ids)}])" if column_ids else ''} {{ 
                {fields} 
            }}
        """

        args = {
            'item_id': item_id,
            'fields': fields
        }

        query_string = GraphQLQueryBuilder.build_query(
            'items',
            'query',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        try:
            items = data['data']['items'][0]
        except IndexError as e:
            raise MondayAPIError from e

        return items['column_values']

    async def change_column_values(
        self,
        item_id: int,
        column_values: Dict[str, Any],
        create_labels_if_missing: bool = False,
        fields: str = 'id',
    ) -> Dict[str, Any]:
        """
        Change an item's column values.

        Args:
            item_id: The ID of the item.
            column_values: The updated column values.
            fields: Additional fields to query.

        Returns:
            Dictionary containing info for the updated columns.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
        """

        board_id_query = await self.query(item_id, fields='board { id }')
        board_id = int(board_id_query[0]['board']['id'])

        args = {
            'item_id': item_id,
            'board_id': board_id,
            'column_values': column_values,
            'create_labels_if_missing': create_labels_if_missing,
            'fields': fields
        }

        query_string = GraphQLQueryBuilder.build_query(
            'change_multiple_column_values',
            'mutation',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['change_multiple_column_values']

    async def get_name(
        self,
        item_id: int
    ) -> str:
        """
        Get an item name from an item ID.

        Args:
            item_id: The ID of the item.

        Returns:
            The item name.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
        """

        args = {
            'item_id': item_id,
            'fields': 'name'
        }

        query_string = GraphQLQueryBuilder.build_query(
            'items',
            'query',
            args
        )

        data = await self.client.post_request(query_string)

        return data['data']['items'][0]['name']
