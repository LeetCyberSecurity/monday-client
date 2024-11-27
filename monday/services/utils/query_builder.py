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

"""Utility class for building query strings."""

import json
from typing import Any, Dict, Literal


class GraphQLQueryBuilder:
    """
    A utility class for building GraphQL query strings for Monday.com API requests.

    This class provides a centralized way to construct GraphQL queries with consistent
    formatting and proper handling of different data types. It supports both query
    and mutation operations and handles special cases for various input types.
    """

    @staticmethod
    def build_query(
        operation: str,
        query_type: Literal['query', 'mutation'],
        args: Dict[str, Any]
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

        processed_args = {}

        # Special handling for common field types
        for key, value in args.items():
            if not value:
                continue
            elif isinstance(value, bool):
                processed_args[key] = str(value).lower()
            elif isinstance(value, dict):
                processed_args[key] = json.dumps(json.dumps(value))
            elif isinstance(value, str):
                if key in enum_fields:
                    processed_args[key] = value  # No quotes for enum values
                else:
                    processed_args[key] = f'"{value}"'  # Quote regular strings
            else:
                processed_args[key] = value

        fields = processed_args.pop('fields', 'id')

        args_str = ', '.join(f'{k}: {v}' for k, v in processed_args.items() if v)

        return f"""
            {query_type} {{
                {operation} {f'({args_str})' if args_str else ''} {{
                    {fields}
                }}
            }}
        """
