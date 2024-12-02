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

"""Utility function for managing fields in query strings."""

import logging
from typing import Union

logger: logging.Logger = logging.getLogger(__name__)


def manage_temp_fields(
    data: Union[dict, list],
    original_fields: Union[str, set],
    temp_fields: list[str]
) -> Union[dict, list]:
    """
    Manage temporary fields in query results by removing fields that weren't in the original fields set.

    Args:
        data: Query result data (dict or list)
        original_fields: Space-separated string or set of original field names
        temp_fields: List of field names that were temporarily added

    Returns:
        Data structure with temporary fields removed if they weren't in original fields
    """
    # Convert original_fields to set if it's a string
    orig_fields_set = set(original_fields.split()) if isinstance(original_fields, str) else set(original_fields)

    # Find which temp fields weren't in original fields
    fields_to_remove = set(temp_fields) - orig_fields_set

    if not fields_to_remove:
        return data

    if isinstance(data, list):
        return [manage_temp_fields(item, orig_fields_set, temp_fields) for item in data]

    if isinstance(data, dict):
        return {
            k: manage_temp_fields(v, orig_fields_set, temp_fields) if isinstance(v, (dict, list)) else v
            for k, v in data.items()
            if k not in fields_to_remove
        }

    return data


def add_temp_fields(
    fields: str,
    temp_fields: list[str]
) -> str:
    """
    Add temporary fields to a query string while preserving nested structures.

    Args:
        fields: Original fields string (can include nested structures)
        temp_fields: List of field names to temporarily add

    Returns:
        Updated fields string with temporary fields added
    """
    # Split only on top level, preserving nested structures
    top_level_fields = [f.strip() for f in fields.split() if f.strip()]

    # Only add temp fields that aren't already present
    new_fields = [f for f in temp_fields if f not in top_level_fields]

    # Add temp fields
    all_fields = top_level_fields + new_fields

    return ' '.join(all_fields)
