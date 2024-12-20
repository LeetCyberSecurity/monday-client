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

from typing import Literal, Optional, Required, TypedDict

ColumnType = Literal[
    'auto_number',
    'board_relation',
    'button',
    'checkbox',
    'color_picker',
    'country',
    'creation_log',
    'date',
    'dependency',
    'doc',
    'subtasks',
    'dropdown',
    'email',
    'file',
    'formula',
    'hour',
    'item_assignees',
    'item_id',
    'last_updated',
    'link',
    'location',
    'long_text',
    'mirror',
    'name',
    'numbers',
    'people',
    'phone',
    'progress',
    'rating',
    'status',
    'tags',
    'team',
    'text',
    'timeline',
    'time_tracking',
    'vote',
    'week',
    'world_clock',
    'unsupported'
]
"""ColumnType accepts enum values to specify which column type to filter, read, or update in your query or mutation."""


class Column(TypedDict, total=False):
    """
    Type definitions for monday.com API column structures.

    These types correspond to Monday.com's column fields as documented in their API reference:
    https://developer.monday.com/api-reference/reference/columns#fields
    """

    archived: bool
    """Returns ``True`` if the column is archived"""

    description: str
    """The column's description"""

    id: Required[str]
    """The column's unique identifier"""

    settings_str: Required[str]
    """The column's settings"""

    title: Required[str]
    """The column's title"""

    type: Required[ColumnType]
    """The column's type"""

    width: int
    """The column's width"""


class ColumnValue(TypedDict, total=False):
    """
    Type definitions for monday.com API column value structures.

    These types correspond to Monday.com's column fields as documented in their API reference:
    https://developer.monday.com/api-reference/reference/column-values-v2#fields
    """

    column: Required[Column]
    """The column the value belongs to"""

    id: Required[str]
    """The column's unique identifier"""

    text: str
    """The text representation of the column's value. Not every column supports the text value."""

    type: ColumnType
    """The column's type"""

    value: dict[str, Optional[str]]
    """The column's raw value"""
