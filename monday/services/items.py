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
Monday.com boards. It includes functionality for querying, creating, duplicating,
moving, archiving, and deleting items, as well as clearing item updates and
retrieving paginated lists of items based on various criteria.

Key features:
- Query items by ID
- Create new items on boards
- Duplicate existing items
- Move items between groups and boards
- Archive and delete items
- Clear item updates
- Retrieve paginated lists of items, including filtering by column values

This module is part of the monday-client package and relies on the MondayClient
for making API requests. It also utilizes various utility functions and schema
validators to ensure proper data handling and error checking.

Usage of this module requires proper authentication and initialization of the
MondayClient instance.
"""

import json
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Union

from .schemas.items import *  # pylint: disable=wildcard-import
from .utils.error_handlers import check_query_result, check_schema
from .utils.pagination import paginated_item_request

if TYPE_CHECKING:
    from ..client import MondayClient


class Items:
    """
    Handles operations related to Monday.com items.

    This class provides a comprehensive set of methods for interacting with items
    on Monday.com boards. It encapsulates functionality for creating, querying,
    modifying, and deleting items, as well as managing their properties and relationships.

    Each method in this class corresponds to a specific Monday.com API endpoint,
    providing a pythonic interface for item-related operations.

    Note:
        This class requires an initialized MondayClient instance for making API requests.
    """

    logger = logging.getLogger(__name__)

    def __init__(self, client: 'MondayClient'):
        """
        Initialize an Items instance with specified parameters.

        Args:
            client: The MondayClient instance to use for API requests.
        """
        self.client: 'MondayClient' = client

    async def query(
        self,
        item_ids: Union[int, List[int]],
        limit: int = 25,
        fields: str = 'name',
        page: int = 1,
        exclude_nonactive: bool = False,
        newest_first: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Query items to return metadata about one or multiple items.

        Args:
            item_ids: The ID or list of IDs of the specific items, subitems, or parent items to return. You can only return up to 100 IDs at a time.
            limit: The maximum number of items to retrieve per page. Defaults to 25.
            fields: The fields to include in the response. Defaults to 'name'.
            page: The page number at which to start. Defaults to 1.
            exclude_nonactive: Excludes items that are inactive, deleted, or belong to deleted items. Defaults to False.
            newest_first: Lists the most recently created items at the top. Defaults to False.

        Returns:
            A list of dictionaries containing the items retrieved.

        Raises:
            MondayAPIError: If API request fails or returns unexpected format.
            ValueError: If input parameters are invalid.

        Note:
            To return all items on a board, use :meth:`Items.page() <monday.Items.page>` or :meth:`Items.page_by_column_values() <monday.Items.page_by_column_values>` instead.
        """
        input_data = check_schema(
            QueryItemInput,
            item_ids=item_ids,
            limit=limit,
            fields=fields,
            page=page,
            exclude_nonactive=exclude_nonactive,
            newest_first=newest_first
        )

        page = input_data.page
        items_data = []
        while True:
            query_string = self._build_items_query_string(input_data, page)

            query_result = await self.client.post_request(query_string)

            data = check_query_result(query_result)

            if not data['data']['items']:
                break

            items_data.extend(data['data']['items'])

            page += 1

        return items_data

    async def create(
        self,
        board_id: int,
        item_name: str,
        column_values: Optional[Dict[str, Any]] = None,
        fields: str = 'id',
        group_id: Optional[str] = None,
        create_labels_if_missing: bool = False,
        position_relative_method: Optional[Literal['before_at', 'after_at']] = None,
        relative_to: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new item on a board.

        Args:
            board_id: The ID of the board where the item will be created.
            item_name: The name of the item.
            column_values: Column values for the item. Defaults to None.
            fields: Fields to query back from the created item. Defaults to 'id'.
            group_id: The ID of the group where the item will be created. Defaults to None.
            create_labels_if_missing: Creates status/dropdown labels if they are missing. Defaults to False.
            position_relative_method: Specify which item you want to create the new item above or below.
            relative_to: The ID of the item you want to create the new one in relation to.

        Returns:
            Dictionary containing info for the new item.

        Raises:
            MondayAPIError: If API request fails or returns unexpected format.
            ValueError: If input parameters are invalid.
        """
        input_data = check_schema(
            CreateItemInput,
            board_id=board_id,
            item_name=item_name,
            column_values=column_values,
            fields=fields,
            group_id=group_id,
            create_labels_if_missing=create_labels_if_missing,
            position_relative_method=position_relative_method,
            relative_to=relative_to
        )

        query_string = self._build_create_query_string(input_data)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['create_item']

    async def duplicate(
        self,
        item_id: int,
        board_id: int,
        fields: str = 'id',
        with_updates: bool = False
    ) -> Dict[str, Any]:
        """
        Duplicate an item.

        Args:
            item_id: The ID of the item to be duplicated.
            board_id: The ID of the board where the item will be duplicated.
            fields: Fields to query back from the duplicated item. Defaults to 'id'.
            with_updates: Duplicates the item with existing updates. Defaults to False.

        Returns:
            Dictionary containing info for the duplicated item.

        Raises:
            MondayAPIError: If API request fails or returns unexpected format.
            ValueError: If input parameters are invalid.
        """
        input_data = check_schema(
            DuplicateItemInput,
            item_id=item_id,
            board_id=board_id,
            fields=fields,
            with_updates=with_updates
        )

        query_string = self._build_duplicate_query_string(input_data)

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
            fields: Fields to query back from the moved item. Defaults to 'id'.

        Returns:
            Dictionary containing info for the moved item.

        Raises:
            MondayAPIError: If API request fails or returns unexpected format.
            ValueError: If input parameters are invalid.
        """
        input_data = check_schema(
            MoveToGroupInput,
            item_id=item_id,
            group_id=group_id,
            fields=fields
        )

        query_string = self._build_move_to_group_query_string(input_data)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['move_item_to_group']

    async def move_to_board(
        self,
        item_id: int,
        board_id: int,
        group_id: str,
        fields: str = 'id',
        columns_mapping: Optional[List[Dict[str, str]]] = None,
        subitems_columns_mapping: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Move an item to a different board.

        Args:
            item_id: The ID of the item to be moved.
            board_id: The ID of the board to move the item to.
            group_id: The ID of the group to move the item to.
            fields: Fields to query back from the moved item. Defaults to 'id'.
            columns_mapping: Defines the column mapping between the original and target board.
            subitems_columns_mapping: Defines the subitems' column mapping between the original and target board.

        Returns:
            Dictionary containing info for the moved item.

        Raises:
            MondayAPIError: If API request fails or returns unexpected format.
            ValueError: If input parameters are invalid.
        """
        input_data = check_schema(
            MoveToBoardInput,
            item_id=item_id,
            board_id=board_id,
            group_id=group_id,
            fields=fields,
            columns_mapping=columns_mapping,
            subitems_columns_mapping=subitems_columns_mapping
        )

        query_string = self._build_move_to_board_query_string(input_data)

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
            fields: Fields to query back from the archived item. Defaults to 'id'.

        Returns:
            Dictionary containing info for the archived item.

        Raises:
            MondayAPIError: If API request fails or returns unexpected format.
            ValueError: If input parameters are invalid.
        """
        input_data = check_schema(
            ArchiveItemInput,
            item_id=item_id,
            fields=fields
        )

        query_string = self._build_archive_query_string(input_data)

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
            fields: Fields to query back from the deleted item. Defaults to 'id'.

        Returns:
            Dictionary containing info for the deleted item.

        Raises:
            MondayAPIError: If API request fails or returns unexpected format.
            ValueError: If input parameters are invalid.
        """
        input_data = check_schema(
            DeleteItemInput,
            item_id=item_id,
            fields=fields
        )

        query_string = self._build_delete_query_string(input_data)

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
            fields: Fields to query back from the cleared item. Defaults to 'id'.

        Returns:
            Dictionary containing info for the cleared item.

        Raises:
            MondayAPIError: If API request fails or returns unexpected format.
            ValueError: If input parameters are invalid.
        """
        input_data = check_schema(
            ClearItemUpdatesInput,
            item_id=item_id,
            fields=fields
        )

        query_string = self._build_clear_updates_query_string(input_data)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['clear_item_updates']

    async def page_by_column_values(
        self,
        board_id: int,
        columns: List[ColumnInput],
        limit: int = 25,
        fields: str = 'id name',
        paginate_items: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieves a paginated list of items from a specified board on Monday.com.

        Args:
            board_id: The ID of the board from which to retrieve items.
            columns: One or more columns and their values to search by.
            limit: The maximum number of items to retrieve per page. Defaults to 25.
            fields: The fields to include in the response. Defaults to 'id name'.
            paginate_items: Whether to paginate items. Defaults to True.

        Returns:
            A list of dictionaries containing the combined items retrieved.

        Raises:
            MondayAPIError: If API request fails or returns unexpected format.
            ValueError: If input parameters are invalid.
        """
        input_data = check_schema(
            ItemsPageByColumnValuesInput,
            board_id=board_id,
            columns=columns,
            limit=limit,
            fields=fields,
            paginate_items=paginate_items
        )

        query_string = self._build_by_column_values_query_string(input_data)

        if input_data.paginate_items:
            data = await paginated_item_request(self.client, query_string, limit=input_data.limit)
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
        fields: str = 'id name',
        group_id: Optional[str] = None,
        paginate_items: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieves a paginated list of items from specified boards.

        Args:
            board_ids: The ID or list of IDs of the boards from which to retrieve items.
            query_params: A set of parameters to filter, sort, and control the scope of the underlying boards query.
                          Use this to customize the results based on specific criteria. Defaults to None.
            limit: The maximum number of items to retrieve per page. Must be > 0 and <= 500. Defaults to 25.
            fields: The fields to include in the response. Defaults to 'id name'.
            group_id: Only retrieve items from the specified group ID. Default is None.
            paginate_items: Whether to paginate items. Defaults to True.

        Returns:
            A list of dictionaries containing the board IDs and their combined items retrieved.

        Raises:
            MondayAPIError: If API request fails or returns unexpected format.
            ValueError: If input parameters are invalid.
        """
        input_data = check_schema(
            ItemsPageInput,
            board_ids=board_ids,
            query_params=query_params,
            limit=limit,
            fields=fields,
            group_id=group_id,
            paginate_items=paginate_items
        )

        query_string = self._build_items_page_query_string(input_data)

        if input_data.paginate_items:
            data = await paginated_item_request(self.client, query_string, limit=input_data.limit)
            if 'error' in data:
                check_query_result(data)
            data = data['items']
        else:
            query_result = await self.client.post_request(query_string)
            data = check_query_result(query_result)
            data = [{'board_id': board['id'], 'items': board['items_page']['items']} for board in data['data']['boards']]

        return data

    async def get_column_values(
        self,
        item_id: int,
        fields: str = 'id text',
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        Retrieves a list of column values for a specific item.

        Args:
            item_id: The ID of the item.
            fields: Additional fields to query from the item column values
            **kwargs: Keyword arguments for the underlying :meth:`Items.query() <monday.Items.query>` call.

        Returns:
            A list of dictionaries containing the item column values.

        Raises:
            MondayAPIError: If API request fails or returns unexpected format.
            ValueError: If input parameters are invalid.
        """
        if not isinstance(item_id, int):
            raise ValueError("item_id must be positive int")

        input_data = check_schema(
            QueryItemInput,
            item_ids=item_id,
            fields=fields,
            **kwargs
        )

        input_data.fields = f'column_values {{ {fields} }}'

        query_string = self._build_items_query_string(input_data)

        data = await self.client.post_request(query_string)

        return data['data']['items'][0]['column_values']

    async def change_column_values(
        self,
        item_id: int,
        column_values: Dict[str, Any],
        create_labels_if_missing: bool = False,
        fields: str = 'id',
    ) -> List[Dict[str, Any]]:
        """
        Change an item's column values.

        Args:
            item_id: The ID of the item.
            column_values: The updated column values.
            fields: Additional fields to query.

        Returns:
            A list of dictionaries containing the item column values.

        Raises:
            MondayAPIError: If API request fails or returns unexpected format.
            ValueError: If input parameters are invalid.
        """
        input_data = check_schema(
            ChangeColumnValuesInput,
            item_id=item_id,
            column_values=column_values,
            create_labels_if_missing=create_labels_if_missing,
            fields=fields
        )

        board_id_query = await self.query(input_data.item_id, fields='board { id }')
        board_id = int(board_id_query[0]['board']['id'])

        query_string = self._build_change_column_values_query_string(input_data, board_id)

        data = await self.client.post_request(query_string)

        return data

    async def get_name(
        self,
        item_id: int,
        **kwargs: Any
    ) -> str:
        """
        Get an item name from an item ID.

        Args:
            item_id: The ID of the item.
            fields: Additional fields to query from the item column values
            **kwargs: Keyword arguments for the underlying :meth:`Items.query() <monday.Items.query>` call.

        Returns:
            The item name.

        Raises:
            MondayAPIError: If API request fails or returns unexpected format.
            ValueError: If input parameters are invalid.
        """
        if not isinstance(item_id, int):
            raise ValueError("item_id must be positive int")

        input_data = check_schema(
            QueryItemInput,
            item_ids=item_id,
            **kwargs
        )

        input_data.fields = 'name'

        query_string = self._build_items_query_string(input_data)

        data = await self.client.post_request(query_string)

        return data['data']['items'][0]['name']

    def _build_items_query_string(self, input_data: QueryItemInput, page: Optional[int] = None) -> str:
        """
        Build GraphQL query string for querying items.

        Args:
            input_data: Query item input data.
            page: Page number for pagination.

        Returns:
            Formatted GraphQL query string for querying items.
        """
        args = {
            'ids': f"[{', '.join(map(str, input_data.item_ids))}]",
            'limit': input_data.limit,
            'newest_first': str(input_data.newest_first).lower(),
            'exclude_nonactive': str(input_data.exclude_nonactive).lower(),
            'page': page
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items() if v is not None)

        return f"""
        	query {{
                    items ({args_str}) {{
                    {input_data.fields}
                }}
            }}
        """

    def _build_create_query_string(self, input_data: CreateItemInput) -> str:
        """
        Build GraphQL query string for creating an item.

        Args:
            input_data: Create item input data.

        Returns:
            Formatted GraphQL query string for creating an item.
        """
        column_values = input_data.column_values or {}
        args = {
            'board_id': input_data.board_id,
            'item_name': f'"{input_data.item_name}"',
            'column_values': json.dumps(json.dumps(column_values)),
            'group_id': f'"{input_data.group_id}"' if input_data.group_id else None,
            'create_labels_if_missing': str(input_data.create_labels_if_missing).lower(),
            'position_relative_method': input_data.position_relative_method,
            'relative_to': input_data.relative_to
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items() if v is not None)

        return f"""
            mutation {{
                create_item ({args_str}) {{
                    {input_data.fields}
                }}
            }}
        """

    def _build_duplicate_query_string(self, input_data: DuplicateItemInput) -> str:
        """
        Build GraphQL query string for duplicating an item.

        Args:
            input_data: Duplicate item input data.

        Returns:
            Formatted GraphQL query string for duplicating an item.
        """
        args = {
            'item_id': input_data.item_id,
            'board_id': input_data.board_id,
            'with_updates': str(input_data.with_updates).lower()
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items() if v is not None)

        return f"""
            mutation {{
                duplicate_item ({args_str}) {{
                    {input_data.fields}
                }}
            }}
        """

    def _build_move_to_group_query_string(self, input_data: MoveToGroupInput) -> str:
        """
        Build GraphQL query string for moving an item to a group.

        Args:
            input_data: Move to group input data.

        Returns:
            Formatted GraphQL query string for moving an item to a group.
        """
        args = {
            'item_id': input_data.item_id,
            'group_id': f'"{input_data.group_id}"'
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items())

        return f"""
            mutation {{
                move_item_to_group ({args_str}) {{
                    {input_data.fields}
                }}
            }}
        """

    def _build_move_to_board_query_string(self, input_data: MoveToBoardInput) -> str:
        """
        Build GraphQL query string for moving an item to a board.

        Args:
            input_data: Move to board input data.

        Returns:
            Formatted GraphQL query string for moving an item to a board.
        """
        args = {
            'item_id': input_data.item_id,
            'board_id': input_data.board_id,
            'group_id': f'"{input_data.group_id}"',
            'columns_mapping': json.dumps(input_data.columns_mapping),
            'subitems_columns_mapping': json.dumps(input_data.subitems_columns_mapping)
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items() if v is not None)

        return f"""
            mutation {{
                move_item_to_board ({args_str}) {{
                    {input_data.fields}
                }}
            }}
        """

    def _build_archive_query_string(self, input_data: ArchiveItemInput) -> str:
        """
        Build GraphQL query string for archiving an item.

        Args:
            input_data: Item archive input data.

        Returns:
            Formatted GraphQL query string for archiving an item.
        """
        args = {
            'item_id': input_data.item_id
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items())

        return f"""
            mutation {{
                archive_item ({args_str}) {{
                    {input_data.fields}
                }}
            }}
        """

    def _build_delete_query_string(self, input_data: DeleteItemInput) -> str:
        """
        Build GraphQL query string for deleting an item.

        Args:
            input_data: Item delete input data.

        Returns:
            Formatted GraphQL query string for deleting an item.
        """
        args = {
            'item_id': input_data.item_id
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items())

        return f"""
            mutation {{
                delete_item ({args_str}) {{
                    {input_data.fields}
                }}
            }}
        """

    def _build_clear_updates_query_string(self, input_data: ClearItemUpdatesInput) -> str:
        """
        Build GraphQL query string for clearing an item's updates.

        Args:
            input_data: Item clear updates input data.

        Returns:
            Formatted GraphQL query string for clearing an item's updates.
        """
        args = {
            'item_id': input_data.item_id
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items())

        return f"""
            mutation {{
                clear_item_updates ({args_str}) {{
                    {input_data.fields}
                }}
            }}
        """

    def _build_by_column_values_query_string(self, input_data: ItemsPageByColumnValuesInput) -> str:
        """
        Build GraphQL query string for querying items by column values.

        Args:
            input_data: Items page by column values input data.

        Returns:
            Formatted GraphQL query string for querying items by column values.
        """
        args = {
            'board_id': input_data.board_id,
            'limit': input_data.limit
        }

        columns_list = []
        for column in input_data.columns:
            column_id_str = f'"{column.column_id}"'
            column_values_str = '[' + ', '.join(f'"{v}"' for v in column.column_values) + ']'
            columns_list.append(f'{{column_id: {column_id_str}, column_values: {column_values_str}}}')

        columns_str = '[' + ', '.join(columns_list) + ']'
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items())
        args_str += f', columns: {columns_str}'

        return f"""
        	query {{
                items_page_by_column_values ({args_str}) {{
                    cursor
                    items {{ {input_data.fields} }}
                }}
            }}
        """

    def _build_items_page_query_string(self, input_data: ItemsPageInput) -> str:
        """
        Build GraphQL query string for querying a page of items.

        Args:
            input_data: Items page input data.

        Returns:
            Formatted GraphQL query string for querying a page of items.
        """
        args = {
            'limit': input_data.limit,
            'query_params': input_data.query_params
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items() if v is not None)

        board_ids_string = ', '.join(map(str, input_data.board_ids))

        group_query = f'groups (ids: "{input_data.group_id}") {{' if input_data.group_id else ''
        group_query_end = '}' if input_data.group_id else ''

        return f"""
            query {{
                boards (ids: [{board_ids_string}]) {{
                    id
                    {group_query}
                    items_page ({args_str}) {{
                        cursor
                        items {{ {input_data.fields} }}
                    }}
                    {group_query_end}
                }}
            }}
        """

    def _build_change_column_values_query_string(
        self,
        input_data: ChangeColumnValuesInput,
        board_id: int
    ) -> str:
        """
        Build GraphQL query string for updating column values.

        Args:
            input_data: Items page input data.

        Returns:
            Formatted GraphQL query string for updating column values.
        """
        args = {
            'item_id': input_data.item_id,
            'board_id': board_id,
            'column_values': json.dumps(json.dumps(input_data.column_values)),
            'create_labels_if_missing': str(input_data.create_labels_if_missing).lower()
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items())

        return f"""
            mutation {{
                change_multiple_column_values ({args_str}) {{
                    {input_data.fields}
                }}
            }}
        """
