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
Monday.com API item type definitions and structures.

This module contains dataclasses that represent Monday.com item objects,
including items, item lists, and their relationships to boards and groups.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from monday.types.asset import Asset
    from monday.types.board import Board
    from monday.types.column import ColumnValue
    from monday.types.group import Group
    from monday.types.subitem import Subitem
    from monday.types.update import Update
    from monday.types.user import User


@dataclass
class ItemList:
    """
    Type definition for a list of items associated with a board.

    This structure is used by the Boards.get_items() method to return items
    grouped by their board ID.
    """

    board_id: str
    """The ID of the board that contains the items"""

    items: list[Item]
    """The list of items belonging to the board"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {
            'id': self.board_id,
            'items': [item.to_dict() if hasattr(item, 'to_dict') else item for item in self.items]
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ItemList:
        """Create from dictionary."""
        return cls(
            board_id=str(data.get('id', '')),
            items=[Item.from_dict(item) if isinstance(item, dict) else item for item in data.get('items', [])]
        )


@dataclass
class Item:
    """
    Represents a Monday.com item (row) with its data and relationships.

    This dataclass maps to the Monday.com API item object structure, containing
    fields like name, column values, updates, and associated board/group information.

    See also:
        https://developer.monday.com/api-reference/reference/items#fields
    """

    assets: list[Asset] | None = None
    """The item's assets/files"""

    board: Board | None = None
    """The board that contains the item"""

    column_values: list[ColumnValue] | None = None
    """The item's column values"""

    created_at: str = ''
    """The item's creation date. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    creator: User | None = None
    """The item's creator"""

    creator_id: str = ''
    """The unique identifier of the item's creator. Returns ``None`` if the item was created by default on the board."""

    group: Group | None = None
    """The item's group"""

    id: str = ''
    """The item's unique identifier"""

    name: str = ''
    """The item's name"""

    state: str = ''
    """The item's state"""

    subitems: list[Subitem] | None = None
    """The item's subitems"""

    subscribers: list[User] | None = None
    """The item's subscribers"""

    updated_at: str = ''
    """The date the item was last updated. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    updates: list[Update] | None = None
    """The item's updates"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        result = {}

        if self.assets:
            result['assets'] = [asset.to_dict() if hasattr(asset, 'to_dict') else asset for asset in self.assets]
        if self.board:
            result['board'] = self.board.to_dict()
        if self.column_values:
            result['column_values'] = [cv.to_dict() if hasattr(cv, 'to_dict') else cv for cv in self.column_values]
        if self.created_at:
            result['created_at'] = self.created_at
        if self.creator:
            result['creator'] = self.creator.to_dict()
        if self.creator_id:
            result['creator_id'] = self.creator_id
        if self.group:
            result['group'] = self.group.to_dict()
        if self.id:
            result['id'] = self.id
        if self.name:
            result['name'] = self.name
        if self.state:
            result['state'] = self.state
        if self.subitems:
            result['subitems'] = [subitem.to_dict() if hasattr(subitem, 'to_dict') else subitem for subitem in self.subitems]
        if self.subscribers:
            result['subscribers'] = [subscriber.to_dict() if hasattr(subscriber, 'to_dict') else subscriber for subscriber in self.subscribers]
        if self.updated_at:
            result['updated_at'] = self.updated_at
        if self.updates:
            result['updates'] = [update.to_dict() if hasattr(update, 'to_dict') else update for update in self.updates]

        return result

    @classmethod
    # pylint: disable=import-outside-toplevel
    def from_dict(cls, data: dict[str, Any]) -> Item:
        """Create from dictionary."""
        from monday.types.asset import Asset
        from monday.types.board import Board
        from monday.types.column import ColumnValue
        from monday.types.group import Group
        from monday.types.subitem import Subitem
        from monday.types.update import Update
        from monday.types.user import User

        return cls(
            assets=[Asset.from_dict(asset) if hasattr(Asset, 'from_dict') else asset for asset in data.get('assets', [])] if data.get('assets') else None,
            board=Board.from_dict(data['board']) if data.get('board') else None,
            column_values=[ColumnValue.from_dict(cv) if hasattr(ColumnValue, 'from_dict') else cv for cv in data.get('column_values', [])] if data.get('column_values') else None,
            created_at=str(data.get('created_at', '')),
            creator=User.from_dict(data['creator']) if data.get('creator') else None,
            creator_id=str(data.get('creator_id', '')),
            group=Group.from_dict(data['group']) if data.get('group') else None,
            id=str(data.get('id', '')),
            name=str(data.get('name', '')),
            state=str(data.get('state', '')),
            subitems=[Subitem.from_dict(subitem) if hasattr(Subitem, 'from_dict') else subitem for subitem in data.get('subitems', [])] if data.get('subitems') else None,
            subscribers=[User.from_dict(subscriber) if hasattr(User, 'from_dict') else subscriber for subscriber in data.get('subscribers', [])] if data.get('subscribers') else None,
            updated_at=str(data.get('updated_at', '')),
            updates=[Update.from_dict(update) if hasattr(Update, 'from_dict') else update for update in data.get('updates', [])] if data.get('updates') else None
        )
