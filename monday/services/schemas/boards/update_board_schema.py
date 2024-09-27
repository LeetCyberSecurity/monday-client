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

"""Defines the schema for updating a board."""

from typing import Literal

from pydantic import BaseModel, field_validator


class UpdateBoardInput(BaseModel):
    """Input model for updating a board."""
    board_id: int
    board_attribute: Literal['communication', 'description', 'name']
    new_value: str

    @field_validator('board_attribute')
    @classmethod
    def ensure_valid_attribute_type(cls, v):
        """Validate and normalize the 'board_attribute' field."""
        valid_types = ['communication', 'description', 'name']
        try:
            v = str(v).lower().strip()
            if v not in valid_types:
                raise ValueError(f"board_attribute must be one of {valid_types}")
            return v
        except AttributeError:
            raise ValueError("board_attribute must be a string") from None

    @field_validator('new_value')
    @classmethod
    def ensure_string(cls, v):
        """Ensure the input is a stripped string"""
        if not isinstance(v, str):
            raise ValueError("new_value must be a string")
        return v.strip()

    @field_validator('board_id')
    @classmethod
    def ensure_positive_int(cls, v):
        """Ensure the input is a positive integer"""
        try:
            v = int(v)
            if v <= 0:
                raise ValueError("board_id must be a positive integer")
            return v
        except ValueError:
            raise ValueError("board_id must be a valid integer") from None

    model_config = {
        'strict': True,
        'extra': 'forbid',
    }
