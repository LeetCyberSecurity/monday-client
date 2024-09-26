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

"""Defines the schema for querying items."""


from typing import List, Union

from pydantic import BaseModel, Field, field_validator


class QueryItemInput(BaseModel):
    """Input model for querying items."""
    item_ids: Union[int, List[int]]
    limit: int = Field(default=25, gt=0, le=500)
    fields: str = 'name'
    page: int = Field(default=1, gt=0)
    exclude_nonactive: bool = False
    newest_first: bool = False

    @field_validator('item_ids')
    @classmethod
    def ensure_list_of_ints(cls, v):
        """Ensure the input is a positive integer or list of positive integers."""
        try:
            if isinstance(v, int):
                if v <= 0:
                    raise ValueError("item_ids must be positive integers")
                return [v]
            if isinstance(v, list):
                if not v or len(v) > 100:
                    raise ValueError("item_ids must be a non-empty list with at most 100 items")
                result = []
                for item in v:
                    item = int(item)
                    if item <= 0:
                        raise ValueError("All item_ids must be positive integers")
                    result.append(item)
                return result
            raise ValueError("item_ids must be an int or list of ints")
        except ValueError as e:
            raise ValueError(f"item_ids: {str(e)}") from None
        except TypeError:
            raise ValueError("item_ids must be an int or list of ints") from None

    @field_validator('page', 'limit')
    @classmethod
    def ensure_positive_int(cls, v, info):
        """Validate that the input is a positive integer."""
        field_name = info.field_name
        try:
            v = int(v)
            if v <= 0:
                raise ValueError(f"{field_name} must be a positive integer")
            if field_name == 'limit' and v > 500:
                raise ValueError("limit must not exceed 500")
            return v
        except ValueError as e:
            raise ValueError(f"{field_name}: {str(e)}") from None

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

    @field_validator('exclude_nonactive', 'newest_first')
    @classmethod
    def ensure_bool(cls, v, info):
        """Ensure the input is a boolean."""
        field_name = info.field_name
        if not isinstance(v, bool):
            raise ValueError(f"{field_name} must be a boolean")
        return v

    model_config = {
        'strict': True,
        'extra': 'forbid',
    }
