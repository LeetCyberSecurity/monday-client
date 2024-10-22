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
Module for handling Monday.com board operations.

This module provides a comprehensive set of functions and classes for interacting
with Monday.com boards. It encapsulates various operations such as querying,
creating, updating, duplicating, archiving, and deleting boards.

Key features:
- Query boards with customizable fields and pagination
- Create new boards with specified attributes
- Duplicate existing boards with various options
- Update board properties (name, description, communication settings)
- Archive and delete boards
- Retrieve groups within a board

The Boards class in this module serves as the main interface for these operations,
providing methods that correspond to different Monday.com API endpoints related to boards.

This module is part of the monday-client package and relies on the MondayClient
for making API requests. It also utilizes various utility functions and schema
validators to ensure proper data handling and error checking.

Usage of this module requires proper authentication and initialization of the
MondayClient instance.
"""

import json
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Union

from ..exceptions import QueryFormatError
from .schemas.boards.archive_board_schema import ArchiveBoardInput
from .schemas.boards.create_board_schema import CreateBoardInput
from .schemas.boards.delete_board_schema import DeleteBoardInput
from .schemas.boards.duplicate_board_schema import DuplicateBoardInput
from .schemas.boards.query_board_schema import QueryBoardInput
from .schemas.boards.update_board_schema import UpdateBoardInput
from .utils.data_modifiers import update_items_page_in_place
from .utils.error_handlers import check_query_result, check_schema
from .utils.pagination import extract_items_page_value, paginated_item_request

if TYPE_CHECKING:
    from ..client import MondayClient


class Boards:
    """
    Handles operations related to Monday.com boards.

    This class provides a comprehensive set of methods for interacting with boards
    on Monday.com. It encapsulates functionality for creating, querying, modifying,
    and deleting boards, as well as managing their properties and relationships.

    Each method in this class corresponds to a specific Monday.com API endpoint,
    providing a pythonic interface for board-related operations.

    Note:
        This class requires an initialized MondayClient instance for making API requests.
    """

    logger: logging.Logger = logging.getLogger(__name__)

    def __init__(self, client: 'MondayClient'):
        """
        Initialize a Boards instance with specified parameters.

        Args:
            client: The MondayClient instance to use for API requests.
        """
        self.client: 'MondayClient' = client

    async def query(
        self,
        board_ids: Optional[Union[int, List[int]]] = None,
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
            board_ids: The ID or list of IDs of the boards to query.
            fields: Fields to specify in the boards query.
            paginate_items: Whether to paginate items if items_page is in fields.
            board_kind: The kind of boards to include.
            order_by: The order in which to return the boards.
            items_page_limit: The number of items to return per page when items_page is part of your fields.
            boards_limit: The number of boards to return per page.
            page: The page number to start from.
            state: The state of the boards to include.
            workspace_ids: The ID or list of IDs of the workspaces to filter by.

        Returns:
            List of dictionaries containing queried board data.

        Raises:
            QueryFormatError: If 'items_page' is in fields but 'cursor' is not, when paginate_items is True.
            MondayAPIError: If API request fails or returns unexpected format.
            ValueError: If input parameters are invalid.
            PaginationError: If item pagination fails during the request.
        """
        input_data = check_schema(
            QueryBoardInput,
            board_ids=board_ids,
            fields=fields,
            board_kind=board_kind,
            order_by=order_by,
            items_page_limit=items_page_limit,
            boards_limit=boards_limit,
            page=page,
            state=state,
            workspace_ids=workspace_ids
        )

        if paginate_items and 'items_page' in fields and 'cursor' not in fields:
            raise QueryFormatError(
                'Pagination requires a cursor in the items_page field. '
                'Use boards.items_page() or update your fields parameter to include cursor, '
                'e.g.: "id name items_page { cursor items { id } }"'
            )

        page = input_data.page
        boards_data = []
        while True:
            query_string = self._build_boards_query_string(input_data, page)

            query_result = await self.client.post_request(query_string)

            data = check_query_result(query_result)

            if not data['data']['boards']:
                break

            boards_data.extend(data['data']['boards'])

            page += 1

        if 'items_page' in fields and paginate_items:
            query_result = await self._paginate_items(query_string, boards_data, input_data.items_page_limit)
            boards_data = query_result

        return boards_data

    async def create(
        self,
        name: str,
        fields: str = 'id',
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
        Create a new board.

        Args:
            name: The name of the new board.
            fields: Fields to query back from the created board.
            kind: The kind of board to create.
            owner_ids: List of user IDs to set as board owners.
            subscriber_ids: List of user IDs to set as board subscribers.
            subscriber_teams_ids: List of team IDs to set as board subscribers.
            description: Description of the board.
            folder_id: ID of the folder to place the board in.
            template_id: ID of the template to use for the board.
            workspace_id: ID of the workspace to create the board in.

        Returns:
            Dictionary containing info for the new board.

        Raises:
            MondayAPIError: If API request fails or returns unexpected format.
            ValueError: If input parameters are invalid.
        """
        input_data = check_schema(
            CreateBoardInput,
            name=name,
            fields=fields,
            kind=kind,
            owner_ids=owner_ids,
            subscriber_ids=subscriber_ids,
            subscriber_teams_ids=subscriber_teams_ids,
            description=description,
            folder_id=folder_id,
            template_id=template_id,
            workspace_id=workspace_id,
        )

        query_string = self._build_create_query_string(input_data)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['create_board']

    async def duplicate(
        self,
        board_id: int,
        fields: str = 'board { id }',
        board_name: Optional[str] = None,
        duplicate_type: Literal['duplicate_board_with_pulses', 'duplicate_board_with_pulses_and_updates', 'duplicate_board_with_structure'] = 'duplicate_board_with_structure',
        folder_id: Optional[int] = None,
        keep_subscribers: bool = False,
        workspace_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Duplicate a board.

        Args:
            board_id: The ID of the board to duplicate.
            fields: Fields to query back from the duplicated board.
            board_name: The duplicated board's name.
            duplicate_type: The duplication type.
            folder_id: The destination folder within the destination workspace.
            keep_subscribers: Duplicate the subscribers to the new board.
            workspace_id: The destination workspace.

        Returns:
            Dictionary containing info for the new board.

        Raises:
            ValueError: If input parameters are invalid.
            MondayAPIError: If API request fails or returns unexpected format.
        """
        input_data = check_schema(
            DuplicateBoardInput,
            board_id=board_id,
            fields=fields,
            board_name=board_name,
            duplicate_type=duplicate_type,
            folder_id=folder_id,
            keep_subscribers=keep_subscribers,
            workspace_id=workspace_id,
        )

        query_string = self._build_duplicate_query_string(input_data)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['duplicate_board']

    async def update(
        self,
        board_id: int,
        board_attribute: Literal['communication', 'description', 'name'],
        new_value: str
    ) -> Dict[str, Any]:
        """
        Update a board.

        Args:
            board_id: The ID of the board to update.
            board_attribute: The board's attribute to update.
            new_value: The new attribute value.

        Returns:
            Dictionary containing updated board info.

        Raises:
            ValueError: If input parameters are invalid.
            MondayAPIError: If API request fails or returns unexpected format.
        """
        input_data = check_schema(
            UpdateBoardInput,
            board_id=board_id,
            board_attribute=board_attribute,
            new_value=new_value
        )

        query_string = self._build_update_query_string(input_data)

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
    ) -> Dict[str, Any]:
        """
        Archive a board.

        Args:
            board_id: The ID of the board to archive.
            fields: Fields to query back from the archived board.

        Returns:
            Dictionary containing archived board info.

        Raises:
            ValueError: If input parameters are invalid.
            MondayAPIError: If API request fails or returns unexpected format.
        """
        input_data = check_schema(
            ArchiveBoardInput,
            board_id=board_id,
            fields=fields
        )

        query_string = self._build_archive_query_string(input_data)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['archive_board']

    async def delete(
        self,
        board_id: int,
        fields: str = 'id'
    ) -> Dict[str, Any]:
        """
        Delete a board.

        Args:
            board_id: The ID of the board to delete.
            fields: Fields to query back from the deleted board.

        Returns:
            Dictionary containing deleted board info.

        Raises:
            ValueError: If input parameters are invalid.
            MondayAPIError: If API request fails or returns unexpected format.
        """
        input_data = check_schema(
            DeleteBoardInput,
            board_id=board_id,
            fields=fields
        )

        query_string = self._build_delete_query_string(input_data)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['delete_board']

    async def get_group_items_by_name(
        self,
        board_id: int,
        group_id: str,
        item_name: str,
        fields: str = 'id name',
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        Get all items from a group with names that match item_name

        Args:
            board_id: The ID of the board to query.
            group_id: A single group ID.
            item_name: The name of the item to match.
            fields: Additional fields to query from the matched items.
            **kwargs: Keyword arguments for the underlying :meth:`Boards.query() <monday.Boards.query>` call.

        Returns:
            List of dictionaries containing item info.

        Raises:
            ValueError: If input parameters are invalid.
            MondayAPIError: If API request fails or returns unexpected format.
        """

        if not isinstance(board_id, int):
            raise ValueError("board_id must be positive int")

        if not isinstance(group_id, str):
            raise ValueError("group_id must be str")

        input_data = check_schema(
            QueryBoardInput,
            board_ids=board_id,
            item_name=item_name,
            group_id=group_id,
            fields=fields,
            **kwargs
        )

        fields = f"""
            groups (ids: "{group_id}") {{
               items_page (
                   query_params: {{
                       rules: [
                           {{
                               column_id: "name",
                               compare_value: ["{item_name}"]
                           }}
                       ]
                   }}
               ) {{
                   cursor
                   items {{
                       {fields}
                   }}
               }}
            }}
        """
        input_data.fields = fields

        query_string = self._build_boards_query_string(input_data)

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return data['data']['boards'][0]['groups'][0]['items_page']['items']

    async def _paginate_items(
        self,
        query_string: str,
        boards: List[Dict[str, Any]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Paginate items for each board.

        Args:
            query_string: GraphQL query string.
            boards: List of board data.
            limit: The number of items to return per page.

        Returns:
            Updated list of board data with paginated items.

        Raises:
            MondayAPIError: If API request fails.
            PaginationError: If pagination fails for a board.
        """
        boards_list = boards
        for board in boards_list:
            items_page = extract_items_page_value(board)
            if items_page['cursor']:
                query_result = await paginated_item_request(self.client, query_string, limit=limit, _cursor=items_page['cursor'])
                items_page['items'].extend(query_result['items'])
            del items_page['cursor']
            board = update_items_page_in_place(board, lambda ip, items_page=items_page: ip.update(items_page))
        return boards_list

    def _build_boards_query_string(self, input_data: QueryBoardInput, page: Optional[int] = None) -> str:
        """
        Build GraphQL query string for board queries.

        Args:
            input_data: Board query input data.
            page: Page number for pagination.

        Returns:
            Formatted GraphQL query string for querying boards.
        """
        args = {
            'ids': f"[{', '.join(map(str, input_data.board_ids))}]" if input_data.board_ids else None,
            'board_kind': input_data.board_kind if input_data.board_kind != 'all' else None,
            'limit': input_data.boards_limit,
            'order_by': input_data.order_by,
            'page': page,
            'state': input_data.state,
            'workspace_ids': f"[{', '.join(map(str, input_data.workspace_ids))}]" if input_data.workspace_ids else None,
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items() if v is not None)

        return f"""
            query {{
                boards ({args_str}) {{
                    {input_data.fields}
                }}
            }}
        """

    def _build_create_query_string(self, input_data: CreateBoardInput) -> str:
        """
        Build GraphQL query string for board creation.

        Args:
            input_data: Board creation input data.

        Returns:
            Formatted GraphQL query string for creating a board.
        """
        description = input_data.description.replace('"', '\\"') if input_data.description else None
        name = input_data.name.replace('"', '\\"')
        args = {
            'board_name': f'"{name}"',
            'board_kind': input_data.kind if input_data.kind != 'all' else None,
            'board_owner_ids': f"[{', '.join(map(str, input_data.owner_ids))}]" if input_data.owner_ids else None,
            'board_subscriber_ids': f"[{', '.join(map(str, input_data.subscriber_ids))}]" if input_data.subscriber_ids else None,
            'board_subscriber_teams_ids': f"[{', '.join(map(str, input_data.subscriber_teams_ids))}]" if input_data.subscriber_teams_ids else None,
            'description': f'"{description}"' if description else None,
            'folder_id': input_data.folder_id,
            'template_id': input_data.template_id,
            'workspace_id': input_data.workspace_id
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items() if v is not None)

        return f"""
            mutation {{
                create_board ({args_str}) {{
                    {input_data.fields}
                }}
            }}
        """

    def _build_duplicate_query_string(self, input_data: DuplicateBoardInput) -> str:
        """
        Build GraphQL query string for board duplication.

        Args:
            input_data: Board duplication input data.

        Returns:
            Formatted GraphQL query string for duplicating a board.
        """
        board_name = input_data.board_name.replace('"', '\\"') if input_data.board_name else None
        args = {
            'board_id': input_data.board_id,
            'board_name': f'"{board_name}"' if board_name else None,
            'duplicate_type': input_data.duplicate_type,
            'folder_id': input_data.folder_id,
            'keep_subscribers': str(input_data.keep_subscribers).lower(),
            'workspace_id': input_data.workspace_id
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items() if v is not None)

        return f"""
            mutation {{
                duplicate_board ({args_str}) {{
                    {input_data.fields}
                }}
            }}
        """

    def _build_update_query_string(self, input_data: UpdateBoardInput) -> str:
        """
        Build GraphQL query string for board update.

        Args:
            input_data: Board update input data.

        Returns:
            Formatted GraphQL query string for updating a board.
        """
        args = {
            'board_id': input_data.board_id,
            'board_attribute': input_data.board_attribute,
            'new_value': f'"{input_data.new_value}"'
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items() if v is not None)

        return f"""
            mutation {{
                update_board ({args_str})
            }}
        """

    def _build_archive_query_string(self, input_data: ArchiveBoardInput) -> str:
        """
        Build GraphQL query string for archiving a board.

        Args:
            input_data: Board archive input data.

        Returns:
            Formatted GraphQL query string for archiving a board.
        """
        args = {
            'board_id': input_data.board_id
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items())

        return f"""
            mutation {{
                archive_board ({args_str}) {{
                    {input_data.fields}
                }}
            }}
        """

    def _build_delete_query_string(self, input_data: DeleteBoardInput) -> str:
        """
        Build GraphQL query string for deleting a board.

        Args:
            input_data: Board delete input data.

        Returns:
            Formatted GraphQL query string for deleting a board.
        """
        args = {
            'board_id': input_data.board_id
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items())

        return f"""
            mutation {{
                delete_board ({args_str}) {{
                    {input_data.fields}
                }}
            }}
        """
