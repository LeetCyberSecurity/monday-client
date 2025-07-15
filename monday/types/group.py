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
Monday.com API group type definitions and structures.

This module contains dataclasses that represent Monday.com group objects,
including groups, group lists, and their relationships to boards and items.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from monday.types.item import Item


@dataclass
class GroupList:
    """
    Type definition for a list of groups associated with a board.

    This structure is used by the Groups.query() method to return groups
    grouped by their board ID.
    """

    board_id: str
    """The ID of the board that contains the groups"""

    groups: list[Group]
    """The list of groups belonging to the board"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {
            'id': self.board_id,
            'groups': [
                group.to_dict() if hasattr(group, 'to_dict') else group
                for group in self.groups
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GroupList:
        """Create from dictionary."""
        return cls(
            board_id=str(data.get('id', '')),
            groups=[
                Group.from_dict(group) if isinstance(group, dict) else group
                for group in data.get('groups', [])
            ],
        )


@dataclass
class Group:
    """
    Represents a Monday.com group with its properties and items.

    This dataclass maps to the Monday.com API group object structure, containing
    fields like title, color, position, and associated items.

    See Also:
        https://developer.monday.com/api-reference/reference/groups#fields

    """

    archived: bool = False
    """Returns ``True`` if the group is archived"""

    color: str = ''
    """The group's color"""

    deleted: bool = False
    """Returns ``True`` if the group is deleted"""

    id: str = ''
    """The group's unique identifier"""

    items: list[Item] | None = None
    """The group's items"""

    position: str = ''
    """The group's position on the board"""

    title: str = ''
    """The group's title"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        result = {}

        if self.archived:
            result['archived'] = self.archived
        if self.color:
            result['color'] = self.color
        if self.deleted:
            result['deleted'] = self.deleted
        if self.id:
            result['id'] = self.id
        if self.items:
            result['items'] = [
                item.to_dict() if hasattr(item, 'to_dict') else item
                for item in self.items
            ]
        if self.position:
            result['position'] = self.position
        if self.title:
            result['title'] = self.title

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Group:
        """Create from dictionary."""
        from monday.types.item import Item  # noqa: PLC0415

        items = None
        if data.get('items'):
            items = [
                Item.from_dict(item) if isinstance(item, dict) else item
                for item in data.get('items', [])
            ]
        return cls(
            archived=data.get('archived', False),
            color=str(data.get('color', '')),
            deleted=data.get('deleted', False),
            id=str(data.get('id', '')),
            items=items,
            position=str(data.get('position', '')),
            title=str(data.get('title', '')),
        )
