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
Monday.com API subitem type definitions and structures.

This module contains dataclasses that represent Monday.com subitem objects,
including subitems and their relationships to parent items and boards.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from monday.types.board import Board
    from monday.types.group import Group


@dataclass
class SubitemList:
    """
    Type definition for a list of subitems associated with a parent item.

    This structure is used by the Subitems.query() method to return subitems
    grouped by their parent item ID.
    """

    item_id: str
    """The ID of the parent item that contains the subitems"""

    subitems: list[Subitem]
    """The list of subitems belonging to the parent item"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {
            'id': self.item_id,
            'subitems': [subitem.to_dict() if hasattr(subitem, 'to_dict') else subitem for subitem in self.subitems]
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SubitemList:
        """Create from dictionary."""
        return cls(
            item_id=str(data.get('id', '')),
            subitems=[Subitem.from_dict(subitem) if isinstance(subitem, dict) else subitem for subitem in data.get('subitems', [])]
        )


@dataclass
class Subitem:
    """
    Represents a Monday.com subitem with its properties and relationships.

    This dataclass maps to the Monday.com API subitem object structure, containing
    fields like name, state, and associated board/group information.

    See also:
        https://developer.monday.com/api-reference/reference/subitems#fields
    """

    board: Board | None = None
    """The subitem's board"""

    created_at: str = ''
    """The subitem's creation date. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    creator_id: str = ''
    """The subitem's creator unique identifier"""

    group: Group | None = None
    """The subitem's group"""

    id: str = ''
    """The subitem's unique identifier"""

    item_id: str = ''
    """The subitem's parent item unique identifier"""

    name: str = ''
    """The subitem's name"""

    state: str = ''
    """The subitem's state"""

    updated_at: str = ''
    """The subitem's last update date. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        result = {}

        if self.board:
            result['board'] = self.board.to_dict()
        if self.created_at:
            result['created_at'] = self.created_at
        if self.creator_id:
            result['creator_id'] = self.creator_id
        if self.group:
            result['group'] = self.group.to_dict()
        if self.id:
            result['id'] = self.id
        if self.item_id:
            result['item_id'] = self.item_id
        if self.name:
            result['name'] = self.name
        if self.state:
            result['state'] = self.state
        if self.updated_at:
            result['updated_at'] = self.updated_at

        return result

    @classmethod
    # pylint: disable=import-outside-toplevel
    def from_dict(cls, data: dict[str, Any]) -> Subitem:
        """Create from dictionary."""
        from monday.types.board import Board
        from monday.types.group import Group

        return cls(
            board=Board.from_dict(data['board']) if data.get('board') else None,
            created_at=str(data.get('created_at', '')),
            creator_id=str(data.get('creator_id', '')),
            group=Group.from_dict(data['group']) if data.get('group') else None,
            id=str(data.get('id', '')),
            item_id=str(data.get('item_id', '')),
            name=str(data.get('name', '')),
            state=str(data.get('state', '')),
            updated_at=str(data.get('updated_at', ''))
        )
