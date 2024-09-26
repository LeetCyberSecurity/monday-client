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

"""Utility functions for modifying data structures."""


def update_items_page_in_place(data, modify_fn):
    """
    Update items in a nested data structure in place.

    This function recursively traverses a nested data structure (dict or list)
    and applies the provided modify_fn to each item.

    Args:
        data (dict or list): The nested data structure to be modified.
        modify_fn (callable): A function that will be applied to each item.

    Returns:
        None. The function modifies the data structure in place.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'items_page' and isinstance(value, dict):
                modify_fn(value)
                return True  # Stop after first occurrence
            else:
                if update_items_page_in_place(value, modify_fn):
                    return True
    elif isinstance(data, list):
        for item in data:
            if update_items_page_in_place(item, modify_fn):
                return True
    return False
