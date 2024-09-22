"""Module for handling Monday.com board operations."""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Union

from pydantic import ValidationError

from ..exceptions import QueryFormatError
from .schemas.create_board_schema import CreateBoardInput
from .schemas.duplicate_board_schema import DuplicateBoardInput
from .schemas.query_board_schema import QueryBoardInput
from .schemas.update_board_schema import UpdateBoardInput
from .utils.error_handlers import check_query_result
from .utils.pagination import paginated_item_request

if TYPE_CHECKING:
    from ..client import MondayClient


class Boards:
    """Handles operations related to Monday.com boards."""

    logger: logging.Logger = logging.getLogger(__name__)

    def __init__(self, client: 'MondayClient'):
        """
        Initialize a Boards instance with specified parameters.

        Args:
            client ('MondayClient'): The MondayClient instance to use for API requests.
        """
        self.client: 'MondayClient' = client

    async def query(
        self,
        board_ids: Union[int, List[int]],
        fields: str = 'id name',
        paginate_items: bool = True,
        board_kind: Literal['private', 'public', 'share', 'all'] = 'all',
        order_by: Literal['created_at', 'used_at'] = 'created_at',
        items_page_limit: int = 25,
        boards_limit: int = 25,
        page: int = 1,
        state: Literal['active', 'all', 'archived', 'deleted'] = 'active',
        workspace_ids: Optional[Union[int, List[int]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query boards to return metadata about one or multiple boards.

        Args:
            board_ids (Union[int, List[int]]): The ID or list of IDs of the boards to query.
            fields (str): Fields to specify in the boards query. Default: 'id name'.
            paginate_items (bool): Whether to paginate items if items_page is in fields. Default: True.
            board_kind (Literal['private', 'public', 'share', 'all']): The kind of boards to include. Default: 'all'.
            order_by (Literal['created_at', 'used_at']): The order in which to return the boards. Default: 'created_at'.
            items_page_limit (int): The number of items to return per page when items_page is part of your fields. Must be > 0 and <= 500. Default: 25.
            boards_limit (int): The number of boards to return per page. Must be > 0. Default: 25.
            page (int): The page number to start from. Default: 1.
            state (Literal['active', 'all', 'archived', 'deleted']): The state of the boards to include. Default: 'active'.
            workspace_ids (Optional[Union[int, List[int]]]): The ID or list of IDs of the workspaces to filter by. Default: None.

        Returns:
            List[Dict[str, Any]]: List of queried board data.

        Raises:
            QueryFormatError: If 'items_page' is in fields but 'cursor' is not, when paginate_items is True.
            MondayAPIError: If API request fails or returns unexpected format.
            ValueError: If input parameters are invalid.
            PaginationError: If item pagination fails during the request.
        """
        try:
            input_data = QueryBoardInput(
                board_ids=board_ids,
                board_kind=board_kind,
                order_by=order_by,
                items_page_limit=items_page_limit,
                boards_limit=boards_limit,
                page=page,
                state=state,
                workspace_ids=workspace_ids
            )
        except ValidationError as e:
            error_messages = [f"{''.join([m.strip() for m in error['msg'].split(',', 1)[1:]])}" for error in e.errors()]
            if not any(msg for msg in error_messages):
                error_messages = ["Invalid arguments"] + [f"Invalid argument {error['loc'][0]}" for error in e.errors()]
            raise ValueError('\n'.join(error_messages)) from None

        if paginate_items and 'items_page' in fields and 'cursor' not in fields:
            raise QueryFormatError(
                'Pagination requires a cursor in the items_page field. '
                'Use boards.items_page() or update your fields parameter to include cursor, '
                'e.g.: "id name items_page { cursor items { id } }"'
            )

        page = input_data.page
        boards_data = []
        while True:
            query_string = self._build_boards_query_string(fields, input_data, page)

            query_result = await self.client.post_request(query_string)

            data = check_query_result(query_result)

            if not data['data']['boards']:
                break

            boards_data.extend(data['data']['boards'])

            page += 1

        if 'items_page' in fields and paginate_items:
            query_result = await self._paginate_items(query_string, boards_data, input_data.items_page_limit)
            boards_data = check_query_result(query_result)

        return boards_data

    async def create(
        self,
        name: str,
        kind: Optional[Literal['private', 'public', 'share']] = 'public',
        owner_ids: Optional[List[int]] = None,
        subscriber_ids: Optional[List[int]] = None,
        subscriber_teams_ids: Optional[List[int]] = None,
        description: Optional[str] = None,
        folder_id: Optional[int] = None,
        template_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a new board on Monday.com.

        Args:
            name (str): The name of the new board.
            kind (Optional[Literal['private', 'public', 'share']]): The kind of board to create. Defaults to 'public'.
            owner_ids (Optional[List[int]]): List of user IDs to set as board owners.
            subscriber_ids (Optional[List[int]]): List of user IDs to set as board subscribers.
            subscriber_teams_ids (Optional[List[int]]): List of team IDs to set as board subscribers.
            description (Optional[str]): Description of the board.
            folder_id (Optional[int]): ID of the folder to place the board in.
            template_id (Optional[int]): ID of the template to use for the board.
            workspace_id (Optional[int]): ID of the workspace to create the board in.

        Returns:
            Dict[str, Any]: Dictionary containing info for the new board.

        Raises:
            MondayAPIError: If API request fails or returns unexpected format.
            ValueError: If input parameters are invalid.
        """
        try:
            input_data = CreateBoardInput(
                name=name,
                kind=kind,
                owner_ids=owner_ids,
                subscriber_ids=subscriber_ids,
                subscriber_teams_ids=subscriber_teams_ids,
                description=description,
                folder_id=folder_id,
                template_id=template_id,
                workspace_id=workspace_id,
            )
        except ValidationError as e:
            error_messages = [f"{''.join([m.strip() for m in error['msg'].split(',', 1)[1:]])}" for error in e.errors()]
            if not any(msg for msg in error_messages):
                error_messages = ["Invalid arguments"] + [f"Invalid argument {error['loc'][0]}" for error in e.errors()]
            raise ValueError('\n'.join(error_messages)) from None

        query_string = self._build_create_query_string(input_data)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data

    async def duplicate(
        self,
        board_id: int,
        board_name: Optional[str] = None,
        duplicate_type: Literal['duplicate_board_with_pulses', 'duplicate_board_with_pulses_and_updates', 'duplicate_board_with_structure'] = 'duplicate_board_with_structure',
        folder_id: Optional[int] = None,
        keep_subscribers: bool = False,
        workspace_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Duplicate a board on Monday.com.

        Args:
            board_id (int): The ID of the board to duplicate.
            board_name (Optional[str]): The duplicated board's name. If omitted, it will be automatically generated.
            duplicate_type (Literal['duplicate_board_with_pulses', 'duplicate_board_with_pulses_and_updates', 'duplicate_board_with_structure']):
                The duplication type. Defaults to 'duplicate_board_with_structure'.
            folder_id (Optional[int]): The destination folder within the destination workspace.
                The folder_id is required if you are duplicating to another workspace, otherwise, it is optional.
                If omitted, it will default to the original board's folder.
            keep_subscribers (bool): Duplicate the subscribers to the new board. Defaults to False.
            workspace_id (Optional[int]): The destination workspace. If omitted, it will default to the original board's workspace.

        Returns:
            Dict[str, Any]: Dictionary containing info for the new board.

        Raises:
            ValueError: If input parameters are invalid.
            MondayAPIError: If API request fails or returns unexpected format.
        """
        try:
            input_data = DuplicateBoardInput(
                board_id=board_id,
                board_name=board_name,
                duplicate_type=duplicate_type,
                folder_id=folder_id,
                keep_subscribers=keep_subscribers,
                workspace_id=workspace_id,
            )
        except ValidationError as e:
            error_messages = [f"{''.join([m.strip() for m in error['msg'].split(',', 1)[1:]])}" for error in e.errors()]
            if not any(msg for msg in error_messages):
                error_messages = ["Invalid arguments"] + [f"Invalid argument {error['loc'][0]}" for error in e.errors()]
            raise ValueError('\n'.join(error_messages)) from None

        query_string = self._build_duplicate_query_string(input_data)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data

    async def update(
        self,
        board_id: int,
        board_attribute: Literal['communication', 'description', 'name'],
        new_value: str
    ) -> Dict[str, Any]:
        """
        Update a board on Monday.com.

        Args:
            board_id (int): The ID of the board to update.
            board_attribute (Literal['communication', 'description', 'name']): The board's attribute to update.
            new_value (str): The new attribute value.

        Returns:
            Dict[str, Any]: Dictionary containing updated board info.

        Raises:
            ValueError: If input parameters are invalid.
            MondayAPIError: If API request fails or returns unexpected format.
        """
        try:
            input_data = UpdateBoardInput(board_id=board_id, board_attribute=board_attribute, new_value=new_value)
        except ValidationError as e:
            error_messages = [f"{''.join([m.strip() for m in error['msg'].split(',', 1)[1:]])}" for error in e.errors()]
            if not any(msg for msg in error_messages):
                error_messages = ["Invalid arguments"] + [f"Invalid argument {error['loc'][0]}" for error in e.errors()]
            raise ValueError('\n'.join(error_messages)) from None

        query_string = self._build_update_query_string(input_data)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data

    async def archive(
        self,
        board_id: int,
        fields: str = 'id'
    ) -> Dict[str, Any]:
        """
        Archive a board on Monday.com.

        Args:
            board_id (int): The ID of the board to archive.
            fields (str): Fields to query back from the archived board. Defaults to 'id'.

        Returns:
            Dict[str, Any]: Dictionary containing archived board info.

        Raises:
            ValueError: If board_id is not a positive integer.
            MondayAPIError: If API request fails or returns unexpected format.
        """
        if not isinstance(board_id, int) or board_id <= 0:
            raise ValueError('board_id must be a positive integer') from None

        query_string = f"""
            mutation {{
                archive_board (board_id: {board_id}) {{
                    {fields or 'id'}
                }}
            }}
        """

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data

    async def delete(
        self,
        board_id: int,
        fields: str = 'id'
    ) -> Dict[str, Any]:
        """
        Delete a board on Monday.com.

        Args:
            board_id (int): The ID of the board to delete.
            fields (str): Fields to query back from the deleted board. Defaults to 'id'.

        Returns:
            Dict[str, Any]: Dictionary containing deleted board info.

        Raises:
            ValueError: If board_id is not a positive integer.
            MondayAPIError: If API request fails or returns unexpected format.
        """
        if not isinstance(board_id, int) or board_id <= 0:
            raise ValueError('board_id must be a positive integer') from None

        query_string = f"""
            mutation {{
                delete_board (board_id: {board_id}) {{
                    {fields or 'id'}
                }}
            }}
        """

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data

    async def _paginate_items(
        self,
        query_string: List[Dict[str, Any]],
        boards: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Paginate items for each board.

        Args:
            query_string (str): GraphQL query string.
            boards (List[Dict[str, Any]]): List of board data.
            limit (int): The amount of items to return per page.

        Returns:
            List[Dict[str, Any]]: Updated list of board data with paginated items.

        Raises:
            MondayAPIError: If API request fails.
            PaginationError: If pagination fails for a board.
        """
        boards_list = boards
        for board in boards_list:
            all_board_items = board['items_page']['items']
            if board['items_page']['cursor']:
                query_result = await paginated_item_request(self.client, query_string, limit=limit, _cursor=board['items_page']['cursor'])
                data = check_query_result(query_result)
                all_board_items.extend(data['items'])
            board['items_page']['items'] = all_board_items
            del board['items_page']['cursor']
        return boards_list

    def _build_create_query_string(self, data: CreateBoardInput) -> str:
        """
        Build GraphQL query string for board creation.

        Args:
            data (CreateBoardInput): Board creation input data.

        Returns:
            str: Formatted GraphQL query string.
        """
        description = data.description.replace('"', '\\"') if data.description else None
        name = data.name.replace('"', '\\"')
        args = {
            'board_name': name,
            'board_kind': data.kind if data.kind != 'all' else None,
            'board_owner_ids': f"[{', '.join(map(str, data.owner_ids))}]" if data.owner_ids else None,
            'board_subscriber_ids': f"[{', '.join(map(str, data.subscriber_ids))}]" if data.subscriber_ids else None,
            'board_subscriber_teams_ids': f"[{', '.join(map(str, data.subscriber_teams_ids))}]" if data.subscriber_teams_ids else None,
            'description': description,
            'folder_id': data.folder_id,
            'template_id': data.template_id,
            'workspace_id': data.workspace_id
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items() if v is not None)

        return f"""
            mutation {{
                create_board ({args_str}) {{
                    id
                }}
            }}
        """

    def _build_duplicate_query_string(self, data: DuplicateBoardInput) -> str:
        """
        Build GraphQL query string for board duplication.

        Args:
            data (DuplicateBoardInput): Board duplication input data.

        Returns:
            str: Formatted GraphQL query string.
        """
        args = {
            'board_id': data.board_id,
            'board_name': data.board_name,
            'duplicate_type': data.duplicate_type,
            'folder_id': data.folder_id,
            'keep_subscribers': str(data.keep_subscribers).lower(),
            'workspace_id': data.workspace_id
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items() if v is not None)

        return f"""
            mutation {{
                duplicate_board ({args_str}) {{
                    board {{
                        id
                    }}
                }}
            }}
        """

    def _build_update_query_string(self, data: UpdateBoardInput) -> str:
        """
        Build GraphQL query string for board update.

        Args:
            data (UpdateBoardInput): Board update input data.

        Returns:
            str: Formatted GraphQL query string.
        """
        args = {
            'board_id': data.board_id,
            'board_attribute': data.board_attribute,
            'new_value': f'"{data.new_value}"'
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items() if v is not None)

        return f"""
            mutation {{
                update_board ({args_str})
            }}
        """

    def _build_boards_query_string(self, fields: str, data: QueryBoardInput, page: int) -> str:
        """
        Build GraphQL query string for board queries.

        Args:
            fields (str): Fields to include in the query.
            item_fields (str): Fields for item queries.

        Returns:
            str: Formatted GraphQL query string.
        """
        args = {
            'ids': f"[{', '.join(map(str, data.board_ids))}]",
            'board_kind': data.board_kind if data.board_kind != 'all' else None,
            'limit': data.boards_limit,
            'order_by': data.order_by,
            'page': page,
            'state': data.state,
            'workspace_ids': f"[{', '.join(map(str, data.workspace_ids))}]" if data.workspace_ids else None,
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items() if v is not None)

        return f"""
            query {{
                boards ({args_str}) {{
                    {fields}
                }}
            }}
        """
