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

"""Utility functions and types for building GraphQL query strings."""

import ast
import json
import logging
from typing import Any, Literal

from monday.exceptions import QueryFormatError
from monday.types.item import QueryParams

logger: logging.Logger = logging.getLogger(__name__)


ENUM_FIELDS = {
    'board_attribute',
    'board_kind',
    'column_type',
    'duplicate_type',
    'fields',
    'group_attribute',
    'kind',
    'order_by',
    'position_relative_method',
    'query_params',
    'state',
}
"""Fields that should be treated as GraphQL enums (unquoted)"""

NUMERIC_ID_FIELDS = {
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
    'ids',
}
"""Fields that should be treated as numeric IDs (unquoted when they are numeric strings)"""


def build_graphql_query(
    operation: str,
    query_type: Literal['query', 'mutation'],
    args: dict[str, Any] | None = None,
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
    processed_args = {}
    if args:
        args = _convert_numeric_args(args)
        processed_args = _process_args(args)

    fields = processed_args.pop('fields', None)
    if fields:
        fields = _format_fields(fields)

    args_str = ', '.join(
        f'{k}: {v}' for k, v in processed_args.items() if v is not None
    )

    return f"""
        {query_type} {{
            {operation} {f'({args_str})' if args_str else ''}
                {f'{{ {fields} }}' if fields else ''}
        }}
    """


def build_operation_with_variables(  # noqa: PLR0913
    operation: str,
    query_type: Literal['query', 'mutation'],
    variable_types: dict[str, str],
    arg_var_mapping: dict[str, str],
    fields: Any,
    *,
    arg_literals: dict[str, str] | None = None,
) -> str:
    """
    Build a GraphQL operation string using variables.

    Args:
        operation: Operation name (e.g., 'create_board')
        query_type: 'query' or 'mutation'
        variable_types: Mapping of variable name -> GraphQL type (e.g., 'name': 'String!')
        arg_var_mapping: Mapping of argument name -> variable name (e.g., 'board_name': 'name')
        fields: Selection set fields (string or Fields-like)
        arg_literals: Literal argument strings to include verbatim (e.g., formatted lists)

    Returns:
        GraphQL operation string with variable definitions and arguments bound to variables.

    """
    var_defs = ', '.join(
        f'${var}: {gql_type}' for var, gql_type in variable_types.items()
    )

    arg_pairs: list[str] = []
    for arg, var in arg_var_mapping.items():
        arg_pairs.append(f'{arg}: ${var}')

    if arg_literals:
        for arg, literal in arg_literals.items():
            if literal is not None:
                arg_pairs.append(f'{arg}: {literal}')

    args_str = ', '.join(arg_pairs)

    fields_fmt = _format_fields(fields) if fields is not None else None

    selection = f' {{ {fields_fmt} }}' if fields_fmt else ''

    return f'{query_type} ({var_defs})\n{{\n    {operation} ({args_str}){selection}\n}}'


def format_columns_mapping(mapping: dict[str, Any]) -> str:
    """
    Format columns mapping dict to GraphQL argument value.

    Input: {'source_col': 'target_col'}
    Output: [{source: "source_col", target: "target_col"}, ...]
    """
    if not mapping:
        return '[]'
    pairs = [f'{{source: "{k}", target: "{v}"}}' for k, v in mapping.items()]
    return '[' + ', '.join(pairs) + ']'


def _process_dict_value(key: str, value: dict) -> str:
    """Process dictionary values for GraphQL formatting."""
    if key in {'columns_mapping', 'subitems_columns_mapping'}:
        pairs = []
        for k, v in value.items():
            pairs.append(f'{{source: "{k}", target: "{v}"}}')
        return '[' + ', '.join(pairs) + ']'
    return json.dumps(json.dumps(value))


def _process_column_values(column_dict: dict) -> list[str]:
    """Process column values for GraphQL formatting."""
    values = column_dict['column_values']
    if isinstance(values, str) and values.startswith('[') and values.endswith(']'):
        return [f'column_id: "{column_dict["column_id"]}", column_values: {values}']
    if isinstance(values, list):
        formatted_values = [f'"{v}"' for v in values]
        return [
            f'column_id: "{column_dict["column_id"]}", column_values: [{", ".join(formatted_values)}]'
        ]
    return [f'column_id: "{column_dict["column_id"]}", column_values: ["{values}"]']


def _process_columns_list(value: list) -> str:
    """Process columns list for GraphQL formatting."""
    processed_columns = []
    for column in value:
        if hasattr(column, 'column_id') and hasattr(column, 'column_values'):
            column_dict = {
                'column_id': column.column_id,
                'column_values': column.column_values,
            }
        else:
            column_dict = column

        if 'column_values' in column_dict:
            formatted_pairs = _process_column_values(column_dict)
        else:
            formatted_pairs = [f'{k}: "{v}"' for k, v in column_dict.items()]

        processed_columns.append('{' + ', '.join(formatted_pairs) + '}')
    return '[' + ', '.join(processed_columns) + ']'


def _process_list_value(key: str, value: list) -> str:
    """Process list values for GraphQL formatting."""
    if key == 'columns':
        return _process_columns_list(value)

    processed_values = []
    for item in value:
        # Treat any *_ids list (or known numeric fields) as numeric (unquoted)
        if key == 'ids' or key.endswith(('_ids',)) or key in NUMERIC_ID_FIELDS:
            processed_values.append(str(item))
        else:
            processed_values.append(f'"{item}"')
    return '[' + ', '.join(processed_values) + ']'


def _process_string_value(key: str, value: str) -> str:
    """Process string values for GraphQL formatting."""
    if key in ENUM_FIELDS:
        return value.strip()
    # Treat singular or plural *_id/_ids as numeric when digits
    if (key in NUMERIC_ID_FIELDS or key.endswith(('_id', '_ids'))) and value.isdigit():
        return value
    return f'"{value}"'


def _process_args(args: dict[str, Any]) -> dict[str, Any]:
    """Process arguments for GraphQL formatting."""
    processed_args = {}
    for key, value in args.items():
        stripped_key = key.strip()
        if value is None:
            continue
        if isinstance(value, bool):
            processed_args[stripped_key] = str(value).lower()
        elif isinstance(value, dict):
            processed_args[stripped_key] = _process_dict_value(stripped_key, value)
        elif isinstance(value, list):
            processed_args[stripped_key] = _process_list_value(stripped_key, value)
        elif isinstance(value, str):
            processed_args[stripped_key] = _process_string_value(stripped_key, value)
        else:
            processed_args[stripped_key] = value
    return processed_args


def _format_fields(fields: Any) -> str:
    """Format fields for GraphQL query."""
    fields_str = str(fields)
    fields_str = ' '.join(fields_str.split())
    fields_str = (
        fields_str.replace('{', ' { ')
        .replace('}', ' } ')
        .replace('(', ' ( ')
        .replace(')', ' ) ')
    )
    return ' '.join(fields_str.split())


def _convert_list_value(value: list) -> list:
    """Convert list values to integers where possible."""
    converted = []
    for x in value:
        if x is None:
            continue
        try:
            converted.append(int(x))
        except (ValueError, TypeError):
            converted.append(x)
    return converted


def _convert_string_array_value(value: str) -> list | str:
    """Convert string array values to actual arrays with numeric conversion."""
    try:
        parsed_array = ast.literal_eval(value)
        if isinstance(parsed_array, list):
            converted_array = []
            for x in parsed_array:
                if x is None:
                    continue
                try:
                    converted_array.append(int(x))
                except (ValueError, TypeError):
                    converted_array.append(x)
            return converted_array
        return value  # noqa: TRY300
    except (ValueError, SyntaxError):
        return value


def _convert_single_value(value: Any) -> Any:
    """Convert single values to integers where possible."""
    try:
        return int(value) if not isinstance(value, bool) else value
    except (ValueError, TypeError):
        return value


def _convert_numeric_args(args_dict: dict) -> dict:
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
        if isinstance(value, bool):
            converted[key] = value
        elif isinstance(value, list):
            converted[key] = _convert_list_value(value)
        elif isinstance(value, str) and value.startswith('[') and value.endswith(']'):
            converted[key] = _convert_string_array_value(value)
        else:
            converted[key] = _convert_single_value(value)
    return converted


def _process_rule(rule) -> str:
    """Process a single rule for GraphQL formatting."""
    rule_items = []
    rule_items.append(f'column_id: "{rule.column_id}"')
    rule_items.append(f'operator: {rule.operator}')

    compare_values = [
        str(int(v)) if str(v).isdigit() else f'"{v}"' for v in rule.compare_value
    ]
    rule_items.append(f'compare_value: [{", ".join(compare_values)}]')

    if rule.compare_attribute:
        rule_items.append(f'compare_attribute: "{rule.compare_attribute}"')

    return '{' + ', '.join(rule_items) + '}'


def _process_rules(rules) -> str | None:
    """Process rules for GraphQL formatting."""
    if not rules:
        return None

    rule_parts = [_process_rule(rule) for rule in rules]
    return f'rules: [{", ".join(rule_parts)}]' if rule_parts else None


def _process_order_by(order_by) -> str:
    """Process order_by for GraphQL formatting."""
    return f'{{column_id: "{order_by.column_id}", direction: {order_by.direction}}}'


def _process_ids(ids) -> str | None:
    """Process ids for GraphQL formatting."""
    if not ids:
        return None

    if isinstance(ids, str) and ids.startswith('[') and ids.endswith(']'):
        try:
            parsed_ids = ast.literal_eval(ids)
            if isinstance(parsed_ids, list):
                ids_list = [str(item_id) for item_id in parsed_ids]
            else:
                ids_list = [str(ids)]
        except (ValueError, SyntaxError):
            ids_list = [str(ids)]
    else:
        ids_list = [str(item_id) for item_id in ids]

    return f'ids: [{", ".join(ids_list)}]'


def build_query_params_string(query_params: QueryParams | dict[str, Any] | None) -> str:
    """
    Builds a GraphQL-compatible query parameters string.

    Args:
        query_params: QueryParams dataclass or dictionary containing rules, operator and order_by parameters

    Returns:
        Formatted query parameters string for GraphQL query

    """
    if not query_params:
        return ''

    # Convert dict to QueryParams if needed
    if isinstance(query_params, dict):
        query_params = QueryParams.from_dict(query_params)

    parts = []

    # Process rules
    rules_part = _process_rules(query_params.rules)
    if rules_part:
        parts.append(rules_part)

    # Add operator if present
    if query_params.operator:
        parts.append(f'operator: {query_params.operator}')

    # Add order_by if present
    if query_params.order_by:
        parts.append(f'order_by: {_process_order_by(query_params.order_by)}')

    # Process ids
    ids_part = _process_ids(query_params.ids)
    if ids_part:
        parts.append(ids_part)

    return '{' + ', '.join(parts) + '}' if parts else ''


def map_hex_to_color(color_hex: str) -> str:
    """
    Maps a color's hex value to its string representation in monday.com.

    Args:
        color_hex: The hex representation of the color

    Returns:
        The string representation of the color used by monday.com

    """
    unmapped_hex = {'#cab641'}

    if color_hex in unmapped_hex:
        raise QueryFormatError(
            message=f'{color_hex} is currently not mapped to a string value on monday.com'
        )

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
        '#808080': 'trolley-grey',
    }

    if color_hex not in hex_color_map:
        raise QueryFormatError(message=f'Invalid color hex {color_hex}')

    return hex_color_map[color_hex]
