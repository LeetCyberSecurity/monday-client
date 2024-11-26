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
Module for handling Monday.com group operations.

This module provides a comprehensive set of functions and classes for interacting
with Monday.com groups. It encapsulates various operations such as querying,
creating, updating, duplicating, archiving, and deleting groups.

Key features:
- Query groups with customizable fields and pagination

The Groups class in this module serves as the main interface for these operations,
providing methods that correspond to different Monday.com API endpoints related to groups.

This module is part of the monday-client package and relies on the MondayClient
for making API requests. It also utilizes various utility functions and schema
validators to ensure proper data handling and error checking.

Usage of this module requires proper authentication and initialization of the
MondayClient instance.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

if TYPE_CHECKING:
    from monday import MondayClient
    from monday.services import Boards, Items


class Groups:
    """
    Handles operations related to Monday.com groups within boards.

    This class provides methods for interacting with groups on Monday.com boards.
    It encapsulates functionality for querying and managing groups, always in the
    context of their parent boards.

    Note:
        This class requires initialized MondayClient and Boards instances for making API requests.
    """

    logger: logging.Logger = logging.getLogger(__name__)

    def __init__(
        self,
        client: 'MondayClient',
        boards: 'Boards',
        items: 'Items'
    ):
        """
        Initialize a Groups instance with specified parameters.

        Args:
            client: The MondayClient instance to use for API requests.
            boards: The Boards instance to use for board-related operations.
            items: The Items instance to use for item-related operations.
        """
        self.client: 'MondayClient' = client
        self.boards: 'Boards' = boards
        self.items: 'Items' = items

    async def query(
        self,
        board_ids: Union[int, List[int]],
        group_ids: Optional[Union[str, List[str]]] = None,
        group_name: Optional[Union[str, List[str]]] = None,
        fields: str = 'id'
    ) -> List[Dict[str, Any]]:
        """
        Query groups from boards. Optionally specify the group names and/or IDs to filter by.

        Args:
            board_ids: The ID or list of IDs of the boards to query.
            group_ids: The ID or list of IDs of the specific groups to return.
            group_name: A single group name or list of group names.
            fields: Additional fields to return from the groups.

        Returns:
            List of dictionaries containing group info.

        Raises:
            ValueError: If input parameters are invalid.
            MondayAPIError: If API request fails or returns unexpected format.
        """

        group_ids_list = [group_ids] if isinstance(group_ids, str) else group_ids
        group_ids_quoted = [f'"{i}"' for i in group_ids_list] if group_ids_list else None

        group_fields = f"""
            id groups {f"(ids: [{', '.join(group_ids_quoted)}])" if group_ids_quoted else ""} {{
                {fields}
            }}
        """

        boards_data = await self.boards.query(
            board_ids=board_ids,
            fields=group_fields
        )

        groups = []
        for board in boards_data:
            board_groups = board.get('groups', [])
            if group_name:
                board_groups = [group for group in board_groups if group['title'] in (group_name if isinstance(group_name, list) else [group_name])]
            groups.append({
                'id': board['id'],
                'groups': board_groups
            })

        return groups
