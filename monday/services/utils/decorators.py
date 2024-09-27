# This file is part of monday-client.
#
# Copyright (C) 2024 Leet Cyber Security <https://leetcybersecurity.com/>
#
# monday-client is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# monday-client is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with monday-client. If not, see <https://www.gnu.org/licenses/>.

"""Utility decorators for Monday API interactions."""

from functools import wraps
from typing import Callable


def board_action(method_name: str) -> Callable:
    """
    Decorator for board actions.

    Args:
        method_name: The name of the method to be decorated.

    Returns:
        A decorator function.
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
        method_name: The name of the method to be decorated.

    Returns:
        A decorator function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            items = self.items()
            item_method = getattr(items, method_name)
            return await item_method(*args, **kwargs)
        return wrapper
    return decorator
