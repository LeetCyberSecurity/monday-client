"""Provides utilities for validating board configurations."""

from pydantic import ValidationError

from .board_config_schema import BoardConfig


class ConfigValidatedAttribute:
    """Descriptor for validating and setting board configuration attributes."""

    def __init__(self, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj._config, self.name)

    def __set__(self, obj, value):
        try:
            new_config = BoardConfig(**{**obj._config.model_dump(), self.name: value})
            obj._config = new_config
        except ValidationError as e:
            error_messages = [f"{''.join([m.strip() for m in error['msg'].split(',', 1)[1:]])}" for error in e.errors()]
            if not any(msg for msg in error_messages):
                error_messages = ["Invalid arguments"] + [f"Invalid argument {error['loc'][0]} given to boards.configure()" for error in e.errors()]
            raise ValueError('\n'.join(error_messages)) from None
