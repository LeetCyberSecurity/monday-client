"""Defines the schema for updating a board in the Monday service."""

from typing import Literal

from pydantic import BaseModel, field_validator


class UpdateBoardInput(BaseModel):
    """
    Input model for updating a board on Monday.com.

    This model validates and normalizes the input parameters for the board update process.
    It ensures that only one board is being updated and that all input values are in the correct format.

    Attributes:
        board_id (int): The ID of the board to update. Can only be called on a single board ID
        board_attribute (Literal): The board's attribute to update.
        new_value (str): The new attribute value.
    """
    board_id: int
    board_attribute: Literal['communication', 'description', 'name']
    new_value: str

    @field_validator('board_attribute')
    @classmethod
    def ensure_valid_attribute_type(cls, v):
        """Validate and normalize the 'board_attribute' field."""
        valid_types = ['communication', 'description', 'name']
        try:
            v = str(v).lower().strip()
            if v not in valid_types:
                raise ValueError(f"board_attribute must be one of {valid_types}")
            return v
        except AttributeError:
            raise ValueError("board_attribute must be a string") from None

    @field_validator('new_value')
    @classmethod
    def ensure_string(cls, v):
        """Ensure the input is a stripped string"""
        if not isinstance(v, str):
            raise ValueError("new_value must be a string")
        return v.strip()

    @field_validator('board_id')
    @classmethod
    def ensure_positive_int(cls, v):
        """Ensure the input is a positive integer"""
        try:
            v = int(v)
            if v <= 0:
                raise ValueError("board_id must be a positive integer")
            return v
        except ValueError:
            raise ValueError("board_id must be a valid integer") from None

    model_config = {
        'strict': True,
        'extra': 'forbid',
    }
