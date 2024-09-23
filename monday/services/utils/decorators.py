"""Utility decorators for Monday API interactions."""

from functools import wraps
from typing import Callable


def board_action(method_name: str) -> Callable:
    """
    Decorator for board actions.

    Args:
        method_name (str): The name of the method to be decorated.

    Returns:
        Callable: A decorator function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            boards = self.boards()
            board_method = getattr(boards, method_name)
            return await board_method(*args, **kwargs)
        return wrapper
    return decorator


def item_action(method_name: str) -> Callable:
    """
    Decorator for item actions.

    Args:
        method_name (str): The name of the method to be decorated.

    Returns:
        Callable: A decorator function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            items = self.items()
            item_method = getattr(items, method_name)
            return await item_method(*args, **kwargs)
        return wrapper
    return decorator
