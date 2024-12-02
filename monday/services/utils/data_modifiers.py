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

import logging
from typing import Any, Callable, Union

logger: logging.Logger = logging.getLogger(__name__)


def update_data_in_place(
    data: Union[dict[str, Any], list[Any]],
    modify_fn: Callable[[dict[str, Any]], None]
) -> None:
    """
    Update items in a nested data structure in place.

    This function recursively traverses a nested data structure (dict or list)
    and applies the provided modify_fn to each item.

    Args:
        data: The nested data structure to be modified.
        modify_fn: A function that will be applied to each item.

    Returns:
        None. The function modifies the data structure in place.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'items_page' and isinstance(value, dict):
                modify_fn(value)
                return True  # Stop after first occurrence
            else:
                if update_data_in_place(value, modify_fn):
                    return True
    elif isinstance(data, list):
        for item in data:
            if update_data_in_place(item, modify_fn):
                return True
    return False
