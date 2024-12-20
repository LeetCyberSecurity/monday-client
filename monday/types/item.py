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
Type definitions for monday.com API item related structures.
"""

from __future__ import annotations

from typing import Literal, Required, TypedDict

from monday.types.asset import Asset
from monday.types.board import Board
from monday.types.column import ColumnValue
from monday.types.group import Group
from monday.types.subitem import Subitem
from monday.types.update import Update
from monday.types.user import User


class Item(TypedDict, total=False):
    """
    Type definitions for monday.com API item structures.

    These types correspond to Monday.com's item fields as documented in their API reference:
    https://developer.monday.com/api-reference/reference/items#fields
    """

    assets: Asset
    """The item's assets/files"""

    board: Board
    """The board that contains the item"""

    column_values: list[ColumnValue]
    """The item's column values"""

    column_values_str: Required[str]
    """The item's string-formatted column values"""

    created_at: str
    """The item's creation date. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    creator: User
    """The item's creator"""

    creator_id: Required[str]
    """The unique identifier of the item's creator. Returns ``None`` if the item was created by default on the board."""

    email: Required[str]
    """The item's email"""

    group: Group
    """The item's group"""

    id: Required[str]
    """The item's unique identifier"""

    linked_items: Required[list[Item]]
    """The item's linked items"""

    name: Required[str]
    """The item's name"""

    parent_item: Item
    """A subitem's parent item. If used for a parent item, it will return ``None``"""

    relative_link: str
    """The item's relative path"""

    state: Literal['active', 'archived', 'deleted']
    """The item's state"""

    subitems: list[Subitem]
    """The item's subitems"""

    subscribers: Required[list[User]]
    """The item's subscribers"""

    updated_at: str
    """The date the item was last updated. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    updates: list[Update]
    """The item's updates"""

    url: Required[str]
    """The item's URL"""
