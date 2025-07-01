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
from typing import TYPE_CHECKING, Any, Literal, Optional, Union

from monday.fields.board_fields import BoardFields
from monday.services.utils.data_modifiers import update_data_in_place
from monday.services.utils.error_handlers import check_query_result
from monday.services.utils.fields import Fields
from monday.services.utils.pagination import (extract_items_page_value,
                                              paginated_item_request)
from monday.services.utils.query_builder import (ColumnFilter, QueryParams,
                                                 build_graphql_query,
                                                 build_query_params_string)
from monday.types.board import Board, UpdateBoard
from monday.types.item import Item, ItemList

if TYPE_CHECKING:
    from monday.client import MondayClient


class Boards:
    """
    Service class for handling monday.com board operations.
    """

    _logger: logging.Logger = logging.getLogger(__name__)

    def __init__(
        self,
        client: 'MondayClient'
    ):
        """
        Initialize a Boards instance with specified parameters.

        Args:
            client: The MondayClient instance to use for API requests.
        """
        self.client = client

    async def query(
        self,
        board_ids: Optional[Union[int | str, list[int | str]]] = None,
        paginate_items: bool = True,
        board_kind: Literal['private', 'public', 'share', 'all'] = 'all',
        order_by: Literal['created', 'used'] = 'created',
        items_page_limit: int = 25,
        boards_limit: int = 25,
        page: int = 1,
        state: Literal['active', 'all', 'archived', 'deleted'] = 'active',
        workspace_ids: Optional[Union[int | str, list[int | str]]] = None,
        fields: Union[str, Fields] = BoardFields.BASIC
    ) -> list[Board]:
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
            fields: Fields to return from the queried board. Can be a string of space-separated field names or a :meth:`Fields() <monday.Fields>` instance.

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

        # Only add items_page { cursor } if items_page exists but doesn't have arguments
        # and doesn't already include cursor
        if paginate_items and 'items_page' in fields and 'cursor' not in fields:
            # Check if items_page already has arguments (contains parentheses)
            fields_str = str(fields)
            if 'items_page (' not in fields_str:
                fields += 'items_page { cursor }'

        board_ids = [board_ids] if board_ids is not None and not isinstance(board_ids, list) else board_ids

        args = {
            'ids': board_ids,
            'board_kind': board_kind if board_kind != 'all' else None,
            'order_by': f'{order_by}_at',
            'limit': boards_limit,
            'page': page,
            'state': state,
            'workspace_ids': workspace_ids,
            'fields': fields
        }

        boards_data = []

        while True:
            query_string = build_graphql_query(
                'boards',
                'query',
                args
            )

            query_result = await self.client.post_request(query_string)
            data = check_query_result(query_result)

            # Handle pagination and data collection
            if not data['data'].get('boards'):
                if paginate_items and 'items_page' in fields and 'next_items_page' in data['data']:
                    # Handle next_items_page response
                    items_page = data['data']['next_items_page']
                    for board in boards_data:
                        if 'items_page' in board:
                            board['items_page']['items'].extend(items_page['items'])
                            board['items_page']['cursor'] = items_page['cursor']
                else:
                    break
            else:
                boards_data.extend(data['data']['boards'])

            args['page'] += 1

        # Process items if needed
        if 'items_page' in fields and paginate_items:
            for board in boards_data:
                items_page = extract_items_page_value(board)
                if not items_page or not items_page['cursor']:
                    continue

                query_result = await paginated_item_request(
                    self.client,
                    query_string,
                    limit=items_page_limit,
                    cursor=items_page['cursor']
                )
                # Extract items from PaginatedResult
                new_items = query_result.items if query_result.items else []
                items_page['items'].extend(new_items)
                del items_page['cursor']
                update_data_in_place(board, lambda ip, items_page=items_page: ip.update(items_page))

            # Convert items_page to items if using BoardFields.ITEMS
            if fields == BoardFields.ITEMS:
                for board in boards_data:
                    board['items'] = board.pop('items_page')['items']

        # Convert raw dictionaries to Board dataclass instances
        boards = [Board.from_dict(board) for board in boards_data]
        return boards

    async def get_items(
        self,
        board_ids: Union[int | str, list[int | str]],
        query_params: Optional[Union[QueryParams, dict[str, Any]]] = None,
        limit: int = 25,
        group_id: Optional[str] = None,
        paginate_items: bool = True,
        fields: Union[str, Fields] = BoardFields.BASIC
    ) -> list[ItemList]:
        """
        Retrieves a paginated list of items from specified boards.

        Args:
            board_ids: The ID or list of IDs of the boards from which to retrieve items.
            query_params: A set of parameters to filter, sort, and control the scope of the underlying boards query. Use this to customize the results based on specific criteria. Can be a QueryParams object or a dictionary.
            limit: The maximum number of items to retrieve per page.
            group_id: Only retrieve items from the specified group ID.
            paginate_items: Whether to paginate items.
            fields: Fields to return from the items. Can be a string of space-separated field names or a :meth:`Fields() <monday.Fields>` instance.

        Returns:
            A list of ItemList dataclass instances containing the board IDs and their combined items retrieved.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> item_lists = await monday_client.boards.get_items(
                ...     board_ids=987654321,
                ...     query_params={
                ...         'rules': [
                ...             {
                ...                 'column_id': 'status',
                ...                 'compare_value': ['Done'],
                ...                 'operator': 'contains_terms'
                ...             },
                ...             {
                ...                 'column_id': 'status_2',
                ...                 'compare_value': [2],
                ...                 'operator': 'not_any_of'
                ...             }
                ...         ]
                ...     },
                ...     fields='id column_values { id text }'   
                ... )
                >>> item_lists[0].board_id
                "987654321"
                >>> item_lists[0].items[0].id
                "123456789"
                >>> item_lists[0].items[0].column_values[0].text
                "Done"

        Note:
            The ``query_params`` argument allows complex filtering and sorting of items.

            Filter by status column:

            .. code-block:: python

                query_params={
                    'rules': [
                        {
                            'column_id': 'status',
                            'compare_value': ['Done', 'In Progress'],
                            'operator': 'contains_terms'
                        }
                    ]
                }

            Filter by date range:

            .. code-block:: python

                query_params={
                    'rules': [
                        {
                            'column_id': 'date_column',
                            'compare_value': ['2024-01-01', '2024-12-31'],
                            'operator': 'between'
                        }
                    ]
                }

            Multiple conditions with AND:

            .. code-block:: python

                query_params={
                    'rules': [
                        {
                            'column_id': 'status',
                            'compare_value': ['Done'],
                            'operator': 'contains_terms'
                        },
                        {
                            'column_id': 'priority',
                            'compare_value': [2],
                            'operator': 'not_any_of'
                        }
                    ],
                    'operator': 'and'
                }

            Sort by creation date:

            .. code-block:: python

                query_params={
                    'rules': [],  # No filtering
                    'order_by': {
                        'column_id': 'creation_date',
                        'direction': 'desc'
                    }
                }

            Text search in multiple columns:

            .. code-block:: python

                query_params={
                    'rules': [
                        {
                            'column_id': 'text_column',
                            'compare_value': ['search term'],
                            'operator': 'contains_text'
                        },
                        {
                            'column_id': 'name',
                            'compare_value': ['search term'],
                            'operator': 'contains_text'
                        }
                    ],
                    'operator': 'or'
                }

            **No data will be returned if you use invalid operators in your rules.**

            See the `monday.com API documentation (column types reference) <https://developer.monday.com/api-reference/reference/column-types-reference>`_ for more details on which operators are supported for each column type.

            See the `monday.com API documentation (items page) <https://developer.monday.com/api-reference/reference/items-page#queries>`_ for more details on query params.
        """

        # Convert dictionary to QueryParams object if needed
        if isinstance(query_params, dict):
            query_params = QueryParams.from_dict(query_params)

        query_params_str = build_query_params_string(query_params) if query_params else ''

        group_query = f'groups (ids: "{group_id}") {{' if group_id else ''
        group_query_end = '}' if group_id else ''
        field_str = f"""
            id
            {group_query}
            items_page (
                limit: {limit}{f', query_params: {query_params_str}' if query_params_str else ''}
            ) {{
                cursor
                items {{ {fields} }}
            }}
            {group_query_end}
        """
        fields = Fields(field_str)

        data = await self.query(
            board_ids,
            fields=fields,
            paginate_items=paginate_items,
            items_page_limit=limit
        )

        if group_id:
            boards = []
            for board in data:
                try:
                    if board.groups and board.groups[0] and board.groups[0].items_page:
                        items = board.groups[0].items_page.items if board.groups[0].items_page.items else []
                        boards.append(ItemList(board_id=board.id, items=items))
                    else:
                        boards.append(ItemList(board_id=board.id, items=[]))
                except IndexError:
                    boards.append(ItemList(board_id=board.id, items=[]))
            return boards

        items = [ItemList(board_id=b.id, items=b.items_page.items if b.items_page and b.items_page.items else []) for b in data]

        return items

    async def get_items_by_column_values(
        self,
        board_id: int | str,
        columns: list[ColumnFilter],
        limit: int = 25,
        paginate_items: bool = True,
        fields: Union[str, Fields] = BoardFields.BASIC
    ) -> list[Item]:
        """
        Retrieves items from a board filtered by specific column values.

        Args:
            board_id: The ID of the board from which to retrieve items.
            columns: List of column filters to search by.
            limit: The maximum number of items to retrieve per page.
            paginate_items: Whether to paginate items.
            fields: Fields to return from the matching items. Can be a string of space-separated field names or a :meth:`Fields() <monday.Fields>` instance.

        Returns:
            A list of Item dataclass instances containing the combined items retrieved.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
            PaginationError: If pagination fails.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> items = await monday_client.boards.get_items_by_column_values(
                ...     board_id=987654321,
                ...     columns=[
                ...         {
                ...             'column_id': 'status',
                ...             'column_values': ['Done', 'In Progress']
                ...         },
                ...         {
                ...             'column_id': 'text',
                ...             'column_values': 'This item is done'
                ...         }
                ...     ],
                ...     fields='id column_values { id text }'
                ... )
                >>> items[0].id
                "123456789"
                >>> items[0].column_values[0].id
                "status"
                >>> items[0].column_values[0].text
                "Done"
        """

        fields = Fields(fields)

        args = {
            'board_id': board_id,
            'columns': columns,
            'fields': f'cursor items {{ {fields} }}'
        }

        query_string = build_graphql_query(
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
            # Extract items from PaginatedResult
            items = data.items if data.items else []
        else:
            query_result = await self.client.post_request(query_string)
            data = check_query_result(query_result)
            items = data['data']['items_page_by_column_values']['items']

        items_list = [Item.from_dict(item) for item in items]

        return items_list

    async def get_column_values(
        self,
        board_id: int | str,
        column_ids: Union[str, list[str]],
        column_fields: Union[str, Fields] = 'id text',
        item_fields: Union[str, Fields] = BoardFields.BASIC
    ) -> list[Item]:
        """
        Retrieves specific column values for items on a board.

        Args:
            board_id: The ID of the board from which to retrieve item column values.
            column_ids: The specific column IDs to return.
            column_fields: Fields to return from the matching columns. Can be a string of space-separated field names or a :meth:`Fields() <monday.Fields>` instance.
            item_fields: Fields to return from the matching items. Can be a string of space-separated field names or a :meth:`Fields() <monday.Fields>` instance.

        Returns:
            A list of Item dataclass instances containing the combined items retrieved and their column values.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
            PaginationError: If pagination fails.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> await client.boards.get_column_values(
                ...     board_id=987654321,
                ...     column_ids=[
                ...         'text',
                ...         'status'
                ...     ]
                ... )
                [
                    {
                        "id": "123456789",
                        "name": "Item 1",
                        "column_values": [
                            {
                                "id": "text",
                                "text": "Item 1 text"
                            },
                            {
                                "id": "status",
                                "text": "Done"
                            }
                        ]
                    },
                    {
                        "id": "02345678",
                        "name": "Item 2",
                        "column_values": [
                            {
                                "id": "text",
                                "text": "Item 2 text"
                            },
                            {
                                "id": "status",
                                "text": "Working on it"
                            }
                        ]
                    }
                ]

        Note:
            Use :meth:`Items.get_column_values() <monday.services.Items.get_column_values>` to retrieve column values for a specific item.
        """

        column_ids = [f'"{i}"' for i in column_ids] if isinstance(column_ids, list) else [f'"{column_ids}"']

        if 'column_values' in item_fields:
            # Construct a new query that explicitly includes column_values with specific column IDs.
            # Having two column_values fields in the query would cause issues, so this removes any
            # existing column_values field from the input fields string
            item_fields_list = []  # Will hold the filtered fields
            fields_list = [i.strip() for i in str(item_fields).split()]  # Split into tokens
            skip_until_closing_brace = False  # Flag to track if we're in column_values block

            for field in fields_list:
                if field == 'column_values':  # Start skipping
                    skip_until_closing_brace = True
                    continue

                if skip_until_closing_brace:  # Keep skipping until we find }
                    if '}' in field:
                        skip_until_closing_brace = False
                    continue

                item_fields_list.append(field)  # Add non-skipped fields

            item_fields = ' '.join(item_fields_list)  # Rejoin filtered fields

        fields = Fields(f"{item_fields} column_values (ids: [{', '.join(column_ids)}]) {{ {column_fields} }}")

        query_result = await self.get_items(
            board_ids=board_id,
            fields=fields
        )

        if not query_result:
            return []

        # Handle case where query_result is empty or doesn't have the expected structure
        if len(query_result) == 0:
            return []

        try:
            items = query_result[0].items
            if isinstance(items, list):
                # Convert to Item instances if they're not already
                items_list = [item if isinstance(item, Item) else Item.from_dict(item) for item in items]
                return items_list
        except (IndexError, AttributeError):
            # Handle case where query_result[0] doesn't have items attribute
            return []

        return []

    async def create(
        self,
        name: str,
        board_kind: Optional[Literal['private', 'public', 'share']] = 'public',
        owner_ids: Optional[list[int | str]] = None,
        subscriber_ids: Optional[list[int | str]] = None,
        subscriber_teams_ids: Optional[list[int | str]] = None,
        description: Optional[str | str] = None,
        folder_id: Optional[int | str] = None,
        template_id: Optional[int | str] = None,
        workspace_id: Optional[int | str] = None,
        fields: Union[str, Fields] = BoardFields.BASIC
    ) -> Board:
        """
        Create a new board.

        Args:
            name: The name of the new board.
            kind: The kind of board to create.
            owner_ids: List of user IDs to set as board owners.
            subscriber_ids: List of user IDs to set as board subscribers.
            subscriber_teams_ids: List of team IDs to set as board subscribers.
            description: Description of the board.
            folder_id: ID of the folder to place the board in.
            template_id: ID of the template to use for the board.
            workspace_id: ID of the workspace to create the board in.
            fields: Fields to return from the created board. Can be a string of space-separated field names or a :meth:`Fields() <monday.Fields>` instance.

        Returns:
            Board dataclass instance containing info for the new board.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            MutationLimitExceeded: When the mutation API rate limit is exceeded.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> board = await monday_client.boards.create(
                ...     name='Board 1',
                ...     workspace_id=1234567,
                ...     description='Board 1 description',
                ...     fields='id name state description workspace_id'
                ... )
                >>> board.id
                "987654321"
                >>> board.name
                "Board 1"
                >>> board.state
                "active"
                >>> board.description
                "Board 1 description"
        """

        fields = Fields(fields)

        args = {
            'board_name': name,
            'board_kind': board_kind,
            'owner_ids': owner_ids,
            'subscriber_ids': subscriber_ids,
            'subscriber_teams_ids': subscriber_teams_ids,
            'description': description,
            'folder_id': folder_id,
            'template_id': template_id,
            'workspace_id': workspace_id,
            'fields': fields
        }

        query_string = build_graphql_query(
            'create_board',
            'mutation',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return Board.from_dict(data['data']['create_board'])

    async def duplicate(
        self,
        board_id: int | str,
        board_name: Optional[str] = None,
        duplicate_type: Literal['with_structure', 'with_pulses', 'with_pulses_and_updates'] = 'with_structure',
        folder_id: Optional[int | str] = None,
        keep_subscribers: bool = False,
        workspace_id: Optional[int | str] = None,
        fields: Union[str, Fields] = 'board { id }'
    ) -> Board:
        """
        Duplicate a board.

        Args:
            board_id: The ID of the board to duplicate.
            board_name: The duplicated board's name.
            duplicate_type: The duplication type.
            folder_id: The destination folder within the destination workspace.
            keep_subscribers: Duplicate the subscribers to the new board.
            workspace_id: The destination workspace.
            fields: Fields to return from the duplicated board. Can be a string of space-separated field names or a :meth:`Fields() <monday.Fields>` instance.

        Returns:
            Board dataclass instance containing info for the duplicated board.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            MutationLimitExceeded: When the mutation API rate limit is exceeded.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> board = await monday_client.boards.duplicate(
                ...     board_id=987654321,
                ...     fields='id name state'
                ... )
                >>> board.id
                "987654321"
                >>> board.name
                "Duplicate of Board 1"
                >>> board.state
                "active"
        """

        fields = Fields(fields) + 'board { id }'

        args = {
            'board_id': board_id,
            'board_name ': board_name,
            'duplicate_type ': f'duplicate_board_{duplicate_type}',
            'folder_id': folder_id,
            'keep_subscribers': keep_subscribers,
            'workspace_id': workspace_id,
            'fields': fields  # f'board {{ {fields} }}' if 'board' not in fields else fields
        }

        query_string = build_graphql_query(
            'duplicate_board',
            'mutation',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return Board.from_dict(data['data']['duplicate_board']['board'])

    async def update(
        self,
        board_id: int | str,
        board_attribute: Literal['communication', 'description', 'name'],
        new_value: str
    ) -> UpdateBoard:
        """
        Update a board.

        Args:
            board_id: The ID of the board to update.
            board_attribute: The board's attribute to update.
            new_value: The new attribute value.

        Returns:
            UpdateBoard dataclass instance containing updated board info.

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
                ...     new_value='New Board Name'
                ... )
                >>> result.success
                True
                >>> result.undo_data.undo_record_id
                "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        """

        args = {
            'board_id': board_id,
            'board_attribute': board_attribute,
            'new_value ': new_value
        }

        query_string = build_graphql_query(
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

        return UpdateBoard.from_dict(data)

    async def archive(
        self,
        board_id: int | str,
        fields: Union[str, Fields] = BoardFields.BASIC
    ) -> Board:
        """
        Archive a board.

        Args:
            board_id: The ID of the board to archive.
            fields: Fields to return from the archived board. Can be a string of space-separated field names or a :meth:`Fields() <monday.Fields>` instance.

        Returns:
            Board dataclass instance containing info for the archived board.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> board = await monday_client.boards.archive(
                ...     board_id=987654321,
                ...     fields='id name state'
                ... )
                >>> board.id
                "987654321"
                >>> board.name
                "Board 1"
                >>> board.state
                "archived"
        """

        fields = Fields(fields)

        args = {
            'board_id': board_id,
            'fields': fields
        }

        query_string = build_graphql_query(
            'archive_board',
            'mutation',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return Board.from_dict(data['data']['archive_board'])

    async def delete(
        self,
        board_id: int | str,
        fields: Union[str, Fields] = BoardFields.BASIC
    ) -> Board:
        """
        Delete a board.

        Args:
            board_id: The ID of the board to delete.
            fields: Fields to return from the deleted board. Can be a string of space-separated field names or a :meth:`Fields() <monday.Fields>` instance.

        Returns:
            Board dataclass instance containing info for the deleted board.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> board = await monday_client.boards.delete(
                ...     board_id=987654321,
                ...     fields='id name state'
                ... )
                >>> board.id
                "987654321"
                >>> board.name
                "Board 1"
                >>> board.state
                "deleted"
        """

        fields = Fields(fields)

        args = {
            'board_id': board_id,
            'fields': fields
        }

        query_string = build_graphql_query(
            'delete_board',
            'mutation',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return Board.from_dict(data['data']['delete_board'])
