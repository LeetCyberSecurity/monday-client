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

"""Tests for monday-client data modifiers."""

import pytest

pytestmark = pytest.mark.unit

from monday.services.utils.data_modifiers import update_data_in_place


def test_update_data_in_place_updates_first_items_page():
    """Test that first board's items_page is updated and cursor removed."""
    data = {
        'data': {
            'boards': [
                {'id': 1, 'items_page': {'cursor': 'abc', 'items': [1]}},
                {'id': 2, 'items_page': {'cursor': 'def', 'items': [2]}},
            ]
        }
    }

    def modifier(ip):
        ip['items'].append(3)
        ip.pop('cursor', None)

    applied = update_data_in_place(data, modifier)
    assert applied is True
    assert 'cursor' not in data['data']['boards'][0]['items_page']
    assert data['data']['boards'][0]['items_page']['items'] == [1, 3]


def test_update_data_in_place_list_root():
    """Test that list root items_page is modified in place."""
    data = [
        {'x': 1},
        {'items_page': {'cursor': 'z', 'items': []}},
    ]

    def modifier(ip):
        ip['items'] = [42]

    applied = update_data_in_place(data, modifier)
    assert applied is True
    assert data[1]['items_page']['items'] == [42]
