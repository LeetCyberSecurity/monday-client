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

# pylint: disable=too-many-lines

"""
Utilities for handling GraphQL field combinations.

This module provides the Fields class for managing GraphQL field strings in a structured way.
It handles field parsing, combination, and deduplication while maintaining field order and
nested structure integrity.

Example:

.. code-block:: python

    Basic field combination:
    >>> fields1 = Fields('id name')
    >>> fields2 = Fields('name description')
    >>> combined = fields1 + fields2
    >>> str(combined)
    'id name description'

    Handling nested fields:
    >>> nested = Fields('id name items { id title }')
    >>> str(nested)
    'id name items { id title }'

    String addition:
    >>> fields = Fields('id name') + 'description'
    >>> str(fields)
    'id name description'
"""

import ast
import logging
import re
from typing import Any, Optional, Union


class Fields:
    """
    Helper class for handling GraphQL field combinations.

    This class provides structured handling of GraphQL field strings, including:

        - Parsing field strings while preserving nested structures
        - Combining multiple field sets while maintaining order
        - Converting back to GraphQL-compatible strings

    Args:
        fields (Union[str, Fields]): Either a space-separated string of field names or another Fields instance. Can include nested structures using GraphQL syntax.

    Attributes:
        fields (list[str]): List of parsed and normalized field strings.

    Example:
        >>> basic_fields = Fields('id name')
        >>> extended_fields = basic_fields + 'description'
        >>> print(extended_fields)
        'id name description'

        >>> nested_fields = Fields('id items { id name }')
        >>> print(nested_fields)
        'id items { id name }'
    """

    _logger: logging.Logger = logging.getLogger(__name__)

    def __init__(self, fields: Union[str, 'Fields']):
        """
        Initialize a Fields instance.
        """
        if isinstance(fields, Fields):
            fields_str = str(fields)
        else:
            fields_str = str(fields)
        # Validate fields before parsing/deduplication
        self._validate_fields(fields_str)
        # Always deduplicate and merge
        deduped = self._deduplicate_nested_fields(fields_str)
        self.fields = self._parse_fields(deduped)

    def __str__(self) -> str:
        """
        Convert back to a GraphQL-compatible field string.
        """
        return ' '.join(self.fields)

    def __repr__(self) -> str:
        """
        Return a string representation of the Fields object.

        Returns:
            String representation that can be used to recreate the object.

        Example:
            >>> fields = Fields('id name')
            >>> repr(fields)
            "Fields('id name')"
        """
        return f"Fields('{str(self)}')"

    def __add__(self, other: Union['Fields', str]) -> 'Fields':
        """
        Combine two field lists, maintaining order and preserving nested structures.

        Args:
            other: Either a Fields instance or a field string to combine with this instance.

        Returns:
            New Fields instance containing combined fields.

        Example:
            >>> fields1 = Fields('id name top_group { id title }')
            >>> fields2 = Fields('groups { id title }')
            >>> str(fields1 + fields2)
            'id name top_group { id title } groups { id title }'
        """
        # Convert string to Fields if needed
        if isinstance(other, str):
            other = Fields(other)

        # Create a combined string and let the parser handle deduplication
        # Track the original order by combining the input strings
        combined_str = str(self) + ' ' + str(other)
        return Fields(combined_str)

    def __sub__(self, other: Union['Fields', str]) -> 'Fields':
        """
        Subtract fields from another Fields object or a string.

        Args:
            other: Fields instance or string containing fields to subtract.

        Returns:
            New Fields instance with specified fields removed.

        Example:
            >>> fields1 = Fields('id name board { id title }')
            >>> fields2 = Fields('name board { title }')
            >>> str(fields1 - fields2)
            'id board { id }'
        """
        # Convert string to Fields object if needed
        if isinstance(other, str):
            other = Fields(other)

        if not other.fields:
            return Fields(str(self))

        result_fields = []

        for field in self.fields:
            # Check if this is a nested field
            if '{' in field:
                base_field = field.split(' {')[0].split(' (')[0]

                # Find corresponding field in other
                other_field = next((f for f in other.fields if f.startswith(f'{base_field} {{')
                                    or f == base_field), None)

                if other_field:
                    if '{' in other_field:  # Both have nested content
                        # Extract and compare nested content
                        self_nested = self._extract_nested_content(field)
                        other_nested = self._extract_nested_content(other_field)

                        # Create new Fields objects for nested content
                        self_nested_fields = Fields(self_nested)
                        other_nested_fields = Fields(other_nested)

                        # Recursively subtract nested fields
                        diff_nested = self_nested_fields - other_nested_fields
                        if str(diff_nested):  # If there are remaining fields
                            # Preserve arguments if they exist
                            args_start = field.find('(')
                            args_end = field.find(')')
                            if args_start != -1 and args_end != -1:
                                args = field[args_start:args_end + 1]
                                result_fields.append(f'{base_field}{args} {{ {str(diff_nested)} }}')
                            else:
                                result_fields.append(f'{base_field} {{ {str(diff_nested)} }}')
                    else:
                        # Other field has no nested content, so remove this field entirely
                        continue
                else:
                    result_fields.append(field)
            else:
                # Handle non-nested fields
                if field not in other.fields:
                    result_fields.append(field)

        return Fields(' '.join(result_fields))

    def __contains__(self, field: str) -> bool:
        """
        Check if a field exists in the Fields instance.

        Args:
            field: Field name to check for.

        Returns:
            True if field exists, False otherwise.

        Example:
            >>> fields = Fields('id name')
            >>> 'name' in fields
            True
            >>> ' name ' in fields  # Whitespace is normalized
            True
            >>> 'board' in fields
            False
        """
        field = field.strip()  # Normalize the input field by stripping whitespace
        return any(
            f.strip().startswith(field + ' ') or  # field at start
            f.strip() == field or                 # exact match
            f' {field} ' in f or                  # field in middle
            f.strip().endswith(f' {field}')       # field at end
            for f in self.fields
        )

    def __eq__(self, other: 'Fields') -> bool:
        """
        Check if two Fields instances are equal.

        Args:
            other: Another Fields instance to compare with.

        Returns:
            True if both instances have identical fields, False otherwise.

        Example:
            >>> fields1 = Fields('id name')
            >>> fields2 = Fields('id name')
            >>> fields1 == fields2
            True
            >>> fields3 = Fields('id description')
            >>> fields1 == fields3
            False
        """
        if isinstance(other, Fields):
            return self.fields == other.fields
        return False

    def add_temp_fields(self, temp_fields: list[str]) -> 'Fields':
        """
        Add temporary fields while preserving nested structures.

        Args:
            temp_fields: List of field names to temporarily add

        Returns:
            New Fields instance with temporary fields added

        Example:
            >>> fields = Fields('id name')
            >>> new_fields = fields.add_temp_fields(['temp1', 'temp2'])
            >>> str(new_fields)
            'id name temp1 temp2'

            >>> fields = Fields('name products { kind }')
            >>> new_fields = fields.add_temp_fields(['id', 'products { id }'])
            >>> str(new_fields)
            'name id products { kind id }'
        """
        if not temp_fields:
            return self

        # Create a mapping of base fields to their nested content
        field_map = {}

        # Process original fields
        for field in self.fields:
            base_field = field.split(' {')[0].split(' (')[0]
            if '{' in field:
                nested_content = field[field.find('{') + 1:field.rfind('}')].strip()
                field_map[base_field] = Fields(nested_content)
            else:
                field_map[base_field] = None

        # Process temp fields and merge with existing fields
        for field in temp_fields:
            base_field = field.split(' {')[0].split(' (')[0]
            if '{' in field:
                nested_content = field[field.find('{') + 1:field.rfind('}')].strip()
                temp_nested_fields = Fields(nested_content)

                if base_field in field_map and field_map[base_field] is not None:
                    # Merge with existing nested fields
                    field_map[base_field] = field_map[base_field] + temp_nested_fields
                else:
                    # Create new nested field
                    field_map[base_field] = temp_nested_fields
            else:
                # Simple field - add to map if not already present
                if base_field not in field_map:
                    field_map[base_field] = None

        # Reconstruct the field string
        result_fields = []
        for base_field, nested_fields in field_map.items():
            if nested_fields is not None:
                result_fields.append(f'{base_field} {{ {str(nested_fields)} }}')
            else:
                result_fields.append(base_field)

        return Fields(' '.join(result_fields))

    @staticmethod
    def manage_temp_fields(
        data: dict[str, Any] | list[Any],
        original_fields: Union[str, set[str], 'Fields'],
        temp_fields: list[str],
        preserve_fields: Optional[list[str]] = None
    ) -> dict[str, Any] | list[Any]:
        """
        Remove temporary fields from query results that weren't in original fields.

        Args:
            data: Query result data
            original_fields: Space-separated string, set of field names, or Fields object
            temp_fields: List of field names that were temporarily added
            preserve_fields: List of field names that should be preserved even if they're temp fields

        Returns:
            Data structure with temporary fields removed if they weren't in original fields

        Example:
            >>> data = {
            ...     'id': '123456789',
            ...     'name': 'Task',
            ...     'temp_status': 'active',
            ...     'board': {'id': '987654321', 'temp_field': 'value'}
            ... }
            >>> original = 'id name board { id }'
            >>> temp_fields = ['temp_status', 'temp_field']
            >>> Fields.manage_temp_fields(data, original, temp_fields)
            {'id': '123456789', 'name': 'Task', 'board': {'id': '987654321'}}
        """
        # Convert original_fields to Fields object if needed
        if isinstance(original_fields, str):
            fields_obj = Fields(original_fields)
        elif isinstance(original_fields, Fields):
            fields_obj = original_fields
        else:
            fields_obj = Fields(' '.join(original_fields))

        # Get top-level fields and their nested structure
        field_structure = {}
        for field in fields_obj.fields:
            base_field = field.split(' {')[0].split(' (')[0]
            if '{' in field:
                nested_content = field[field.find('{') + 1:field.rfind('}')].strip()
                field_structure[base_field] = Fields(nested_content)
            else:
                field_structure[base_field] = None

        # Identify top-level temp fields that should be removed entirely
        top_level_temp_fields = set()
        nested_temp_fields = {}

        for temp_field in temp_fields:
            if '{' in temp_field:
                # This is a nested temp field
                base_field = temp_field.split(' {')[0].strip()
                nested_content = temp_field[temp_field.find('{') + 1:temp_field.rfind('}')].strip()
                if base_field not in nested_temp_fields:
                    nested_temp_fields[base_field] = []
                nested_temp_fields[base_field].append(nested_content)
            else:
                # This is a top-level temp field
                top_level_temp_fields.add(temp_field)

        # Find which top-level temp fields weren't in original fields
        fields_to_remove = top_level_temp_fields - set(field_structure.keys())

        # Preserve specified fields
        if preserve_fields:
            for field in preserve_fields:
                if field in fields_to_remove:
                    fields_to_remove.remove(field)

        if not fields_to_remove and not nested_temp_fields:
            return data

        if isinstance(data, list):
            # If we have a parent context, use it for nested lists
            # This block is only called from the parent dict handler, so we need to pass the correct nested context
            # We'll use the temp_fields relevant to this context if available
            # (This block is only called directly for top-level lists, so we keep the default behavior)
            return [Fields.manage_temp_fields(item, fields_obj, temp_fields) for item in data]

        if isinstance(data, dict):
            result = {}
            for k, v in data.items():
                # Skip top-level temporary fields that weren't in original fields
                if k in fields_to_remove:
                    continue

                # Handle nested structures
                if isinstance(v, (dict, list)):
                    if k in field_structure and field_structure[k] is not None:
                        nested_temp_fields_for_k = Fields._extract_nested_temp_fields(temp_fields, k)
                        if isinstance(v, list):
                            processed_list = [Fields.manage_temp_fields(item, field_structure[k], nested_temp_fields_for_k) for item in v]
                            processed_list = [item for item in processed_list if item or item == 0 or item is False]  # Remove empty dicts/lists but keep falsy values
                            if processed_list:
                                result[k] = processed_list
                        else:
                            processed = Fields.manage_temp_fields(v, field_structure[k], nested_temp_fields_for_k)
                            if processed or processed == 0 or processed is False:
                                if not (isinstance(processed, dict) and not processed):
                                    result[k] = processed
                    elif k in nested_temp_fields:
                        nested_temp_fields_for_k = nested_temp_fields.get(k, [])
                        if isinstance(v, list):
                            processed = [Fields.manage_temp_fields(item, Fields(''), nested_temp_fields_for_k) for item in v]
                            processed = [item for item in processed if item or item == 0 or item is False]
                            if processed:
                                result[k] = processed
                        else:
                            processed = Fields.manage_temp_fields(v, Fields(''), nested_temp_fields_for_k)
                            if processed or processed == 0 or processed is False:
                                if not (isinstance(processed, dict) and not processed):
                                    result[k] = processed
                    else:
                        if isinstance(v, list):
                            nested_temp_fields_for_k = Fields._extract_nested_temp_fields(temp_fields, k)
                            processed_list = [Fields.manage_temp_fields(item, fields_obj, nested_temp_fields_for_k) for item in v]
                            processed_list = [item for item in processed_list if item or item == 0 or item is False]
                            if processed_list:
                                result[k] = processed_list
                        else:
                            processed = Fields.manage_temp_fields(v, fields_obj, temp_fields)
                            if processed or processed == 0 or processed is False:
                                if not (isinstance(processed, dict) and not processed):
                                    result[k] = processed
                else:
                    result[k] = v
            return result

        return data

    @staticmethod
    def extract_parent_fields(temp_fields: list[str]) -> list[str]:
        """
        Extract parent field names from nested temp fields.

        Args:
            temp_fields: List of temp field strings that may contain nested structures

        Returns:
            List of parent field names that contain the temp fields

        Example:
            >>> Fields.extract_parent_fields(['id', 'products { id }', 'products { kind { id } }'])
            ['products']
            >>> Fields.extract_parent_fields(['id', 'board { id }', 'board { items { id } }'])
            ['board']
        """
        parent_fields = set()

        for field in temp_fields:
            # Look for nested structures like 'field { ... }'
            if '{' in field:
                # Extract the base field name before the opening brace
                base_field = field.split(' {')[0].strip()
                parent_fields.add(base_field)

        return list(parent_fields)

    @staticmethod
    def _extract_nested_temp_fields(temp_fields: list[str], parent_field: str) -> list[str]:
        """
        Extract temp fields that are relevant to a specific nested context.

        Args:
            temp_fields: List of all temp fields
            parent_field: The parent field name (e.g., 'products')

        Returns:
            List of temp fields that apply to the nested context

        Example:
            >>> Fields._extract_nested_temp_fields(['id', 'products { id }', 'board { id }'], 'products')
            ['id']
            >>> Fields._extract_nested_temp_fields(['id', 'products { id kind }'], 'products')
            ['id', 'kind']
        """
        nested_fields = []

        for field in temp_fields:
            # Check if this temp field is for the specific parent
            if field.startswith(f'{parent_field} {{'):
                # Extract the content inside the braces
                content_start = field.find('{') + 1
                content_end = field.rfind('}')
                if content_start > 0 and content_end > content_start:
                    nested_content = field[content_start:content_end].strip()
                    # Split the nested content into individual fields
                    nested_fields.extend(nested_content.split())
            elif not '{' in field:
                # Top-level fields that should be available in all contexts
                nested_fields.append(field)

        return nested_fields

    @staticmethod
    def _parse_args(args_str: str) -> dict[str, Any]:
        """
        Parse GraphQL arguments string into a dictionary.

        Args:
            args_str: String containing GraphQL arguments

        Returns:
            Dictionary of parsed arguments with their types and values

        Example:
            >>> fields = Fields('')
            >>> fields._parse_args('(limit: 10, ids: ["123", "456"])')
            {'limit': 10, 'ids': [('string', '123'), ('string', '456')]}
        """
        args_dict = {}
        content = args_str.strip('()').strip()
        if not content:
            return args_dict

        parts = []
        current = []
        in_array = 0
        in_quotes = False

        for char in content:
            if char == '[':
                in_array += 1
                current.append(char)
            elif char == ']':
                in_array -= 1
                current.append(char)
            elif char == '"':
                in_quotes = not in_quotes
                current.append(char)
            elif char == ',' and not in_array and not in_quotes:
                parts.append(''.join(current).strip())
                current = []
            else:
                current.append(char)

        if current:
            parts.append(''.join(current).strip())

        for part in parts:
            if ':' in part:
                key, value = [x.strip() for x in part.split(':', 1)]
                if value.startswith('[') and value.endswith(']'):
                    # Handle arrays
                    parsed_values = []
                    nested_value = value[1:-1].strip()
                    if nested_value:
                        in_array = 0
                        in_quotes = False
                        current = []

                        for char in nested_value:
                            if char == '[':
                                in_array += 1
                                if in_array == 1:
                                    current = ['[']
                                else:
                                    current.append(char)
                            elif char == ']':
                                in_array -= 1
                                if in_array == 0:
                                    current.append(']')
                                    parsed_values.append(('array', ''.join(current)))
                                    current = []
                            elif char == '"':
                                in_quotes = not in_quotes
                                current.append(char)
                            elif char == ',' and not in_array and not in_quotes:
                                if current:
                                    val = ''.join(current).strip()
                                    if val.startswith('"') and val.endswith('"'):
                                        parsed_values.append(('string', val.strip('"')))
                                    elif val.isdigit():
                                        parsed_values.append(('number', int(val)))
                                    else:
                                        parsed_values.append(('string', val))
                                    current = []
                            else:
                                current.append(char)

                        if current:
                            val = ''.join(current).strip()
                            if val.startswith('"') and val.endswith('"'):
                                parsed_values.append(('string', val.strip('"')))
                            elif val.isdigit():
                                parsed_values.append(('number', int(val)))
                            else:
                                parsed_values.append(('string', val))

                    args_dict[key] = parsed_values
                elif value.lower() in ('true', 'false'):
                    args_dict[key] = value.lower() == 'true'
                elif value.startswith('"') and value.endswith('"'):
                    args_dict[key] = value[1:-1]
                elif value.isdigit():
                    args_dict[key] = int(value)
                else:
                    try:
                        args_dict[key] = float(value)
                    except ValueError:
                        args_dict[key] = value

        return args_dict

    @staticmethod
    def _format_value(value: Any) -> str:
        """
        Format a value for GraphQL argument representation.

        Args:
            value: The value to format (can be list, bool, str, or other types)

        Returns:
            Formatted string representation suitable for GraphQL arguments
        """
        if isinstance(value, list):
            formatted = []
            for val_type, val in value:
                if val_type == 'string':
                    formatted.append(f'"{val}"')
                elif val_type == 'array':
                    formatted.append(val)
                else:
                    formatted.append(str(val))
            return f'[{", ".join(formatted)}]'
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, str):
            return f'"{value}"'
        return str(value)

    @staticmethod
    def _validate_fields(fields_str: str) -> None:
        """
        Validate the field string format according to GraphQL rules.

        Args:
            fields_str: String containing fields to validate

        Raises:
            ValueError: If the field string is malformed
        """
        # Remove whitespace for easier parsing
        fields_str = fields_str.strip()
        if not fields_str:
            return

        # Track brace matching and current field
        brace_count = 0
        current_field = []
        last_field = []

        for i, char in enumerate(fields_str):

            if char == '{':
                current_field_str = ''.join(last_field).strip()
                if not current_field_str:
                    raise ValueError('Selection set must be preceded by a field name')
                brace_count += 1
                current_field = []
            elif char == '}':
                brace_count -= 1
                if brace_count < 0:
                    raise ValueError('Unmatched closing brace')
                current_field = []
                last_field = []
            elif char.isspace():
                if current_field:  # Only update last_field if current_field is not empty
                    last_field = current_field.copy()
                current_field = []
            else:
                current_field.append(char)
                if not char.isspace():  # If not a space, update last_field
                    last_field = current_field.copy()

            # Check for invalid selection sets
            if i < len(fields_str) - 1:
                next_char = fields_str[i + 1]
                if char == '}' and next_char == '{':
                    raise ValueError('Invalid syntax: multiple selection sets for single field')

        if brace_count != 0:
            raise ValueError('Unmatched braces in field string')

    # Private methods (in logical order)
    def _parse_fields(self, fields_str: str) -> list[str]:
        """
        Parse a GraphQL field string into individual field components.

        Args:
            fields_str: String containing GraphQL fields with optional arguments and nested structures

        Returns:
            List of parsed field strings, each representing a complete field with arguments and nested content
        """
        fields = []
        i = 0
        n = len(fields_str)
        while i < n:
            # Skip whitespace
            while i < n and fields_str[i].isspace():
                i += 1
            if i >= n:
                break
            start = i
            # Read field name
            while i < n and not fields_str[i].isspace() and fields_str[i] not in '({':
                i += 1
            field_name = fields_str[start:i].strip()
            # Skip whitespace after field name
            while i < n and fields_str[i].isspace():
                i += 1
            # Check for arguments
            args_str = ''
            if i < n and fields_str[i] == '(':
                paren_start = i
                depth = 1
                i += 1
                while i < n and depth > 0:
                    if fields_str[i] == '(':
                        depth += 1
                    elif fields_str[i] == ')':
                        depth -= 1
                    i += 1
                args_str = fields_str[paren_start:i]
                if not args_str.endswith(')'):
                    args_str += ')'
                # Skip all whitespace (including newlines) after arguments
                while i < n and fields_str[i].isspace():
                    i += 1
            # Check for selection set
            if i < n and fields_str[i] == '{':
                brace_depth = 1
                i += 1
                nested_start = i
                while i < n and brace_depth > 0:
                    if fields_str[i] == '{':
                        brace_depth += 1
                    elif fields_str[i] == '}':
                        brace_depth -= 1
                    i += 1
                nested_content = fields_str[nested_start:i - 1].strip()
                # Preserve original spacing around parentheses
                if args_str:
                    field = f'{field_name} {args_str} {{ {nested_content} }}'
                else:
                    field = f'{field_name} {{ {nested_content} }}'
                fields.append(field)
            else:
                # Preserve original spacing around parentheses
                if args_str:
                    field = f'{field_name} {args_str}'
                else:
                    field = field_name
                if field.strip():
                    fields.append(field)
        return fields

    def _deduplicate_nested_fields(self, fields_str: str) -> str:
        """
        Deduplicate nested field structures while preserving order.

        Args:
            fields_str: String containing fields that may have duplicates

        Returns:
            Deduplicated field string with nested structures preserved
        """
        parsed_fields = self._parse_fields(fields_str)
        seen = {}
        field_pattern = re.compile(r'^(\w+)(\([^)]*\))?(\s*\{.*\})?$')
        for field in parsed_fields:
            match = field_pattern.match(field.strip())
            if not match:
                base_name = field.strip()
                args = ''
                selection = ''
            else:
                base_name = match.group(1)
                args = match.group(2) or ''
                selection = match.group(3) or ''
            # If this field has a selection set, recursively deduplicate
            if selection:
                nested_content = self._extract_nested_content(field)
                dedup_nested = self._deduplicate_nested_fields(nested_content)
                seen[base_name] = f'{base_name}{args} {{ {dedup_nested} }}'
            else:
                seen[base_name] = f'{base_name}{args}'
        result = ' '.join(seen.values())
        return result

    def _merge_field_structures(self, field1: str, field2: str) -> str:
        """
        Merge two field structures, combining arguments and nested content.

        Args:
            field1: First field string to merge
            field2: Second field string to merge

        Returns:
            Merged field string with combined arguments and nested content
        """
        base1 = field1.split(' {')[0].strip()
        base2 = field2.split(' {')[0].strip()
        # Extract arguments if present
        args1 = ''
        args2 = ''
        if '(' in base1:
            base1, args1 = base1.split('(', 1)
            args1 = '(' + args1
        if '(' in base2:
            base2, args2 = base2.split('(', 1)
            args2 = '(' + args2
        # Use the full field strings for canonical order
        merged_args = self._merge_args(args1, args2, field1, field2)
        # Extract nested content
        nested1 = self._extract_nested_content(field1)
        nested2 = self._extract_nested_content(field2)
        # Merge nested content recursively
        if nested1 and nested2:
            merged_nested = self._deduplicate_nested_fields(f'{nested1} {nested2}')
        elif nested1:
            merged_nested = self._deduplicate_nested_fields(nested1)
        elif nested2:
            merged_nested = self._deduplicate_nested_fields(nested2)
        else:
            merged_nested = ''
        # Build result
        result = base1
        if merged_args:
            result += merged_args
        if merged_nested:
            result += f' {{ {merged_nested} }}'
        return result

    def _extract_nested_content(self, field: str) -> str:
        """
        Extract the content inside nested braces.

        Args:
            field: Field string containing nested content

        Returns:
            Content between the outermost braces, or empty string if no braces found

        Example:
            >>> fields = Fields('')
            >>> fields._extract_nested_content('board { id name }')
            'id name'
        """
        start = field.find('{')
        if start == -1:
            return ''

        # Count braces to handle nested structures
        count = 1
        start += 1
        for i in range(start, len(field)):
            if field[i] == '{':
                count += 1
            elif field[i] == '}':
                count -= 1
                if count == 0:
                    return field[start:i].strip()
        return ''

    def _process_nested_content(self, content: str) -> str:
        """
        Process and deduplicate nested field structures recursively.

        Args:
            content: String containing nested field structures

        Returns:
            Processed and deduplicated field string

        Example:
            >>> fields = Fields('')
            >>> fields._process_nested_content('id name board { id id name }')
            'id name board { id name }'
        """
        # Quick check for simple fields without nesting or arguments
        if not any(char in content for char in '{}()'):
            # Simple list of fields
            unique_fields = []
            for field in content.split():
                if field not in unique_fields:
                    unique_fields.append(field)
            return ' '.join(unique_fields)

        content = ' '.join(content.split())
        if not content:
            return ''

        # Handle potential GraphQL fragments first
        if content.startswith('...'):
            return content

        # Check if this is a field with arguments and/or nested content
        field_name = content.split(' ', maxsplit=1)[0].split('(')[0]
        rest_of_content = content[len(field_name):].strip()

        # Extract arguments if present
        args = ''
        if rest_of_content.startswith('('):
            paren_count = 1
            i = 1
            while i < len(rest_of_content) and paren_count > 0:
                if rest_of_content[i] == '(':
                    paren_count += 1
                elif rest_of_content[i] == ')':
                    paren_count -= 1
                i += 1
            args = rest_of_content[:i]
            rest_of_content = rest_of_content[i:].strip()

        # Extract nested content if present
        nested_content = ''
        if rest_of_content.startswith('{'):
            brace_count = 1
            i = 1
            while i < len(rest_of_content) and brace_count > 0:
                if rest_of_content[i] == '{':
                    brace_count += 1
                elif rest_of_content[i] == '}':
                    brace_count -= 1
                i += 1
            nested_content = rest_of_content[:i]
            rest_of_content = rest_of_content[i:].strip()

        # Process nested content recursively if present
        if nested_content:
            # Extract inner content between braces
            inner_content = nested_content[1:-1].strip()
            # If the inner content itself starts with a brace, flatten it
            if inner_content.startswith('{') and inner_content.endswith('}'):
                inner_content = inner_content[1:-1].strip()
            processed_inner = self._process_nested_content(inner_content)
            nested_content = f'{{ {processed_inner} }}'

        # Build the processed field
        processed_field = field_name
        if args:
            processed_field += args
        if nested_content:
            processed_field += f' {nested_content}'

        # Process any remaining content as separate fields
        if rest_of_content:
            additional_fields = self._process_nested_content(rest_of_content)
            return f'{processed_field} {additional_fields}'

        return processed_field

    def _parse_structure(self, s: str, start: int) -> tuple[int, str]:
        """
        Parse a nested structure starting from a given position.

        Args:
            s: String containing the structure to parse
            start: Starting position in the string

        Returns:
            Tuple containing (end position, processed content)

        Example:
            >>> fields = Fields('')
            >>> fields._parse_structure('{ id name }', 0)
            (11, ' id name ')
        """
        brace_count = 1
        pos = start
        while pos < len(s) and brace_count > 0:
            if s[pos] == '{':
                brace_count += 1
            elif s[pos] == '}':
                brace_count -= 1
            pos += 1
        return pos, s[start:pos - 1]

    def _extract_arg_keys_and_array_values_in_order(self, field_str: str) -> tuple[list[str], dict[str, list[Any]]]:
        """
        Extract the order of argument keys and array values from the full field string.

        Args:
            field_str: The field string to parse for arguments

        Returns:
            Tuple of (list of argument keys in order, dict of key -> list of array values in order)
        """
        arg_keys = []
        array_values = {}
        seen_keys = set()
        # Find all argument lists in the field string
        for match in re.finditer(r'\(([^)]*)\)', field_str):
            args_content = match.group(1)
            # Split by comma, but handle nested brackets/quotes
            i = 0
            n = len(args_content)
            while i < n:
                # Skip whitespace
                while i < n and args_content[i].isspace():
                    i += 1
                if i >= n:
                    break
                # Find key
                key_start = i
                while i < n and args_content[i] != ':':
                    i += 1
                if i >= n:
                    break
                key = args_content[key_start:i].strip()
                if key and key not in seen_keys:
                    arg_keys.append(key)
                    seen_keys.add(key)
                i += 1  # skip ':'
                # Now parse the value
                value_start = i
                bracket = 0
                brace = 0
                paren = 0
                in_quotes = False
                while i < n:
                    c = args_content[i]
                    if c == '"' and (i == 0 or args_content[i - 1] != '\\'):
                        in_quotes = not in_quotes
                    elif not in_quotes:
                        if c == '[':
                            bracket += 1
                        elif c == ']':
                            bracket -= 1
                        elif c == '{':
                            brace += 1
                        elif c == '}':
                            brace -= 1
                        elif c == '(':
                            paren += 1
                        elif c == ')':
                            paren -= 1
                        elif c == ',' and bracket == 0 and brace == 0 and paren == 0:
                            break
                    i += 1
                value = args_content[value_start:i].strip()
                # If value is an array, extract its values
                if value.startswith('['):
                    # Use a simple eval for array values (safe because only used for order)
                    try:
                        arr = ast.literal_eval(value)
                        if isinstance(arr, list):
                            if key not in array_values:
                                array_values[key] = []
                            for v in arr:
                                if v not in array_values[key]:
                                    array_values[key].append(v)
                    except Exception:  # pylint: disable=broad-exception-caught
                        pass
                # Skip comma
                if i < n and args_content[i] == ',':
                    i += 1
        return arg_keys, array_values

    def _merge_args(self, args1: str, args2: str, field_str1: str = '', field_str2: str = '') -> str:
        """
        Merge two sets of GraphQL field arguments, preserving order of first appearance.

        Args:
            args1: First argument string to merge
            args2: Second argument string to merge
            field_str1: First field string for order determination
            field_str2: Second field string for order determination

        Returns:
            Merged argument string preserving order of first appearance
        """
        if not args1:
            return args2
        if not args2:
            return args1

        # Parse both argument strings
        args1_dict = self._parse_args(args1)
        args2_dict = self._parse_args(args2)

        # Use the order from the concatenated field strings
        concat_fields = (field_str1 or '') + ' ' + (field_str2 or '')
        arg_keys, _ = self._extract_arg_keys_and_array_values_in_order(concat_fields)
        seen = set()
        ordered_keys = []
        for key in arg_keys:
            if key not in seen:
                ordered_keys.append(key)
                seen.add(key)

        # Merge arguments using the order of first appearance
        merged = {}
        for key in ordered_keys:
            v1 = args1_dict.get(key)
            v2 = args2_dict.get(key)

            if isinstance(v1, list) and isinstance(v2, list):
                merged_list = self._merge_arrays_preserving_order(v1, v2, concat_fields, concat_fields, key=str(key))
                merged[key] = merged_list
            elif v1 is not None and v2 is not None and v1 != v2:
                merged[key] = v2
            elif v1 is not None:
                merged[key] = v1
            else:
                merged[key] = v2

        if merged:
            formatted_args = [f'{key}: {self._format_value(merged[key])}' for key in ordered_keys]
            return f'({", ".join(formatted_args)})'
        return ''

    def _merge_arrays_preserving_order(self, arr1: list[Any], arr2: list[Any], field_str1: str = '', field_str2: str = '', key: str = '') -> list[Any]:
        """
        Merge two arrays, preserving the order of first appearance in the full field string.

        Args:
            arr1: First array of tuples (type, value)
            arr2: Second array of tuples (type, value)
            field_str1: First field string for order determination
            field_str2: Second field string for order determination
            key: Key name for array order lookup

        Returns:
            Merged array of tuples (type, value) preserving order
        """
        seen = set()
        merged = []
        # Use the order from the concatenated field strings
        concat_fields = (field_str1 or '') + ' ' + (field_str2 or '')
        _, arr_order = self._extract_arg_keys_and_array_values_in_order(concat_fields)
        order = arr_order.get(key, [])
        for v in order:
            v_key = str(v)
            if v_key not in seen:
                merged.append(('string', v) if isinstance(v, str) else ('int', v))
                seen.add(v_key)
        # Add any remaining from arr1 and arr2
        for arr in (arr1, arr2):
            for v in arr:
                v_key = str(v[1])
                if v_key not in seen:
                    merged.append(v)
                    seen.add(v_key)
        return merged
