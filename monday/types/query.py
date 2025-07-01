# This file is part of monday.com API query related structures.
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
Type definitions for monday.com API query related structures.

These types help construct queries for the Monday.com API, including filters,
ordering, and complex query rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Union


@dataclass
class ColumnFilter:
    """
    Structure for filtering items by column values.

    Example:
        .. code-block:: python

            column_filter = ColumnFilter(
                column_id='status',
                column_values=['Done', 'In Progress']
            )

            # Or with a single value
            column_filter = ColumnFilter(
                column_id='text',
                column_values='Search term'
            )
    """

    column_id: str
    """The ID of the column to filter by"""

    column_values: Union[str, list[str]]
    """The value(s) to filter for. Can be a single string or list of strings"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {
            'column_id': self.column_id,
            'column_values': self.column_values
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ColumnFilter:
        """Create from dictionary."""
        return cls(
            column_id=str(data['column_id']),
            column_values=data['column_values']
        )


@dataclass
class OrderBy:
    """Structure for ordering items in queries."""

    column_id: str
    """The ID of the column to order by"""

    direction: Literal['asc', 'desc'] = 'asc'
    """The direction to order items. Defaults to 'asc' if not specified"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {
            'column_id': self.column_id,
            'direction': self.direction
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OrderBy:
        """Create from dictionary."""
        return cls(
            column_id=str(data['column_id']),
            direction=data.get('direction', 'asc')
        )


@dataclass
class QueryRule:
    """Structure for defining item query rules."""

    column_id: str
    """The ID of the column to filter on"""

    compare_value: list[Union[str, int]]
    """List of values to compare against"""

    operator: Literal[
        'any_of', 'not_any_of', 'is_empty', 'is_not_empty',
        'greater_than', 'greater_than_or_equals',
        'lower_than', 'lower_than_or_equal',
        'between', 'not_contains_text', 'contains_text',
        'contains_terms', 'starts_with', 'ends_with',
        'within_the_next', 'within_the_last'
    ] = 'any_of'
    """The comparison operator to use. Defaults to ``any_of`` if not specified"""

    compare_attribute: str = ''
    """The attribute to compare (optional)"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        result = {
            'column_id': self.column_id,
            'compare_value': self.compare_value,
            'operator': self.operator
        }
        if self.compare_attribute:
            result['compare_attribute'] = self.compare_attribute
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QueryRule:
        """Create from dictionary."""
        # Handle cases where column_id might not be present but compare_attribute is
        column_id = data.get('column_id', '')
        if not column_id and 'compare_attribute' in data:
            # Use compare_attribute as column_id if column_id is not present
            column_id = data['compare_attribute']

        return cls(
            column_id=str(column_id),
            compare_value=data['compare_value'],
            operator=data.get('operator', 'any_of'),
            compare_attribute=data.get('compare_attribute', '')
        )


@dataclass
class QueryParams:
    """
    Structure for complex item queries.

    Example:
        .. code-block:: python

            query_params = QueryParams(
                rules=[
                    QueryRule(
                        column_id='status',
                        compare_value=['Done', 'In Progress'],
                        operator='any_of'
                    )
                ],
                operator='and',
                order_by=OrderBy(
                    column_id='date',
                    direction='desc'
                )
            )
    """

    rules: list[QueryRule] = field(default_factory=list)
    """List of query rules to apply"""

    operator: Literal['and', 'or'] = 'and'
    """How to combine multiple rules. Defaults to 'and' if not specified"""

    order_by: OrderBy | None = None
    """Optional ordering configuration"""

    ids: list[int] = field(default_factory=list)
    """The specific item IDs to return. The maximum is 100."""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        result = {
            'rules': [rule.to_dict() for rule in self.rules],
            'operator': self.operator
        }
        if self.order_by:
            result['order_by'] = self.order_by.to_dict()
        if self.ids:
            result['ids'] = self.ids
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QueryParams:
        """Create from dictionary."""
        return cls(
            rules=[QueryRule.from_dict(rule) for rule in data.get('rules', [])],
            operator=data.get('operator', 'and'),
            order_by=OrderBy.from_dict(data['order_by']) if data.get('order_by') else None,
            ids=data.get('ids', [])
        )


@dataclass
class PersonOrTeam:
    """Structure for person/team references in column values."""

    id: str
    """Unique identifier of the person or team"""

    kind: Literal['person', 'team']
    """The type of the people column"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {
            'id': self.id,
            'kind': self.kind
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PersonOrTeam:
        """Create from dictionary."""
        return cls(
            id=str(data['id'], ''),
            kind=data['kind']
        )
