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

"""Utility functions for building GraphQL query strings."""

import json
import logging
from typing import Any, Literal

from monday.exceptions import QueryFormatError
from monday.types import QueryParams

logger: logging.Logger = logging.getLogger(__name__)


def convert_numeric_args(args_dict: dict) -> dict:
    """
    Convert numeric arguments to integers in a dictionary.

    Args:
        args_dict: Dictionary containing arguments that may need numeric conversion

    Returns:
        Dictionary with numeric values converted to integers
    """
    converted = {}
    for key, value in args_dict.items():
        if value is None:
            continue
        elif isinstance(value, bool):
            converted[key] = value
        elif isinstance(value, list):
            # Handle lists of values
            converted[key] = []
            for x in value:
                if x is None:
                    continue
                try:
                    converted[key].append(int(x))
                except (ValueError, TypeError):
                    converted[key].append(x)
        else:
            # Handle single values
            try:
                converted[key] = int(value) if not isinstance(value, bool) else value
            except (ValueError, TypeError):
                converted[key] = value
    return converted


def build_graphql_query(
    operation: str,
    query_type: Literal['query', 'mutation'],
    args: dict[str, Any]
) -> str:
    """
    Builds a formatted GraphQL query string based on the provided parameters.

    Args:
        operation: The GraphQL operation name (e.g., 'items', 'create_item')
        query_type: The type of GraphQL operation ('query' or 'mutation')
        args: GraphQL query arguments

    Returns:
        A formatted GraphQL query string ready for API submission
    """

    # Fields that should be treated as GraphQL enums (unquoted)
    enum_fields = {
        'board_attribute',
        'board_kind',
        'duplicate_type',
        'fields',
        'group_attribute',
        'kind',
        'order_by',
        'query_params',
        'state'
    }

    args = convert_numeric_args(args)
    processed_args = {}

    # Special handling for common field types
    for key, value in args.items():
        key = key.strip()
        if not value:
            continue
        elif isinstance(value, bool):
            processed_args[key] = str(value).lower()
        elif isinstance(value, dict):
            if key == 'columns_mapping':
                columns_mapping = []
                for k, v in value.items():
                    columns_mapping.append(f'{{source: "{k}", target: "{v}"}}')
                processed_args[key] = '[' + ', '.join(columns_mapping) + ']'
            else:
                processed_args[key] = json.dumps(json.dumps(value))
        elif isinstance(value, list):
            if key == 'columns':
                processed_columns = []
                for column in value:
                    # Remove extra quotes for column_values
                    if 'column_values' in column:
                        # Handle column_values as a list without additional quotes
                        values = column['column_values']
                        if isinstance(values, str) and values.startswith('[') and values.endswith(']'):
                            # Already formatted as a string list
                            formatted_pairs = [f'column_id: "{column["column_id"]}", column_values: {values}']
                        else:
                            # Format as a proper list
                            formatted_pairs = [f'column_id: "{column["column_id"]}", column_values: {json.dumps(values)}']
                    else:
                        # Handle other column properties
                        formatted_pairs = [f'{k}: "{v}"' for k, v in column.items()]
                    processed_columns.append('{' + ', '.join(formatted_pairs) + '}')
                processed_args[key] = '[' + ', '.join(processed_columns) + ']'
            else:
                processed_values = []
                for item in value:
                    processed_values.append(f'"{item}"')
                processed_args[key] = '[' + ', '.join(processed_values) + ']'
        elif isinstance(value, str):
            if key in enum_fields:
                processed_args[key] = value.strip()  # No quotes for enum values
            else:
                processed_args[key] = f'"{value}"'  # Quote regular strings
        else:
            processed_args[key] = value

    fields = processed_args.pop('fields', None)

    args_str = ', '.join(f'{k}: {v}' for k, v in processed_args.items() if v)

    return f"""
        {query_type} {{
            {operation} {f'({args_str})' if args_str else ''} 
                {f'{{ {fields} }}' if fields else ''}
        }}
    """


def build_query_params_string(
    query_params: 'QueryParams'
) -> str:
    """
    Builds a GraphQL-compatible query parameters string.

    Args:
        query_params: Dictionary containing rules, operator and order_by parameters

    Returns:
        Formatted query parameters string for GraphQL query
    """
    if not query_params:
        return ""

    parts = []

    # Process rules
    if rules := query_params.get('rules'):
        rule_parts = []
        for rule in rules:
            rule_items = []
            for key, value in rule.items():
                if key == 'operator':
                    rule_items.append(f'{key}: {value}')
                elif key == 'compare_value':
                    compare_values = [
                        str(int(v)) if str(v).isdigit() else f'"{v}"'
                        for v in value
                    ]
                    rule_items.append(f'compare_value: [{", ".join(compare_values)}]')
                elif key in ['compare_attribute', 'column_id']:
                    rule_items.append(f'{key}: "{value}"')
            rule_parts.append('{' + ', '.join(rule_items) + '}')

        if rule_parts:
            parts.append(f'rules: [{", ".join(rule_parts)}]')

    # Add operator if present
    if operator := query_params.get('operator'):
        parts.append(f'operator: {operator}')

    # Add order_by if present
    if order_by := query_params.get('order_by'):
        order_str = ('{' +
                     f'column_id: "{order_by["column_id"]}", ' +
                     f'direction: {order_by["direction"]}' +
                     '}')
        parts.append(f'order_by: {order_str}')

    return '{' + ', '.join(parts) + '}' if parts else ''


def map_color_to_hex(
    color: str
) -> str:
    """
    Maps a color string to it's hex value.

    Args:
        color: The string representation of the color

    Returns:
        The hex representation of the color
    """

    unmapped_hex = {
        '#cab641'
    }

    if color in unmapped_hex:
        raise QueryFormatError(f'{color} is currently not mapped to a string value on monday.com')

    hex_color_map = {
        '#ff5ac4': 'light-pink',
        '#ff158a': 'dark-pink',
        '#bb3354': 'dark-red',
        '#e2445c': 'red',
        '#ff642e': 'dark-orange',
        '#fdab3d': 'orange',
        '#ffcb00': 'yellow',
        '#9cd326': 'lime-green',
        '#00c875': 'green',
        '#037f4c': 'dark-green',
        '#0086c0': 'dark-blue',
        '#579bfc': 'blue',
        '#66ccff': 'turquoise',
        '#a25ddc': 'purple',
        '#784bd1': 'dark-purple',
        '#7f5347': 'brown',
        '#c4c4c4': 'grey',
        '#808080': 'trolley-grey'
    }

    if color not in hex_color_map:
        raise QueryFormatError(f'Invalid color {color}')

    return hex_color_map[color]
