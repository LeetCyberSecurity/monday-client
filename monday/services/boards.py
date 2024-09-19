import logging
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Union

from ..exceptions import PaginationError, QueryFormatError
from .utils.pagination import paginated_item_request

if TYPE_CHECKING:
    from ..client import MondayClient

class Boards:
    logger = logging.getLogger(__name__)

    def __init__(self, client: 'MondayClient'):
        self.client = client

    def query(
        self, 
        board_ids: Union[int, List[int]],
        board_kind: Literal['private', 'public', 'share'] = 'public',
        limit: int = 25,
        order_by: Literal['created_at', 'used_at'] = 'created_at',
        page: int = 1,
        state: Literal['active', 'all', 'archived', 'deleted'] = 'active',
        workspace_ids: Optional[Union[int, List[int]]] = None, 
        fields: str = 'id name',
        paginate_items: bool = True
    ) -> Dict[str, Union[bool, List[Dict[str, Any]], Optional[str]]]:
        """
        Query boards from Monday.com.

        Args:
            board_ids (Union[int, List[int]]): Single board ID or list of board IDs to return.
            board_kind (str, optional): The type of board to return. Defaults to public.
            limit (int, optional): The number of boards to return per page. Defaults to 25.
            order_by (Literal['created_at', 'used_at'], optional): The order in which to retrieve boards. Defaults to 'created_at'.
            page (int, optional): The page number to return. Defaults to 1.
            state (Literal['active', 'all', 'archived', 'deleted'], optional): The state of board to return. Defaults to 'active'.
            workspace_ids (Optional[Union[int, List[int]]], optional): The specific workspace IDs that contain the boards to return. Defaults to None.
            fields (str, optional): Fields to specify what information the boards query will return. Defaults to 'id name'.
            paginate_items (bool, optional): Whether to paginate items if items_page is part of your fields. Defaults to True.

        Returns:
            Dict[str, Union[bool, List[Dict[str, Any]], Optional[str]]]: Query results containing board data.

        Raises:
            TypeError: If board_ids is not an int or list of ints.
            TypeError: If workspace_ids is not None and is not a list of ints.
        """
        if not (isinstance(board_ids, int) or (isinstance(board_ids, list) and all(isinstance(id, int) for id in board_ids))):
            raise TypeError('board_ids must be an int or list of ints')
        
        if workspace_ids is not None and not (isinstance(workspace_ids, int) or (isinstance(workspace_ids, list) and all(isinstance(id, int) for id in workspace_ids))):
            raise TypeError('workspace_ids must be an int or list of ints')
        
        board_ids = [board_ids] if isinstance(board_ids, int) else board_ids
        board_ids = ', '.join(map(str, board_ids))
        if workspace_ids:
            workspace_ids = [workspace_ids] if isinstance(workspace_ids, int) else workspace_ids
            workspace_ids = ', '.join(map(str, workspace_ids))
        query_string = f'query {{ boards (ids: [{board_ids}], limit: {limit}, order_by: {order_by}, page: {page}, state: {state}{", workspace_ids: [" + workspace_ids + "]" if workspace_ids else ""}) {{ {fields} }} }}'
        if paginate_items and 'items_page' in fields and 'cursor' not in fields:
            raise QueryFormatError(
                'Pagination requires a cursor in the items_page field. '
                'Update your fields parameter to include cursor, e.g.: '
                '"id name items_page { cursor items { id } }"'
            )
        boards_data = self.client._execute_post_request(query_string)
        if 'error' in boards_data:
            return boards_data
        boards = boards_data['data']['boards']
        for index, board in enumerate(boards):
            if 'items_page' in board:
                all_board_items = board['items_page']['items']
                if board['items_page']['cursor']:
                    try:
                        board_items = paginated_item_request(self.client, query_string, limit=limit, _cursor=board['items_page']['cursor'])
                        if 'error' in board_items:
                            return board_items
                    except PaginationError as e:
                        e.add_note(f'board id {board["id"]}')
                        raise
                    all_board_items.extend(board_items['items'])
                board['items_page']['items'] = all_board_items
                del board['items_page']['cursor']
                boards_data['data']['boards'][index] = board
        return boards_data
