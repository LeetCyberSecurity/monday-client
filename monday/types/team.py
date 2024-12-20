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

"""
Type definitions for monday.com API team related structures.
"""

from typing import TYPE_CHECKING, Required, TypedDict

if TYPE_CHECKING:
    from monday.types.user import User


class Team(TypedDict, total=False):
    """
    Type definitions for monday.com API team structures.

    These types correspond to Monday.com's team fields as documented in their API reference:
    https://developer.monday.com/api-reference/reference/teams#fields
    """

    id: Required[str]
    """The team's unique identifier"""

    name: Required[str]
    """The team's name"""

    owners: Required[list['User']]
    """The users that are the team's owners (see :class:`User <monday.types.User>`)"""

    picture_url: str
    """The team's picture URL"""

    users: list['User']
    """The team's users (see :class:`User <monday.types.User>`)"""
