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
from typing import TYPE_CHECKING, Any, Literal

from monday.fields.column_fields import ColumnFields
from monday.fields.item_fields import ItemFields
from monday.services.utils.error_handlers import check_query_result
from monday.services.utils.fields import Fields
from monday.services.utils.query_builder import build_graphql_query
from monday.types.column import ColumnFilter, ColumnValue
from monday.types.column_inputs import ColumnInput
from monday.types.item import Item

if TYPE_CHECKING:
    from monday.client import MondayClient
    from monday.services.boards import Boards


class Items:
    """
    Service class for handling monday.com item operations.
    """

    _logger: logging.Logger = logging.getLogger(__name__)

    def __init__(self, client: 'MondayClient', boards: 'Boards'):
        """
        Initialize an Items instance with specified parameters.

        Args:
            client: The MondayClient instance to use for API requests.
            boards: The Boards instance to use for board-related operations.

        """
        self.client = client
        self.boards = boards

    async def query(  # noqa: PLR0913
        self,
        item_ids: int | str | list[int | str],
        limit: int = 25,
        page: int = 1,
        fields: str | Fields = ItemFields.BASIC,
        *,
        exclude_nonactive: bool = False,
        newest_first: bool = False,
    ) -> list[Item]:
        """
        Query items to return metadata about one or multiple items.

        Args:
            item_ids: The ID or list of IDs of the specific items to return. Maximum of 100 IDs allowed in a single query.
            limit: The maximum number of items to retrieve per page. Must be greater than 0 and less than 100.
            page: The page number at which to start.
            exclude_nonactive: Excludes items that are inactive, deleted, or belong to deleted items.
            newest_first: Lists the most recently created items at the top.
            fields: Fields to return from the queried items.

        Returns:
            A list of Item dataclass instances containing info for the queried items.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> items = await monday_client.items.query(
                ...     item_ids=[123456789, 012345678],
                ...     fields='id name state updates { text_body }',
                ...     limit=50
                ... )
                >>> items[0].id
                "123456789"
                >>> items[0].name
                "Task 1"
                >>> items[0].state
                "active"
                >>> items[0].updates[0].text_body
                "Started working on this"

        Note:
            To return all items on a board, use :meth:`Boards.get_items() <monday.services.boards.Boards.get_items>` instead.

        """
        fields = Fields(fields)

        args = {
            'ids': item_ids,
            'limit': limit,
            'page': page,
            'exclude_nonactive': exclude_nonactive,
            'newest_first': newest_first,
            'fields': fields,
        }

        items_data = []
        while True:
            query_string = build_graphql_query('items', 'query', args)

            query_result = await self.client.post_request(query_string)
            data = check_query_result(query_result)

            if not data.get('data', {}).get('items'):
                break

            items_data.extend(data['data']['items'])
            args['page'] += 1

        # Convert raw dictionaries to Item dataclass instances
        return [Item.from_dict(item) for item in items_data]

    async def create(  # noqa: PLR0913
        self,
        board_id: int | str,
        item_name: str,
        column_values: list[ColumnInput] | dict[str, Any] | None = None,
        group_id: str | None = None,
        position_relative_method: Literal['before_at', 'after_at'] | None = None,
        relative_to: int | None = None,
        fields: str | Fields = ItemFields.BASIC,
        *,
        create_labels_if_missing: bool = False,
    ) -> Item:
        """
        Create a new item on a board.

        Args:
            board_id: The ID of the board where the item will be created.
            item_name: The name of the item.
            column_values: Column values for the item. Can be a list of ColumnInput objects or a dictionary. When using ColumnInput objects, the column_id is extracted from each object. When using a dictionary, keys are column IDs and values are the column values.
            group_id: The ID of the group where the item will be created.
            create_labels_if_missing: Creates status/dropdown labels if they are missing.
            position_relative_method: Specify whether you want to create the new item above or below the item given to relative_to.
            relative_to: The ID of the item you want to create the new one in relation to.
            fields: Fields to return from the created item.

        Returns:
            Item dataclass instance containing info for the created item.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> from monday.types.column_inputs import StatusInput, TextInput, DateInput
                >>> monday_client = MondayClient('your_api_key')

                # Using ColumnInput objects (recommended for type safety)
                >>> item = await monday_client.items.create(
                ...     board_id=987654321,
                ...     item_name='New Item',
                ...     column_values=[
                ...         StatusInput('status_column_id', 'Done'),
                ...         TextInput('text_column_id', 'This item is done'),
                ...         DateInput('date_column_id', '2024-01-15')
                ...     ],
                ...     group_id='group',
                ...     fields='id name column_values (ids: ["status_column_id", "text_column_id"]) { id text }'
                ... )

                # Using dictionary format (equivalent functionality)
                >>> item = await monday_client.items.create(
                ...     board_id=987654321,
                ...     item_name='New Item',
                ...     column_values={
                ...         'status_column_id': {'label': 'Done'},
                ...         'text_column_id': 'This item is done',
                ...         'date_column_id': {'date': '2024-01-15'}
                ...     },
                ...     group_id='group',
                ...     fields='id name column_values (ids: ["status_column_id", "text_column_id"]) { id text }'
                ... )
                >>> item.id
                "987654321"
                >>> item.name
                "New Item"
                >>> item.column_values[0].id
                "status_column_id"
                >>> item.column_values[0].text
                "Done"

        """
        fields = Fields(fields)

        # Process column values to handle value classes
        processed_column_values = None
        if column_values:
            processed_column_values = Items._process_column_values(column_values)

        args = {
            'board_id': board_id,
            'item_name': item_name,
            'column_values': processed_column_values,
            'group_id': group_id,
            'create_labels_if_missing': create_labels_if_missing,
            'position_relative_method': position_relative_method,
            'relative_to': relative_to,
            'fields': fields,
        }

        query_string = build_graphql_query('create_item', 'mutation', args)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return Item.from_dict(data['data']['create_item'])

    async def duplicate(
        self,
        item_id: int | str,
        board_id: int | str,
        new_item_name: str | None = None,
        fields: str | Fields = ItemFields.BASIC,
        *,
        with_updates: bool = False,
    ) -> Item:
        """
        Duplicate an item.

        Args:
            item_id: The ID of the item to be duplicated.
            board_id: The ID of the board where the item will be duplicated.
            with_updates: Duplicates the item with existing updates.
            new_item_name: Name of the duplicated item. If omitted the duplicated item's name will be the original item's name with (copy) appended.
            fields: Fields to return from the duplicated item.

        Returns:
            Item dataclass instance containing info for the duplicated item.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> item = await monday_client.items.duplicate(
                ...     item_id=123456789,
                ...     board_id=987654321,
                ...     fields='id name column_values { id text }'
                ... )
                >>> item.id
                "123456789"
                >>> item.name
                "Item 1 (copy)"
                >>> item.column_values[0].id
                "status"
                >>> item.column_values[0].text
                "Done"

        """
        fields = Fields(fields)

        # Only query the ID first if the duplicated item name is being changed
        # Other potential fields are added back in during the change column values query
        query_fields = 'id' if new_item_name else fields

        args = {
            'item_id': item_id,
            'board_id': board_id,
            'with_updates': with_updates,
            'fields': query_fields,
        }

        query_string = build_graphql_query('duplicate_item', 'mutation', args)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        if new_item_name:
            await self.change_column_values(
                data['data']['duplicate_item']['id'],
                column_values={'name': new_item_name},
                fields=fields,
            )
            # Query the complete item after changing the name
            return (
                await self.query(data['data']['duplicate_item']['id'], fields=fields)
            )[0]
        return Item.from_dict(data['data']['duplicate_item'])

    async def move_to_group(
        self, item_id: int | str, group_id: str, fields: str | Fields = ItemFields.BASIC
    ) -> Item:
        """
        Move an item to a different group.

        Args:
            item_id: The ID of the item to be moved.
            group_id: The ID of the group to move the item to.
            fields: Fields to return from the moved item.

        Returns:
            Item dataclass instance containing info for the moved item.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> item = await monday_client.items.move_to_group(
                ...     item_id=123456789,
                ...     group_id='group',
                ...     fields='id name group { id title }'
                ... )
                >>> item.id
                "123456789"
                >>> item.name
                "Item 1"
                >>> item.group.id
                "group"
                >>> item.group.title
                "Group 1"

        """
        fields = Fields(fields)

        args = {'item_id': item_id, 'group_id': group_id, 'fields': fields}

        query_string = build_graphql_query('move_item_to_group', 'mutation', args)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return Item.from_dict(data['data']['move_item_to_group'])

    async def move_to_board(  # noqa: PLR0913
        self,
        item_id: int | str,
        board_id: int | str,
        group_id: str,
        columns_mapping: list[dict[str, str]] | None = None,
        subitems_columns_mapping: list[dict[str, str]] | None = None,
        fields: str | Fields = ItemFields.BASIC,
    ) -> Item:
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
            Item dataclass instance containing info for the moved item.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> item = await monday_client.items.move_to_board(
                ...     item_id=123456789,
                ...     board_id=987654321,
                ...     group_id='group',
                ...     columns_mapping={
                ...         'original_status_id': 'target_status_id',
                ...         'original_text_id': 'target_text_id'
                ...     },
                ...     fields='id board { id } group { id } column_values { id text }'
                ... )
                >>> item.id
                "123456789"
                >>> item.board.id
                "987654321"
                >>> item.group.id
                "group"
                >>> item.column_values[0].id
                "target_status_id"
                >>> item.column_values[0].text
                "Done"

        Note:
            Every column type can be mapped **except for formula columns.**

            When using the columns_mapping and subitem_columns_mapping arguments, you must specify the mapping for **all** columns.
            You can set the target as ``None`` for any columns you don't want to map, but doing so will lose the column's data.

            If you omit this argument, the columns will be mapped based on the best match.

            See the `monday.com API documentation (move item) <https://developer.monday.com/api-reference/reference/items#move-item-to-board>`_ for more details.

        """
        fields = Fields(fields)

        args = {
            'item_id': item_id,
            'board_id': board_id,
            'group_id': group_id,
            'columns_mapping': columns_mapping,
            'subitems_columns_mapping': subitems_columns_mapping,
            'fields': fields,
        }

        query_string = build_graphql_query('move_item_to_board', 'mutation', args)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return Item.from_dict(data['data']['move_item_to_board'])

    async def archive(
        self, item_id: int | str, fields: str | Fields = ItemFields.BASIC
    ) -> Item:
        """
        Archive an item.

        Args:
            item_id: The ID of the item to be archived.
            fields: Fields to return from the archived item.

        Returns:
            Item dataclass instance containing info for the archived item.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> item = await monday_client.items.archive(
                ...     item_id=123456789,
                ...     fields='id state'
                ... )
                >>> item.id
                "123456789"
                >>> item.state
                "archived"

        """
        fields = Fields(fields)

        args = {'item_id': item_id, 'fields': fields}

        query_string = build_graphql_query('archive_item', 'mutation', args)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return Item.from_dict(data['data']['archive_item'])

    async def delete(
        self, item_id: int | str, fields: str | Fields = ItemFields.BASIC
    ) -> Item:
        """
        Delete an item.

        Args:
            item_id: The ID of the item to be deleted.
            fields: Fields to return from the deleted item.

        Returns:
            Item dataclass instance containing info for the deleted item.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> item = await monday_client.items.delete(
                ...     item_id=123456789,
                ...     fields='id state'
                ... )
                >>> item.id
                "123456789"
                >>> item.state
                "deleted"

        """
        fields = Fields(fields)

        args = {'item_id': item_id, 'fields': fields}

        query_string = build_graphql_query('delete_item', 'mutation', args)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return Item.from_dict(data['data']['delete_item'])

    async def clear_updates(
        self, item_id: int | str, fields: str | Fields = ItemFields.BASIC
    ) -> Item:
        """
        Clear an item's updates.

        Args:
            item_id: The ID of the item to be cleared.
            fields: Fields to return from the cleared item.

        Returns:
            Item dataclass instance containing info for the cleared item.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> item = await monday_client.items.clear_updates(
                ...     item_id=123456789,
                ...     fields='id updates { text_body }'
                ... )
                >>> item.id
                "123456789"
                >>> item.updates
                []

        """
        fields = Fields(fields)

        args = {'item_id': item_id, 'fields': fields}

        query_string = build_graphql_query('clear_item_updates', 'mutation', args)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return Item.from_dict(data['data']['clear_item_updates'])

    async def get_column_values(
        self,
        item_id: int | str,
        column_ids: list[str] | None = None,
        fields: str | Fields = ColumnFields.BASIC,
    ) -> list[ColumnValue]:
        """
        Retrieves a list of column values for a specific item.

        Args:
            item_id: The ID of the item.
            column_ids: The specific column IDs to return. Will return all columns if no IDs specified.
            fields: Fields to return from the item column values.

        Returns:
            A list of ColumnValue dataclass instances containing the item column values.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> column_values = await monday_client.items.get_column_values(
                ...     item_id=123456789,
                ...     column_ids=['status', 'text'],
                ...     fields='id text'
                ... )
                >>> column_values[0].id
                "status"
                >>> column_values[0].text
                "Done"
                >>> column_values[1].id
                "text"
                >>> column_values[1].text
                "This item is done"

        Note:
            Use :meth:`Boards.get_column_values() <monday.services.boards.Boards.get_column_values>` to retrieve column values for all items on a board.

        """
        column_ids = [f'"{i}"' for i in column_ids] if column_ids else None

        fields = Fields(f"""
            column_values {f'(ids: [{", ".join(column_ids)}])' if column_ids else ''} {{
                {fields}
            }}
        """)

        args = {'ids': item_id, 'fields': fields}

        query_string = build_graphql_query('items', 'query', args)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        try:
            items = data['data']['items'][0]
        except IndexError:
            return []

        return [ColumnValue.from_dict(cv) for cv in items['column_values']]

    async def change_column_values(
        self,
        item_id: int | str,
        column_values: list[ColumnInput] | dict[str, Any],
        fields: str | Fields = ColumnFields.BASIC,
        *,
        create_labels_if_missing: bool = False,
    ) -> ColumnValue:
        """
        Change an item's column values.

        Args:
            item_id: The ID of the item.
            column_values: The updated column values. Can be a list of ColumnInput objects or a dictionary. When using ColumnInput objects, the column_id is extracted from each object. When using a dictionary, keys are column IDs and values are the column values.
            create_labels_if_missing: Creates status/dropdown labels if they are missing.
            fields: Fields to return from the updated columns.

        Returns:
            ColumnValue dataclass instance containing info for the updated columns.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> from monday.types.column_inputs import DateInput, StatusInput, TextInput
                >>> monday_client = MondayClient('your_api_key')

                # Using ColumnInput objects (recommended for type safety)
                >>> result = await monday_client.items.change_column_values(
                ...     item_id=123456789,
                ...     column_values=[
                ...         StatusInput('status_column_id', 'Working on it'),
                ...         TextInput('text_column_id', 'Working on this item'),
                ...         DateInput('date_column_id', '2024-01-15', '14:30:00')
                ...     ],
                ...     fields='id column_values { id text }'
                ... )

                # Using dictionary format (equivalent functionality)
                >>> result = await monday_client.items.change_column_values(
                ...     item_id=123456789,
                ...     column_values={
                ...         'status_column_id': {'label': 'Working on it'},
                ...         'text_column_id': 'Working on this item',
                ...         'date_column_id': {'date': '2024-01-15', 'time': '14:30:00'},
                ...         'status_2_column_id': {'label': 'Done'}  # Supports dict format
                ...     },
                ...     fields='id column_values { id text }'
                ... )
                >>> result.id
                "123456789"
                >>> result.column_values[0].id
                "status_column_id"
                >>> result.column_values[0].text
                "Working on it"

        Note:
            Each column has a certain type, and different column types expect a different set of parameters to update their values.

            For better type safety and documentation, you can use the value classes from :ref:`Column Input Types <column_input_types>`:

            - :class:`~monday.types.column_inputs.DateInput` for date columns
            - :class:`~monday.types.column_inputs.StatusInput` for status columns
            - :class:`~monday.types.column_inputs.TextInput` for text columns
            - :class:`~monday.types.column_inputs.NumberInput` for number columns
            - :class:`~monday.types.column_inputs.CheckboxInput` for checkbox columns
            - :class:`~monday.types.column_inputs.DropdownInput` for dropdown columns
            - :class:`~monday.types.column_inputs.PeopleInput` for people columns
            - etc...

            These classes handle the proper formatting required by the Monday.com API and provide validation.

            See the `monday.com API documentation (column types reference) <https://developer.monday.com/api-reference/reference/column-types-reference>`_ for more details on which parameters to use for each column type.

        """
        board_id_query = await self.query(item_id, fields='board { id }')
        board_id = int(board_id_query[0].board.id if board_id_query[0].board else 0)

        fields = Fields(fields)

        # Process column values to handle value classes
        processed_column_values = Items._process_column_values(column_values)

        args = {
            'item_id': item_id,
            'board_id': board_id,
            'column_values': processed_column_values,
            'create_labels_if_missing': create_labels_if_missing,
            'fields': fields,
        }

        query_string = build_graphql_query(
            'change_multiple_column_values', 'mutation', args
        )

        self._logger.debug('query: %s', query_string)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        self._logger.debug('query result: %s', data)

        column_value = ColumnValue.from_dict(
            data['data']['change_multiple_column_values']
        )

        self._logger.debug('Final column value: %s', column_value)

        return column_value

    async def get_name(self, item_id: int | str) -> str:
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
                "Item 1"

        """
        args = {'ids': item_id, 'fields': 'name'}

        query_string = build_graphql_query('items', 'query', args)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        items = [Item.from_dict(item) for item in data['data']['items']]
        return items[0].name if items else ''

    async def get_id(self, board_id: int | str, item_name: str) -> list[str]:
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
        columns = [ColumnFilter(column_id='name', column_values=item_name)]

        data = await self.boards.get_items_by_column_values(board_id, columns)

        return [str(item.id) for item in data]

    @staticmethod
    def _process_column_values(
        column_values: list[ColumnInput] | dict[str, Any],
    ) -> dict[str, Any]:
        """
        Process column values to handle both ColumnInput objects and dictionary formats.

        This method converts column values into the format expected by the Monday.com API.
        When given a list of ColumnInput objects, it extracts the column_id from each object
        and converts the value using the appropriate method (to_str() or to_dict()).
        When given a dictionary, it passes through the values as-is.

        Args:
            column_values: Either a list of ColumnInput objects or a dictionary of column values. For ColumnInput objects, the column_id is extracted from the object. For dictionaries, keys are column IDs and values are the column values.

        Returns:
            A dictionary where keys are column IDs and values are the processed column values
            ready for API submission.

        Example:
            .. code-block:: python

                # List of ColumnInput objects
                column_values = [
                    StatusInput('status_1', 'Done'),
                    TextInput('text_1', 'Some text'),
                    NumberInput('number_1', 42.5),
                ]
                processed = Items._process_column_values(column_values)
                # Result: {
                #     'status_1': {'label': 'Done'},
                #     'text_1': 'Some text',
                #     'number_1': '42.5'
                # }

                # Dictionary format
                column_values = {
                    'status_1': StatusInput('status_1', 'Done'),
                    'text_1': 'Some text',
                    'number_1': 42.5,
                }
                processed = Items._process_column_values(column_values)
                # Result: {
                #     'status_1': {'label': 'Done'},
                #     'text_1': 'Some text',
                #     'number_1': 42.5
                # }

        """
        # Process column values to handle value classes
        processed_column_values = {}
        if isinstance(column_values, list):
            for column_value in column_values:
                # Handle value classes - some use to_str(), others use to_dict()
                if not isinstance(column_value, (str, dict)):
                    if hasattr(column_value, 'to_str'):
                        processed_column_values[column_value.column_id] = (
                            column_value.to_str()  # pyright: ignore [reportAttributeAccessIssue]
                        )
                    elif hasattr(column_value, 'to_dict'):
                        processed_column_values[column_value.column_id] = (
                            column_value.to_dict()  # pyright: ignore [reportAttributeAccessIssue]
                        )
        else:
            # Handle regular string/dict values
            processed_column_values = dict(column_values)

        return processed_column_values
