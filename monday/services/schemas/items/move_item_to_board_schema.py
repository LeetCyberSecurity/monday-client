"""Defines the schema for moving an item to a different board in the Monday service."""

from typing import Dict, List, Optional

from pydantic import BaseModel, field_validator


class MoveToBoardInput(BaseModel):
    """Input model for moving an item to a different board."""
    item_id: int
    board_id: int
    fields: str = 'id'
    group_id: Optional[str] = None
    columns_mapping: Optional[List[Dict[str, str]]] = None
    subitems_columns_mapping: Optional[List[Dict[str, str]]] = None

    @field_validator('item_id', 'board_id')
    @classmethod
    def ensure_positive_int(cls, v, info):
        """Ensure the input is a positive integer."""
        field_name = info.field_name
        try:
            v = int(v)
            if v <= 0:
                raise ValueError(f"{field_name} must be a positive integer")
            return v
        except ValueError:
            raise ValueError(f"{field_name} must be a valid integer") from None

    @field_validator('fields', 'group_id')
    @classmethod
    def ensure_string(cls, v, info):
        """Ensure the input is a non-empty string or None."""
        field_name = info.field_name
        if v is None and field_name == 'group_id':
            return None
        try:
            v = str(v).strip()
            if not v:
                raise ValueError(f"{field_name} must be a non-empty string")
            return v
        except AttributeError:
            raise ValueError(f"{field_name} must be a string") from None

    @field_validator('columns_mapping', 'subitems_columns_mapping', mode='before')
    @classmethod
    def ensure_list_of_dicts(cls, v, info):
        """Ensure the input is a list of dictionaries with string keys and values or None."""
        field_name = info.field_name
        if v is None:
            return None
        if not isinstance(v, list):
            raise ValueError(f"{field_name} must be a list of dictionaries")
        for item in v:
            if not isinstance(item, dict):
                raise ValueError(f"All items in {field_name} must be dictionaries")
            for key, value in item.items():
                if not isinstance(key, str):
                    raise ValueError(f"All keys in dictionaries of {field_name} must be strings")
                if not isinstance(value, str):
                    raise ValueError(f"All values in dictionaries of {field_name} must be strings")
        return v

    model_config = {
        'strict': True,
        'extra': 'forbid',
    }