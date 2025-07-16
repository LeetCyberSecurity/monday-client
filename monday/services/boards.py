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
Module for handling monday.com board operations.

This module provides a comprehensive set of functions and classes for interacting
with monday.com boards.

This module is part of the monday-client package and relies on the MondayClient
for making API requests. It also utilizes various utility functions to ensure proper
data handling and error checking.

Usage of this module requires proper authentication and initialization of the
MondayClient instance.
"""

import json
import logging
from typing import TYPE_CHECKING, Any, Literal, cast

from monday.fields.board_fields import BoardFields
from monday.fields.column_fields import ColumnFields
from monday.fields.item_fields import ItemFields
from monday.services.utils.data_modifiers import update_data_in_place
from monday.services.utils.error_handlers import check_query_result
from monday.services.utils.fields import Fields
from monday.services.utils.pagination import (
    extract_items_page_value,
    paginated_item_request,
)
from monday.services.utils.query_builder import (
    build_graphql_query,
    build_query_params_string,
)
from monday.types.board import Board, UpdateBoard
from monday.types.column import Column, ColumnFilter, ColumnType
from monday.types.column_defaults import ColumnDefaults
from monday.types.item import Item, ItemList, QueryParams, QueryRule

if TYPE_CHECKING:
    from monday.client import MondayClient


class Boards:
    """
    Service class for handling monday.com board operations.
    """

    _logger: logging.Logger = logging.getLogger(__name__)

    def __init__(self, client: 'MondayClient'):
        """
        Initialize a Boards instance with specified parameters.

        Args:
            client: The MondayClient instance to use for API requests.

        """
        self.client = client

    async def query(  # noqa: PLR0913
        self,
        board_ids: int | str | list[int | str] | None = None,
        board_kind: Literal['private', 'public', 'share', 'all'] = 'all',
        order_by: Literal['created', 'used'] = 'created',
        items_page_limit: int = 25,
        boards_limit: int = 25,
        page: int = 1,
        state: Literal['active', 'all', 'archived', 'deleted'] = 'active',
        workspace_ids: int | str | list[int | str] | None = None,
        fields: str | Fields = BoardFields.BASIC,
        *,
        paginate_items: bool = True,
        paginate_boards: bool = True,
    ) -> list[Board]:
        """
        Query boards to return metadata about one or multiple boards.

        Args:
            board_ids: The ID or list of IDs of the boards to query.
            paginate_items: Whether to paginate items if items_page is in fields.
            paginate_boards: Whether to paginate boards. If False, only returns the first page.
            board_kind: The kind of boards to include.
            order_by: The order in which to return the boards.
            items_page_limit: The number of items to return per page when items_page is part of your fields.
            boards_limit: The number of boards to return per page.
            page: The page number to start from.
            state: The state of the boards to include.
            workspace_ids: The ID or list of IDs of the workspaces to filter by.
            fields: Fields to return from the queried board. Can be a string of space-separated field names or a :meth:`Fields() <monday.services.utils.fields.Fields>` instance.

        Returns:
            List of Board dataclass instances containing queried board data.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> boards = await monday_client.boards.query(
                ...     board_ids=987654321,
                ...     fields='id name state'
                ... )
                >>> boards[0].id
                "987654321"
                >>> boards[0].name
                "Board 1"
                >>> boards[0].state
                "active"

        """
        fields = Fields(fields)
        fields, cursor_added = self._prepare_fields_with_cursor(
            fields, paginate_items=paginate_items
        )
        original_fields = str(fields) if cursor_added else None

        args = self._build_query_args(
            board_ids,
            board_kind,
            order_by,
            boards_limit,
            page,
            state,
            workspace_ids,
            fields,
        )

        boards_data = []
        query_string = None

        while True:
            query_string = build_graphql_query('boards', 'query', args)

            self._logger.debug('query_string: %s', query_string)

            query_result = await self.client.post_request(query_string)
            data = check_query_result(query_result)
            self._logger.debug('Received API data: %s', data)

            should_continue = await self._handle_pagination_response(
                data, boards_data, fields, paginate_items=paginate_items
            )
            if not should_continue:
                break

            if not paginate_boards:
                break

            args['page'] += 1

        await self._process_items_pagination(
            boards_data,
            fields,
            items_page_limit,
            query_string,
            paginate_items=paginate_items,
        )

        if cursor_added and original_fields:
            temp_fields = ['items_page { cursor }']
            processed_data = Fields.manage_temp_fields(
                boards_data, original_fields, temp_fields
            )
            if isinstance(processed_data, list):
                boards_data = processed_data

        boards = [Board.from_dict(board) for board in boards_data]
        self._logger.debug('Final boards data: %s', boards)
        return boards

    async def get_items(  # noqa: PLR0913
        self,
        board_ids: int | str | list[int | str],
        query_params: QueryParams | dict[str, Any] | None = None,
        limit: int = 25,
        group_id: str | None = None,
        fields: str | Fields = ItemFields.BASIC,
        *,
        paginate_items: bool = True,
    ) -> list[ItemList]:
        """
        Retrieves a paginated list of items from specified boards.

        Note:
            This method supports filtering using :class:`~monday.types.item.QueryParams`. For examples and detailed information about building complex queries, see :ref:`Query Types <query_types>` in the Types documentation.

        Args:
            board_ids: The ID or list of IDs of the boards from which to retrieve items.
            query_params: A set of parameters to filter, sort, and control the scope of the underlying boards query. Use this to customize the results based on specific criteria. Can be a QueryParams object or a dictionary.
            limit: The maximum number of items to retrieve per page.
            group_id: Only retrieve items from the specified group ID.
            paginate_items: Whether to paginate items. If False, only returns the first page.
            fields: Fields to return from the items. Can be a string of space-separated field names or a :meth:`Fields() <monday.services.utils.fields.Fields>` instance.

        Returns:
            A list of ItemList dataclass instances containing the board IDs and their combined items retrieved.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient, QueryParams, QueryRule
                >>> monday_client = MondayClient('your_api_key')

                # Using QueryParams objects (recommended for type safety)
                >>> query_params = QueryParams(
                ...     rules=[
                ...         QueryRule(
                ...             column_id='status',
                ...             compare_value=['Done'],
                ...             operator='contains_terms'
                ...         )
                ...     ]
                ... )
                >>> item_lists = await monday_client.boards.get_items(
                ...     board_ids=987654321,
                ...     query_params=query_params,
                ...     limit=50
                ... )

                # Using dictionary format (equivalent functionality)
                >>> item_lists = await monday_client.boards.get_items(
                ...     board_ids=987654321,
                ...     query_params={
                ...         'rules': [
                ...             {
                ...                 'column_id': 'status',
                ...                 'compare_value': ['Done'],
                ...                 'operator': 'contains_terms'
                ...             }
                ...         ]
                ...     },
                ...     limit=50
                ... )
                >>> item_lists[0].board_id
                "987654321"
                >>> len(item_lists[0].items)
                25
                >>> item_lists[0].items[0].name
                "Task 1"

        """
        fields = Fields(fields)
        board_ids = (
            [board_ids]
            if board_ids is not None and not isinstance(board_ids, list)
            else board_ids
        )

        if query_params is None:
            query_params = QueryParams()

        if isinstance(query_params, dict):
            query_params = QueryParams(**query_params)

        # Build the items_page field with query parameters if provided
        items_page_field = 'items_page'
        if (
            query_params.rules
            or query_params.operator
            or query_params.order_by
            or query_params.ids
        ):
            query_params_str = build_query_params_string(query_params)
            if query_params_str:
                items_page_field = f'items_page (query_params: {query_params_str})'

        boards_fields = f'id {items_page_field} {{ cursor items {{ {fields!s} }} }}'
        boards_data = await self._fetch_paginated_boards(board_ids, boards_fields)

        if group_id:
            return self._process_group_items(boards_data)

        return await self._process_board_items_pagination(
            boards_data, fields, limit, paginate_items=paginate_items
        )

    async def get_items_by_column_values(
        self,
        board_id: int | str,
        columns: list[ColumnFilter],
        limit: int = 25,
        *,
        paginate_items: bool = True,
        fields: str | Fields = ItemFields.BASIC,
    ) -> list[Item]:
        """
        Retrieves items from a board based on specific column values.

        Args:
            board_id: The ID of the board from which to retrieve items.
            columns: A list of ColumnFilter objects specifying the column values to filter by.
            limit: The maximum number of items to retrieve per page.
            paginate_items: Whether to paginate items. If False, only returns the first page.
            fields: Fields to return from the items. Can be a string of space-separated field names or a :meth:`Fields() <monday.services.utils.fields.Fields>` instance.

        Returns:
            A list of Item dataclass instances containing the filtered items.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient, ColumnFilter
                >>> monday_client = MondayClient('your_api_key')

                # Using ColumnFilter objects (recommended for type safety)
                >>> columns = [
                ...     ColumnFilter(
                ...         column_id='status',
                ...         column_values=['Done', 'In Progress']
                ...     ),
                ...     ColumnFilter(
                ...         column_id='priority',
                ...         column_values=['High']
                ...     )
                ... ]
                >>> items = await monday_client.boards.get_items_by_column_values(
                ...     board_id=987654321,
                ...     columns=columns,
                ...     limit=50
                ... )

                # Using dictionary format (equivalent functionality)
                >>> columns = [
                ...     {'column_id': 'status', 'column_values': ['Done', 'In Progress']},
                ...     {'column_id': 'priority', 'column_values': ['High']}
                ... ]
                >>> items = await monday_client.boards.get_items_by_column_values(
                ...     board_id=987654321,
                ...     columns=[ColumnFilter(**col) for col in columns],
                ...     limit=50
                ... )
                >>> len(items)
                25

        """
        # Convert ColumnFilter objects to QueryRule objects
        rules = []
        for column_filter in columns:
            # Convert column_values to list if it's a string
            compare_values = (
                [column_filter.column_values]
                if isinstance(column_filter.column_values, str)
                else list(column_filter.column_values)
            )
            rules.append(
                QueryRule(
                    column_id=column_filter.column_id,
                    compare_value=cast('list[str | int]', compare_values),
                    operator='contains_terms',
                )
            )

        # Use the get_items method with query parameters
        query_params = QueryParams(rules=rules)

        item_lists = await self.get_items(
            board_ids=board_id,
            query_params=query_params,
            limit=limit,
            fields=fields,
            paginate_items=paginate_items,
        )

        # Extract items from the ItemList objects
        items = []
        for item_list in item_lists:
            items.extend(item_list.items)

        return items

    async def get_column_values(
        self,
        board_id: int | str,
        column_ids: str | list[str],
        column_fields: str | Fields = ColumnFields.BASIC,
        item_fields: str | Fields = ItemFields.BASIC,
    ) -> list[Item]:
        """
        Retrieves column values for specific columns on a board.

        Args:
            board_id: The ID of the board from which to retrieve column values.
            column_ids: The ID or list of IDs of the columns to retrieve values for.
            column_fields: Fields to return from the columns. Can be a string of space-separated field names or a :meth:`Fields() <monday.services.utils.fields.Fields>` instance.
            item_fields: Fields to return from the items. Can be a string of space-separated field names or a :meth:`Fields() <monday.services.utils.fields.Fields>` instance.

        Returns:
            A list of Item dataclass instances containing the column values.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> items = await monday_client.boards.get_column_values(
                ...     board_id=987654321,
                ...     column_ids=['status', 'priority'],
                ...     column_fields='id title type',
                ...     item_fields='id name'
                ... )
                >>> len(items)
                25

        """
        column_fields = Fields(column_fields)
        item_fields = Fields(item_fields)

        column_ids = (
            [column_ids]
            if column_ids is not None and not isinstance(column_ids, list)
            else column_ids
        )

        # Ensure column_ids are rendered as double-quoted strings
        if isinstance(column_ids, list):
            column_ids_str = '[' + ', '.join(f'"{col}"' for col in column_ids) + ']'
        else:
            column_ids_str = f'"{column_ids}"'

        query = f"""
            query {{
                boards (ids: {board_id}) {{
                    items_page {{
                        items {{
                            {item_fields}
                            column_values (ids: {column_ids_str}) {{
                                {column_fields}
                            }}
                        }}
                    }}
                }}
            }}
        """

        self._logger.debug('query: %s', query)

        query_result = await self.client.post_request(query)
        data = check_query_result(query_result)

        items_data = []
        if data['data'].get('boards'):
            for board in data['data']['boards']:
                if board.get('items_page'):
                    items_data.extend(board['items_page'].get('items', []))

        items = [Item.from_dict(item) for item in items_data]

        self._logger.debug('Final items data: %s', items)

        return items

    async def create(  # noqa: PLR0913
        self,
        name: str,
        board_kind: Literal['private', 'public', 'share'] | None = 'public',
        owner_ids: list[int | str] | None = None,
        subscriber_ids: list[int | str] | None = None,
        subscriber_teams_ids: list[int | str] | None = None,
        description: str | None = None,
        folder_id: int | str | None = None,
        template_id: int | str | None = None,
        workspace_id: int | str | None = None,
        fields: str | Fields = BoardFields.BASIC,
    ) -> Board:
        """
        Creates a new board on monday.com.

        Args:
            name: The name of the board to create.
            board_kind: The kind of board to create.
            owner_ids: List of user IDs to set as board owners.
            subscriber_ids: List of user IDs to subscribe to the board.
            subscriber_teams_ids: List of team IDs to subscribe to the board.
            description: A description for the board.
            folder_id: The ID of the folder to place the board in.
            template_id: The ID of the template to use for the board.
            workspace_id: The ID of the workspace to place the board in.
            fields: Fields to return from the created board. Can be a string of space-separated field names or a :meth:`Fields() <monday.services.utils.fields.Fields>` instance.

        Returns:
            A Board dataclass instance containing the created board data.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> board = await monday_client.boards.create(
                ...     name='New Project Board',
                ...     board_kind='public',
                ...     description='A board for tracking project progress'
                ... )
                >>> board.id
                "987654321"
                >>> board.name
                "New Project Board"

        """
        fields = Fields(fields)

        mutation_args = {
            'board_name': name,
            'board_kind': board_kind,
            'fields': fields,
        }

        if owner_ids is not None:
            mutation_args['board_owners_ids'] = owner_ids
        if subscriber_ids is not None:
            mutation_args['board_subscribers_ids'] = subscriber_ids
        if subscriber_teams_ids is not None:
            mutation_args['board_subscribers_teams_ids'] = subscriber_teams_ids
        if description is not None:
            mutation_args['board_description'] = description
        if folder_id is not None:
            mutation_args['board_folder_id'] = folder_id
        if template_id is not None:
            mutation_args['board_template_id'] = template_id
        if workspace_id is not None:
            mutation_args['board_workspace_id'] = workspace_id

        query = build_graphql_query('create_board', 'mutation', mutation_args)
        query_result = await self.client.post_request(query)
        data = check_query_result(query_result)

        board_data = data['data']['create_board']
        return Board.from_dict(board_data)

    async def duplicate(  # noqa: PLR0913
        self,
        board_id: int | str,
        board_name: str | None = None,
        duplicate_type: Literal[
            'with_pulses',
            'with_pulses_and_updates',
            'with_structure',
        ] = 'with_structure',
        folder_id: int | str | None = None,
        workspace_id: int | str | None = None,
        fields: str | Fields = BoardFields.BASIC,
        *,
        keep_subscribers: bool = False,
    ) -> Board:
        """
        Duplicates an existing board on monday.com.

        Args:
            board_id: The ID of the board to duplicate.
            board_name: The name for the duplicated board. If None, will use the original name with "Copy" appended.
            duplicate_type: The type of duplication to perform.
            folder_id: The ID of the folder to place the duplicated board in.
            workspace_id: The ID of the workspace to place the duplicated board in.
            fields: Fields to return from the duplicated board. Can be a string of space-separated field names or a :meth:`Fields() <monday.services.utils.fields.Fields>` instance.
            keep_subscribers: Whether to keep the original board's subscribers on the duplicated board.

        Returns:
            A Board dataclass instance containing the duplicated board data.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> duplicated_board = await monday_client.boards.duplicate(
                ...     board_id=987654321,
                ...     board_name='Project Board Copy',
                ...     duplicate_type='with_structure'
                ... )
                >>> duplicated_board.id
                "987654322"
                >>> duplicated_board.name
                "Project Board Copy"

        """
        fields = Fields(fields)

        # Create nested board field structure
        board_fields = f'board {{ {fields} }}'
        fields = Fields(board_fields)

        mutation_args = {
            'board_id': board_id,
            'duplicate_type': f'duplicate_board_{duplicate_type}',
            'keep_subscribers': keep_subscribers,
            'fields': fields,
        }

        if board_name is not None:
            mutation_args['board_name'] = board_name
        if folder_id is not None:
            mutation_args['folder_id'] = folder_id
        if workspace_id is not None:
            mutation_args['workspace_id'] = workspace_id

        query = build_graphql_query('duplicate_board', 'mutation', mutation_args)

        self._logger.debug('query: %s', query)

        query_result = await self.client.post_request(query)
        data = check_query_result(query_result)

        board_data = data['data']['duplicate_board']

        # Handle both nested and direct response structures
        if 'board' in board_data:
            board_data = board_data['board']

        return Board.from_dict(board_data)

    async def update(
        self,
        board_id: int | str,
        board_attribute: Literal['communication', 'description', 'name'],
        new_value: str,
    ) -> UpdateBoard:
        """
        Updates a specific attribute of a board.

        Args:
            board_id: The ID of the board to update.
            board_attribute: The attribute of the board to update.
            new_value: The new value for the specified attribute.

        Returns:
            An UpdateBoard dataclass instance containing the update result.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> result = await monday_client.boards.update(
                ...     board_id=987654321,
                ...     board_attribute='name',
                ...     new_value='Updated Board Name'
                ... )
                >>> result.success
                True
                >>> result.name
                "Updated Board Name"

        """
        # Get the previous value of the attribute
        previous_attribute_query = f"""
            query {{
                boards (ids: {board_id}) {{
                    {board_attribute}
                }}
            }}
        """
        previous_attribute_result = await self.client.post_request(
            previous_attribute_query
        )
        previous_attribute_data = check_query_result(previous_attribute_result)
        previous_value = None
        if previous_attribute_data['data'].get('boards'):
            previous_value = previous_attribute_data['data']['boards'][0].get(
                board_attribute
            )

        mutation_args = {
            'board_id': board_id,
            'board_attribute': board_attribute,
            'new_value': new_value,
        }

        query = build_graphql_query('update_board', 'mutation', mutation_args)

        self._logger.debug('query: %s', query)

        query_result = await self.client.post_request(query)
        data = check_query_result(query_result)

        self._logger.debug('update_board response data: %s', data)

        # Parse the JSON response string
        update_response_str = data['data']['update_board']
        update_response = json.loads(update_response_str)

        # Create the response data structure
        response_data = {
            'success': update_response.get('success', True),
            'board_id': board_id,
            'board_attribute': board_attribute,
            'new_value': new_value,
        }

        # Set the name field based on the new_value if updating the name attribute
        if board_attribute == 'name':
            response_data['name'] = new_value

        # Set the previous_attribute field
        if previous_value is not None:
            response_data['previous_attribute'] = previous_value

        # Include the undo_data if present
        if 'undo_data' in update_response:
            response_data['undo_data'] = update_response['undo_data']

        update_data = UpdateBoard.from_dict(response_data)

        self._logger.debug('final update data: %s', update_data)

        return update_data

    async def archive(
        self, board_id: int | str, fields: str | Fields = BoardFields.BASIC
    ) -> Board:
        """
        Archives a board on monday.com.

        Args:
            board_id: The ID of the board to archive.
            fields: Fields to return from the archived board. Can be a string of space-separated field names or a :meth:`Fields() <monday.services.utils.fields.Fields>` instance.

        Returns:
            A Board dataclass instance containing the archived board data.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> archived_board = await monday_client.boards.archive(
                ...     board_id=987654321
                ... )
                >>> archived_board.state
                "archived"

        """
        fields = Fields(fields)

        mutation_args = {
            'board_id': board_id,
            'fields': fields,
        }

        query = build_graphql_query('archive_board', 'mutation', mutation_args)
        query_result = await self.client.post_request(query)
        data = check_query_result(query_result)

        board_data = data['data']['archive_board']
        return Board.from_dict(board_data)

    async def delete(
        self, board_id: int | str, fields: str | Fields = BoardFields.BASIC
    ) -> Board:
        """
        Deletes a board from monday.com.

        Args:
            board_id: The ID of the board to delete.
            fields: Fields to return from the deleted board. Can be a string of space-separated field names or a :meth:`Fields() <monday.services.utils.fields.Fields>` instance.

        Returns:
            A Board dataclass instance containing the deleted board data.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> deleted_board = await monday_client.boards.delete(
                ...     board_id=987654321
                ... )
                >>> deleted_board.state
                "deleted"

        """
        fields = Fields(fields)

        mutation_args = {
            'board_id': board_id,
            'fields': fields,
        }

        query = build_graphql_query('delete_board', 'mutation', mutation_args)
        query_result = await self.client.post_request(query)
        data = check_query_result(query_result)

        board_data = data['data']['delete_board']
        return Board.from_dict(board_data)

    async def create_column(  # noqa: PLR0913
        self,
        board_id: int | str,
        column_type: ColumnType,
        title: str,
        defaults: dict[str, Any] | ColumnDefaults | None = None,
        after_column_id: str | None = None,
        fields: str | Fields = ColumnFields.BASIC,
    ) -> Column:
        """
        Creates a new column on a board.

        Args:
            board_id: The ID of the board to add the column to.
            column_type: The type of column to create.
            title: The title of the new column.
            defaults: Default values for the column. Can be a dictionary or ColumnDefaults object. The format depends on the column type.
            after_column_id: The ID of the column to place the new column after.
            fields: Fields to return from the created column. Can be a string of space-separated field names or a :meth:`Fields() <monday.services.utils.fields.Fields>` instance.

        Returns:
            A Column dataclass instance containing the created column data.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> from monday.types.column_defaults import StatusDefaults, StatusLabel, DropdownDefaults, DropdownLabel
                >>> monday_client = MondayClient('your_api_key')

                # Using StatusDefaults objects (recommended for type safety)
                >>> column = await monday_client.boards.create_column(
                ...     board_id=987654321,
                ...     column_type='status',
                ...     title='Priority',
                ...     defaults=StatusDefaults(
                ...         labels=[
                ...             StatusLabel('Low', 0),
                ...             StatusLabel('Medium', 1),
                ...             StatusLabel('High', 2)
                ...         ]
                ...     )
                ... )

                # Using dictionary format (equivalent functionality)
                >>> column = await monday_client.boards.create_column(
                ...     board_id=987654321,
                ...     column_type='status',
                ...     title='Priority',
                ...     defaults={
                ...         'labels': {
                ...             0: 'Low',
                ...             1: 'Medium',
                ...             2: 'High'
                ...         }
                ...     }
                ... )
                >>> column.id
                "status_123"
                >>> column.title
                "Priority"

                # Creating a dropdown column with custom options
                >>> dropdown_column = await monday_client.boards.create_column(
                ...     board_id=987654321,
                ...     column_type='dropdown',
                ...     title='Category',
                ...     defaults=DropdownDefaults(
                ...         options=[
                ...             DropdownLabel('Bug'),
                ...             DropdownLabel('Feature'),
                ...             DropdownLabel('Enhancement'),
                ...             DropdownLabel('Documentation')
                ...         ]
                ...     )
                ... )

                # Using dictionary format for dropdown (equivalent functionality)
                >>> dropdown_column = await monday_client.boards.create_column(
                ...     board_id=987654321,
                ...     column_type='dropdown',
                ...     title='Category',
                ...     defaults={
                ...         'settings': {
                ...             'labels': [
                ...                 {'id': 0, 'name': 'Bug'},
                ...                 {'id': 1, 'name': 'Feature'},
                ...                 {'id': 2, 'name': 'Enhancement'},
                ...                 {'id': 3, 'name': 'Documentation'}
                ...             ]
                ...         }
                ...     }
                ... )

        """
        fields = Fields(fields)

        mutation_args = {
            'board_id': board_id,
            'column_type': column_type,
            'title': title,
            'fields': fields,
        }

        if defaults is not None:
            if isinstance(defaults, dict):
                # Convert to JSON and escape double quotes for GraphQL
                json_str = json.dumps(defaults)
                mutation_args['defaults'] = json_str.replace('"', '\\"')
            else:
                # Convert to JSON and escape double quotes for GraphQL
                json_str = json.dumps(defaults.to_dict())
                mutation_args['defaults'] = json_str.replace('"', '\\"')

        if after_column_id is not None:
            mutation_args['after_column_id'] = after_column_id

        query = build_graphql_query('create_column', 'mutation', mutation_args)

        self._logger.debug('query %s', query)

        query_result = await self.client.post_request(query)
        data = check_query_result(query_result)

        self._logger.debug('create_column response data: %s', data)

        column_data = data['data']['create_column']
        return Column.from_dict(column_data)

    def _prepare_fields_with_cursor(
        self, fields: Fields, *, paginate_items: bool
    ) -> tuple[Fields, bool]:
        """Prepare fields with cursor for pagination if needed."""
        cursor_added = False

        if paginate_items and 'items_page' in fields:
            fields_str = str(fields)
            block_pos = self._find_items_page_block(fields_str)
            if block_pos:
                start, end = block_pos
                inner = fields_str[start:end].strip()
                if 'cursor' not in inner:
                    items_page_start = fields_str.rfind('items_page', 0, start)
                    brace_end = end + 1
                    # Add cursor at the beginning of the inner content
                    new_inner = 'cursor ' + inner
                    new_items_page_block = f'items_page {{ {new_inner} }}'
                    new_fields_str = (
                        fields_str[:items_page_start]
                        + new_items_page_block
                        + fields_str[brace_end:]
                    )
                    fields = Fields(new_fields_str)
                    cursor_added = True
            elif 'items_page (' not in fields_str and 'cursor' not in fields_str:
                # If no items_page block found, add a simple one
                fields += 'items_page { cursor }'
                cursor_added = True

        return fields, cursor_added

    def _build_query_args(  # noqa: PLR0913
        self,
        board_ids: int | str | list[int | str] | None,
        board_kind: str,
        order_by: str,
        boards_limit: int,
        page: int,
        state: str,
        workspace_ids: int | str | list[int | str] | None,
        fields: Fields,
    ) -> dict[str, Any]:
        """Build query arguments dictionary."""
        board_ids = (
            [board_ids]
            if board_ids is not None and not isinstance(board_ids, list)
            else board_ids
        )

        return {
            'ids': board_ids,
            'board_kind': board_kind if board_kind != 'all' else None,
            'order_by': f'{order_by}_at',
            'limit': boards_limit,
            'page': page,
            'state': state,
            'workspace_ids': workspace_ids,
            'fields': fields,
        }

    async def _handle_pagination_response(
        self,
        data: dict[str, Any],
        boards_data: list[dict[str, Any]],
        fields: Fields,
        *,
        paginate_items: bool,
    ) -> bool:
        """Handle pagination response and return whether to continue."""
        if not data['data'].get('boards'):
            if (
                paginate_items
                and 'items_page' in fields
                and 'next_items_page' in data['data']
            ):
                items_page = data['data']['next_items_page']
                for board in boards_data:
                    if 'items_page' in board:
                        board['items_page']['items'].extend(items_page['items'])
                        board['items_page']['cursor'] = items_page['cursor']
                return True
            return False
        boards_data.extend(data['data']['boards'])
        return True

    async def _process_items_pagination(
        self,
        boards_data: list[dict[str, Any]],
        fields: Fields,
        items_page_limit: int,
        query_string: str,
        *,
        paginate_items: bool,
    ) -> None:
        """Process items pagination for boards."""
        if 'items_page' not in fields or not paginate_items:
            return

        for board in boards_data:
            items_page = extract_items_page_value(board)
            if not items_page or not items_page['cursor']:
                continue

            query_result = await paginated_item_request(
                self.client,
                query_string,
                limit=items_page_limit,
                cursor=items_page['cursor'],
            )
            new_items = query_result.items if query_result.items else []
            items_page['items'].extend(new_items)
            del items_page['cursor']
            update_data_in_place(
                board, lambda ip, items_page=items_page: ip.update(items_page)
            )

        # Convert items_page to items if fields contain items_page
        if 'items_page' in str(fields):
            for board in boards_data:
                board['items'] = board.pop('items_page')['items']

    def _build_items_query(
        self,
        board_ids: int | str | list[int | str],
        fields: Fields,
        limit: int,
        group_id: str | None,
    ) -> str:
        """Build items query string."""
        board_ids = (
            [board_ids]
            if board_ids is not None and not isinstance(board_ids, list)
            else board_ids
        )

        query_args = {
            'ids': board_ids,
            'limit': limit,
            'fields': f'id items_page {{ cursor items {{ {fields} }} }}',
        }

        if group_id:
            query_args['group_id'] = group_id

        return build_graphql_query('boards', 'query', query_args)

    async def _fetch_paginated_boards(
        self, board_ids: int | str | list[int | str], boards_fields: str
    ) -> list[dict[str, Any]]:
        """Fetch paginated boards data."""
        board_ids = (
            [board_ids]
            if board_ids is not None and not isinstance(board_ids, list)
            else board_ids
        )

        query_args = {
            'ids': board_ids,
            'fields': boards_fields,
        }

        query = build_graphql_query('boards', 'query', query_args)
        query_result = await self.client.post_request(query)
        data = check_query_result(query_result)

        return data['data'].get('boards', [])

    def _process_group_items(self, boards_data: list[dict[str, Any]]) -> list[ItemList]:
        """Process group items from boards data."""
        items = []
        for board in boards_data:
            if board.get('groups'):
                # Handle items in groups
                board_items = []
                for group in board['groups']:
                    if group.get('items_page'):
                        items_page = group['items_page']
                        board_items.extend(items_page.get('items', []))
                items.append(
                    ItemList(
                        board_id=str(board['id']),
                        items=[Item.from_dict(i) for i in board_items],
                    )
                )
            elif board.get('items_page'):
                # Handle items directly in board
                items_page = board['items_page']
                board_items = items_page.get('items', [])
                items.append(
                    ItemList(
                        board_id=str(board['id']),
                        items=[Item.from_dict(i) for i in board_items],
                    )
                )
            else:
                items.append(ItemList(board_id=str(board['id']), items=[]))
        return items

    async def _process_board_items_pagination(
        self,
        boards_data: list[dict[str, Any]],
        fields: Fields,
        limit: int,
        *,
        paginate_items: bool = True,
    ) -> list[ItemList]:
        """Process board items pagination."""
        items = []
        for board in boards_data:
            if board.get('items_page'):
                items_page = board['items_page']
                board_items = items_page.get('items', [])

                # Only paginate if paginate_items is True
                if paginate_items and items_page.get('cursor'):
                    cursor = items_page['cursor']
                    while cursor:
                        items_selection_set = str(fields)
                        next_query = f"""
                            query {{
                                next_items_page (
                                    limit: {limit},
                                    cursor: "{cursor}"
                                ) {{
                                    cursor items {{ {items_selection_set} }}
                                }}
                            }}
                        """

                        next_data = await self.client.post_request(next_query)
                        next_data = check_query_result(next_data)

                        if 'next_items_page' in next_data['data']:
                            next_items_page = next_data['data']['next_items_page']
                            board_items.extend(next_items_page.get('items', []))
                            cursor = next_items_page.get('cursor')
                        else:
                            break

                items.append(
                    ItemList(
                        board_id=str(board['id']),
                        items=[Item.from_dict(i) for i in board_items],
                    )
                )
            else:
                items.append(ItemList(board_id=str(board['id']), items=[]))
        return items

    @staticmethod
    def _find_items_page_block(fields_str: str) -> tuple[int, int] | None:
        """Find the position of items_page block in fields string."""
        start = fields_str.find('items_page {')
        if start == -1:
            return None

        brace_count = 0
        in_block = False
        inner_start = -1

        for i, char in enumerate(fields_str[start:], start):
            if char == '{':
                if not in_block:
                    in_block = True
                    inner_start = i + 1  # Position after the opening brace
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if in_block and brace_count == 0:
                    if inner_start != -1:
                        return inner_start, i  # Return positions for inner content only
                    return None

        return None
