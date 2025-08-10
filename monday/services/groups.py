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
Module for handling monday.com group operations.

This module provides a comprehensive set of functions and classes for interacting
with groups on monday.com boards.

This module is part of the monday-client package and relies on the MondayClient
for making API requests. It also utilizes various utility functions to ensure proper
data handling and error checking.

Usage of this module requires proper authentication and initialization of the
MondayClient instance.
"""

import logging
from typing import TYPE_CHECKING, Literal

from monday.fields.group_fields import GroupFields
from monday.fields.item_fields import ItemFields
from monday.protocols import MondayClientProtocol
from monday.services.utils.error_handlers import check_query_result
from monday.services.utils.fields import Fields
from monday.services.utils.query_builder import (
    build_graphql_query,
    build_operation_with_variables,
    map_hex_to_color,
)
from monday.types.group import Group, GroupList
from monday.types.item import Item

if TYPE_CHECKING:
    from monday.services.boards import Boards


class Groups:
    """
    Service class for handling monday.com group operations.
    """

    _logger: logging.Logger = logging.getLogger(__name__)

    def __init__(self, client: MondayClientProtocol, boards: 'Boards'):
        """
        Initialize a Groups instance with specified parameters.

        Args:
            client: A client implementing MondayClientProtocol for API requests.
            boards: The Boards instance to use for board-related operations.

        """
        self.client = client
        self.boards = boards

    async def query(
        self,
        board_ids: int | str | list[int | str],
        group_ids: str | list[str] | None = None,
        group_name: str | list[str] | None = None,
        fields: str | Fields = GroupFields.BASIC,
    ) -> list[GroupList]:
        """
        Query groups from boards. Optionally specify the group names and/or IDs to filter by.

        Args:
            board_ids: The ID or list of IDs of the boards to query.
            group_ids: The ID or list of IDs of the specific groups to return.
            group_name: A single group name or list of group names.
            fields: Fields to return from the queried groups.

        Returns:
            List of GroupList dataclass instances containing board IDs and their associated Group dataclass instances.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient(api_key='your_api_key')
                >>> result = await monday_client.groups.query(
                ...     board_ids=987654321,
                ...     fields='id title'
                ... )
                >>> result[0].board_id
                "987654321"
                >>> result[0].groups[0].id
                "group"
                >>> result[0].groups[0].title
                "Group Name"

        """
        fields = Fields(fields)

        group_ids_list = [group_ids] if isinstance(group_ids, str) else group_ids
        group_ids_quoted = (
            [f'"{i}"' for i in group_ids_list] if group_ids_list else None
        )

        temp_fields = ['title'] if group_name else []

        group_fields = Fields(f"""
            id groups {f'(ids: [{", ".join(group_ids_quoted)}])' if group_ids_quoted else ''} {{
                {fields.add_temp_fields(temp_fields)}
            }}
        """)

        boards_data = await self.boards.query(board_ids=board_ids, fields=group_fields)

        groups: list[GroupList] = []
        for board in boards_data:
            board_groups = board.groups if board.groups else []
            if group_name:
                board_groups = [
                    group
                    for group in board_groups
                    if group.title
                    in (group_name if isinstance(group_name, list) else [group_name])
                ]
            if board_groups:  # Only add board if it has matching groups
                groups.append(GroupList(board_id=board.id, groups=board_groups))

        result_data = Fields.manage_temp_fields(
            [g.to_dict() for g in groups], fields, temp_fields
        )
        if isinstance(result_data, list):
            return [GroupList.from_dict(g) for g in result_data]
        return [GroupList.from_dict(result_data)]

    async def create(  # noqa: PLR0913
        self,
        board_id: int | str,
        group_name: str,
        group_color: str | None = None,
        relative_to: str | None = None,
        position_relative_method: Literal['before', 'after'] | None = None,
        fields: str | Fields = GroupFields.BASIC,
    ) -> Group:
        """
        Create a new group on a board.

        Args:
            board_id: The ID of the board where the group will be created.
            group_name: The new group's name.
            group_color: The new group's HEX code color.
            relative_to: The ID of the group you want to create the new one in relation to.
            position_relative_method: Specify whether you want to create the new group above or below the group given to ``relative_to``. Accepts ``'before'`` or ``'after'`` (internally mapped to API enums ``before_at``/``after_at``).
            fields: Fields to return from the created group.

        Returns:
            Group dataclass instance containing info for the new group.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient(api_key='your_api_key')
                >>> group = await monday_client.groups.create(
                ...     board_id=987654321,
                ...     group_name='Group Name',
                ...     group_color='#0086c0',
                ...     fields='id title'
                ... )
                >>> group.id
                "group"
                >>> group.title
                "Group Name"
                >>> group.color
                "#0086c0"

        Note:
            See a full list of accepted HEX code values for ``group_color`` and their corresponding colors :ref:`here <color_reference>`.

        """
        fields = Fields(fields)

        variable_types = {
            'boardId': 'ID!',
            'name': 'String!',
        }
        variables = {
            'boardId': str(board_id),
            'name': group_name,
        }
        arg_var_mapping = {
            'board_id': 'boardId',
            'group_name': 'name',
        }

        if group_color is not None:
            variable_types['color'] = 'String'
            variables['color'] = group_color
            arg_var_mapping['group_color'] = 'color'

        if relative_to is not None:
            variable_types['relativeTo'] = 'String'
            variables['relativeTo'] = relative_to
            arg_var_mapping['relative_to'] = 'relativeTo'

        if position_relative_method is not None:
            variable_types['relativeMethod'] = 'PositionRelative'
            variables['relativeMethod'] = f'{position_relative_method}_at'
            arg_var_mapping['position_relative_method'] = 'relativeMethod'

        operation = build_operation_with_variables(
            'create_group', 'mutation', variable_types, arg_var_mapping, fields
        )

        query_result = await self.client.post_request(operation, variables)

        data = check_query_result(query_result)

        return Group.from_dict(data['data']['create_group'])

    async def update(
        self,
        board_id: int | str,
        group_id: str,
        attribute: Literal[
            'color',
            'position',
            'relative_position_after',
            'relative_position_before',
            'title',
        ],
        new_value: str,
        fields: str | Fields = GroupFields.BASIC,
    ) -> Group:
        """
        Update a group.

        Args:
            board_id: The ID of the board where the group will be updated.
            group_id: The ID of the group to update.
            attribute: The group attribute to update. When ``'color'``, provide a supported hex code (e.g., ``#0086c0``). When using position-related attributes (``relative_position_after`` or ``relative_position_before``), ``new_value`` should be the ID of the reference group. When ``'title'``, ``new_value`` is the new title string.
            new_value: The new value for the specified ``attribute``. For ``'color'``, pass a supported hex code (e.g., ``#0086c0``); for position attributes (``relative_position_after``/``relative_position_before``), pass the reference group ID; for ``'title'``, pass the new title string.
            fields: Fields to return from the updated group.

        Returns:
            Group dataclass instance containing info for the updated group.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient(api_key='your_api_key')
                >>> group = await monday_client.groups.update(
                ...     board_id=987654321,
                ...     group_id='group',
                ...     attribute='color',
                ...     new_value='#7f5347',
                ...     fields='id title color'
                ... )
                >>> group.id
                "group"
                >>> group.title
                "Group Name"
                >>> group.color
                "#7F5347"

        Note:
            When using ``attribute='color'``, see a full list of accepted HEX color codes and their corresponding colors :ref:`here <color_reference>`.

            When updating a group's position using ``relative_position_after`` or ``relative_position_before``, the ``new_value`` should be the ID of the group you intend to place the updated group above or below.

        """
        fields = Fields(fields)

        if attribute == 'color':
            new_value = map_hex_to_color(new_value)

        variable_types = {
            'boardId': 'ID!',
            'groupId': 'String!',
            'newValue': 'String!',
        }
        variables = {
            'boardId': str(board_id),
            'groupId': group_id,
            'newValue': new_value,
        }
        arg_var_mapping = {
            'board_id': 'boardId',
            'group_id': 'groupId',
            'new_value': 'newValue',
        }
        arg_literals = {'group_attribute': attribute}

        operation = build_operation_with_variables(
            'update_group',
            'mutation',
            variable_types,
            arg_var_mapping,
            fields,
            arg_literals=arg_literals,
        )

        query_result = await self.client.post_request(operation, variables)

        data = check_query_result(query_result)

        return Group.from_dict(data['data']['update_group'])

    async def duplicate(
        self,
        board_id: int | str,
        group_id: str,
        group_title: str | None = None,
        fields: str | Fields = GroupFields.BASIC,
        *,
        add_to_top: bool = False,
    ) -> Group:
        """
        Duplicate a group.

        Args:
            board_id: The ID of the board where the group will be duplicated.
            group_id: The ID of the group to duplicate.
            add_to_top: Whether to add the new group to the top of the board.
            group_title: The new group's title.
            fields: Fields to return from the duplicated group.

        Returns:
            Group dataclass instance containing info for the duplicated group.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            MutationLimitExceeded: When the mutation API rate limit is exceeded.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient(api_key='your_api_key')
                >>> group = await monday_client.groups.duplicate(
                ...     board_id=987654321,
                ...     group_id='group',
                ...     fields='id title'
                ... )
                >>> group.id
                "group_2"
                >>> group.title
                "Duplicate of Group Name"

        """
        fields = Fields(fields)

        variable_types = {
            'boardId': 'ID!',
            'groupId': 'String!',
            'addToTop': 'Boolean',
        }
        variables = {
            'boardId': str(board_id),
            'groupId': group_id,
            'addToTop': bool(add_to_top),
        }
        arg_var_mapping = {
            'board_id': 'boardId',
            'group_id': 'groupId',
            'add_to_top': 'addToTop',
        }
        if group_title is not None:
            variable_types['groupTitle'] = 'String'
            variables['groupTitle'] = group_title
            arg_var_mapping['group_title'] = 'groupTitle'

        operation = build_operation_with_variables(
            'duplicate_group', 'mutation', variable_types, arg_var_mapping, fields
        )

        query_result = await self.client.post_request(operation, variables)

        data = check_query_result(query_result)

        return Group.from_dict(data['data']['duplicate_group'])

    async def archive(
        self,
        board_id: int | str,
        group_id: str,
        fields: str | Fields = GroupFields.BASIC,
    ) -> Group:
        """
        Archive a group.

        Args:
            board_id: The ID of the board where the group will be archived.
            group_id: The ID of the group to archive.
            fields: Fields to return from the archived group.

        Returns:
            Group dataclass instance containing info for the archived group.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient(api_key='your_api_key')
                >>> group = await monday_client.groups.archive(
                ...     board_id=987654321,
                ...     group_id='group',
                ...     fields='id title archived'
                ... )
                >>> group.id
                "group"
                >>> group.title
                "Group Name"
                >>> group.archived
                True

        """
        fields = Fields(fields)

        variable_types = {
            'boardId': 'ID!',
            'groupId': 'String!',
        }
        variables = {
            'boardId': str(board_id),
            'groupId': group_id,
        }
        arg_var_mapping = {'board_id': 'boardId', 'group_id': 'groupId'}

        operation = build_operation_with_variables(
            'archive_group', 'mutation', variable_types, arg_var_mapping, fields
        )

        query_result = await self.client.post_request(operation, variables)

        data = check_query_result(query_result)

        return Group.from_dict(data['data']['archive_group'])

    async def delete(
        self,
        board_id: int | str,
        group_id: str,
        fields: str | Fields = GroupFields.BASIC,
    ) -> Group:
        """
        Delete a group.

        Args:
            board_id: The ID of the board where the group will be deleted.
            group_id: The ID of the group to delete.
            fields: Fields to return from the deleted group.

        Returns:
            Group dataclass instance containing info for the deleted group.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient(api_key='your_api_key')
                >>> group = await monday_client.groups.delete(
                ...     board_id=987654321,
                ...     group_id='group',
                ...     fields='id title deleted'
                ... )
                >>> group.id
                "group"
                >>> group.title
                "Group Name"
                >>> group.deleted
                True

        """
        fields = Fields(fields)

        variable_types = {
            'boardId': 'ID!',
            'groupId': 'String!',
        }
        variables = {
            'boardId': str(board_id),
            'groupId': group_id,
        }
        arg_var_mapping = {'board_id': 'boardId', 'group_id': 'groupId'}

        operation = build_operation_with_variables(
            'delete_group', 'mutation', variable_types, arg_var_mapping, fields
        )

        query_result = await self.client.post_request(operation, variables)

        data = check_query_result(query_result)

        return Group.from_dict(data['data']['delete_group'])

    async def get_items_by_name(
        self,
        board_id: int | str,
        group_id: str,
        item_name: str,
        item_fields: str | Fields = ItemFields.BASIC,
    ) -> list[Item]:
        """
        Get all items from a group with names that match ``item_name``

        Args:
            board_id: The ID of the board to query.
            group_id: A single group ID.
            item_name: The name of the item to match.
            item_fields: Fields to return from the matched items.

        Returns:
            List of Item dataclass instances containing item info.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient(api_key='your_api_key')
                >>> items = await monday_client.groups.get_items_by_name(
                ...     board_id=987654321,
                ...     group_id='group',
                ...     item_name='Item Name',
                ...     item_fields='id name'
                ... )
                >>> items[0].id
                "123456789"
                >>> items[0].name
                "Item Name"
                >>> items[1].id
                "012345678"
                >>> items[1].name
                "Item Name"

        """
        fields = Fields(f"""
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
                        {item_fields}
                    }}
                }}
            }}
        """)

        args = {'ids': board_id, 'fields': fields}

        query_string = build_graphql_query('boards', 'query', args)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return [
            Item.from_dict(item)
            for item in data['data']['boards'][0]['groups'][0]['items_page']['items']
        ]
