"""Module for handling Monday.com board operations."""

import logging
from typing import (TYPE_CHECKING, Any, Dict, List, Literal, Optional, Tuple,
                    TypedDict, Union)

from pydantic import ValidationError

from ..exceptions import QueryFormatError
from .utils.board_config_schema import BoardConfig
from .utils.board_config_validator import ConfigValidatedAttribute
from .utils.create_board_schema import CreateBoardInput
from .utils.duplicate_board_schema import DuplicateBoardInput
from .utils.error_handlers import check_query_result
from .utils.pagination import paginated_item_request
from .utils.update_board_schema import UpdateBoardInput

if TYPE_CHECKING:
    from ..client import MondayClient

BoardData = TypedDict('BoardData', {
    'board_id': int,
    'workspace_ids': Optional[List[int]],
    'board_kind': str,
    'order_by': str,
    'limit': int,
    'page': int,
    'state': str
})


class Boards:
    """Handles operations related to Monday.com boards."""

    logger: logging.Logger = logging.getLogger(__name__)

    board_ids = ConfigValidatedAttribute('board_ids')
    board_kind = ConfigValidatedAttribute('board_kind')
    order_by = ConfigValidatedAttribute('order_by')
    limit = ConfigValidatedAttribute('limit')
    page = ConfigValidatedAttribute('page')
    state = ConfigValidatedAttribute('state')
    workspace_ids = ConfigValidatedAttribute('workspace_ids')

    def __init__(self, client: 'MondayClient', **kwargs):
        """
        Initialize a Boards instance with specified parameters.

        Args:
            client ('MondayClient'): The MondayClient instance to use for API requests.

            **kwargs: Additional keyword arguments:
                board_ids (Union[int, List[int]]): The ID or list of IDs of the boards to initialize.
                board_kind (Literal['private', 'public', 'share', 'all'], optional): The kind of boards to include. Defaults to 'all'.
                order_by (Literal['created_at', 'used_at'], optional): The order in which to return the boards. Defaults to 'created_at'.
                limit (int, optional): The number of boards to return per page. Must be greater than 0. Defaults to 25.
                page (int, optional): The page number to start from. Must be greater than 0. Defaults to 1.
                state (Literal['active', 'all', 'archived', 'deleted'], optional): The state of the boards to include. Defaults to 'active'.
                workspace_ids (Optional[List[Union[int, List[int]]]], optional): The ID or list of IDs of the workspaces to filter by. Defaults to None.

        Raises:
            ValueError: If any of the input parameters are invalid or out of the allowed range.
        """
        self.client: 'MondayClient' = client
        self._config = BoardConfig(**kwargs)

    def __call__(self, board_id=None, **kwargs):
        """Allow reconfiguration by calling the instance."""
        if board_id is not None:
            kwargs['board_ids'] = board_id
        self._config = BoardConfig(**{**self._config.model_dump(), **kwargs})
        return self

    def __repr__(self) -> str:
        """Return a string representation of the Boards object."""
        return f'Boards(board_ids={self._config.board_ids}, workspace_ids={self._config.workspace_ids})'

    def __str__(self) -> str:
        """Return a human-readable string representation of the Boards object."""
        board_str = f'Boards: {self._config.board_ids}' if self._config.board_ids else 'No boards'
        workspace_str = f'Workspaces: {self._config.workspace_ids}' if self._config.workspace_ids else 'No workspaces'
        return f'Monday.com: {board_str}, {workspace_str}'

    def __len__(self) -> int:
        """Return the number of board IDs."""
        return len(self._config.board_ids)

    def __bool__(self) -> bool:
        """Return True if there are any board IDs, False otherwise."""
        return bool(self._config.board_ids)

    def __iter__(self):
        """Allow iteration over the board IDs with associated workspace IDs."""
        for board_id in self._config.board_ids:
            yield BoardData(
                board_id=board_id,
                workspace_ids=self._config.workspace_ids,
                board_kind=self._config.board_kind,
                order_by=self._config.order_by,
                limit=self._config.limit,
                page=self._config.page,
                state=self._config.state
            )

    def __getitem__(self, index: int) -> Dict[str, Any]:
        """Allow indexing to access specific board IDs."""
        if self._config.board_ids:
            return {
                'board_id': self._config.board_ids[index],
                'workspace_ids': self._config.workspace_ids
            }
        raise IndexError('No board IDs available')

    def configure(self, **kwargs) -> 'Boards':
        """
        Update or extend the configuration of a Boards instance.

        Args:
            **kwargs: Keyword arguments to update the BoardConfig.

        Returns:
            Boards: The updated Boards instance.

        Raises:
            ValueError: If any of the input parameters are invalid or out of the allowed range.
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
        return self

    def edit_board_list(
        self,
        add: Optional[Union[int, List[int]]] = None,
        remove: Optional[Union[int, List[int]]] = None
    ) -> 'Boards':
        """
        Update the list of board IDs by adding and/or removing specified boards.

        Args:
            add (Optional[Union[int, List[int]]], optional): Board ID(s) to add. Defaults to None.
            remove (Optional[Union[int, List[int]]], optional): Board ID(s) to remove. Defaults to None.

        Returns:
            Boards: The updated Boards instance.

        Raises:
            ValueError: If any of the input parameters are invalid or out of the allowed range.
        """
        current_boards = set(self._config.board_ids)

        if add is not None:
            current_boards.update(add if isinstance(add, list) else [add])

        if remove is not None:
            current_boards.difference_update(remove if isinstance(remove, list) else [remove])

        self.board_ids = list(current_boards)

        return self

    def edit_workspace_list(
        self,
        add: Optional[Union[int, List[int]]] = None,
        remove: Optional[Union[int, List[int]]] = None
    ) -> 'Boards':
        """
        Update the list of workspace IDs by adding and/or removing specified workspace.

        Args:
            add (Optional[Union[int, List[int]]], optional): Workspace ID(s) to add. Defaults to None.
            remove (Optional[Union[int, List[int]]], optional): Workspace ID(s) to remove. Defaults to None.

        Returns:
            Boards: The updated Boards instance.

        Raises:
            ValueError: If any of the input parameters are invalid or out of the allowed range.
        """
        current_workspaces = set(self._config.workspace_ids or [])

        if add is not None:
            current_workspaces.update(add if isinstance(add, list) else [add])

        if remove is not None:
            current_workspaces.difference_update(remove if isinstance(remove, list) else [remove])

        self.workspace_ids = list(current_workspaces)

        return self

    async def items_page(
        self,
        fields: str = 'items { id name }',
        query_params: str = '',
        limit: int = 25,
        board_fields: str = '',
        paginate_items: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Query boards to return items filtered by specified criteria. This will always be nested within a boards query.

        Args:
            fields (str): Additional fields for items_page query. Default: 'items { id name }'.
            query_params (str): Additional query parameters.
            limit (int): Number of items per page. Default: 25.
            board_fields (str): Additional fields for boards query.
            paginate_items (bool): Whether to paginate items. Default: True.

        Returns:
            List[Dict[str, Any]]: List of queried board data.

        Raises:
            MondayAPIError: If API request fails.
            PaginationError: If item pagination fails.
        """
        query_string = self._build_query_string(self._config.page, board_fields, fields, query_params, limit)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        if paginate_items:
            query_result = await self._paginate_items(data['data']['boards'], query_string)
            data = check_query_result(query_result)

        return data

    async def query(
        self,
        fields: str = 'id name',
        paginate_items: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Query boards to return metadata about one or multiple boards.

        Args:
            fields (str): Fields to specify in the boards query. Default: 'id name'.
            paginate_items (bool): Whether to paginate items if items_page is in fields. Default: True.

        Returns:
            List[Dict[str, Any]]: List of queried board data.

        Raises:
            QueryFormatError: If 'items_page' is in fields but 'cursor' is not, when paginate_items is True.
            MondayAPIError: If API request fails.
            PaginationError: If item pagination fails.
        """
        query_string = self._build_query_string(self._config.page, fields)

        if paginate_items and 'items_page' in fields and 'cursor' not in fields:
            raise QueryFormatError(
                'Pagination requires a cursor in the items_page field. '
                'Use boards.items_page() or update your fields parameter to include cursor, '
                'e.g.: "id name items_page { cursor items { id } }"'
            )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        if 'items_page' in fields and paginate_items:
            query_result = await self._paginate_items(data['data']['boards'], query_string)
            data = check_query_result(query_result)

        return data

    async def create(self, name: str, **kwargs) -> 'Boards':
        """
        Create a new board on Monday.com.

        Args:
            name (str): The name of the new board.

            **kwargs: Additional keyword arguments for board creation:
                kind (str, optional): The kind of board to create.
                    Options: 'private', 'public', 'share'. Defaults to 'public'.
                owner_ids (List[int], optional): List of user IDs to set as board owners.
                subscriber_ids (List[int], optional): List of user IDs to set as board subscribers.
                subscriber_teams_ids (List[int], optional): List of team IDs to set as board subscribers.
                description (str, optional): Description of the board.
                folder_id (int, optional): ID of the folder to place the board in.
                template_id (int, optional): ID of the template to use for the board.
                workspace_id (int, optional): ID of the workspace to create the board in.

        Returns:
            Boards: Updated Boards instance including the new board.

        Raises:
            MondayAPIError: If API request fails or returns unexpected format.
            ValueError: If input parameters are invalid.
        """
        try:
            input_data = CreateBoardInput(name=name, **kwargs)
        except ValidationError as e:
            error_messages = [f"{''.join([m.strip() for m in error['msg'].split(',', 1)[1:]])}" for error in e.errors()]
            raise ValueError('\n'.join(error_messages)) from None

        query_string = self._build_create_query_string(input_data)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        new_board_id = int(data['data']['create_board']['id'])

        if self._config.board_ids is None:
            self._config.board_ids = [new_board_id]
        else:
            self._config.board_ids.append(new_board_id)

        return self

    async def duplicate(
        self,
        board_id: Optional[int] = None,
        return_original: bool = False,
        **kwargs
    ) -> Union['Boards', Tuple['Boards', 'Boards']]:
        """
        Duplicate a board on Monday.com.

        Args:
            board_id (Optional[int]): The ID of the board to duplicate. Can only be called on a single board ID. Defaults to boards.board_ids.
            return_original (bool): If True, returns both the original and new Boards instances. Defaults to False.

            **kwargs: Additional keyword arguments for board duplication:
                board_name (str, optional): The duplicated board's name. If omitted, it will be automatically generated.
                duplicate_type (str, optional): The duplication type.
                    Options: 'duplicate_board_with_pulses', 'duplicate_board_with_pulses_and_updates', 'duplicate_board_with_structure'. Defaults to 'duplicate_board_with_structure'
                folder_id (int, optional): The destination folder within the destination workspace. The folder_id is required if you are duplicating to another workspace, otherwise, it is optional. If omitted, it will default to the original board's folder.
                keep_subscribers (bool, optional): Duplicate the subscribers to the new board. Defaults to False.
                workspace_id (int, optional): The destination workspace. If omitted, it will default to the original board's workspace.

        Returns:
            Union['Boards', Tuple['Boards', 'Boards']]: New Boards instance or tuple of original and new instances.

        Raises:
            ValueError: If board_ids is empty and no board_id is provided.
            MondayAPIError: If API request fails or returns unexpected format.

        Note:
            Only one board can be duplicated at a time.
        """
        if board_id is None:
            if not self._config.board_ids:
                raise ValueError("No board ID available to duplicate. Provide a board_id or ensure board_ids is set.")
            elif len(self._config.board_ids) != 1:
                raise ValueError(f"duplicate() can only be called on 1 board ID. Current length of boards_ids = {len(self._config.board_ids)}")
            board_id = self._config.board_ids[0]

        try:
            input_data = DuplicateBoardInput(board_id=board_id, **kwargs)
        except ValidationError as e:
            error_messages = [f"{error['loc'][0]}: {error['msg']}" for error in e.errors()]
            raise ValueError('\n'.join(error_messages)) from None

        query_string = self._build_duplicate_query_string(input_data)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        new_board_id = int(data['data']['duplicate_board']['board']['id'])

        new_board = Boards(self.client, board_ids=[new_board_id])

        if return_original:
            return self, new_board
        else:
            return new_board

    async def update(
        self,
        board_attribute: Literal['communication', 'description', 'name'],
        new_value: str,
        board_id: Optional[int] = None
    ):
        """
        Update a board on Monday.com.

        Args:
            board_attribute (Literal['communication', 'description', 'name']): The board's attribute to update.
            new_value (str): The new attribute value.
            board_id (Optional[int]): The ID of the board to update. Can only be called on a single board ID. Defaults to boards.board_ids.

        Raises:
            ValueError: If board_ids is empty and no board_id is provided.
            MondayAPIError: If API request fails or returns unexpected format.

        Note:
            Only one board can be updated at a time.
        """
        if board_id is None:
            if not self._config.board_ids or len(self._config.board_ids) != 1:
                raise ValueError("Exactly one board ID is required for update. Provide a board_id or ensure board_ids contains exactly one ID.")
            board_id = self._config.board_ids[0]

        try:
            input_data = UpdateBoardInput(board_id=board_id, board_attribute=board_attribute, new_value=new_value)
        except ValidationError as e:
            error_messages = [f"{error['loc'][0]}: {error['msg']}" for error in e.errors()]
            raise ValueError('\n'.join(error_messages)) from None

        query_string = self._build_update_query_string(input_data)

        query_result = await self.client.post_request(query_string)

        check_query_result(query_result)

    async def _fetch_boards(self, query: str) -> List[Dict[str, Any]]:
        """
        Fetch boards from Monday.com API using pagination.

        Args:
            query (str): GraphQL query string to fetch boards.

        Returns:
            List[Dict[str, Any]]: List of board data dictionaries.

        Raises:
            MondayAPIError: If API request fails or returns unexpected format.
        """
        boards = []
        current_page = self._config.page
        query_string = query

        while True:
            query_result = await self.client.post_request(query_string)
            data = check_query_result(query_result)
            current_boards = data['data']['boards']
            if not current_boards:
                break

            boards.extend(current_boards)
            query_string = query_string.replace(f'page: {current_page}', f'page: {current_page + 1}')
            current_page += 1

        return boards

    async def _paginate_items(
        self,
        boards: List[Dict[str, Any]],
        query_string: str
    ) -> List[Dict[str, Any]]:
        """
        Paginate items for each board.

        Args:
            boards (List[Dict[str, Any]]): List of board data.
            query_string (str): GraphQL query string.

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
                query_result = await paginated_item_request(self.client, query_string, limit=self._config.limit, _cursor=board['items_page']['cursor'])
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
            'board_kind': data.kind,
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

    def _build_query_string(
        self,
        page: int,
        fields: str,
        item_fields: str = '',
        query_params: str = '',
        item_limit: int = 25
    ) -> str:
        """
        Build GraphQL query string for board queries.

        Args:
            page (int): Page number for pagination.
            fields (str): Fields to include in the query.
            item_fields (str): Fields for item queries.
            query_params (str): Additional query parameters.
            item_limit (int): Limit for item queries.

        Returns:
            str: Formatted GraphQL query string.
        """
        board_ids = ', '.join(map(str, self._config.board_ids))
        workspace_ids = ', '.join(map(str, self._config.workspace_ids)) if self._config.workspace_ids else None

        items_page = f"""
            items_page (
                limit: {item_limit}
                {f", query_params: {query_params}" if query_params else ""}
            ) {{
                cursor {item_fields}
            }}
        """ if item_fields else ''

        return f"""
            query {{
                boards (
                    ids: [{board_ids}],
                    limit: {self._config.limit},
                    order_by: {self._config.order_by},
                    page: {page},
                    state: {self._config.state}
                    {f", workspace_ids: [{workspace_ids}]" if workspace_ids else ""}
                    {f", board_kind: {self._config.board_kind}" if self._config.board_kind != 'all' else ""}
                ) {{
                    {fields}
                    {items_page}
                }}
            }}
        """
