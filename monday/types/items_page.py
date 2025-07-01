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
Monday.com API items page type definitions and structures.

This module contains dataclasses that represent Monday.com paginated item responses,
including items pages with cursors for navigation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from monday.types.item import Item


@dataclass
class ItemsPage:
    """
    Represents a paginated page of Monday.com items with cursor for navigation.

    This dataclass maps to the Monday.com API items page structure, containing
    a list of items and a cursor for retrieving the next page.

    See also:
        https://developer.monday.com/api-reference/reference/items#fields
    """

    items: list['Item'] | None = None
    """List of items"""

    cursor: str = ''
    """cursor for retrieving the next page of items"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        result = {}

        if self.items:
            result['items'] = [item.to_dict() if hasattr(item, 'to_dict') else item for item in self.items]
        if self.cursor:
            result['cursor'] = self.cursor

        return result

    @classmethod
    # pylint: disable=import-outside-toplevel
    def from_dict(cls, data: dict[str, Any]) -> ItemsPage:
        """Create from dictionary."""
        from monday.types.item import Item

        return cls(
            items=[Item.from_dict(item) if hasattr(Item, 'from_dict') else item for item in data.get('items', [])] if data.get('items') else None,
            cursor=str(data.get('cursor', ''))
        )
