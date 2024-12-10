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
Type definitions for monday.com API structures.

This module contains TypedDict definitions for various API request and response structures
used in the monday.com client.
"""

from typing import Literal, NotRequired, TypedDict, Union


class OrderBy(TypedDict, total=False):
    """Structure for ordering items in queries."""

    column_id: str
    """The ID of the column to order by"""

    direction: NotRequired[Literal['asc', 'desc']]
    """The direction to order items. Defaults to 'asc' if not specified"""


class QueryRule(TypedDict, total=False):
    """Structure for defining item query rules."""

    column_id: str
    """The ID of the column to filter on"""

    compare_attribute: NotRequired[str]
    """The attribute to compare (optional)"""

    compare_value: list[Union[str, int]]
    """List of values to compare against"""

    operator: NotRequired[Literal[
        'any_of', 'not_any_of', 'is_empty', 'is_not_empty',
        'greater_than', 'greater_than_or_equals',
        'lower_than', 'lower_than_or_equal',
        'between', 'not_contains_text', 'contains_text',
        'contains_terms', 'starts_with', 'ends_with',
        'within_the_next', 'within_the_last'
    ]]
    """The comparison operator to use. Defaults to ``any_of`` if not specified.

    Can be one of:
        * ``any_of`` - Match any of the values (default)
        * ``not_any_of`` - Don't match any of the values
        * ``is_empty`` - Field is empty
        * ``is_not_empty`` - Field is not empty
        * ``greater_than`` - Greater than the value
        * ``greater_than_or_equals`` - Greater than or equal to the value
        * ``lower_than`` - Less than the value
        * ``lower_than_or_equal`` - Less than or equal to the value
        * ``between`` - Between two values
        * ``not_contains_text`` - Does not contain text
        * ``contains_text`` - Contains text
        * ``contains_terms`` - Contains specific terms
        * ``starts_with`` - Starts with text
        * ``ends_with`` - Ends with text
        * ``within_the_next`` - Within the next time period
        * ``within_the_last`` - Within the last time period
    """


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

    operator: NotRequired[Literal['and', 'or']]
    """How to combine multiple rules. Defaults to 'and' if not specified"""

    order_by: NotRequired[OrderBy]
    """Optional ordering configuration"""
