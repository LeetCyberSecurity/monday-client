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
Type definitions for monday.com API tag related structures.
"""

from typing import Required, TypedDict


class Tag(TypedDict, total=False):
    """
    Type definitions for monday.com API tag structures.

    These types correspond to Monday.com's tag fields as documented in their API reference:
    https://developer.monday.com/api-reference/reference/tags-1#fields
    """

    color: Required[str]
    """The tag's color"""

    id: Required[str]
    """The tag's unique identifier"""

    name: Required[str]
    """The tag's name"""
