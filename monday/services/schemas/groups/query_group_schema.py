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

"""Defines the schema for querying groups."""


from typing import List, Optional, Union

from pydantic import BaseModel, field_validator


class QueryGroupInput(BaseModel):
    """Input model for querying groups."""
    board_ids: Union[int, List[int]]
    group_ids: Optional[Union[str, List[str]]] = None
    group_name: Optional[Union[str, List[str]]] = None
    fields: str = 'id title'

    @field_validator('board_ids')
    @classmethod
    def ensure_list_of_ints(cls, v):
        """Ensure the input is a positive integer or list of positive integers."""
        try:
            if isinstance(v, int):
                if v <= 0:
                    raise ValueError("board_ids must be positive integers")
                return [v]
            if isinstance(v, list):
                if not v or len(v) > 100:
                    raise ValueError("board_ids must be a non-empty list with at most 100 items")
                result = []
                for item in v:
                    item = int(item)
                    if item <= 0:
                        raise ValueError("All board_ids must be positive integers")
                    result.append(item)
                return result
            raise ValueError("board_ids must be an int or list of ints")
        except ValueError as e:
            raise ValueError(f"board_ids: {str(e)}") from None
        except TypeError:
            raise ValueError("board_ids must be an int or list of ints") from None

    @field_validator('group_ids', 'group_name')
    @classmethod
    def ensure_list_of_strings(cls, v, info):
        """Ensure the input is a non-empty string, list of non-empty strings, or None."""
        field_name = info.field_name
        if v is None:
            return v
        try:
            if isinstance(v, str):
                if not v.strip():
                    raise ValueError(f"{field_name} must be a non-empty string")
                return [v.strip()]
            if isinstance(v, list):
                if not v:
                    raise ValueError(f"{field_name} must be a non-empty list")
                result = []
                for item in v:
                    if not isinstance(item, str) or not item.strip():
                        raise ValueError("All group_ids must be non-empty strings")
                    result.append(item.strip())
                return result
            raise ValueError(f"{field_name} must be a string, list of strings, or None")
        except AttributeError:
            raise ValueError(f"{field_name} must be a string, list of strings, or None") from None

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
