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
Type definitions for monday.com API items page related structures.
"""

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from monday.types.item import Item


class ItemsPage(TypedDict):
    """Type definition for ItemsPage structure."""

    items: list['Item']
    """List of items"""

    cursor: str
    """cursor for retrieving the next page of items"""
