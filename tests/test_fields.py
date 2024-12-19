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

# pylint: disable=protected-access,redefined-outer-name

"""Comprehensive tests for Fields methods"""

import pytest

from monday.services.utils.fields import Fields


def test_basic_field_initialization():
    """Test basic field initialization with simple fields."""
    fields = Fields('id name description')
    assert str(fields) == 'id name description'
    assert 'id' in fields
    assert 'name' in fields
    assert 'description' in fields
    assert 'nonexistent' not in fields
    fields2 = Fields('id name creator { id email name } owners { id email name } subscribers { id email name }')
    assert str(fields2) == 'id name creator { id email name } owners { id email name } subscribers { id email name }'


def test_nested_field_initialization():
    """Test initialization with nested fields."""
    fields = Fields('id name items { id title description }')
    assert str(fields) == 'id name items { id title description }'
    assert 'items' in fields


def test_field_combination():
    """Test combining fields using + operator."""
    fields1 = Fields('id name')
    fields2 = Fields('description')
    combined = fields1 + fields2
    assert str(combined) == 'id name description'


def test_string_addition():
    """Test adding a string to Fields instance."""
    fields = Fields('id name') + 'description'
    assert str(fields) == 'id name description'


def test_nested_addition():
    """Test adding with nested Fields instances."""
    fields = Fields('id name items { id }') + 'items { id name description }'
    fields2 = Fields('id name items { id }') + Fields('items { id name description }')
    assert str(fields) == str(fields2) == 'id name items { id name description }'


def test_args_addition():
    """Test adding args in Fields instances."""
    fields = Fields('id name items (ids: [[1], 2, 2]) { id column_values (ids: ["1"], arg: true, arg: true) { id } }') + 'items (ids: [1, 2]) { id name column_values (ids: ["2"], arg2: false) { id } description }' + 'items (ids: [3, [4]]) { column_values (ids: [["3"], "4"]) { status } text }'
    assert str(fields) == 'id name items (ids: [[1], 2, 1, 3, [4]]) { id column_values (ids: ["1", "2", ["3"], "4"], arg: true, arg2: false) { id status } name description text }'


def test_field_deduplication():
    """Test that duplicate fields are removed."""
    fields = Fields('id name id description name')
    assert str(fields) == 'id name description'


def test_nested_field_deduplication():
    """Test deduplication in nested structures."""
    fields = Fields('id items { id title id } id')
    assert str(fields) == 'id items { id title }'


def test_equality():
    """Test equality comparison between Fields instances."""
    fields1 = Fields('id name')
    fields2 = Fields('id name')
    fields3 = Fields('id description')

    assert fields1 == fields2
    assert fields1 != fields3


@pytest.mark.parametrize('invalid_input', [
    'item { id } { name }',      # Multiple selection sets
    'id name {',                 # Unclosed brace
    'id name }',                 # Unopened brace
    '{ id name }',               # Selection set without field name
    'id name { text column { id }'  # Nested unclosed brace
])
def test_invalid_field_strings(invalid_input):
    """Test that invalid field strings raise ValueError."""
    with pytest.raises(ValueError):
        Fields(invalid_input)


def test_complex_nested_structures():
    """Test handling of complex nested structures."""
    complex_fields = Fields('''
        id 
        name 
        groups (ids: ["1", "2", "3"]) { 
            id 
            title 
            users { 
                id 
                name 
                email 
                account {
                    id
                    team {
                        name
                        name        
                    }
                    team {
                        id
                        text {
                            text
                            name    
                        }
                    }            
                }
            } 
            id
            board { 
                id 
                name 
                id
                users {
                    id
                    name 
                    email      
                }
                items {
                    id
                    name
                    column_values {
                        column (ids: ["1", "2"]) {
                            title
                            id    
                        }
                        column (ids: ["1", "2", "3"]) {
                            title
                            id
                            name    
                        }
                        text
                    }
                }
            } 
        }
        groups (ids: ["3", "4"]) {
            text
            status
            id
        }
        archived
        id
    ''')
    assert 'groups' in complex_fields
    assert 'board' in complex_fields
    assert 'items' in complex_fields
    assert 'column_values' in complex_fields
    assert 'column' in complex_fields
    assert 'account' in complex_fields
    assert 'team' in complex_fields
    assert str(complex_fields) == 'id name groups (ids: ["1", "2", "3", "4"]) { id title users { id name email account { id team { name id text { text name } } } } board { id name users { id name email } items { id name column_values { column (ids: ["1", "2", "3"]) { title id name } text } } } text status } archived'


def test_empty_fields():
    """Test handling of empty field strings."""
    fields = Fields('')
    assert str(fields) == ''
    assert Fields('  ') == Fields('')


def test_fields_copy():
    """Test that creating Fields from another Fields instance creates a copy."""
    original = Fields('id name')
    copy = Fields(original)

    assert original == copy
    assert original is not copy
    assert original.fields is not copy.fields


def test_contains_with_spaces():
    """Test field containment with various space configurations."""
    fields = Fields('id name description')
    assert 'name' in fields
    assert ' name ' in fields
    assert 'name ' in fields
    assert ' name' in fields


def test_basic_field_subtraction():
    """Test basic field subtraction with simple fields."""
    fields1 = Fields('id name description')
    fields2 = Fields('name')
    result = fields1 - fields2
    assert str(result) == 'id description'


def test_string_subtraction():
    """Test subtracting a string from Fields instance."""
    fields = Fields('id name description')
    result = fields - 'name'
    assert str(result) == 'id description'


def test_nested_field_subtraction():
    """Test subtraction with nested fields."""
    fields1 = Fields('id name items { id title description }')
    fields2 = Fields('items { title }')
    result = fields1 - fields2
    assert str(result) == 'id name items { id description }'


def test_complex_nested_subtraction():
    """Test subtraction with complex nested structures."""
    fields1 = Fields('''
        id
        name
        groups {
            id
            title
            users {
                id
                name
                email
            }
        }
    ''')
    fields2 = Fields('groups { users { email name } title }')
    result = fields1 - fields2
    assert str(result) == 'id name groups { id users { id } }'


def test_complete_nested_removal():
    """Test removing an entire nested structure."""
    fields1 = Fields('id name groups { id title users { id name } }')
    fields2 = Fields('groups')
    result = fields1 - fields2
    assert str(result) == 'id name'


def test_multiple_nested_subtraction():
    """Test subtraction with multiple nested levels."""
    fields1 = Fields('''
        id
        items {
            id
            name
            column_values {
                id
                text
                value
            }
        }
    ''')
    fields2 = Fields('items { column_values { text value } }')
    result = fields1 - fields2
    assert str(result) == 'id items { id name column_values { id } }'


def test_subtraction_with_nonexistent_fields():
    """Test subtracting fields that don't exist."""
    fields1 = Fields('id name description')
    fields2 = Fields('nonexistent other_field')
    result = fields1 - fields2
    assert str(result) == 'id name description'


def test_empty_subtraction():
    """Test subtracting empty fields."""
    fields1 = Fields('id name description')
    fields2 = Fields('')
    result = fields1 - fields2
    assert str(result) == 'id name description'


def test_subtraction_to_empty():
    """Test subtracting all fields."""
    fields1 = Fields('id name')
    fields2 = Fields('id name')
    result = fields1 - fields2
    assert str(result) == ''


def test_nested_partial_subtraction():
    """Test partial subtraction of nested fields while preserving structure."""
    fields1 = Fields('''
        id
        board {
            id
            name
            items {
                id
                title
                description
            }
        }
    ''')
    fields2 = Fields('board { items { title } }')
    result = fields1 - fields2
    assert str(result) == 'id board { id name items { id description } }'


def test_add_temp_fields():
    """Test adding temporary fields."""
    fields = Fields('id name')
    temp_fields = ['temp1', 'temp2']
    result = fields.add_temp_fields(temp_fields)
    assert str(result) == 'id name temp1 temp2'

    # Test with duplicate fields
    fields = Fields('id name temp1')
    result = fields.add_temp_fields(temp_fields)
    assert str(result) == 'id name temp1 temp2'

    fields = Fields('id name')
    temp_fields = ['temp1', 'field { temp2 }', 'name { user id { account } }']
    result = fields.add_temp_fields(temp_fields)
    assert str(result) == 'id name { user id { account } } temp1 field { temp2 }'


def test_manage_temp_fields():
    """Test managing temporary fields in query results."""
    # Test with dict input
    data = {'id': 1, 'name': 'test', 'temp1': 'value1', 'temp2': 'value2'}
    original_fields = 'id name'
    temp_fields = ['temp1', 'temp2']
    result = Fields.manage_temp_fields(data, original_fields, temp_fields)
    assert result == {'id': 1, 'name': 'test'}

    # Test with list input
    data = [
        {'id': 1, 'name': 'test1', 'temp1': 'value1'},
        {'id': 2, 'name': 'test2', 'temp1': 'value2'}
    ]
    result = Fields.manage_temp_fields(data, original_fields, temp_fields)
    assert result == [
        {'id': 1, 'name': 'test1'},
        {'id': 2, 'name': 'test2'}
    ]

    # Test with nested structures
    data = {
        'id': 1,
        'name': 'test',
        'items': [
            {'id': 2, 'temp1': 'value1'},
            {'id': 3, 'temp1': 'value2'}
        ]
    }
    original_fields = 'id name items { id }'
    result = Fields.manage_temp_fields(data, original_fields, temp_fields)
    assert result == {
        'id': 1,
        'name': 'test',
        'items': [
            {'id': 2},
            {'id': 3}
        ]
    }

    # Test with Fields instance as original_fields
    original_fields = Fields('id name')
    result = Fields.manage_temp_fields(data, original_fields, temp_fields)
    assert result == {'id': 1, 'name': 'test'}

    data = {
        'id': 1,
        'field': {
            'temp2': 'value'
        },
        'name': {
            'user': 'value',
            'id': {'account': 'value'}
        }
    }
    original_fields = Fields('id name { user }')
    temp_fields = ['temp1', 'field { temp2 }', 'name { user id { account } }']
    result = Fields.manage_temp_fields(data, original_fields, temp_fields)
    assert result == {'id': 1, 'name': {'user': 'value'}}


def test_field_args_parsing():
    """Test handling of field arguments."""
    # Test basic arguments
    fields = Fields('items (limit: 10) { id }')
    assert str(fields) == 'items (limit: 10) { id }'

    # Test string arguments
    fields = Fields('items (name: "test") { id }')
    assert str(fields) == 'items (name: "test") { id }'

    # Test boolean arguments
    fields = Fields('items (active: true, archived: false) { id }')
    assert str(fields) == 'items (active: true, archived: false) { id }'

    # Test array arguments
    fields = Fields('items (ids: [1, 2, 3]) { id }')
    assert str(fields) == 'items (ids: [1, 2, 3]) { id }'

    # Test nested array arguments
    fields = Fields('items (ids: [[1, 2], [3, 4]]) { id }')
    assert str(fields) == 'items (ids: [[1, 2], [3, 4]]) { id }'


def test_args_merging():
    """Test merging of field arguments."""
    # Test merging simple arguments
    fields1 = Fields('items (limit: 10) { id }')
    fields2 = Fields('items (offset: 20) { name }')
    result = fields1 + fields2
    assert str(result) == 'items (limit: 10, offset: 20) { id name }'

    # Test merging array arguments
    fields1 = Fields('items (ids: [1, 2]) { id }')
    fields2 = Fields('items (ids: [3, 4]) { name }')
    result = fields1 + fields2
    assert str(result) == 'items (ids: [1, 2, 3, 4]) { id name }'

    # Test merging with duplicate values
    fields1 = Fields('items (ids: [1, 2]) { id }')
    fields2 = Fields('items (ids: [2, 3]) { name }')
    result = fields1 + fields2
    assert str(result) == 'items (ids: [1, 2, 3]) { id name }'

    # Test merging boolean arguments
    fields1 = Fields('items (active: true) { id }')
    fields2 = Fields('items (active: false) { name }')
    result = fields1 + fields2
    assert str(result) == 'items (active: false) { id name }'


def test_repr_method():
    """Test the __repr__ method of Fields."""
    fields = Fields('id name')
    assert repr(fields) == "Fields('id name')"

    # Test with nested fields
    fields = Fields('id items { name }')
    assert repr(fields) == "Fields('id items { name }')"


def test_parse_structure():
    """Test the _parse_structure internal method."""
    fields = Fields('')
    end_pos, content = fields._parse_structure('{ id name }', 0)
    assert end_pos == 11
    assert content == '{ id name '

    # Test with nested structures
    end_pos, content = fields._parse_structure('{ id items { name } }', 0)
    assert end_pos == 21
    assert content == '{ id items { name } '


def test_field_validation_edge_cases():
    """Test edge cases in field validation."""
    # Test invalid field names - starting with a brace
    with pytest.raises(ValueError):
        Fields('{ invalid }')

    # Test consecutive nested structures
    with pytest.raises(ValueError):
        Fields('field { id } { name }')

    # Test unmatched braces in nested structure
    with pytest.raises(ValueError):
        Fields('field { id { name }')

    # Add more valid edge cases
    assert str(Fields('field { }')) == 'field {  }'
    assert str(Fields('field { nested { } }')) == 'field { nested {  } }'


def test_args_parsing_complex():
    """Test complex argument parsing scenarios."""
    # Test mixed type arrays
    fields = Fields('items (ids: ["1", 2, true]) { id }')
    assert str(fields) == 'items (ids: ["1", 2, true]) { id }'

    # Test nested arrays with mixed types
    fields = Fields('items (data: [[1, "2"], [true, 3]]) { id }')
    assert str(fields) == 'items (data: [[1, "2"], [true, 3]]) { id }'

    # Test multiple arguments with different types
    fields = Fields('items (limit: 10, ids: ["1", "2"], active: true) { id }')
    assert str(fields) == 'items (limit: 10, ids: ["1", "2"], active: true) { id }'


def test_manage_temp_fields_complex():
    """Test complex scenarios for managing temporary fields."""
    # Test deeply nested structures
    data = {
        'id': 1,
        'board': {
            'items': [
                {
                    'id': 2,
                    'temp1': 'value1',
                    'column_values': {
                        'temp2': 'value2',
                        'id': 3
                    }
                }
            ],
            'temp3': 'value3'
        }
    }
    original_fields = 'id board { items { id column_values { id } } }'
    temp_fields = ['temp1', 'temp2', 'temp3']
    result = Fields.manage_temp_fields(data, original_fields, temp_fields)
    assert result == {
        'id': 1,
        'board': {
            'items': [
                {
                    'id': 2,
                    'column_values': {
                        'id': 3
                    }
                }
            ]
        }
    }


def test_field_combination_with_args():
    """Test combining fields with complex arguments."""
    # Test merging fields with overlapping arguments
    fields1 = Fields('items (ids: ["1"], limit: 10) { id }')
    fields2 = Fields('items (ids: ["2"], offset: 20) { name }')
    result = fields1 + fields2
    assert str(result) == 'items (ids: ["1", "2"], limit: 10, offset: 20) { id name }'

    # Test merging nested fields with arguments
    fields1 = Fields('board { items (limit: 10) { id } }')
    fields2 = Fields('board { items (offset: 20) { name } }')
    result = fields1 + fields2
    assert str(result) == 'board { items (limit: 10, offset: 20) { id name } }'


def test_subtraction_with_args():
    """Test field subtraction with arguments."""
    # Test subtracting fields with arguments
    fields1 = Fields('items (ids: ["1", "2"]) { id name }')
    fields2 = Fields('items { name }')
    result = fields1 - fields2
    assert str(result) == 'items (ids: ["1", "2"]) { id name }'

    # Test subtracting nested fields with arguments
    fields1 = Fields('board { items (limit: 10) { id name } }')
    fields2 = Fields('board { items { name } }')
    result = fields1 - fields2
    assert str(result) == 'board { items (limit: 10) { id name } }'

    # Add more specific subtraction tests
    fields1 = Fields('board { items { id name description } }')
    fields2 = Fields('board { items { name } }')
    result = fields1 - fields2
    assert str(result) == 'board { items { id description } }'


def test_parse_args_edge_cases():
    """Test edge cases in argument parsing."""
    fields = Fields('')

    # Test empty arguments
    assert fields._parse_args('()') == {}  # pylint: disable=use-implicit-booleaness-not-comparison

    # Test whitespace handling
    assert fields._parse_args('(  limit:  10  )') == {'limit': 10}

    # Test nested array with empty values
    args = fields._parse_args('(ids: ["", null, []])')
    assert 'ids' in args
    assert len(args['ids']) == 3


def test_format_value_edge_cases():
    """Test edge cases in value formatting."""
    fields = Fields('')

    # Test empty array
    assert fields._format_value([]) == '[]'

    # Test array with None values
    assert fields._format_value([('string', None)]) == '["None"]'

    # Test boolean values
    assert fields._format_value(True) == 'true'
    assert fields._format_value(False) == 'false'
