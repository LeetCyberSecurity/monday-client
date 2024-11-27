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
Module for handling Monday.com board operations.

The Boards class in this module serves as the main interface for these operations,
providing methods that correspond to different Monday.com API endpoints related to boards.

This module is part of the monday-client package and relies on the MondayClient
for making API requests. It also utilizes various utility functions to ensure proper 
data handling and error checking.

Usage of this module requires proper authentication and initialization of the
MondayClient instance.
"""

import json
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Union

from monday.exceptions import QueryFormatError
from monday.services.utils import (GraphQLQueryBuilder, check_query_result,
                                   extract_items_page_value,
                                   paginated_item_request,
                                   update_data_in_place)

if TYPE_CHECKING:
    from monday import MondayClient


class Boards:
    """
    Handles operations related to Monday.com boards.

    This class provides a comprehensive set of methods for interacting with boards
    on Monday.com.

    Note:
        This class requires an initialized MondayClient instance for making API requests.
    """

    logger: logging.Logger = logging.getLogger(__name__)

    def __init__(
        self,
        client: 'MondayClient'
    ):
        """
        Initialize a Boards instance with specified parameters.

        Args:
            client: The MondayClient instance to use for API requests.
        """
        self.client: 'MondayClient' = client

    async def query(
        self,
        board_ids: Optional[Union[int, List[int]]] = None,
        paginate_items: bool = True,
        board_kind: Literal['private', 'public', 'share', 'all'] = 'all',
        order_by: Literal['created_at', 'used_at'] = 'created_at',
        items_page_limit: int = 25,
        boards_limit: int = 25,
        page: int = 1,
        state: Literal['active', 'all', 'archived', 'deleted'] = 'active',
        workspace_ids: Optional[Union[int, List[int]]] = None,
        fields: str = 'id name',
    ) -> List[Dict[str, Any]]:
        """
        Query boards to return metadata about one or multiple boards.

        Args:
            board_ids: The ID or list of IDs of the boards to query.
            paginate_items: Whether to paginate items if items_page is in fields.
            board_kind: The kind of boards to include.
            order_by: The order in which to return the boards.
            items_page_limit: The number of items to return per page when items_page is part of your fields.
            boards_limit: The number of boards to return per page.
            page: The page number to start from.
            state: The state of the boards to include.
            workspace_ids: The ID or list of IDs of the workspaces to filter by.
            fields: Fields to specify in the boards query.

        Returns:
            List of dictionaries containing queried board data.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
        """

        if paginate_items and 'items_page' in fields and 'cursor' not in fields:
            raise QueryFormatError(
                'Pagination requires a cursor in the items_page field. '
                'Use boards.items_page() or update your fields parameter to include cursor, '
                'e.g.: "id name items_page { cursor items { id } }"'
            )

        board_ids = [board_ids] if not isinstance(board_ids, list) else board_ids

        args = {
            'ids': board_ids,
            'board_kind': board_kind if board_kind != 'all' else None,
            'order_by': order_by,
            'limit': boards_limit,
            'page': page,
            'state': state,
            'workspace_ids': workspace_ids,
            'fields': fields
        }

        boards_data = []

        while True:

            query_string = GraphQLQueryBuilder.build_query(
                'boards',
                'query',
                args
            )

            query_result = await self.client.post_request(query_string)

            data = check_query_result(query_result)

            if not data['data']['boards']:
                break

            boards_data.extend(data['data']['boards'])

            args['page'] += 1

        if 'items_page' in fields and paginate_items:
            query_result = await self._paginate_items(query_string, boards_data, limit=items_page_limit)
            boards_data = query_result

        return boards_data

    async def create(
        self,
        name: str,
        board_kind: Optional[Literal['private', 'public', 'share']] = 'public',
        owner_ids: Optional[List[int]] = None,
        subscriber_ids: Optional[List[int]] = None,
        subscriber_teams_ids: Optional[List[int]] = None,
        description: Optional[str] = None,
        folder_id: Optional[int] = None,
        template_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
        fields: str = 'id'
    ) -> Dict[str, Any]:
        """
        Create a new board.

        Args:
            name: The name of the new board.
            fields: Fields to query back from the created board.
            kind: The kind of board to create.
            owner_ids: List of user IDs to set as board owners.
            subscriber_ids: List of user IDs to set as board subscribers.
            subscriber_teams_ids: List of team IDs to set as board subscribers.
            description: Description of the board.
            folder_id: ID of the folder to place the board in.
            template_id: ID of the template to use for the board.
            workspace_id: ID of the workspace to create the board in.

        Returns:
            Dictionary containing info for the new board.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            MutationLimitExceeded: When the mutation API rate limit is exceeded.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
        """

        args = {
            'name': name,
            'board_kind ': board_kind,
            'owner_ids': owner_ids,
            'subscriber_ids': subscriber_ids,
            'subscriber_teams_ids': subscriber_teams_ids,
            'description': description,
            'folder_id': folder_id,
            'template_id': template_id,
            'workspace_id': workspace_id,
            'fields': fields
        }

        query_string = GraphQLQueryBuilder.build_query(
            'create_board',
            'mutation',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['create_board']

    async def duplicate(
        self,
        board_id: int,
        board_name: Optional[str] = None,
        duplicate_type: Literal['duplicate_board_with_pulses', 'duplicate_board_with_pulses_and_updates', 'duplicate_board_with_structure'] = 'duplicate_board_with_structure',
        folder_id: Optional[int] = None,
        keep_subscribers: bool = False,
        workspace_id: Optional[int] = None,
        fields: str = 'board { id }'
    ) -> Dict[str, Any]:
        """
        Duplicate a board.

        Args:
            board_id: The ID of the board to duplicate.
            board_name: The duplicated board's name.
            duplicate_type: The duplication type.
            folder_id: The destination folder within the destination workspace.
            keep_subscribers: Duplicate the subscribers to the new board.
            workspace_id: The destination workspace.
            fields: Fields to query back from the duplicated board.

        Returns:
            Dictionary containing info for the new board.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            MutationLimitExceeded: When the mutation API rate limit is exceeded.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
        """

        args = {
            'board_id': board_id,
            'board_name ': board_name,
            'duplicate_type ': duplicate_type,
            'folder_id': folder_id,
            'keep_subscribers': keep_subscribers,
            'workspace_id': workspace_id,
            'fields': fields
        }

        query_string = GraphQLQueryBuilder.build_query(
            'duplicate_board',
            'mutation',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['duplicate_board']

    async def update(
        self,
        board_id: int,
        board_attribute: Literal['communication', 'description', 'name'],
        new_value: str
    ) -> Dict[str, Any]:
        """
        Update a board.

        Args:
            board_id: The ID of the board to update.
            board_attribute: The board's attribute to update.
            new_value: The new attribute value.

        Returns:
            Dictionary containing updated board info.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
        """

        args = {
            'board_id': board_id,
            'board_attribute': board_attribute,
            'new_value ': new_value
        }

        query_string = GraphQLQueryBuilder.build_query(
            'update_board',
            'mutation',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        try:
            data = json.loads(data['data']['update_board'])
        except TypeError:
            data = data['data']['update_board']

        return data

    async def archive(
        self,
        board_id: int,
        fields: str = 'id'
    ) -> Dict[str, Any]:
        """
        Archive a board.

        Args:
            board_id: The ID of the board to archive.
            fields: Fields to query back from the archived board.

        Returns:
            Dictionary containing archived board info.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
        """

        args = {
            'board_id': board_id,
            'fields': fields
        }

        query_string = GraphQLQueryBuilder.build_query(
            'archive_board',
            'mutation',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['archive_board']

    async def delete(
        self,
        board_id: int,
        fields: str = 'id'
    ) -> Dict[str, Any]:
        """
        Delete a board.

        Args:
            board_id: The ID of the board to delete.
            fields: Fields to query back from the deleted board.

        Returns:
            Dictionary containing deleted board info.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
        """

        args = {
            'board_id': board_id,
            'fields': fields
        }

        query_string = GraphQLQueryBuilder.build_query(
            'delete_board',
            'mutation',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['delete_board']

    async def get_group_items_by_name(
        self,
        board_id: int,
        group_id: str,
        item_name: str,
        fields: str = 'id',
    ) -> List[Dict[str, Any]]:
        """
        Get all items from a group with names that match item_name

        Args:
            board_id: The ID of the board to query.
            group_id: A single group ID.
            item_name: The name of the item to match.
            fields: Additional fields to query from the matched items.

        Returns:
            List of dictionaries containing item info.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
        """

        fields = f"""
            groups (ids: "{group_id}") {{
               items_page (
                   query_params: {{
                       rules: [
                           {{
                               column_id: "name",
                               compare_value: ["{item_name}"]
                           }}
                       ]
                   }}
               ) {{
                   cursor
                   items {{
                       {fields}
                   }}
               }}
            }}
        """

        args = {
            'board_id': board_id,
            'fields': fields
        }

        query_string = GraphQLQueryBuilder.build_query(
            'boards',
            'query',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['boards'][0]['groups'][0]['items_page']['items']

    async def _paginate_items(
        self,
        query_string: str,
        boards: List[Dict[str, Any]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Paginate items for each board.

        Args:
            query_string: GraphQL query string.
            boards: List of board data.
            limit: The number of items to return per page.

        Returns:
            Updated list of board data with paginated items.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
            PaginationError: If pagination fails.
        """
        boards_list = boards
        for board in boards_list:
            items_page = extract_items_page_value(board)
            if items_page['cursor']:
                query_result = await paginated_item_request(self.client, query_string, limit=limit, cursor=items_page['cursor'])
                items_page['items'].extend(query_result['items'])
            del items_page['cursor']
            board = update_data_in_place(board, lambda ip, items_page=items_page: ip.update(items_page))
        return boards_list
