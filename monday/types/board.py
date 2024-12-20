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
Type definitions for monday.com API board related structures.
"""

from __future__ import annotations

from typing import Any, Literal, Required, TypedDict

from monday.types.column import Column
from monday.types.group import Group
from monday.types.items_page import ItemsPage
from monday.types.tag import Tag
from monday.types.team import Team
from monday.types.update import Update
from monday.types.user import User
from monday.types.workspace import Workspace


class Board(TypedDict, total=False):
    """
    Type definitions for monday.com API board structures.

    These types correspond to Monday.com's board fields as documented in their API reference:
    https://developer.monday.com/api-reference/reference/boards#fields
    """

    activity_logs: list[ActivityLog]
    """The activity log events for the queried board(s)"""

    board_folder_id: str
    """The unique identifier of the folder that contains the board(s). Returns ``None`` if the board is not in a folder."""

    board_kind: Literal['private', 'public', 'share']
    """The type of board"""

    columns: list[Column]
    """The board's visible columns."""

    communication: dict[str, Any]
    """The board's communication value"""

    creator: Required[User]
    """The board's creator"""

    description: str
    """The board's description"""

    groups: list[Group]
    """The board's visible groups"""

    id: Required[str]
    """The board's unique identifier"""

    item_terminology: str
    """The nickname for items on the board. Can be a predefined or custom value."""

    items_count: int
    """The number of items on the board"""

    items_page: dict[Literal['items_page'], ItemsPage]
    """The board's items"""

    name: Required[str]
    """The board's name"""

    owners: Required[list[User]]
    """The board's owners"""

    permissions: Required[Literal['assignee', 'collaborators', 'everyone', 'owners']]
    """The board's permissions"""

    state: Required[Literal['active', 'all', 'archived', 'deleted']]
    """The board's state"""

    subscribers: Required[list[User]]
    """The board's subscribers"""

    tags: list[Tag]
    """The specific tags on the board"""

    team_owners: Required[list[Team]]
    """The board's team owners"""

    team_subscribers: Required[list[Team]]
    """The board's team subscribers"""

    top_group: Required[Group]
    """The group at the top of the board"""

    type: Literal['board', 'custom_object', 'document', 'sub_items_board']
    """The board's object type"""

    updated_at: str
    """The last time the board was updated. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    updates: list[Update]
    """The board's updates"""

    url: Required[str]
    """The board's URL"""

    views: list[BoardView]
    """The board's views"""

    workspace: Workspace
    """The workspace that contains the board. Returns ``None`` for the Main workspace."""

    workspace_id: str
    """The unique identifier of the board's workspace. Returns ``None`` for the Main workspace."""


class ActivityLog(TypedDict, total=False):
    """
    Type definitions for monday.com API activity log structures.

    These types correspond to Monday.com's activity log view fields as documented in their API reference:
    https://developer.monday.com/api-reference/reference/activity-logs#fields
    """

    account_id: Required[str]
    """The unique identifier of the account that initiated the event"""

    data: Required[str]
    """The item's column values"""

    entity: Required[Literal['board', 'pulse']]
    """The entity of the event that was changed"""

    event: Required[str]
    """The action that took place"""

    id: Required[str]
    """The unique identifier of the activity log event"""

    user_id: Required[str]
    """The unique identifier of the user who initiated the event"""

    created_at: Required[str]
    """The time of the event in 17-digit unix time"""


class BoardView(TypedDict, total=False):
    """
    Type definitions for monday.com API board view structures.

    These types correspond to Monday.com's board view fields as documented in their API reference:
    https://developer.monday.com/api-reference/reference/board-views#fields
    """

    id: Required[str]
    """The view's unique identifier"""

    name: Required[str]
    """The view's name"""

    settings_str: Required[str]
    """The view's settings"""

    type: Required[str]
    """The view's type"""

    view_specific_data_str: Required[str]
    """Specific board view data (only supported for forms)"""


class UndoData(TypedDict):
    """Structure containing undo information for board operations.

    Example:
        .. code-block:: python

            undo_data = {
                "undo_record_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                "action_type": "modify_project",
                "entity_type": "Board",
                "entity_id": 987654321,
                "count": 1
            }
    """
    undo_record_id: str
    """Unique identifier for the undo record"""

    action_type: str
    """Type of action performed (e.g., 'modify_project')"""

    entity_type: str
    """Type of entity modified (e.g., 'Board')"""

    entity_id: int
    """ID of the entity that was modified"""

    count: int
    """Number of entities affected by the operation"""


class UpdateBoard(TypedDict):
    """Response structure for board update operations.

    Example:
        .. code-block:: python

            response = {
                "success": True,
                "undo_data": {
                    "undo_record_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                    "action_type": "modify_project",
                    "entity_type": "Board",
                    "entity_id": 987654321,
                    "count": 1
                }
            }
    """
    success: bool
    """Whether the update operation was successful"""

    undo_data: UndoData
    """Information needed to undo the update operation"""
