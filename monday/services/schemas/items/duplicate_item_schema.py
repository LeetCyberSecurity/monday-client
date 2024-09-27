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

"""Defines the schema for duplicating an item."""

from pydantic import BaseModel, field_validator


class DuplicateItemInput(BaseModel):
    """Input model for duplicating an item."""
    item_id: int
    board_id: int
    fields: str = 'id'
    with_updates: bool = False

    @field_validator('item_id', 'board_id')
    @classmethod
    def ensure_positive_int(cls, v, info):
        """Ensure the input is a positive integer or None."""
        field_name = info.field_name
        try:
            v = int(v)
            if v <= 0:
                raise ValueError(f"{field_name} must be a positive integer")
            return v
        except ValueError:
            raise ValueError(f"{field_name} must be a valid integer") from None

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

    @field_validator('with_updates')
    @classmethod
    def ensure_bool(cls, v):
        """Ensure the input is a boolean."""
        if not isinstance(v, bool):
            raise ValueError("with_updates must be a boolean")
        return v

    model_config = {
        'strict': True,
        'extra': 'forbid',
    }
