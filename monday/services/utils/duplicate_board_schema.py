"""Defines the schema for duplicating a board in the Monday service."""

from typing import Literal, Optional

from pydantic import BaseModel, field_validator


class DuplicateBoardInput(BaseModel):
    """
    Input model for duplicating a board on Monday.com.

    This model validates and normalizes the input parameters for the board duplication process.
    It ensures that only one board is being duplicated and that all input values are in the correct format.

    Attributes:
        board_id (int): The ID of the board to duplicate.
        board_name (Optional[str]): The name for the duplicated board. If not provided, Monday.com will auto-generate a name.
        duplicate_type (Literal): The type of duplication to perform. Defaults to 'duplicate_board_with_structure'.
        folder_id (Optional[int]): The ID of the folder to place the duplicated board in.
        keep_subscribers (bool): Whether to keep the subscribers from the original board. Defaults to False.
        workspace_id (Optional[int]): The ID of the workspace to place the duplicated board in.

    Note:
        Only one board can be duplicated at a time.
    """
    board_id: int
    board_name: Optional[str] = None
    duplicate_type: Literal['duplicate_board_with_pulses', 'duplicate_board_with_pulses_and_updates', 'duplicate_board_with_structure'] = 'duplicate_board_with_structure'
    folder_id: Optional[int] = None
    keep_subscribers: bool = False
    workspace_id: Optional[int] = None

    @field_validator('board_name')
    @classmethod
    def ensure_string(cls, v):
        """Ensure the input is a stripped string or None."""
        return str(v).strip() if v is not None else None

    @field_validator('duplicate_type')
    @classmethod
    def ensure_valid_duplicate_type(cls, v):
        """Validate and normalize the 'duplicate_type' field."""
        valid_types = ['duplicate_board_with_pulses', 'duplicate_board_with_pulses_and_updates', 'duplicate_board_with_structure']
        v = str(v).lower()
        if v not in valid_types:
            raise ValueError(f"duplicate_type must be one of {valid_types}")
        return v

    @field_validator('board_id', 'folder_id', 'workspace_id')
    @classmethod
    def ensure_positive_int(cls, v):
        """Ensure the input is a positive integer or None."""
        if v is None:
            return None
        v = int(v)
        if v <= 0:
            raise ValueError("Must be a positive integer")
        return v

    @field_validator('keep_subscribers')
    @classmethod
    def ensure_bool(cls, v):
        """Ensure the input is a boolean."""
        return bool(v)
