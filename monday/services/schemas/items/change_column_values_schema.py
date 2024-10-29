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

"""Defines the schema for changing column values."""

from typing import Any, Dict

from pydantic import BaseModel, field_validator


class ChangeColumnValuesInput(BaseModel):
    """Input model for changing column values."""
    item_id: int
    column_values: Dict[str, Any]
    create_labels_if_missing: bool = False
    fields: str = 'id text'

    @field_validator('item_id')
    @classmethod
    def ensure_positive_int(cls, v):
        """Ensure the input is a positive integer."""
        try:
            v = int(v)
            if v <= 0:
                raise ValueError("item_ids must be a positive integer")
            return v
        except (ValueError, TypeError):
            raise ValueError("item_ids must be a valid integer") from None

    @field_validator('column_values')
    @classmethod
    def ensure_dict(cls, v):
        """Ensure the input is a dictionary."""
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

    @field_validator('fields')
    @classmethod
    def ensure_string(cls, v):
        """Ensure the input is a non-empty string."""
        try:
            v = str(v).strip()
            if not v:
                raise ValueError("fields must be a non-empty string")
            return v
        except AttributeError:
            raise ValueError("fields must be a string") from None

    model_config = {
        'strict': True,
        'extra': 'forbid',
    }
