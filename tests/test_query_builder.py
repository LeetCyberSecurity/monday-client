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

"""Tests for GraphQL query building utilities."""

import pytest

from monday.exceptions import QueryFormatError
from monday.services.utils.query_builder import (build_graphql_query,
                                                 build_query_params_string,
                                                 convert_numeric_args,
                                                 map_hex_to_color)


def test_convert_numeric_args_basic():
    """Test basic numeric conversion functionality."""
    args = {
        'id': '123',
        'name': 'test',
        'active': True,
        'empty': None
    }
    result = convert_numeric_args(args)
    assert result == {
        'id': 123,
        'name': 'test',
        'active': True
    }


def test_convert_numeric_args_lists():
    """Test numeric conversion with list values."""
    args = {
        'ids': ['1', '2', '3'],
        'names': ['test1', 'test2'],
        'mixed': ['1', None, 'test', '4']
    }
    result = convert_numeric_args(args)
    assert result == {
        'ids': [1, 2, 3],
        'names': ['test1', 'test2'],
        'mixed': [1, 'test', 4]
    }


def test_convert_numeric_args_complex():
    """Test numeric conversion with complex nested structures."""
    args = {
        'id': '123',
        'values': ['1', '2', None, 'text'],
        'flag': True,
        'none_value': None,
        'text': 'not_a_number'
    }
    result = convert_numeric_args(args)
    assert result == {
        'id': 123,
        'values': [1, 2, 'text'],
        'flag': True,
        'text': 'not_a_number'
    }


@pytest.mark.parametrize('query_type,operation,args,expected', [
    (
        'query',
        'items',
        {'ids': [1, 2], 'fields': 'id name'},
        '\n        query {\n            items (ids: [1, 2]) \n                { id name }\n        }\n    '
    ),
    (
        'mutation',
        'create_item',
        {'board_id': 123, 'item_name': 'Test', 'fields': 'id'},
        '\n        mutation {\n            create_item (board_id: 123, item_name: "Test") \n                { id }\n        }\n    '
    ),
    (
        'query',
        'boards',
        {'kind': 'public', 'fields': 'id name'},
        '\n        query {\n            boards (kind: public) \n                { id name }\n        }\n    '
    )
])
def test_build_graphql_query(query_type, operation, args, expected):
    """Test building GraphQL queries with various parameters."""
    result = build_graphql_query(operation, query_type, args)
    assert result == expected


def test_build_graphql_query_with_columns():
    """Test building GraphQL query with column mappings."""
    args = {
        'columns': [
            {'column_id': 'status', 'column_values': ['Done', 'In Progress']},
            {'column_id': 'text', 'title': 'Description'}
        ],
        'fields': 'id name'
    }
    result = build_graphql_query('create_item', 'mutation', args)
    assert 'column_id: "status"' in result
    assert 'column_values: ["Done", "In Progress"]' in result
    assert 'column_id: "text"' in result
    assert 'title: "Description"' in result


def test_build_graphql_query_with_columns_mapping():
    """Test building GraphQL query with columns mapping."""
    args = {
        'columns_mapping': {
            'old_status': 'new_status',
            'old_text': 'new_text'
        },
        'fields': 'id'
    }
    result = build_graphql_query('move_item', 'mutation', args)
    assert '{source: "old_status", target: "new_status"}' in result
    assert '{source: "old_text", target: "new_text"}' in result


@pytest.mark.parametrize('query_params,expected_contains', [
    (
        {'rules': [{'column_id': 'status', 'operator': 'eq', 'compare_value': ['Done']}]},
        'rules: [{column_id: "status", operator: eq, compare_value: ["Done"]}]'
    ),
    (
        {'operator': 'and', 'rules': []},
        'operator: and'
    ),
    (
        {'order_by': {'column_id': 'date', 'direction': 'desc'}},
        'order_by: {column_id: "date", direction: desc}'
    ),
    (
        {'ids': '[1, 2, 3]'},
        'ids: [1, 2, 3]'
    )
])
def test_build_query_params_string(query_params, expected_contains):
    """Test building query parameter strings."""
    result = build_query_params_string(query_params)
    assert expected_contains in result


def test_build_query_params_string_complex():
    """Test building complex query parameter strings."""
    query_params = {
        'rules': [
            {
                'column_id': 'status',
                'operator': 'eq',
                'compare_value': ['Done', 'In Progress']
            },
            {
                'compare_attribute': 'date',
                'operator': 'greater_than',
                'compare_value': ['2024-01-01']
            }
        ],
        'operator': 'and',
        'order_by': {
            'column_id': 'priority',
            'direction': 'desc'
        }
    }
    result = build_query_params_string(query_params)
    assert 'rules: [' in result
    assert 'operator: and' in result
    assert 'order_by: {' in result
    assert 'direction: desc' in result


def test_build_query_params_string_empty():
    """Test building query parameter string with empty input."""
    assert build_query_params_string({}) == ""
    assert build_query_params_string(None) == ""


@pytest.mark.parametrize('color,expected', [
    ('#ff5ac4', 'light-pink'),
    ('#ff158a', 'dark-pink'),
    ('#e2445c', 'red'),
    ('#00c875', 'green'),
    ('#579bfc', 'blue'),
    ('#c4c4c4', 'grey')
])
def test_map_color_to_hex_valid(color, expected):
    """Test mapping valid color hex codes to names."""
    assert map_hex_to_color(color) == expected


def test_map_color_to_hex_invalid():
    """Test mapping invalid color hex codes."""
    with pytest.raises(QueryFormatError) as exc_info:
        map_hex_to_color('#invalid')
    assert 'Invalid color hex #invalid' in str(exc_info.value)


def test_map_color_to_hex_unmapped():
    """Test mapping unmapped hex codes."""
    with pytest.raises(QueryFormatError) as exc_info:
        map_hex_to_color('#cab641')
    assert 'currently not mapped' in str(exc_info.value)


def test_build_graphql_query_with_boolean_values():
    """Test building GraphQL query with boolean values."""
    args = {
        'include_archived': True,
        'exclude_nonactive': False,
        'fields': 'id name'
    }
    result = build_graphql_query('items', 'query', args)
    assert 'include_archived: true' in result
    assert 'exclude_nonactive: false' in result


def test_build_graphql_query_with_enum_fields():
    """Test building GraphQL query with enum fields."""
    args = {
        'board_kind': 'public',
        'state': 'active',
        'fields': 'id name'
    }
    result = build_graphql_query('boards', 'query', args)
    assert 'board_kind: public' in result  # No quotes around enum
    assert 'state: active' in result  # No quotes around enum


def test_convert_numeric_args_edge_cases():
    """Test numeric conversion with edge cases."""
    args = {
        'zero': '0',
        'negative': '-123',
        'float_str': '123.45',
        'bool_str': 'true',
        'empty_list': [],
        'mixed_list': ['0', '-1', 'text', True]
    }
    result = convert_numeric_args(args)
    assert result['zero'] == 0
    assert result['negative'] == -123
    assert result['float_str'] == '123.45'  # Should remain string
    assert result['bool_str'] == 'true'  # Should remain string
    assert result['empty_list'] == []
    assert result['mixed_list'] == [0, -1, 'text', True]
