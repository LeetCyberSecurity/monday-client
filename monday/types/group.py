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
Type definitions for monday.com API group related structures.
"""

from typing import Required, TypedDict

from monday.types.items_page import ItemsPage


class Group(TypedDict, total=False):
    """
    Type definitions for monday.com API group structures.

    These types correspond to Monday.com's group fields as documented in their API reference:
    https://developer.monday.com/api-reference/reference/groups#fields
    """

    archived: bool
    """Returns ``True`` if the group is archived"""

    color: Required[str]
    """The group's color"""

    deleted: bool
    """Returns ``True`` if the group is deleted"""

    id: Required[str]
    """The group's unique identifier"""

    items_page: Required[ItemsPage]
    """The group's items"""

    position: Required[str]
    """The group's position on the board"""

    title: Required[str]
    """The group's title"""
