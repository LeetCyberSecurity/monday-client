"""Defines the schema for querying paginated items."""


from typing import List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class ItemsPageInput(BaseModel):
    """Input model for querying paginated items."""
    board_ids: Union[int, List[int]]
    query_params: Optional[str] = None
    limit: int = Field(default=25, gt=0, le=500)
    fields: str = 'items { id name }'
    paginate_items: bool = True

    @field_validator('board_ids')
    @classmethod
    def ensure_positive_int(cls, v):
        """Ensure the input is a positive integer or list of positive integers."""
        try:
            if isinstance(v, int):
                if v <= 0:
                    raise ValueError("board_ids must be positive")
                return [v]
            if isinstance(v, list):
                result = []
                for item in v:
                    item = int(item)
                    if item <= 0:
                        raise ValueError("All board_ids must be positive")
                    result.append(item)
                return result
            raise ValueError("board_ids must be int or list of ints")
        except ValueError as e:
            raise ValueError(str(e)) from None
        except TypeError:
            raise ValueError("board_ids must be int or list of ints") from None

    @field_validator('query_params', 'fields')
    @classmethod
    def ensure_string(cls, v, info):
        """Ensure the input is a non-empty string."""
        field_name = info.field_name
        if v is None and field_name == 'query_params':
            return v
        try:
            v = str(v).strip()
            if not v:
                raise ValueError(f"{field_name} must be a non-empty string")
            return v.replace('cursor', '')
        except AttributeError:
            raise ValueError(f"{field_name} must be a string") from None

    @field_validator('limit')
    @classmethod
    def check_limit(cls, v):
        """Validate that the limit is within the allowed range."""
        try:
            v = int(v)
            if v <= 0 or v > 500:
                raise ValueError("limit must be a positive integer not exceeding 500")
            return v
        except ValueError:
            raise ValueError("limit must be a valid integer") from None

    @field_validator('paginate_items')
    @classmethod
    def ensure_bool(cls, v):
        """Ensure the input is a boolean."""
        if not isinstance(v, bool):
            raise ValueError("paginate_items must be a boolean")
        return v

    model_config = {
        'strict': True,
        'extra': 'forbid',
    }
