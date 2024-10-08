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

"""Defines the schema for user querying."""

from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator


class QueryUserInput(BaseModel):
    """Input model for user querying."""
    fields: str = 'id email'
    emails: Optional[Union[str, List[str]]] = None
    ids: Optional[Union[int, List[int]]] = None
    name: Optional[str] = None
    kind: Literal['all', 'guests', 'non_guests', 'non_pending'] = 'all'
    newest_first: bool = False
    non_active: bool = False
    limit: int = Field(default=50, gt=0, le=1000)
    page: int = Field(default=1, gt=0)
    paginate: bool = True

    @field_validator('emails')
    @classmethod
    def validate_emails(cls, v):
        """Validate that the input is a non-empty string or a list of non-empty strings."""
        if v is None:
            return v
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Email string must not be empty")
            return [v]
        if isinstance(v, list):
            result = []
            for item in v:
                if not isinstance(item, str):
                    raise ValueError("All items in emails list must be strings")
                item = item.strip()
                if not item:
                    raise ValueError("Emails list must not contain empty strings")
                result.append(item)
            return result
        raise ValueError("Emails must be a string or a list of strings")

    @field_validator('ids')
    @classmethod
    def validate_ids(cls, v):
        """Validate that the input is a positive integer or a list of positive integers."""
        if v is None:
            return v
        if isinstance(v, int):
            if v <= 0:
                raise ValueError("ID must be positive")
            return [v]
        if isinstance(v, list):
            result = []
            for item in v:
                try:
                    item = int(item)
                    if item <= 0:
                        raise ValueError("All IDs must be positive")
                    result.append(item)
                except ValueError:
                    raise ValueError("All items in IDs list must be integers") from None
            return result
        raise ValueError("IDs must be an integer or a list of integers")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate literal values against allowed values."""
        if v is None:
            return v
        v = str(v).strip()
        if not v:
            raise ValueError("Name must not be empty")
        return v

    @field_validator('kind')
    @classmethod
    def validate_kind(cls, v):
        """Validate the kind of users to search by."""
        allowed_values = ['all', 'guests', 'non_guests', 'non_pending']
        v = str(v).lower()
        if v not in allowed_values:
            raise ValueError(f"Kind must be one of {allowed_values}")
        return v

    model_config = {
        'strict': True,
        'extra': 'forbid',
    }
