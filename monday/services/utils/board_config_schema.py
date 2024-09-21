"""Utility module for board configuration."""

from typing import List, Literal, Optional, Union, get_args

from pydantic import BaseModel, Field, field_validator


class BoardConfig(BaseModel):
    """Configuration for board selection and filtering."""
    board_ids: Optional[Union[int, List[int]]] = None
    board_kind: Literal['private', 'public', 'share', 'all'] = 'all'
    order_by: Literal['created_at', 'used_at'] = 'created_at'
    limit: int = Field(default=25, gt=0)
    page: int = Field(default=1, gt=0)
    state: Literal['active', 'all', 'archived', 'deleted'] = 'active'
    workspace_ids: Optional[Union[int, List[int]]] = None

    def __getattribute__(self, name):
        """Ensure board_ids is always a list when accessed."""
        value = object.__getattribute__(self, name)
        if name == 'board_ids' and value is None:
            return []
        return value

    @field_validator('board_ids', 'workspace_ids', mode='before')
    @classmethod
    def ensure_list_of_ints(cls, v, info):
        """Ensure the input is a list of integers or None."""
        if v is None:
            return None
        if isinstance(v, int):
            return [v]
        if isinstance(v, list) and all(isinstance(i, int) for i in v):
            return [int(item) for item in v]
        raise ValueError(f"{info.field_name} must be int or list of ints")

    @field_validator('board_kind', 'order_by', 'state')
    @classmethod
    def check_literal_values(cls, v, info):
        """Validate literal values against allowed values."""
        field = cls.model_fields[info.field_name]
        allowed_values = get_args(field.annotation)
        if v not in allowed_values:
            raise ValueError(f"{info.field_name} must be one of {allowed_values}")
        return v

    @field_validator('limit', 'page')
    @classmethod
    def check_positive_int(cls, v, info):
        """Validate that the input is a positive integer."""
        if not isinstance(v, int) or v <= 0:
            raise ValueError(f"{info.field_name} must be a positive integer")
        return v

    model_config = {
        'strict': True,
        'extra': 'forbid',
    }
