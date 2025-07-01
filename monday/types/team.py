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
Monday.com API team type definitions and structures.

This module contains dataclasses that represent Monday.com team objects,
including teams and their relationships to users and workspaces.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from monday.types.user import User


@dataclass
class Team:
    """
    Represents a Monday.com team with its members and owners.

    This dataclass maps to the Monday.com API team object structure, containing
    fields like name, picture URL, owners, and team members.

    See also:
        https://developer.monday.com/api-reference/reference/teams#fields
    """

    id: str = ''
    """The team's unique identifier"""

    name: str = ''
    """The team's name"""

    owners: list['User'] | None = None
    """The users that are the team's owners (see :class:`User <monday.types.User>`)"""

    picture_url: str = ''
    """The team's picture URL"""

    users: list['User'] | None = None
    """The team's users (see :class:`User <monday.types.User>`)"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        result = {}

        if self.id:
            result['id'] = self.id
        if self.name:
            result['name'] = self.name
        if self.owners:
            result['owners'] = [owner.to_dict() if hasattr(owner, 'to_dict') else owner for owner in self.owners]
        if self.picture_url:
            result['picture_url'] = self.picture_url
        if self.users:
            result['users'] = [user.to_dict() if hasattr(user, 'to_dict') else user for user in self.users]

        return result

    @classmethod
    # pylint: disable=import-outside-toplevel
    def from_dict(cls, data: dict[str, Any]) -> Team:
        """Create from dictionary."""
        from monday.types.user import User

        return cls(
            id=str(data.get('id', '')),
            name=str(data.get('name', '')),
            owners=[User.from_dict(owner) if hasattr(User, 'from_dict') else owner for owner in data.get('owners', [])] if data.get('owners') else None,
            picture_url=str(data.get('picture_url', '')),
            users=[User.from_dict(user) if hasattr(User, 'from_dict') else user for user in data.get('users', [])] if data.get('users') else None
        )
