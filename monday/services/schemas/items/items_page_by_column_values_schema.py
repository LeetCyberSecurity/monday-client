"""Defines the schema for querying paginated items based on their column values."""


from pydantic import BaseModel, Field, field_validator


class ItemsPageByColumnValuesInput(BaseModel):
    """Input model for querying paginated items by column values."""
    board_id: int
    columns: str
    limit: int = Field(default=25, gt=0, le=500)
    fields: str = 'items { id name }'
    paginate_items: bool = True

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

    @field_validator('columns', 'fields')
    @classmethod
    def ensure_string(cls, v, info):
        """Ensure the input is a non-empty string."""
        field_name = info.field_name
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
