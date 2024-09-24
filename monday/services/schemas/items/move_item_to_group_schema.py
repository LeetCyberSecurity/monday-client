"""Defines the schema for moving an item to a group in the Monday service."""

from pydantic import BaseModel, field_validator


class MoveToGroupInput(BaseModel):
    """Input model for moving an item to a group."""
    item_id: int
    group_id: str
    fields: str = 'id'

    @field_validator('item_id')
    @classmethod
    def ensure_positive_int(cls, v):
        """Ensure the input is a positive integer."""
        try:
            v = int(v)
            if v <= 0:
                raise ValueError("item_id must be a positive integer")
            return v
        except ValueError:
            raise ValueError("item_id must be a valid integer") from None

    @field_validator('group_id', 'fields')
    @classmethod
    def ensure_string(cls, v, info):
        """Ensure the input is a non-empty string."""
        field_name = info.field_name
        try:
            v = str(v).strip()
            if not v:
                raise ValueError(f"{field_name} must be a non-empty string")
            return v
        except AttributeError:
            raise ValueError(f"{field_name} must be a string") from None

    model_config = {
        'strict': True,
        'extra': 'forbid',
    }
