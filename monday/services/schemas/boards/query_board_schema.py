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

"""Defines the schema for board querying."""

from typing import List, Literal, Optional, Union, get_args

from pydantic import BaseModel, Field, field_validator


class QueryBoardInput(BaseModel):
    """Input model for board querying."""
    board_ids: Optional[Union[int, List[int]]]
    fields: str = 'id name'
    board_kind: Literal['private', 'public', 'share', 'all'] = 'all'
    order_by: Literal['created_at', 'used_at'] = 'created_at'
    items_page_limit: int = Field(default=25, gt=0, lt=500)
    boards_limit: int = Field(default=25, gt=0)
    page: int = Field(default=1, gt=0)
    state: Literal['active', 'all', 'archived', 'deleted'] = 'active'
    workspace_ids: Optional[Union[int, List[int]]] = None

    @field_validator('board_ids', 'workspace_ids', mode='before')
    @classmethod
    def ensure_list_of_ints(cls, v, info):
        """Ensure the input is a positive integer or list of positive integers or None."""
        field_name = info.field_name
        if v is None:
            return v
        try:
            if isinstance(v, int):
                if v <= 0:
                    raise ValueError(f"{field_name} must be positive")
                return [v]
            if isinstance(v, list):
                result = []
                for item in v:
                    item = int(item)
                    if item <= 0:
                        raise ValueError(f"All {field_name} must be positive")
                    result.append(item)
                return result
            raise ValueError(f"{field_name} must be int or list of ints")
        except ValueError as e:
            raise ValueError(str(e)) from None
        except TypeError:
            raise ValueError(f"{field_name} must be int or list of ints") from None

    @field_validator('board_kind', 'order_by', 'state')
    @classmethod
    def ensure_literal_values(cls, v, info):
        """Validate literal values against allowed values."""
        field_name = info.field_name
        field = cls.model_fields[field_name]
        allowed_values = get_args(field.annotation)
        try:
            v = str(v).lower().strip()
            if v not in allowed_values:
                raise ValueError(f"{field_name} must be one of {allowed_values}")
            return v
        except AttributeError:
            raise ValueError(f"{field_name} must be a string") from None

    @field_validator('boards_limit', 'items_page_limit', 'page')
    @classmethod
    def ensure_positive_int(cls, v, info):
        """Validate that the input is a positive integer."""
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

    model_config = {
        'strict': True,
        'extra': 'forbid',
    }
