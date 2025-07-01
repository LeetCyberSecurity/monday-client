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
Monday.com API tag type definitions and structures.

This module contains dataclasses that represent Monday.com tag objects,
including tags with their colors and names for item categorization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Tag:
    """
    Represents a Monday.com tag with its color and name.

    This dataclass maps to the Monday.com API tag object structure, containing
    fields like name, color, and unique identifier.

    See also:
        https://developer.monday.com/api-reference/reference/tags#fields
    """

    color: str = ''
    """The tag's color"""

    id: str = ''
    """The tag's unique identifier"""

    name: str = ''
    """The tag's name"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        result = {}

        if self.color:
            result['color'] = self.color
        if self.id:
            result['id'] = self.id
        if self.name:
            result['name'] = self.name

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Tag:
        """Create from dictionary."""
        return cls(
            color=str(data.get('color', '')),
            id=str(data.get('id', '')),
            name=str(data.get('name', ''))
        )
