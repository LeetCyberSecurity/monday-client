"""Utility module for board configuration."""

from typing import List, Literal, Optional, Union, get_args

from pydantic import BaseModel, Field, field_validator


class QueryBoardInput(BaseModel):
    """Configuration for board selection and filtering."""
    board_ids: Optional[Union[int, List[int]]] = None
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
        """Ensure the input is an integer"""
        error_info = f"{info.field_name} must be int or list of ints" + " or None" if info.field_name == 'workspace_ids' else ""
        if v is None and info.field_name == 'workspace_ids':
            return v
        if isinstance(v, int):
            return [v]
        if isinstance(v, list) and all(isinstance(item, int) for item in v):
            return v
        raise ValueError(error_info)

    @field_validator('board_kind', 'order_by', 'state')
    @classmethod
    def check_literal_values(cls, v, info):
        """Validate literal values against allowed values."""
        field = cls.model_fields[info.field_name]
        allowed_values = get_args(field.annotation)
        if v not in allowed_values:
            raise ValueError(f"{info.field_name} must be one of {allowed_values}")
        return v

    @field_validator('boards_limit', 'items_page_limit', 'page')
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
