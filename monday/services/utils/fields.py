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
Utilities for handling GraphQL field combinations.

This module provides the Fields class for managing GraphQL field strings in a structured way.
It handles field parsing, combination, and deduplication while maintaining field order and
nested structure integrity.

Example:
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

import logging
from typing import Union


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

        Args:
            fields: Either a space-separated string of field names or another Fields instance. Can include nested structures using GraphQL syntax.

        Raises:
            ValueError: If the field string is malformed

        Example:
            >>> fields = Fields('id name items { id title }')  # Valid
            >>> fields = Fields('item { id } { name }')  # Raises ValueError
        """
        # If fields is already a Fields instance, extract its field list
        if isinstance(fields, Fields):
            self.fields = fields.fields.copy()  # Make a copy to prevent shared state
        else:
            # Validate fields before parsing
            self._validate_fields(str(fields))
            # Convert field string to list of individual fields
            self.fields = self._parse_fields(str(fields))

    def __str__(self) -> str:
        """
        Convert back to a GraphQL-compatible field string.

        Returns:
            Space-separated string of fields in their original order.

        Example:
            >>> fields = Fields('id name items { id title }')
            >>> str(fields)
            'id name items { id title }'
        """
        return ' '.join(self.fields)  # No sorting, maintain order

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

        # Concatenate the fields lists
        combined = self.fields + other.fields

        return Fields(' '.join(combined))

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
                base_field = field.split(' {')[0]

                # Find corresponding field in other
                other_field = next((f for f in other.fields if f.startswith(f"{base_field} {{")
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
                            result_fields.append(f"{base_field} {{ {str(diff_nested)} }}")
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
        """
        # Only add temp fields that aren't already present
        new_fields = [f for f in temp_fields if f not in self.fields]

        # Add temp fields
        all_fields = self.fields + new_fields

        return Fields(' '.join(all_fields))

    @staticmethod
    def manage_temp_fields(
        data: Union[dict, list],
        original_fields: Union[str, set, 'Fields'],
        temp_fields: list[str]
    ) -> Union[dict, list]:
        """
        Remove temporary fields from query results that weren't in original fields.

        Args:
            data: Query result data
            original_fields: Space-separated string, set of field names, or Fields object
            temp_fields: List of field names that were temporarily added

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

        # Find which temp fields weren't in original fields
        fields_to_remove = set(temp_fields) - set(field_structure.keys())

        if not fields_to_remove:
            return data

        if isinstance(data, list):
            return [Fields.manage_temp_fields(item, fields_obj, temp_fields) for item in data]

        if isinstance(data, dict):
            result = {}
            for k, v in data.items():
                # Skip temporary fields
                if k in fields_to_remove:
                    continue
                # Skip fields not in original structure
                if k not in field_structure:
                    continue
                # Handle nested structures
                if isinstance(v, (dict, list)) and field_structure[k] is not None:
                    result[k] = Fields.manage_temp_fields(v, field_structure[k], temp_fields)
                else:
                    result[k] = v
            return result

        return data

    def _parse_fields(self, fields_str: str) -> list[str]:
        """
        Parse a fields string into a list of normalized fields.

        Args:
            fields_str: String containing fields to parse

        Returns:
            List of normalized field strings

        Example:
            >>> fields = Fields('')
            >>> fields._parse_fields('id name board { id title }')
            ['id', 'name', 'board { id title }']
        """
        # First deduplicate the entire string
        fields_str = self._deduplicate_nested_fields(fields_str)

        fields = []
        i = 0
        current_field = []
        nested_level = 0
        in_args = False
        args_level = 0

        while i < len(fields_str):
            char = fields_str[i]

            if char == '(':
                if not in_args:
                    in_args = True
                args_level += 1
                current_field.append(char)
            elif char == ')':
                args_level -= 1
                current_field.append(char)
                if args_level == 0:
                    in_args = False
            elif char == '{':
                nested_level += 1
                current_field.append(char)
            elif char == '}':
                nested_level -= 1
                current_field.append(char)
            elif char.isspace() and nested_level == 0 and not in_args:
                # We're at a top-level space, complete the current field
                if current_field:
                    field = ''.join(current_field).strip()
                    if field:
                        fields.append(field)
                    current_field = []
            else:
                current_field.append(char)

            i += 1

        # Add any remaining field
        if current_field:
            field = ''.join(current_field).strip()
            if field:
                fields.append(field)

        return fields

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
        field_name = content.split(' ')[0].split('(')[0]
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
            processed_inner = self._process_nested_content(inner_content)
            nested_content = f"{{ {processed_inner} }}"

        # Build the processed field
        processed_field = field_name
        if args:
            processed_field += args
        if nested_content:
            processed_field += f" {nested_content}"

        # Process any remaining content as separate fields
        if rest_of_content:
            additional_fields = self._process_nested_content(rest_of_content)
            return f"{processed_field} {additional_fields}"

        return processed_field

    def _deduplicate_nested_fields(self, fields_str: str) -> str:
        """
        Deduplicate fields within a nested structure.

        Args:
            fields_str: String containing fields, potentially nested

        Returns:
            Deduplicated fields string

        Example:
            >>> fields = Fields('')
            >>> fields._deduplicate_nested_fields('id id name name board { id id }')
            'id name board { id }'
        """
        # Handle empty or whitespace-only strings
        if not fields_str.strip():
            return ''

        # Normalize whitespace and remove newlines
        fields_str = ' '.join(fields_str.split())

        # Parse fields as separate units to prevent incorrect nesting
        top_level_fields = []
        current_field = []
        i = 0
        nested_level = 0
        in_args = False
        args_level = 0

        while i < len(fields_str):
            char = fields_str[i]
            current_field.append(char)

            if char == '(':
                if not in_args:
                    in_args = True
                args_level += 1
            elif char == ')':
                args_level -= 1
                if args_level == 0:
                    in_args = False
            elif char == '{':
                nested_level += 1
            elif char == '}':
                nested_level -= 1
                # If we're back at top level, this field is complete
                if nested_level == 0 and not in_args:
                    # Add space to ensure we capture the entire field
                    if i + 1 < len(fields_str) and not fields_str[i + 1].isspace():
                        current_field.append(' ')
            elif char.isspace() and nested_level == 0 and not in_args:
                # At a space at top level, check if we have a complete field
                field = ''.join(current_field).strip()
                if field:
                    top_level_fields.append(field)
                    current_field = []

            i += 1

        # Add the last field if there is any
        if current_field:
            field = ''.join(current_field).strip()
            if field:
                top_level_fields.append(field)

        # Process each top-level field separately
        processed_fields = []
        for field in top_level_fields:
            processed = self._process_nested_content(field)
            if processed:
                processed_fields.append(processed)

        return ' '.join(processed_fields)

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

    @staticmethod
    def _parse_args(args_str: str) -> dict:
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
    def _format_value(value) -> str:
        """
        Format a value based on its type for GraphQL arguments.

        Args:
            value: Value to format (can be string, bool, number, or array)

        Returns:
            Formatted string representation of the value

        Example:
            >>> fields = Fields('')
            >>> fields._format_value([('string', 'test'), ('number', 123)])
            '["test", 123]'
            >>> fields._format_value(True)
            'true'
            >>> fields._format_value("test")
            '"test"'
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
            return f"[{', '.join(formatted)}]"
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, str):
            return f'"{value}"'
        return str(value)

    def _merge_args(self, args1: str, args2: str) -> str:
        """
        Merge two sets of GraphQL field arguments.

        Args:
            args1: First argument string
            args2: Second argument string

        Returns:
            Merged argument string with duplicates resolved

        Example:
            >>> fields = Fields('')
            >>> fields._merge_args('(limit: 10)', '(offset: 20)')
            '(limit: 10, offset: 20)'
            >>> fields._merge_args('(ids: ["1"])', '(ids: ["2"])')
            '(ids: ["1", "2"])'
        """
        if not args1:
            return args2
        if not args2:
            return args1

        # Parse both argument strings
        args1_dict = self._parse_args(args1)
        args2_dict = self._parse_args(args2)

        # Merge arguments
        merged = {}
        for key, value in args1_dict.items():
            if key in args2_dict:
                if isinstance(value, list) and isinstance(args2_dict[key], list):
                    # Combine arrays and remove duplicates while preserving order
                    merged[key] = []
                    seen = set()
                    # Process values from first array
                    for v in value:
                        val_key = (v[0], str(v[1]))
                        if val_key not in seen:
                            merged[key].append(v)
                            seen.add(val_key)
                    # Process values from second array
                    for v in args2_dict[key]:
                        val_key = (v[0], str(v[1]))
                        if val_key not in seen:
                            merged[key].append(v)
                            seen.add(val_key)
                else:
                    # Keep the last value for non-array arguments
                    merged[key] = args2_dict[key]
            else:
                merged[key] = value

        # Add remaining args from args2
        for key, value in args2_dict.items():
            if key not in merged:
                merged[key] = value

        # Format the merged arguments
        if merged:
            formatted_args = [f"{key}: {self._format_value(value)}" for key, value in merged.items()]
            return f"({', '.join(formatted_args)})"
        return ""
