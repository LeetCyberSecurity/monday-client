"""Module for handling Monday.com item-related services."""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Union

from .schemas.create_item_schema import CreateItemInput
from .schemas.items_page_by_column_values_schema import \
    ItemsPageByColumnValuesInput
from .schemas.items_page_schema import ItemsPageInput
from .schemas.query_item_schema import QueryItemInput
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
            group_id=group_id,
            create_labels_if_missing=create_labels_if_missing,
            position_relative_method=position_relative_method,
            relative_to=relative_to
        )

        query_string = self._build_create_query_string(input_data)

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
            query_result = await paginated_item_request(self, query_string, limit=input_data.limit)
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
            query_result = await paginated_item_request(self, query_string, limit=input_data.limit)
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
            'column_values': data.column_values,
            'group_id': data.group_id,
            'create_labels_if_missing': data.create_labels_if_missing,
            'position_relative_method': data.position_relative_method,
            'relative_to': data.relative_to
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items() if v is not None)

        return f"""
            mutation {{
                create_item ({args_str}) {{
                    id
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
                boards ([{board_ids_string}]) {{
                    items_page ({args_str}) {{
                        cursor {data.fields}
                    }}
                }}
            }}
        """
