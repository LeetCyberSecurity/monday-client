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
Module for handling monday.com item-related services.

This module provides a comprehensive set of operations for managing items in
monday.com boards.

This module is part of the monday-client package and relies on the MondayClient
for making API requests. It also utilizes various utility functions to ensure proper 
data handling and error checking.

Usage of this module requires proper authentication and initialization of the
MondayClient instance.
"""

import logging
from typing import TYPE_CHECKING, Any, Literal, Optional, Union

from monday.services.utils import (build_graphql_query, check_query_result,
                                   manage_temp_fields)

if TYPE_CHECKING:
    from monday import MondayClient
    from monday.services import Boards


class Items:
    """
    Service class for handling monday.com item operations.
    """

    _logger: logging.Logger = logging.getLogger(__name__)

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
        item_ids: Union[int, list[int]],
        limit: int = 25,
        page: int = 1,
        exclude_nonactive: bool = False,
        newest_first: bool = False,
        fields: str = 'id'
    ) -> list[dict[str, Any]]:
        """
        Query items to return metadata about one or multiple items.

        Args:
            item_ids: The ID or list of IDs of the specific items, subitems, or parent items to return.
            limit: The maximum number of items to retrieve per page. Must be greater than 0 and less than 100.
            page: The page number at which to start.
            exclude_nonactive: Excludes items that are inactive, deleted, or belong to deleted items.
            newest_first: Lists the most recently created items at the top.
            fields: Fields to return from the queried items.

        Returns:
            A list of dictionaries containing info for the queried items.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> await monday_client.items.query(
                ...     item_ids=[123456789, 012345678],
                ...     fields='id name state updates { text_body }',
                ...     limit=50
                ... )
                [
                    {
                        'id': '123456789',
                        'name': 'Task 1',
                        'state': 'active',
                        'updates': [
                            {
                                'text_body': 'Started working on this'
                            },
                            {
                                'text_body': 'Making progress'
                            }
                        ]
                    },
                    {
                        'id': '012345678',
                        'name': 'Task 2',
                        'state': 'active',
                        'updates': []
                    }
                ]

        Note:
            To return all items on a board, use :meth:`Items.page() <monday.services.Items.page>` or :meth:`Items.page_by_column_values() <monday.services.Items.page_by_column_values>` instead.
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

            query_string = build_graphql_query(
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
        column_values: Optional[dict[str, Any]] = None,
        group_id: Optional[str] = None,
        create_labels_if_missing: bool = False,
        position_relative_method: Optional[Literal['before_at', 'after_at']] = None,
        relative_to: Optional[int] = None,
        fields: str = 'id'
    ) -> dict[str, Any]:
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
            fields: Fields to return from the created item.

        Returns:
            Dictionary containing info for the created item.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> await monday_client.items.create(
                ...     board_id=123456789,
                ...     item_name='New Item',
                ...     column_values={
                ...         'status': 'Done',
                ...         'text': 'This item is done'
                ...     },
                ...     group_id='group',
                ...     fields='id name column_values (ids: ["status", "text"]) { id text }'
                ... )
                {
                    "id": "123456789",
                    "name": "New Item",
                    "column_values": [
                        {
                            "id": "status",
                            "text": "Done"
                        },
                        {
                            "id": "text",
                            "text": "This item is done"
                        }
                    ]
                }
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

        query_string = build_graphql_query(
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
        new_item_name: Optional[str] = None,
        fields: str = 'id'
    ) -> dict[str, Any]:
        """
        Duplicate an item.

        Args:
            item_id: The ID of the item to be duplicated.
            board_id: The ID of the board where the item will be duplicated.
            with_updates: Duplicates the item with existing updates.
            new_item_name: Name of the duplicated item. If omitted the duplicated item's name will be the original item's name with (copy) appended.
            fields: Fields to return from the duplicated item.

        Returns:
            Dictionary containing info for the duplicated item.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> await monday_client.items.duplicate(
                ...     item_id=123456789,
                ...     board_id=987654321,
                ...     fields='id name column_values { id text }'
                ... )
                {
                    "id": "123456789",
                    "name": "Item 1 (copy)",
                    "column_values": [
                        {
                            "id": "status",
                            "text": "Done"
                        },
                        {
                            "id": "text",
                            "text": "This item is done"
                        }
                    ]
                }
        """

        # Only query the ID first if the duplicated item name is being changed
        # Other potential fields are added back in the change column values query
        temp_fields, query_fields = (['id'], 'id') if new_item_name else ([], fields)

        args = {
            'item_id': item_id,
            'board_id': board_id,
            'with_updates': with_updates,
            'fields': query_fields
        }

        query_string = build_graphql_query(
            'duplicate_item',
            'mutation',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        if new_item_name:
            query_result = await self.change_column_values(
                int(data['data']['duplicate_item']['id']),
                column_values={'name': new_item_name},
                fields=fields
            )
            data = check_query_result(query_result, errors_only=True)
            return manage_temp_fields(data, fields, temp_fields)
        else:
            return data['data']['duplicate_item']

    async def move_to_group(
        self,
        item_id: int,
        group_id: str,
        fields: str = 'id'
    ) -> dict[str, Any]:
        """
        Move an item to a different group.

        Args:
            item_id: The ID of the item to be moved.
            group_id: The ID of the group to move the item to.
            fields: Fields to return from the moved item.

        Returns:
            Dictionary containing info for the moved item.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> await monday_client.items.move_to_group(
                ...     item_id=123456789,
                ...     group_id='group',
                ...     fields='id name group { id title }'
                ... )
                {
                    "id": "123456789",
                    "name": "Item 1",
                    "group": {
                        "id": "group",
                        "title": "Group 1"
                    }
                }
        """
        args = {
            'item_id': item_id,
            'group_id': group_id,
            'fields': fields
        }

        query_string = build_graphql_query(
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
        columns_mapping: Optional[list[dict[str, str]]] = None,
        subitems_columns_mapping: Optional[list[dict[str, str]]] = None,
        fields: str = 'id'
    ) -> dict[str, Any]:
        """
        Move an item to a different board.

        Args:
            item_id: The ID of the item to be moved.
            board_id: The ID of the board to move the item to.
            group_id: The ID of the group to move the item to.
            columns_mapping: Defines the column mapping between the original and target board.
            subitems_columns_mapping: Defines the subitems' column mapping between the original and target board.
            fields: Fields to return from the moved item.

        Returns:
            Dictionary containing info for the moved item.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> await monday_client.items.move_to_board(
                ...     item_id=123456789,
                ...     board_id=987654321,
                ...     group_id='group',
                ...     columns_mapping={
                ...         'original_status_id': 'target_status_id',
                ...         'original_text_id': 'target_text_id'
                ...     },
                ...     fields='id board { id } group { id } column_values { id text }'
                ... )
                {
                    "id": "123456789",
                    "board": {
                        "id": "987654321"
                    },
                    "group": {
                        "id": "group"
                    },
                    "column_values": [
                        {
                            "id": "target_status_id",
                            "text": "Done"
                        },
                        {
                            "id": "target_text_id",
                            "text": "This item is done"
                        }
                    ]
                }

        Note:
            Every column type can be mapped **except for formula columns.**

            When using the columns_mapping and subitem_columns_mapping arguments, you must specify the mapping for **all** columns. 
            You can set the target as ``None`` for any columns you don't want to map, but doing so will lose the column's data.

            If you omit this argument, the columns will be mapped based on the best match.

            See the `monday.com API documentation (move item) <https://developer.monday.com/api-reference/reference/items#move-item-to-board>`_ for more details.
        """
        args = {
            'item_id': item_id,
            'board_id': board_id,
            'group_id': group_id,
            'columns_mapping': columns_mapping,
            'subitems_columns_mapping': subitems_columns_mapping,
            'fields': fields
        }

        query_string = build_graphql_query(
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
    ) -> dict[str, Any]:
        """
        Archive an item.

        Args:
            item_id: The ID of the item to be archived.
            fields: Fields to return from the archived item.

        Returns:
            Dictionary containing info for the archived item.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> await monday_client.items.archive(
                ...     item_id=123456789,
                ...     fields='id state'
                ... )
                {
                    "id": "123456789",
                    "state": "archived"
                }
        """
        args = {
            'item_id': item_id,
            'fields': fields
        }

        query_string = build_graphql_query(
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
    ) -> dict[str, Any]:
        """
        Delete an item.

        Args:
            item_id: The ID of the item to be deleted.
            fields: Fields to return from the deleted item.

        Returns:
            Dictionary containing info for the deleted item.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> await monday_client.items.delete(
                ...     item_id=123456789,
                ...     fields='id state'
                ... )
                {
                    "id": "123456789",
                    "state": "deleted"
                }
        """
        args = {
            'item_id': item_id,
            'fields': fields
        }

        query_string = build_graphql_query(
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
    ) -> dict[str, Any]:
        """
        Clear an item's updates.

        Args:
            item_id: The ID of the item to be cleared.
            fields: Fields to return from the cleared item.

        Returns:
            Dictionary containing info for the cleared item.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> await monday_client.items.clear_updates(
                ...     item_id=123456789,
                ...     fields='id updates { text_body }'
                ... )
                {
                    "id": "123456789",
                    "updates": []
                }
        """
        args = {
            'item_id': item_id,
            'fields': fields
        }

        query_string = build_graphql_query(
            'clear_item_updates',
            'mutation',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['clear_item_updates']

    async def get_column_values(
        self,
        item_id: int,
        column_ids: Optional[list[str]] = None,
        fields: str = 'id'
    ) -> list[dict[str, Any]]:
        """
        Retrieves a list of column values for a specific item.

        Args:
            item_id: The ID of the item.
            column_ids: The specific column IDs to return. Will return all columns if no IDs specified.
            fields: Fields to return from the item column values.

        Returns:
            A list of dictionaries containing the item column values.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> await monday_client.items.get_column_values(
                ...     item_id=123456789,
                ...     column_ids=['status', 'text'],
                ...     fields='id text'   
                ... )
                [
                    {
                        "id": "status",
                        "text": "Done"
                    },
                    {
                        "id": "text",
                        "text": "This item is done"
                    }
                ]
        """

        column_ids = [f'"{i}"' for i in column_ids] if column_ids else None

        fields = f"""
            column_values {f"(ids: [{', '.join(column_ids)}])" if column_ids else ''} {{ 
                {fields} 
            }}
        """

        args = {
            'ids': item_id,
            'fields': fields
        }

        query_string = build_graphql_query(
            'items',
            'query',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        try:
            items = data['data']['items'][0]
        except IndexError:
            return []

        return items['column_values']

    async def change_column_values(
        self,
        item_id: int,
        column_values: dict[str, Any],
        create_labels_if_missing: bool = False,
        fields: str = 'id',
    ) -> dict[str, Any]:
        """
        Change an item's column values.

        Args:
            item_id: The ID of the item.
            column_values: The updated column values.
            fields: Fields to return from the updated columns.

        Returns:
            Dictionary containing info for the updated columns.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> await monday_client.items.change_column_values(
                ...     item_id=123456789,
                ...     column_values={
                ...         'status': 'Working on it',
                ...         'text': 'Working on this item',
                ...         'status_2': {'label': 'Done'}
                ...     },
                ...     fields='id column_values { id text }'
                ... )
                {
                    "id": "123456789",
                    "column_values": [
                        {
                            "id": "status",
                            "text": "Working on it"
                        },
                        {
                            "id": "status_2",
                            "text": "Done"
                        },
                        {
                            "id": "text",
                            "text": "Working on this item"
                        }
                    ]
                }

        Note:
            Each column has a certain type, and different column types expect a different set of parameters to update their values.

            See the `monday.com API documentation (column types reference) <https://developer.monday.com/api-reference/reference/column-types-reference>`_ for more details on which parameters to use for each column type.
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

        query_string = build_graphql_query(
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
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> await monday_client.items.get_name(item_id=123456789)
                Item 1
        """

        args = {
            'ids': item_id,
            'fields': 'name'
        }

        query_string = build_graphql_query(
            'items',
            'query',
            args
        )

        data = await self.client.post_request(query_string)

        return data['data']['items'][0]['name']

    async def get_id(
        self,
        board_id: int,
        item_name: str
    ) -> list[str]:
        """
        Get the IDs of all items on a board with names matching the given item name.

        Args:
            board_id: The ID of the board to search.
            item_name: The item name to filter on.

        Returns:
            List of item IDs matching the item name.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> await monday_client.items.get_id(
                ...     board_id=987654321,
                ...     item_name='Item 1'
                ... )
                [
                    "123456789",
                    "012345678"
                ]
        """

        columns = [
            {
                'column_id': 'name',
                'column_values': item_name
            }
        ]

        data = await self.boards.get_items_by_column_values(board_id, columns)

        return [str(item['id']) for item in data]
