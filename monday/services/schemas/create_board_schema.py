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
    def ensure_string(cls, v, info):
        """Ensure the input is a stripped string."""
        field_name = info.field_name
        try:
            return str(v).strip()
        except AttributeError:
            raise ValueError(f"{field_name} must be a string") from None

    @field_validator('kind')
    @classmethod
    def ensure_valid_kind(cls, v):
        """Validate and normalize the 'kind' field."""
        valid_kinds = ['private', 'public', 'share', 'all']
        try:
            v = str(v).lower().strip()
            if v not in valid_kinds:
                raise ValueError(f"kind must be one of {valid_kinds}")
            return v
        except AttributeError:
            raise ValueError("kind must be a string") from None

    @field_validator('owner_ids', 'subscriber_ids', 'subscriber_teams_ids', mode='before')
    @classmethod
    def ensure_list_of_ints(cls, v, info):
        """Convert input to a list of integers or None."""
        field_name = info.field_name
        if v is None:
            return None
        try:
            if isinstance(v, int):
                return [v]
            if isinstance(v, list):
                return [int(item) for item in v]
            raise ValueError(f"{field_name} must be an int, list of ints, or None")
        except ValueError:
            raise ValueError(f"All items in {field_name} must be valid integers") from None

    @field_validator('folder_id', 'template_id', 'workspace_id', mode='before')
    @classmethod
    def ensure_int(cls, v, info):
        """Convert input to an integer or None."""
        field_name = info.field_name
        if v is None:
            return None
        try:
            return int(v)
        except ValueError:
            raise ValueError(f"{field_name} must be a valid integer or None") from None

    model_config = {
        'strict': True,
        'extra': 'forbid',
    }
