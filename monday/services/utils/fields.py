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

import ast
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
        # Output deduplicated, merged field string
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
                            # Preserve arguments if they exist
                            args_start = field.find('(')
                            args_end = field.find(')')
                            if args_start != -1 and args_end != -1:
                                args = field[args_start:args_end + 1]
                                result_fields.append(f"{base_field}{args} {{ {str(diff_nested)} }}")
                            else:
                                result_fields.append(f"{base_field} {{ {str(diff_nested)} }}")
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
        """
        # Create a combined string with temp fields and let the parser handle merging
        temp_str = ' '.join(temp_fields)
        combined_str = str(self) + ' ' + temp_str
        return Fields(combined_str)

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
            # Read field name (and possible arguments)
            while i < n and not fields_str[i].isspace() and fields_str[i] != '{':
                if fields_str[i] == '(':  # handle arguments
                    depth = 1
                    i += 1
                    while i < n and depth > 0:
                        if fields_str[i] == '(':
                            depth += 1
                        elif fields_str[i] == ')':
                            depth -= 1
                        i += 1
                else:
                    i += 1
            end_field = i
            # Skip whitespace after field name
            while i < n and fields_str[i].isspace():
                i += 1
            # If next is a nested block, capture the whole block
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
                field = f'{fields_str[start:end_field].strip()} {{ {nested_content} }}'
                fields.append(field)
            else:
                field = fields_str[start:end_field].strip()
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
            # If the inner content itself starts with a brace, flatten it
            if inner_content.startswith('{') and inner_content.endswith('}'):
                inner_content = inner_content[1:-1].strip()
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
        parsed_fields = self._parse_fields(fields_str)
        seen = {}
        for field in parsed_fields:
            # Extract base field name and arguments
            base = field.split(' {')[0].strip()
            args = ''
            if '(' in base:
                base_name, args = base.split('(', 1)
                base_name = base_name.strip()
                args = '(' + args
            else:
                base_name = base
            # If this field has nested content, recursively deduplicate
            if '{' in field:
                nested_content = self._extract_nested_content(field)
                if base_name in seen:
                    # Merge arguments
                    prev_field = seen[base_name]
                    prev_args = ''
                    if '(' in prev_field:
                        _, prev_args = prev_field.split('(', 1)
                        prev_args = '(' + prev_args.split(')')[0] + ')'
                    # Pass full field strings for canonical order
                    merged_args = self._merge_args(args, prev_args, field, prev_field)
                    # Merge nested content recursively
                    prev_nested = self._extract_nested_content(prev_field)
                    merged_nested = self._deduplicate_nested_fields(f'{prev_nested} {nested_content}')
                    # Rebuild the field
                    seen[base_name] = f'{base_name}{merged_args} {{ {merged_nested} }}'
                else:
                    dedup_nested = self._deduplicate_nested_fields(nested_content)
                    seen[base_name] = f'{base_name}{args} {{ {dedup_nested} }}'
            else:
                if base_name in seen:
                    # Merge arguments for non-nested fields
                    prev_field = seen[base_name]
                    prev_args = ''
                    if '(' in prev_field:
                        _, prev_args = prev_field.split('(', 1)
                        prev_args = '(' + prev_args.split(')')[0] + ')'
                    # Pass full field strings for canonical order
                    merged_args = self._merge_args(args, prev_args, field, prev_field)
                    seen[base_name] = f'{base_name}{merged_args}'
                else:
                    seen[base_name] = f'{base_name}{args}'
        return ' '.join(seen.values())

    def _merge_field_structures(self, field1: str, field2: str) -> str:
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

    def _extract_arg_keys_and_array_values_in_order(self, field_str: str) -> tuple[list[str], dict[str, list]]:
        """
        Extract the order of argument keys and array values from the full field string.
        Returns a tuple: (list of argument keys in order, dict of key -> list of array values in order)
        """
        import re
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
        Merge two sets of GraphQL field arguments, preserving order of first appearance in the full field string.
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

    def _merge_arrays_preserving_order(self, arr1: list, arr2: list, field_str1: str = '', field_str2: str = '', key: str = '') -> list:
        """
        Merge two arrays, preserving the order of first appearance in the full field string.
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

    @staticmethod
    def _format_value(value) -> str:
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
