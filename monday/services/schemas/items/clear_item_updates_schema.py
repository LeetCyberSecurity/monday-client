"""Defines the schema for clearing an item's updates in the Monday service."""

from pydantic import BaseModel, field_validator


class ClearItemUpdatesInput(BaseModel):
    """Input model for clearing an item's updates."""
    item_id: int
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
