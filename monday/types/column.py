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
Monday.com API column type definitions and structures.

This module contains dataclasses that represent Monday.com column objects,
including columns, column values, and column types.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

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


@dataclass
class Column:
    """
    Represents a Monday.com column with its properties and settings.

    This dataclass maps to the Monday.com API column object structure, containing
    fields like title, type, settings, and metadata.

    See also:
        https://developer.monday.com/api-reference/reference/columns#fields
    """

    archived: bool = False
    """Returns ``True`` if the column is archived"""

    description: str = ''
    """The column's description"""

    id: str = ''
    """The column's unique identifier"""

    settings_str: str = ''
    """The column's settings as a JSON string"""

    title: str = ''
    """The column's title"""

    type: str = ''
    """The column's type"""

    width: int = 0
    """The column's width"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        result = {}

        if self.archived:
            result['archived'] = self.archived
        if self.description:
            result['description'] = self.description
        if self.id:
            result['id'] = self.id
        if self.settings_str:
            result['settings_str'] = self.settings_str
        if self.title:
            result['title'] = self.title
        if self.type:
            result['type'] = self.type
        if self.width:
            result['width'] = self.width

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Column:
        """Create from dictionary."""
        return cls(
            archived=data.get('archived', False),
            description=str(data.get('description', '')),
            id=str(data.get('id', '')),
            settings_str=str(data.get('settings_str', '')),
            title=str(data.get('title', '')),
            type=str(data.get('type', '')),
            width=int(data.get('width', 0))
        )


@dataclass
class ColumnValue:
    """
    Represents a Monday.com column value with its data and metadata.

    This dataclass maps to the Monday.com API column value object structure, containing
    fields like text, value, type, and associated column metadata.

    See also:
        https://developer.monday.com/api-reference/reference/column-values#fields
    """

    additional_info: str = ''
    """The column value's additional info"""

    id: str = ''
    """The column value's unique identifier"""

    text: str = ''
    """The column value's text"""

    title: str = ''
    """The column value's title"""

    type: str = ''
    """The column value's type"""

    value: str = ''
    """The column value's value"""

    # Additional fields for complex column value structures
    column: Column | None = None
    """The column metadata associated with this value"""

    display_value: str = ''
    """Display value for fragment queries like ... on MirrorValue, ... on BoardRelationValue"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        result = {}

        if self.additional_info:
            result['additional_info'] = self.additional_info
        if self.id:
            result['id'] = self.id
        if self.text:
            result['text'] = self.text
        if self.title:
            result['title'] = self.title
        if self.type:
            result['type'] = self.type
        if self.value:
            result['value'] = self.value
        if self.column:
            result['column'] = self.column.to_dict()
        if self.display_value:
            result['display_value'] = self.display_value

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ColumnValue:
        """Create from dictionary."""
        # Handle column metadata if present
        column_data = data.get('column')
        column = Column.from_dict(column_data) if column_data else None

        return cls(
            additional_info=str(data.get('additional_info', '')),
            id=str(data.get('id', '')),
            text=str(data.get('text', '')),
            title=str(data.get('title', '')),
            type=str(data.get('type', '')),
            value=str(data.get('value', '')),
            column=column,
            display_value=str(data.get('display_value', ''))
        )

    def get_column_title(self) -> str:
        """Get the column title, either from column metadata or fallback to title field."""
        if self.column and self.column.title:
            return self.column.title
        return self.title

    def get_display_value(self) -> str:
        """Get the display value, with fallback to text."""
        if self.display_value:
            return self.display_value
        return self.text
