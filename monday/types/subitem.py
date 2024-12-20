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
Type definitions for monday.com API subitem related structures.
"""

from typing import TYPE_CHECKING, Literal, Required, TypedDict

from monday.types.asset import Asset
from monday.types.board import Board
from monday.types.column import ColumnValue
from monday.types.group import Group
from monday.types.update import Update
from monday.types.user import User

if TYPE_CHECKING:
    from monday.types.item import Item


class Subitem(TypedDict, total=False):
    """
    Type definitions for monday.com API subitem structures.

    These types correspond to Monday.com's subitem fields as documented in their API reference:
    https://developer.monday.com/api-reference/reference/subitems#fields
    """

    assets: Asset
    """The subitem's assets/files"""

    board: Board
    """The board that contains the subitem"""

    column_values: list[ColumnValue]
    """The subitem's column values"""

    created_at: str
    """The subitem's creation date. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    creator: User
    """The subitem's creator"""

    creator_id: Required[str]
    """The unique identifier of the subitem's creator. Returns ``None`` if the item was created by default on the board."""

    email: Required[str]
    """The subitem's email"""

    group: Group
    """The subitem's group"""

    id: Required[str]
    """The subitem's unique identifier"""

    name: Required[str]
    """The subitem's name"""

    parent_item: 'Item'
    """The subitem's parent :class:`Item <monday.types.Item>`"""

    relative_link: str
    """The subitem's relative path"""

    state: Literal['active', 'archived', 'deleted']
    """The subitem's state"""

    subscribers: Required[list[User]]
    """The subitem's subscribers"""

    updated_at: str
    """The date the subitem was last updated. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    updates: list[Update]
    """The subitem's updates"""
