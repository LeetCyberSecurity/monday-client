"""Defines the schema for deleting a board in the Monday service."""

from pydantic import BaseModel, field_validator


class DeleteBoardInput(BaseModel):
    """Input model for deleting a board."""
    board_id: int
    fields: str = 'id'

    @field_validator('board_id')
    @classmethod
    def ensure_positive_int(cls, v):
        """Ensure the input is a positive integer."""
        try:
            v = int(v)
            if v <= 0:
                raise ValueError("board_id must be a positive integer")
            return v
        except ValueError:
            raise ValueError("board_id must be a valid integer") from None

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
