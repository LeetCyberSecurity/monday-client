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
Module for handling Monday.com group operations.

This module provides a comprehensive set of functions and classes for interacting
with Monday.com groups.

This module is part of the monday-client package and relies on the MondayClient
for making API requests. It also utilizes various utility functions to ensure proper 
data handling and error checking.

Usage of this module requires proper authentication and initialization of the
MondayClient instance.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Union

from monday.services.utils import GraphQLQueryBuilder, check_query_result

if TYPE_CHECKING:
    from monday import MondayClient
    from monday.services import Boards


class Groups:
    """
    Handles operations related to Monday.com groups within boards.

    This class provides methods for interacting with groups on Monday.com boards.
    It encapsulates functionality for querying and managing groups, always in the
    context of their parent boards.

    Note:
        This class requires initialized MondayClient and Boards instances for making API requests.
    """

    logger: logging.Logger = logging.getLogger(__name__)

    def __init__(
        self,
        client: 'MondayClient',
        boards: 'Boards'
    ):
        """
        Initialize a Groups instance with specified parameters.

        Args:
            client: The MondayClient instance to use for API requests.
            boards: The Boards instance to use for board-related operations.
        """
        self.client: 'MondayClient' = client
        self.boards: 'Boards' = boards

    async def query(
        self,
        board_ids: Union[int, List[int]],
        group_ids: Optional[Union[str, List[str]]] = None,
        group_name: Optional[Union[str, List[str]]] = None,
        fields: str = 'id'
    ) -> List[Dict[str, Any]]:
        """
        Query groups from boards. Optionally specify the group names and/or IDs to filter by.

        Args:
            board_ids: The ID or list of IDs of the boards to query.
            group_ids: The ID or list of IDs of the specific groups to return.
            group_name: A single group name or list of group names.
            fields: Additional fields to return from the groups.

        Returns:
            List of dictionaries containing group info.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
        """

        group_ids_list = [group_ids] if isinstance(group_ids, str) else group_ids
        group_ids_quoted = [f'"{i}"' for i in group_ids_list] if group_ids_list else None

        fields_set = set(fields.split())
        original_fields_had_title = 'title' in fields_set

        if group_name:
            fields_set.add('title')

        fields = ' '.join(fields_set)

        group_fields = f"""
            id groups {f"(ids: [{', '.join(group_ids_quoted)}])" if group_ids_quoted else ''} {{
                {fields}
            }}
        """

        boards_data = await self.boards.query(
            board_ids=board_ids,
            fields=group_fields
        )

        groups = []
        for board in boards_data:
            board_groups = board.get('groups', [])
            if group_name:
                board_groups = [group for group in board_groups if group['title'] in (group_name if isinstance(group_name, list) else [group_name])]
                if not original_fields_had_title:
                    board_groups = [{k: v for k, v in group.items() if k != 'title'} for group in board_groups]
            groups.append({
                'id': board['id'],
                'groups': board_groups
            })

        return groups

    async def create(
        self,
        board_id: int,
        group_name: str,
        group_color: Optional[str] = None,
        relative_to: Optional[int] = None,
        position_relative_method: Optional[Literal['before_at', 'after_at']] = None,
        fields: str = 'id'
    ) -> Dict[str, Any]:
        """
        Create a new group on a board.

        Args:
            board_id: The ID of the board where the group will be created.
            group_name: The new group's name.
            group_color: The new group's HEX code color.
            relative_to: The ID of the group you want to create the new one in relation to.
            position_relative_method: Specify whether you want to create the new item above or below the item given to relative_to
            fields: Additional fields to return from the created group.

        Returns:
            Dictionary containing info for the new group.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
        """

        args = {
            'board_id': board_id,
            'group_name': group_name,
            'group_color': group_color,
            'relative_to': relative_to,
            'position_relative_method': position_relative_method,
            'fields': fields,
        }

        query_string = GraphQLQueryBuilder.build_query(
            'create_group',
            'mutation',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['create_group']

    async def update(
        self,
        board_id: int,
        group_id: str,
        group_attribute: Literal['color', 'position', 'relative_position_after', 'relative_position_before', 'title'],
        new_value: str,
        fields: str = 'id'
    ) -> Dict[str, Any]:
        """
        Update a group.

        Args:
            board_id: The ID of the board where the group will be updated.
            group_id: The ID of the group to update.
            group_attribute: The group attribute to update.
            new_value: The ID of the group you want to create the new one in relation to.
            fields: Additional fields to return from the updated group.

        Returns:
            Dictionary containing info for the updated group.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
        """

        args = {
            'board_id': board_id,
            'group_id': group_id,
            'group_attribute': group_attribute,
            'new_value': new_value,
            'fields': fields,
        }

        query_string = GraphQLQueryBuilder.build_query(
            'update_group',
            'mutation',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['update_group']

    async def duplicate(
        self,
        board_id: int,
        group_id: str,
        add_to_top: bool = False,
        group_title: Optional[str] = None,
        fields: str = 'id'
    ) -> Dict[str, Any]:
        """
        Duplicate a group.

        Args:
            board_id: The ID of the board where the group will be duplicated.
            group_id: The ID of the group to duplicate.
            add_to_top: Whether to add the new group to the top of the board.
            group_title: The new group's title.
            fields: Additional fields to return from the duplicated group.

        Returns:
            Dictionary containing info for the duplicated group.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            MutationLimitExceeded: When the mutation API rate limit is exceeded.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
        """

        args = {
            'board_id': board_id,
            'group_id': group_id,
            'add_to_top': add_to_top,
            'group_title': group_title,
            'fields': fields,
        }

        query_string = GraphQLQueryBuilder.build_query(
            'duplicate_group',
            'mutation',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['duplicate_group']

    async def archive(
        self,
        board_id: int,
        group_id: str,
        fields: str = 'id'
    ) -> Dict[str, Any]:
        """
        Archive a group.

        Args:
            board_id: The ID of the board where the group will be archived.
            group_id: The ID of the group to archive.
            fields: Additional fields to return from the archived group.

        Returns:
            Dictionary containing info for the archived group.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
        """

        args = {
            'board_id': board_id,
            'group_id': group_id,
            'fields': fields,
        }

        query_string = GraphQLQueryBuilder.build_query(
            'archive_group',
            'mutation',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['archive_group']

    async def delete(
        self,
        board_id: int,
        group_id: str,
        fields: str = 'id'
    ) -> Dict[str, Any]:
        """
        Delete a group.

        Args:
            board_id: The ID of the board where the group will be deleted.
            group_id: The ID of the group to delete.
            fields: Additional fields to return from the deleted group.

        Returns:
            Dictionary containing info for the deleted group.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds Monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled Monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
        """

        args = {
            'board_id': board_id,
            'group_id': group_id,
            'fields': fields,
        }

        query_string = GraphQLQueryBuilder.build_query(
            'delete_group',
            'mutation',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['delete_group']
