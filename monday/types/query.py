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
Type definitions for monday.com API query related structures.
"""

from __future__ import annotations

from typing import Literal, Required, TypedDict, Union


class ColumnFilter(TypedDict):
    """Structure for filtering items by column values.

    Example:
        .. code-block:: python

            column_filter = {
                'column_id': 'status',
                'column_values': ['Done', 'In Progress']
            }

            # Or with a single value
            column_filter = {
                'column_id': 'text',
                'column_values': 'Search term'
            }
    """

    column_id: str
    """The ID of the column to filter by"""

    column_values: Union[str, list[str]]
    """The value(s) to filter for. Can be a single string or list of strings"""


class OrderBy(TypedDict, total=False):
    """Structure for ordering items in queries."""

    column_id: Required[str]
    """The ID of the column to order by"""

    direction: Literal['asc', 'desc']
    """The direction to order items. Defaults to 'asc' if not specified"""


class QueryParams(TypedDict, total=False):
    """Structure for complex item queries.

    Example:
        .. code-block:: python

            query_params = {
                'rules': [{
                    'column_id': 'status',
                    'compare_value': ['Done', 'In Progress'],
                    'operator': 'any_of'
                }],
                'operator': 'and',
                'order_by': {
                    'column_id': 'date',
                    'direction': 'desc'
                }
            }
    """

    ids: list[int]
    """The specific item IDs to return. The maximum is 100."""

    rules: list[QueryRule]
    """List of query rules to apply"""

    operator: Literal['and', 'or']
    """How to combine multiple rules. Defaults to 'and' if not specified"""

    order_by: OrderBy
    """Optional ordering configuration"""


class QueryRule(TypedDict, total=False):
    """Structure for defining item query rules."""

    column_id: Required[str]
    """The ID of the column to filter on"""

    compare_attribute: str
    """The attribute to compare (optional)"""

    compare_value: Required[list[Union[str, int]]]
    """List of values to compare against"""

    operator: Literal[
        'any_of', 'not_any_of', 'is_empty', 'is_not_empty',
        'greater_than', 'greater_than_or_equals',
        'lower_than', 'lower_than_or_equal',
        'between', 'not_contains_text', 'contains_text',
        'contains_terms', 'starts_with', 'ends_with',
        'within_the_next', 'within_the_last'
    ]
    """The comparison operator to use. Defaults to ``any_of`` if not specified"""


class PersonOrTeam(TypedDict):
    """Structure for person/team references in column values."""

    id: int
    """Unique identifier of the person or team"""

    kind: Literal['person', 'team']
    """The type of the people column"""


class ColumnValueDict(TypedDict, total=False):
    """Structure for complex column values that require JSON objects."""

    text: str
    """Text value for text-based columns"""

    index: int
    """Index value for status columns"""

    label: str
    """Label value for status columns"""

    date: str
    """Date string in YYYY-MM-DD format"""

    personsAndTeams: list[PersonOrTeam]
    """List of people/teams for people columns"""
