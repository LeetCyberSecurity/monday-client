"""Defines the schema for duplicating an item in the Monday service."""

from typing import Optional

from pydantic import BaseModel, field_validator


class DuplicateItemInput(BaseModel):
    """Input model for duplicating an item."""
    item_id: int
    fields: str = 'id'
    board_id: Optional[int] = None
    with_updates: bool = False

    @field_validator('item_id', 'board_id')
    @classmethod
    def ensure_positive_int(cls, v, info):
        """Ensure the input is a positive integer or None."""
        field_name = info.field_name
        if v is None and field_name == 'board_id':
            return None
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

    @field_validator('with_updates')
    @classmethod
    def ensure_bool(cls, v):
        """Ensure the input is a boolean."""
        if not isinstance(v, bool):
            raise ValueError("with_updates must be a boolean")
        return v

    model_config = {
        'strict': True,
        'extra': 'forbid',
    }
