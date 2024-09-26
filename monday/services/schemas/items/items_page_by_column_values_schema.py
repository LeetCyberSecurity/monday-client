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

"""Defines the combined schema for querying paginated items based on their column values."""

from typing import List

from pydantic import BaseModel, Field, field_validator


class ColumnInput(BaseModel):
    """Input model for querying paginated items by column values."""

    column_id: str
    column_values: List[str]

    @field_validator('column_id')
    @classmethod
    def validate_column_id(cls, v):
        """Ensure the column_id is a non-empty string."""
        if not isinstance(v, str) or not v.strip():
            raise ValueError("column_id must be a non-empty string")
        return v

    @field_validator('column_values')
    @classmethod
    def validate_column_values(cls, v):
        """Validate that column_values is a non-empty list of non-empty strings."""
        if not isinstance(v, list) or not v:
            raise ValueError("column_values must be a non-empty list")
        if not all(isinstance(value, str) and value.strip() for value in v):
            raise ValueError("All column_values must be non-empty strings")
        return v


class ItemsPageByColumnValuesInput(BaseModel):
    """Input model for querying paginated items by column values."""

    board_id: int
    columns: List[ColumnInput]
    limit: int = Field(default=25, gt=0, le=500)
    fields: str = 'items { id name }'
    paginate_items: bool = True

    @field_validator('board_id')
    @classmethod
    def ensure_positive_int(cls, v):
        """Ensure the board_id is a positive integer."""
        if not isinstance(v, int) or v <= 0:
            raise ValueError("board_id must be a positive integer")
        return v

    @field_validator('limit')
    @classmethod
    def check_limit(cls, v):
        """Validate that the limit is within the allowed range."""
        if not isinstance(v, int) or v <= 0 or v > 500:
            raise ValueError("limit must be a positive integer not exceeding 500")
        return v

    @field_validator('fields')
    @classmethod
    def ensure_fields(cls, v):
        """Ensure the fields parameter is a non-empty string."""
        if not isinstance(v, str) or not v.strip():
            raise ValueError("fields must be a non-empty string")
        return v.replace('cursor', '')

    @field_validator('paginate_items')
    @classmethod
    def ensure_bool(cls, v):
        """Ensure the paginate_items is a boolean."""
        if not isinstance(v, bool):
            raise ValueError("paginate_items must be a boolean")
        return v

    model_config = {
        'strict': True,
        'extra': 'forbid',
    }
