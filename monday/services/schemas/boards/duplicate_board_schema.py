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

"""Defines the schema for duplicating a board."""

from typing import Literal, Optional

from pydantic import BaseModel, field_validator


class DuplicateBoardInput(BaseModel):
    """Input model for duplicating a board."""
    board_id: int
    fields: str = 'id'
    board_name: Optional[str] = None
    duplicate_type: Literal['duplicate_board_with_pulses', 'duplicate_board_with_pulses_and_updates', 'duplicate_board_with_structure'] = 'duplicate_board_with_structure'
    folder_id: Optional[int] = None
    keep_subscribers: bool = False
    workspace_id: Optional[int] = None

    @field_validator('board_name', 'fields')
    @classmethod
    def ensure_string(cls, v, info):
        """Ensure the input is a stripped string."""
        field_name = info.field_name
        if field_name == 'board_name' and v is None:
            return None
        try:
            v = str(v).strip()
            if not v:
                raise ValueError(f"{field_name} must be a non-empty string")
            return v
        except AttributeError:
            raise ValueError(f"{field_name} must be a string") from None

    @field_validator('duplicate_type')
    @classmethod
    def ensure_valid_duplicate_type(cls, v):
        """Validate and normalize the 'duplicate_type' field."""
        valid_types = ['duplicate_board_with_pulses', 'duplicate_board_with_pulses_and_updates', 'duplicate_board_with_structure']
        try:
            v = str(v).lower().strip()
            if v not in valid_types:
                raise ValueError(f"duplicate_type must be one of {valid_types}")
            return v
        except AttributeError:
            raise ValueError("duplicate_type must be a string") from None

    @field_validator('board_id', 'folder_id', 'workspace_id')
    @classmethod
    def ensure_positive_int(cls, v, info):
        """Ensure the input is a positive integer or None."""
        field_name = info.field_name
        if v is None and field_name != 'board_id':
            return None
        try:
            v = int(v)
            if v <= 0:
                raise ValueError(f"{field_name} must be a positive integer")
            return v
        except ValueError:
            raise ValueError(f"{field_name} must be a valid integer") from None

    @field_validator('keep_subscribers')
    @classmethod
    def ensure_bool(cls, v):
        """Ensure the input is a boolean."""
        if not isinstance(v, bool):
            raise ValueError("keep_subscribers must be a boolean")
        return v

    model_config = {
        'strict': True,
        'extra': 'forbid',
    }
