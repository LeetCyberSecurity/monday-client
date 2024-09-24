"""Module for handling Monday.com item-related services."""

import json
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Union

from .schemas.items.archive_item_schema import ArchiveItemInput
from .schemas.items.clear_item_updates_schema import ClearItemUpdatesInput
from .schemas.items.create_item_schema import CreateItemInput
from .schemas.items.delete_item_schema import DeleteItemInput
from .schemas.items.duplicate_item_schema import DuplicateItemInput
from .schemas.items.items_page_by_column_values_schema import \
    ItemsPageByColumnValuesInput
from .schemas.items.items_page_schema import ItemsPageInput
from .schemas.items.move_item_to_board_schema import MoveToBoardInput
from .schemas.items.move_item_to_group_schema import MoveToGroupInput
from .schemas.items.query_item_schema import QueryItemInput
from .utils.error_handlers import check_query_result, check_schema
from .utils.pagination import paginated_item_request

if TYPE_CHECKING:
    from ..client import MondayClient


class Items:
    """Handles operations related to Monday.com items."""

    logger = logging.getLogger(__name__)

    def __init__(self, client: 'MondayClient'):
        """
        Initialize an Items instance with specified parameters.

        Args:
            client ('MondayClient'): The MondayClient instance to use for API requests.
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
    ):
        """
        Query items to return metadata about one or multiple items.

        Args:
            item_ids (Union[int, List[int]]): The ID or list of IDs of the specific items, subitems, or parent items to return. You can only return up to 100 IDs at a time.
            limit (int): The maximum number of items to retrieve per page. Defaults to 25.
            fields (str): The fields to include in the response. Defaults to 'name'.
            page (int): The page number at which to start. Default to 1.
            exclude_nonactive (bool): Excludes items that are inactive, deleted, or belong to deleted items. Defaults to False.
            newest_first (bool): Lists the most recently created items at the top. Defaults to False.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing the items retrieved.

        Raises:
            MondayAPIError: If API request fails or returns unexpected format.
            ValueError: If input parameters are invalid.

        Note:
            To return all items on a board, use Items.items_page() or Items.items_page_by_column_values() instead.
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
    ):
        """
        Query items to return metadata about one or multiple items.

        Args:
            board_id (int): The ID of the board where the item will be created.
            item_name (str): The name of the item.
            column_values (Dict[str, Any]): Column values for the item. Defaults to None.
            fields (str): Fields to query back from the created item. Defaults to 'id'.
            group_id (str): The ID of the group where the item will be created. Defaults to None.
            create_labels_if_missing (bool): Creates status/dropdown labels if they are missing. Defaults to False.
            position_relative_method (Literal['before_at', 'after_at']): You can use this argument in conjunction with relative_to to specify which item you want to create the new item above or below.
            relative_to (int): The ID of the item you want to create the new one in relation to.

        Returns:
            Dict[str, Any]: Dictionary containing info for the new item.

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

        return data

    async def duplicate(
        self,
        item_id: int,
        fields: str = 'id',
        board_id: Optional[int] = None,
        with_updates: bool = False
    ):
        """
        Duplicate an item.

        Args:
            item_id (int): The ID of the item to be copied.
            fields (str): Fields to query back from the duplicated item. Defaults to 'id'.
            board_id (int): The ID of the board where the item will be copied. Defaults to None.
            with_updates (bool): Duplicates the item with existing updates. Defaults to False.

        Returns:
            Dict[str, Any]: Dictionary containing info for the duplicated item.

        Raises:
            MondayAPIError: If API request fails or returns unexpected format.
            ValueError: If input parameters are invalid.
       """
        input_data = check_schema(
            DuplicateItemInput,
            item_id=item_id,
            fields=fields,
            board_id=board_id,
            with_updates=with_updates
        )

        query_string = self._build_duplicate_query_string(input_data)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data

    async def move_to_group(
        self,
        item_id: int,
        group_id: str,
        fields: str = 'id'
    ):
        """
        Move an item to a different group.

        Args:
            item_id (int): The ID of the item to be moved.
            group_id (str): The ID of the group to move the item to.
            fields (str): Fields to query back from the moved item. Defaults to 'id'.

        Returns:
            Dict[str, Any]: Dictionary containing info for the moved item.

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

        return data

    async def move_to_board(
        self,
        item_id: int,
        board_id: int,
        fields: str = 'id',
        group_id: Optional[str] = None,
        columns_mapping: Optional[List[Dict[str, str]]] = None,
        subitems_columns_mapping: Optional[List[Dict[str, str]]] = None
    ):
        """
        Move an item to a different board.

        Args:
            item_id (int): The ID of the item to be moved.
            board_id (int): The ID of the board to move the item to.
            fields (str): Fields to query back from the moved item. Defaults to 'id'.
            group_id (str): The ID of the group to move the item to.
            columns_mapping (List[Dict[str, str]]): Defines the column mapping between the original and target board.
            subitems_columns_mapping (List[Dict[str, str]]): Defines the subitems' column mapping between the original and target board.

        Returns:
            Dict[str, Any]: Dictionary containing info for the moved item.

        Raises:
            MondayAPIError: If API request fails or returns unexpected format.
            ValueError: If input parameters are invalid.
        """
        input_data = check_schema(
            MoveToBoardInput,
            item_id=item_id,
            board_id=board_id,
            fields=fields,
            group_id=group_id,
            columns_mapping=columns_mapping,
            subitems_columns_mapping=subitems_columns_mapping
        )

        query_string = self._build_move_to_board_query_string(input_data)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data

    async def archive(
        self,
        item_id: int,
        fields: str = 'id'
    ):
        """
        Archive an item.

        Args:
            item_id (int): The ID of the item to be archived.
            fields (str): Fields to query back from the archived item. Defaults to 'id'.

        Returns:
            Dict[str, Any]: Dictionary containing info for the archived item.

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

        return data

    async def delete(
        self,
        item_id: int,
        fields: str = 'id'
    ):
        """
        Delete an item.

        Args:
            item_id (int): The ID of the item to be deleted.
            fields (str): Fields to query back from the deleted item. Defaults to 'id'.

        Returns:
            Dict[str, Any]: Dictionary containing info for the deleted item.

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

        return data

    async def clear_updates(
        self,
        item_id: int,
        fields: str = 'id'
    ):
        """
        Clear an item's updates.

        Args:
            item_id (int): The ID of the item to be cleared.
            fields (str): Fields to query back from the cleared item. Defaults to 'id'.

        Returns:
            Dict[str, Any]: Dictionary containing info for the cleared item.

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

        return data

    async def items_page_by_column_values(
            self,
            board_id: int,
            columns: str,
            limit: int = 25,
            fields: str = 'items { id name }',
            paginate_items: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieves a paginated list of items from a specified board on Monday.com.

        Args:
            board_id (int): The ID of the board from which to retrieve items.
            columns (str): One or more columns and their values to search by.
            limit (int): The maximum number of items to retrieve per page. Defaults to 25.
            fields (str): The fields to include in the response. Defaults to 'items { id name }'.
            paginate_items (bool): Whether to paginate items. Defaults to True.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing the combined items retrieved.
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
            query_result = await paginated_item_request(self.client, query_string, limit=input_data.limit)
        else:
            query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data

    async def items_page(
            self,
            board_ids: Union[int, List[int]],
            query_params: Optional[str] = None,
            limit: int = 25,
            fields: str = 'items { id name }',
            paginate_items: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieves a paginated list of items from a specified board on Monday.com.
        This will always be nested within a boards query.

        Args:
            board_ids (int): The ID or list of IDs of the boards from which to retrieve items.
            query_params (str): A set of parameters to filter, sort, and control the scope of the underlying boards query.
                                Use this to customize the results based on specific criteria. Defaults to None.
            limit (int): The maximum number of items to retrieve per page. Must be > 0 and <= 500. Defaults to 25.
            fields (str): The fields to include in the response. Defaults to 'items { id name }'.
            paginate_items (bool): Whether to paginate items. Defaults to True.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing the combined items retrieved.
        """
        input_data = check_schema(
            ItemsPageInput,
            board_ids=board_ids,
            query_params=query_params,
            limit=limit,
            fields=fields,
            paginate_items=paginate_items
        )

        query_string = self._build_items_page_query_string(input_data)

        if input_data.paginate_items:
            data = await paginated_item_request(self.client, query_string, limit=input_data.limit)
        else:
            query_result = await self.client.post_request(query_string)
            data = check_query_result(query_result)

        return data

    def _build_items_query_string(self, data: QueryItemInput, page: int) -> str:
        args = {
            'ids': f"[{', '.join(map(str, data.item_ids))}]",
            'limit': data.limit,
            'newest_first': str(data.newest_first).lower(),
            'exclude_nonactive': str(data.exclude_nonactive).lower(),
            'page': page
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items() if v is not None)

        return f"""
        	query {{
                    items ({args_str}) {{
                    {data.fields}
                }}
            }}
        """

    def _build_create_query_string(self, data: CreateItemInput) -> str:
        args = {
            'board_id': data.board_id,
            'item_name': data.item_name,
            'column_values': json.dumps(json.dumps(data.column_values)),
            'group_id': data.group_id,
            'create_labels_if_missing': str(data.create_labels_if_missing).lower(),
            'position_relative_method': data.position_relative_method,
            'relative_to': data.relative_to
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items() if v is not None)

        return f"""
            mutation {{
                create_item ({args_str}) {{
                    {data.fields}
                }}
            }}
        """

    def _build_duplicate_query_string(self, data: DuplicateItemInput) -> str:
        args = {
            'item_id': data.item_id,
            'board_id': data.board_id,
            'with_updates': str(data.with_updates).lower()
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items() if v is not None)

        return f"""
            mutation {{
                duplicate_item ({args_str}) {{
                    {data.fields}
                }}
            }}
        """

    def _build_move_to_group_query_string(self, data: MoveToGroupInput) -> str:
        args = {
            'item_id': data.item_id,
            'group_id': f'"{data.group_id}"'
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items())

        return f"""
            mutation {{
                move_item_to_group ({args_str}) {{
                    {data.fields}
                }}
            }}
        """

    def _build_move_to_board_query_string(self, data: MoveToBoardInput) -> str:
        args = {
            'item_id': data.item_id,
            'board_id': data.board_id,
            'group_id': f'"{data.group_id}"' if data.group_id else None,
            'columns_mapping': json.dumps(data.columns_mapping),
            'subitems_columns_mapping': json.dumps(data.subitems_columns_mapping)
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items() if v is not None)

        return f"""
            mutation {{
                move_item_to_board ({args_str}) {{
                    {data.fields}
                }}
            }}
        """

    def _build_archive_query_string(self, data: ArchiveItemInput) -> str:
        """
        Build GraphQL query string for archiving an item.

        Args:
            data (ArchiveItemInput): Item archive input data.

        Returns:
            str: Formatted GraphQL query string.
        """
        args = {
            'item_id': data.item_id
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items())

        return f"""
            mutation {{
                archive_item ({args_str}) {{
                    {data.fields}
                }}
            }}
        """

    def _build_delete_query_string(self, data: DeleteItemInput) -> str:
        """
        Build GraphQL query string for deleting an item.

        Args:
            data (DeleteItemInput): Item delete input data.

        Returns:
            str: Formatted GraphQL query string.
        """
        args = {
            'item_id': data.item_id
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items())

        return f"""
            mutation {{
                delete_item ({args_str}) {{
                    {data.fields}
                }}
            }}
        """

    def _build_clear_updates_query_string(self, data: ClearItemUpdatesInput) -> str:
        """
        Build GraphQL query string for clearing an item's updates.

        Args:
            data (ClearItemUpdatesInput): Item clear updates input data.

        Returns:
            str: Formatted GraphQL query string.
        """
        args = {
            'item_id': data.item_id
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items())

        return f"""
            mutation {{
                clear_item_updates ({args_str}) {{
                    {data.fields}
                }}
            }}
        """

    def _build_by_column_values_query_string(self, data: ItemsPageByColumnValuesInput) -> str:
        args = {
            'board': data.board_id,
            'limit': data.limit,
            'columns': data.columns
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items() if v is not None)

        return f"""
        	query {{
                items_page_by_column_values ({args_str}) {{
                    cursor {data.fields}
                }}
            }}
        """

    def _build_items_page_query_string(self, data: ItemsPageInput) -> str:
        args = {
            'limit': data.limit,
            'query_params': data.query_params
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items() if v is not None)

        board_ids_string = ', '.join(map(str, data.board_ids))

        return f"""
            query {{
                boards (ids: [{board_ids_string}]) {{
                    items_page ({args_str}) {{
                        cursor {data.fields}
                    }}
                }}
            }}
        """
