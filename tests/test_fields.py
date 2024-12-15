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

# pylint: disable=redefined-outer-name

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
