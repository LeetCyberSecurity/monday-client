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

"""Defines the schema for board group selection and filtering."""

from pydantic import BaseModel, field_validator


class GetGroupsInput(BaseModel):
    """Input model for board group selection and filtering."""
    board_id: int
    fields: str = 'title name'

    @field_validator('board_id', mode='before')
    @classmethod
    def ensure_list_of_ints(cls, v):
        """Ensure the input is a positive integer"""
        try:
            if isinstance(v, int):
                if v <= 0:
                    raise ValueError("board_id must be positive")
                return v
            raise ValueError("board_id must be int")
        except ValueError as e:
            raise ValueError(str(e)) from None
        except TypeError:
            raise ValueError("board_id must be int") from None

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
