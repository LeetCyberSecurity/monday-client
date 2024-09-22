"""Defines the schema for creating a board in the Monday service."""

from typing import List, Literal, Optional

from pydantic import BaseModel, field_validator


class CreateBoardInput(BaseModel):
    """Input model for creating a board."""
    name: str
    kind: Literal['private', 'public', 'share', 'all'] = 'all'
    owner_ids: Optional[List[int]] = None
    subscriber_ids: Optional[List[int]] = None
    subscriber_teams_ids: Optional[List[int]] = None
    description: str = ''
    folder_id: Optional[int] = None
    template_id: Optional[int] = None
    workspace_id: Optional[int] = None

    @field_validator('name', 'description')
    @classmethod
    def ensure_string(cls, v):
        """Ensure the input is a stripped string."""
        return str(v).strip()

    @field_validator('kind')
    @classmethod
    def ensure_valid_kind(cls, v):
        """Validate and normalize the 'kind' field."""
        valid_kinds = ['private', 'public', 'share', 'all']
        v = str(v).lower()
        if v not in valid_kinds:
            raise ValueError(f"kind must be one of {valid_kinds}")
        return v

    @field_validator('owner_ids', 'subscriber_ids', 'subscriber_teams_ids', mode='before')
    @classmethod
    def ensure_list_of_ints(cls, v):
        """Convert input to a list of integers or None."""
        if v is None:
            return None
        if isinstance(v, int):
            return [v]
        if isinstance(v, list):
            return [int(item) for item in v]
        raise ValueError("Must be an int, list of ints, or None")

    @field_validator('folder_id', 'template_id', 'workspace_id', mode='before')
    @classmethod
    def ensure_int(cls, v):
        """Convert input to an integer or None."""
        if v is None:
            return None
        return int(v)
