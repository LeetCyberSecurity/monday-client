"""Utility module for board configuration."""

from pydantic import BaseModel, field_validator


class GetGroupsInput(BaseModel):
    """Configuration for board group selection and filtering."""
    board_id: int
    fields: str = 'title name'

    @field_validator('board_id', mode='before')
    @classmethod
    def ensure_list_of_ints(cls, v):
        """Ensure the input is a positive integer"""
        try:
            if isinstance(v, int):
                if v <= 0:
                    raise ValueError("board_id must be positive")
                return v
            raise ValueError("board_id must be int")
        except ValueError as e:
            raise ValueError(str(e)) from None
        except TypeError:
            raise ValueError("board_id must be int") from None

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
