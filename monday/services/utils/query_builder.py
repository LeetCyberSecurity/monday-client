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
from typing import Any, Literal, Union

from monday.exceptions import QueryFormatError
from monday.types.query import QueryParams

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
            converted[key] = value  # Preserve boolean values
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
        elif isinstance(value, str) and value.startswith('[') and value.endswith(']'):
            # Handle string arrays - try to parse them as actual arrays
            try:
                import ast
                parsed_array = ast.literal_eval(value)
                if isinstance(parsed_array, list):
                    # Convert numeric strings in the parsed array
                    converted_array = []
                    for x in parsed_array:
                        if x is None:
                            continue
                        try:
                            converted_array.append(int(x))
                        except (ValueError, TypeError):
                            converted_array.append(x)
                    converted[key] = converted_array
                else:
                    converted[key] = value
            except (ValueError, SyntaxError):
                # If parsing fails, keep as string
                converted[key] = value
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
    args: dict[str, Any] | None = None
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

    # Fields that should be treated as numeric IDs (unquoted when they are numeric strings)
    numeric_id_fields = {
        'board_id',
        'board_ids',
        'item_id',
        'item_ids',
        'subitem_id',
        'subitem_ids',
        'parent_item_id',
        'workspace_id',
        'workspace_ids',
        'folder_id',
        'template_id',
        'group_id',
        'group_ids',
        'owner_ids',
        'subscriber_ids',
        'subscriber_teams_ids',
        'relative_to',
        'ids'
    }

    processed_args = {}
    if args:
        args = convert_numeric_args(args)

        # Special handling for common field types
        for key, value in args.items():
            key = key.strip()
            if value is None:
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
                        # Handle ColumnFilter dataclass objects
                        if hasattr(column, 'column_id') and hasattr(column, 'column_values'):
                            # Convert ColumnFilter to dict format
                            column_dict = {
                                'column_id': column.column_id,
                                'column_values': column.column_values
                            }
                        else:
                            # Handle dictionary format for backward compatibility
                            column_dict = column

                        # Remove extra quotes for column_values
                        if 'column_values' in column_dict:
                            # Handle column_values as a list without additional quotes
                            values = column_dict['column_values']
                            if isinstance(values, str) and values.startswith('[') and values.endswith(']'):
                                # Already formatted as a string list
                                formatted_pairs = [f'column_id: "{column_dict["column_id"]}", column_values: {values}']
                            else:
                                # Format as a proper list
                                formatted_pairs = [f'column_id: "{column_dict["column_id"]}", column_values: {json.dumps(values)}']
                        else:
                            # Handle other column properties
                            formatted_pairs = [f'{k}: "{v}"' for k, v in column_dict.items()]
                        processed_columns.append('{' + ', '.join(formatted_pairs) + '}')
                    processed_args[key] = '[' + ', '.join(processed_columns) + ']'
                else:
                    processed_values = []
                    for item in value:
                        if key == 'ids' or (key in numeric_id_fields and key.endswith('_ids')):
                            processed_values.append(str(item))
                        else:
                            processed_values.append(f'"{item}"')
                    processed_args[key] = '[' + ', '.join(processed_values) + ']'
            elif isinstance(value, str):
                if key in enum_fields:
                    processed_args[key] = value.strip()  # No quotes for enum values
                elif key in numeric_id_fields and value.isdigit():
                    processed_args[key] = value  # No quotes for numeric ID strings
                else:
                    processed_args[key] = f'"{value}"'  # Quote regular strings
            else:
                processed_args[key] = value

    fields = processed_args.pop('fields', None)
    if fields:
        # Ensure fields are properly formatted with their arguments and nested structures
        fields_str = str(fields)
        # Remove any extra whitespace between fields
        fields_str = ' '.join(fields_str.split())
        # Ensure proper spacing around braces and parentheses
        fields_str = fields_str.replace('{', ' { ').replace('}', ' } ').replace('(', ' ( ').replace(')', ' ) ')
        fields_str = ' '.join(fields_str.split())
        fields = fields_str

    args_str = ', '.join(f'{k}: {v}' for k, v in processed_args.items() if v is not None)

    return f"""
        {query_type} {{
            {operation} {f'({args_str})' if args_str else ''} 
                {f'{{ {fields} }}' if fields else ''}
        }}
    """


def build_query_params_string(
    query_params: Union['QueryParams', dict[str, Any]]
) -> str:
    """
    Builds a GraphQL-compatible query parameters string.

    Args:
        query_params: QueryParams dataclass or dictionary containing rules, operator and order_by parameters

    Returns:
        Formatted query parameters string for GraphQL query
    """
    if not query_params:
        return ""

    # Convert dict to QueryParams if needed
    if isinstance(query_params, dict):
        query_params = QueryParams.from_dict(query_params)

    parts = []

    # Process rules
    if query_params.rules:
        rule_parts = []
        for rule in query_params.rules:
            rule_items = []
            rule_items.append(f'column_id: "{rule.column_id}"')
            rule_items.append(f'operator: {rule.operator}')

            compare_values = [
                str(int(v)) if str(v).isdigit() else f'"{v}"'
                for v in rule.compare_value
            ]
            rule_items.append(f'compare_value: [{", ".join(compare_values)}]')

            if rule.compare_attribute:
                rule_items.append(f'compare_attribute: "{rule.compare_attribute}"')

            rule_parts.append('{' + ', '.join(rule_items) + '}')

        if rule_parts:
            parts.append(f'rules: [{", ".join(rule_parts)}]')

    # Add operator if present
    if query_params.operator:
        parts.append(f'operator: {query_params.operator}')

    # Add order_by if present
    if query_params.order_by:
        order_str = ('{' +
                     f'column_id: "{query_params.order_by.column_id}", ' +
                     f'direction: {query_params.order_by.direction}' +
                     '}')
        parts.append(f'order_by: {order_str}')

    if query_params.ids:
        # Handle case where ids might be a string that needs to be parsed
        if isinstance(query_params.ids, str) and query_params.ids.startswith('[') and query_params.ids.endswith(']'):
            try:
                import ast
                parsed_ids = ast.literal_eval(query_params.ids)
                if isinstance(parsed_ids, list):
                    ids_list = [str(id) for id in parsed_ids]
                else:
                    ids_list = [str(query_params.ids)]
            except (ValueError, SyntaxError):
                ids_list = [str(query_params.ids)]
        else:
            ids_list = [str(id) for id in query_params.ids]
        parts.append(f'ids: [{", ".join(ids_list)}]')

    return '{' + ', '.join(parts) + '}' if parts else ''


def map_hex_to_color(
    color_hex: str
) -> str:
    """
    Maps a color's hex value to its string representation in monday.com.

    Args:
        color_hex: The hex representation of the color

    Returns:
        The string representation of the color used by monday.com
    """

    unmapped_hex = {
        '#cab641'
    }

    if color_hex in unmapped_hex:
        raise QueryFormatError(f'{color_hex} is currently not mapped to a string value on monday.com')

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

    if color_hex not in hex_color_map:
        raise QueryFormatError(f'Invalid color hex {color_hex}')

    return hex_color_map[color_hex]
