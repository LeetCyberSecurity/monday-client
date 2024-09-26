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

"""Defines the schema for creating an item."""

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, field_validator


class CreateItemInput(BaseModel):
    """Input model for creating an item."""
    board_id: int
    item_name: str
    column_values: Optional[Dict[str, Any]] = None
    fields: str = 'id'
    group_id: Optional[str] = None
    create_labels_if_missing: bool = False
    position_relative_method: Optional[Literal['before_at', 'after_at']] = None
    relative_to: Optional[int] = None

    @field_validator('board_id', 'relative_to')
    @classmethod
    def ensure_positive_int(cls, v, info):
        """Ensure the input is a positive integer or None."""
        field_name = info.field_name
        if v is None and field_name == 'relative_to':
            return None
        try:
            v = int(v)
            if v <= 0:
                raise ValueError(f"{field_name} must be a positive integer")
            return v
        except (ValueError, TypeError):
            raise ValueError(f"{field_name} must be a valid integer") from None

    @field_validator('item_name', 'fields', 'group_id')
    @classmethod
    def ensure_string(cls, v, info):
        """Ensure the input is a non-empty string or None."""
        field_name = info.field_name
        if v is None and field_name == 'group_id':
            return None
        try:
            v = str(v).strip()
            if not v:
                raise ValueError(f"{field_name} must be a non-empty string")
            return v
        except AttributeError:
            raise ValueError(f"{field_name} must be a string") from None

    @field_validator('column_values', mode='before')
    @classmethod
    def ensure_dict(cls, v):
        """Ensure the input is a dictionary or None."""
        if v is None:
            return None
        if not isinstance(v, dict):
            raise ValueError("column_values must be a dictionary")
        return v

    @field_validator('create_labels_if_missing')
    @classmethod
    def ensure_bool(cls, v):
        """Ensure the input is a boolean."""
        if not isinstance(v, bool):
            raise ValueError("create_labels_if_missing must be a boolean")
        return v

    @field_validator('position_relative_method')
    @classmethod
    def ensure_valid_position_method(cls, v):
        """Validate the 'position_relative_method' field."""
        valid_methods = ['before_at', 'after_at']
        if v is None:
            return None
        try:
            v = v.strip()
            if v not in valid_methods:
                raise ValueError(f"position_relative_method must be one of {valid_methods}")
            return v
        except AttributeError:
            raise ValueError("position_relative_method must be a string") from None

    model_config = {
        'strict': True,
        'extra': 'forbid',
    }
