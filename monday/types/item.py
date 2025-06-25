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

from typing import Literal, Protocol, runtime_checkable

from monday.types.asset import Asset
from monday.types.board import Board
from monday.types.column import ColumnValue
from monday.types.group import Group
from monday.types.subitem import Subitem
from monday.types.update import Update
from monday.types.user import User


@runtime_checkable
class Item(Protocol):
    """
    Protocol for monday.com API item structures.

    These types correspond to Monday.com's item fields as documented in their API reference:
    https://developer.monday.com/api-reference/reference/items#fields
    """

    @property
    def assets(self) -> Asset | None:
        """The item's assets/files"""

    @property
    def board(self) -> Board | None:
        """The board that contains the item"""

    @property
    def column_values(self) -> list[ColumnValue] | None:
        """The item's column values"""

    @property
    def column_values_str(self) -> str:
        """The item's string-formatted column values"""

    @property
    def created_at(self) -> str | None:
        """The item's creation date. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    @property
    def creator(self) -> User | None:
        """The item's creator"""

    @property
    def creator_id(self) -> str:
        """The unique identifier of the item's creator. Returns ``None`` if the item was created by default on the board."""

    @property
    def email(self) -> str:
        """The item's email"""

    @property
    def group(self) -> Group | None:
        """The item's group"""

    @property
    def id(self) -> str:
        """The item's unique identifier"""

    @property
    def linked_items(self) -> list[Item]:
        """The item's linked items"""

    @property
    def name(self) -> str:
        """The item's name"""

    @property
    def parent_item(self) -> Item | None:
        """A subitem's parent item. If used for a parent item, it will return ``None``"""

    @property
    def relative_link(self) -> str | None:
        """The item's relative path"""

    @property
    def state(self) -> Literal['active', 'archived', 'deleted'] | None:
        """The item's state"""

    @property
    def subitems(self) -> list[Subitem] | None:
        """The item's subitems"""

    @property
    def subscribers(self) -> list[User]:
        """The item's subscribers"""

    @property
    def updated_at(self) -> str | None:
        """The date the item was last updated. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    @property
    def updates(self) -> list[Update] | None:
        """The item's updates"""

    @property
    def url(self) -> str:
        """The item's URL"""
