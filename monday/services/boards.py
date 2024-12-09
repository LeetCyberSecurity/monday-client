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

from monday.exceptions import QueryFormatError
from monday.services.utils import (build_graphql_query,
                                   build_query_params_string,
                                   check_query_result,
                                   extract_items_page_value,
                                   paginated_item_request,
                                   update_data_in_place)
from monday.types import QueryParams

if TYPE_CHECKING:
    from monday import MondayClient


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
        self.client: 'MondayClient' = client

    async def query(
        self,
        board_ids: Optional[Union[int, list[int]]] = None,
        paginate_items: bool = True,
        board_kind: Literal['private', 'public', 'share', 'all'] = 'all',
        order_by: Literal['created', 'used'] = 'created',
        items_page_limit: int = 25,
        boards_limit: int = 25,
        page: int = 1,
        state: Literal['active', 'all', 'archived', 'deleted'] = 'active',
        workspace_ids: Optional[Union[int, list[int]]] = None,
        fields: str = 'id name',
    ) -> list[dict[str, Any]]:
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
            fields: Fields to return from the queried board.

        Returns:
            List of dictionaries containing queried board data.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> await monday_client.boards.query(
                ...     board_ids=987654321,
                ...     fields='id name state'
                ... )
                [
                    {
                        "id": "987654321",
                        "name": "Board 1",
                        "state": "active"
                    }
                ]
        """

        if paginate_items and 'items_page' in fields and 'cursor' not in fields:
            raise QueryFormatError(
                'Pagination requires a cursor in the items_page field. '
                'Use items.items_page() or update your fields parameter to include cursor, '
                'e.g.: "id name items_page { cursor items { id } }"'
            )

        board_ids = [board_ids] if not isinstance(board_ids, list) else board_ids

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

            if not data['data']['boards']:
                break

            boards_data.extend(data['data']['boards'])

            args['page'] += 1

        if 'items_page' in fields and paginate_items:
            query_result = await self._paginate_items(query_string, boards_data, limit=items_page_limit)
            boards_data = query_result

        return boards_data

    async def get_items(
        self,
        board_ids: Union[int, list[int]],
        query_params: Optional[QueryParams] = None,
        limit: int = 25,
        group_id: Optional[str] = None,
        paginate_items: bool = True,
        fields: str = 'id'
    ) -> list[dict[str, Any]]:
        """
        Retrieves a paginated list of items from specified boards.

        Args:
            board_ids: The ID or list of IDs of the boards from which to retrieve items.
            query_params: A set of parameters to filter, sort, and control the scope of the underlying boards query. Use this to customize the results based on specific criteria.
            limit: The maximum number of items to retrieve per page.
            group_id: Only retrieve items from the specified group ID.
            paginate_items: Whether to paginate items.
            fields: Fields to return from the items.

        Returns:
            A list of dictionaries containing the board IDs and their combined items retrieved.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> await monday_client.boards.get_items(
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
                [
                    {
                        "id": "987654321",
                        "items": [
                            {
                                "id": "123456789",
                                "column_values": [
                                    {
                                        "id": "status",
                                        "text": "Done"
                                    },
                                    {
                                        "id": "status_2",
                                        "text": "Working on it"
                                    }
                                ]
                            }
                        ]
                    }
                ]

        Note:
            The ``query_params`` argument allows complex filtering and sorting of items.

            Filter by status column:

            .. code-block:: python

                query_params={
                    'rules': [{
                        'column_id': 'status',
                        'compare_value': ['Done', 'In Progress'],
                        'operator': 'contains_terms'
                    }]
                }

            Filter by date range:

            .. code-block:: python

                query_params={
                    'rules': [{
                        'column_id': 'date_column',
                        'compare_value': ['2024-01-01', '2024-12-31'],
                        'operator': 'between'
                    }]
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

        query_params_str = build_query_params_string(query_params) if query_params else ''

        group_query = f'groups (ids: "{group_id}") {{' if group_id else ''
        group_query_end = '}' if group_id else ''
        fields = f"""
            id 
            {group_query} 
            items_page (
                limit: {limit} 
                {f', query_params: {query_params_str}' if query_params_str else ''}
            ) {{
                cursor
                items {{ {fields} }}
            }}
            {group_query_end}
        """

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
                    boards.append({'id': board['id'], 'items': board['groups'][0]['items_page']['items']})
                except IndexError:
                    boards.append({'id': board['id'], 'items': []})
            return boards

        return [{'id': b['id'], 'items': b['items_page']['items']} for b in data]

    async def get_items_by_column_values(
        self,
        board_id: int,
        columns: list[dict[Literal['column_id', 'column_values'], Union[str, list[str]]]],
        limit: int = 25,
        paginate_items: bool = True,
        fields: str = 'id'
    ) -> list[dict[str, Any]]:
        """
        Retrieves items from a board filtered by specific column values.

        Args:
            board_id: The ID of the board from which to retrieve items.
            columns: List of column filters to search by.
            limit: The maximum number of items to retrieve per page.
            paginate_items: Whether to paginate items.
            fields: Fields to return from the matching items.

        Returns:
            A list of dictionaries containing the combined items retrieved.

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
                >>> await monday_client.boards.get_items_by_column_values(
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
                [
                    {
                        "id": "123456789",
                        "column_values": [
                            {
                                "id": "status",
                                "text": "Done"
                            },
                            {
                                "id": "text__1",
                                "text": "This item is done"
                            }
                        ]
                    }
                ]
        """

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
            if 'error' in data:
                check_query_result(data)
        else:
            query_result = await self.client.post_request(query_string)
            data = check_query_result(query_result)
            data = {'items': data['data']['items_page_by_column_values']['items']}

        return data['items']

    async def create(
        self,
        name: str,
        board_kind: Optional[Literal['private', 'public', 'share']] = 'public',
        owner_ids: Optional[list[int]] = None,
        subscriber_ids: Optional[list[int]] = None,
        subscriber_teams_ids: Optional[list[int]] = None,
        description: Optional[str] = None,
        folder_id: Optional[int] = None,
        template_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
        fields: str = 'id'
    ) -> dict[str, Any]:
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
            fields: Fields to return from the created board.

        Returns:
            Dictionary containing info for the new board.

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
                >>> await monday_client.boards.create(
                ...     name='Board 1',
                ...     workspace_id=1234567,
                ...     description='Board 1 description',
                ...     fields='id name state description workspace_id'
                ... )
                {
                    "id": "987654321",
                    "name": "Board 1",
                    "state": "active",
                    "description": "Board 1 description",
                    "workspace_id": "1234567"
                }
        """

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

        return data['data']['create_board']

    async def duplicate(
        self,
        board_id: int,
        board_name: Optional[str] = None,
        duplicate_type: Literal['with_structure', 'with_pulses', 'with_pulses_and_updates'] = 'with_structure',
        folder_id: Optional[int] = None,
        keep_subscribers: bool = False,
        workspace_id: Optional[int] = None,
        fields: str = 'board { id }'
    ) -> dict[str, Any]:
        """
        Duplicate a board.

        Args:
            board_id: The ID of the board to duplicate.
            board_name: The duplicated board's name.
            duplicate_type: The duplication type.
            folder_id: The destination folder within the destination workspace.
            keep_subscribers: Duplicate the subscribers to the new board.
            workspace_id: The destination workspace.
            fields: Fields to return from the duplicated board.

        Returns:
            Dictionary containing info for the duplicated board.

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
                >>> await monday_client.boards.duplicate(
                ...     board_id=987654321,
                ...     fields='id name state'
                ... )
                {
                    "id": "987654321",
                    "name": "Duplicate of Board 1",
                    "state": "active"
                }
        """

        args = {
            'board_id': board_id,
            'board_name ': board_name,
            'duplicate_type ': f'duplicate_board_{duplicate_type}',
            'folder_id': folder_id,
            'keep_subscribers': keep_subscribers,
            'workspace_id': workspace_id,
            'fields': f'board {{ {fields} }}' if 'board' not in fields else fields
        }

        query_string = build_graphql_query(
            'duplicate_board',
            'mutation',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['duplicate_board']['board']

    async def update(
        self,
        board_id: int,
        board_attribute: Literal['communication', 'description', 'name'],
        new_value: str
    ) -> dict[str, Any]:
        """
        Update a board.

        Args:
            board_id: The ID of the board to update.
            board_attribute: The board's attribute to update.
            new_value: The new attribute value.

        Returns:
            Dictionary containing updated board info.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> await monday_client.boards.update(
                ...     board_id=987654321,
                ...     board_attribute='name',
                ...     new_value='New Board Name'
                ... )
                {
                    "success": true,
                    "undo_data": {
                        "undo_record_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                        "action_type": "modify_project",
                        "entity_type": "Board",
                        "entity_id": 987654321,
                        "count": 1
                    }
                }
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

        return data

    async def archive(
        self,
        board_id: int,
        fields: str = 'id'
    ) -> dict[str, Any]:
        """
        Archive a board.

        Args:
            board_id: The ID of the board to archive.
            fields: Fields to return from the archived board.

        Returns:
            Dictionary containing info for the archived board.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> await monday_client.boards.archive(
                ...     board_id=987654321,
                ...     fields='id name state'
                ... )
                {
                    "id": "987654321",
                    "name": "Board 1",
                    "state": "archived"
                }
        """

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

        return data['data']['archive_board']

    async def delete(
        self,
        board_id: int,
        fields: str = 'id'
    ) -> dict[str, Any]:
        """
        Delete a board.

        Args:
            board_id: The ID of the board to delete.
            fields: Fields to return from the deleted board.

        Returns:
            Dictionary containing info for the deleted board.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> await monday_client.boards.delete(
                ...     board_id=987654321,
                ...     fields='id name state'
                ... )
                {
                    "id": "987654321",
                    "name": "Board 1",
                    "state": "deleted"
                }
        """

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

        return data['data']['delete_board']

    async def _paginate_items(
        self,
        query_string: str,
        boards: list[dict[str, Any]],
        limit: int
    ) -> list[dict[str, Any]]:
        """
        Paginate items for each board.

        Args:
            query_string: GraphQL query string.
            boards: List of board data.
            limit: The number of items to return per page.

        Returns:
            Updated list of board data with paginated items.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.
            PaginationError: If pagination fails.

        """
        boards_list = boards
        for board in boards_list:
            items_page = extract_items_page_value(board)
            if not items_page:
                continue
            if items_page['cursor']:
                query_result = await paginated_item_request(self.client, query_string, limit=limit, cursor=items_page['cursor'])
                items_page['items'].extend(query_result['items'])
            del items_page['cursor']
            board = update_data_in_place(board, lambda ip, items_page=items_page: ip.update(items_page))
        return boards_list
