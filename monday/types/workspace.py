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
Monday.com API workspace type definitions and structures.

This module contains dataclasses that represent Monday.com workspace objects,
including workspaces and their relationships to boards and users.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from monday.types.board import Board
    from monday.types.user import User


@dataclass
class Workspace:
    """
    Represents a Monday.com workspace with its boards and members.

    This dataclass maps to the Monday.com API workspace object structure, containing
    fields like name, description, boards, owners, and subscribers.

    See also:
        https://developer.monday.com/api-reference/reference/workspaces#fields
    """

    boards: list[Board] | None = None
    """The workspace's boards"""

    created_at: str = ''
    """The workspace's creation date. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    description: str = ''
    """The workspace's description"""

    id: str = ''
    """The workspace's unique identifier"""

    kind: str = ''
    """The workspace's kind"""

    name: str = ''
    """The workspace's name"""

    owners: list[User] | None = None
    """The workspace's owners"""

    picture_url: str = ''
    """The workspace's picture URL"""

    settings_str: str = ''
    """The workspace's settings as a JSON string"""

    state: str = ''
    """The workspace's state"""

    subscribers: list[User] | None = None
    """The workspace's subscribers"""

    teams: list[User] | None = None
    """The workspace's teams"""

    updated_at: str = ''
    """The workspace's last update date. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        result = {}

        if self.boards:
            result['boards'] = [board.to_dict() if hasattr(board, 'to_dict') else board for board in self.boards]
        if self.created_at:
            result['created_at'] = self.created_at
        if self.description:
            result['description'] = self.description
        if self.id:
            result['id'] = self.id
        if self.kind:
            result['kind'] = self.kind
        if self.name:
            result['name'] = self.name
        if self.owners:
            result['owners'] = [owner.to_dict() if hasattr(owner, 'to_dict') else owner for owner in self.owners]
        if self.picture_url:
            result['picture_url'] = self.picture_url
        if self.settings_str:
            result['settings_str'] = self.settings_str
        if self.state:
            result['state'] = self.state
        if self.subscribers:
            result['subscribers'] = [subscriber.to_dict() if hasattr(subscriber, 'to_dict') else subscriber for subscriber in self.subscribers]
        if self.teams:
            result['teams'] = [team.to_dict() if hasattr(team, 'to_dict') else team for team in self.teams]
        if self.updated_at:
            result['updated_at'] = self.updated_at

        return result

    @classmethod
    # pylint: disable=import-outside-toplevel
    def from_dict(cls, data: dict[str, Any]) -> Workspace:
        """Create from dictionary."""
        from monday.types.board import Board
        from monday.types.user import User

        return cls(
            boards=[Board.from_dict(board) if hasattr(Board, 'from_dict') else board for board in data.get('boards', [])] if data.get('boards') else None,
            created_at=str(data.get('created_at', '')),
            description=str(data.get('description', '')),
            id=str(data.get('id', '')),
            kind=str(data.get('kind', '')),
            name=str(data.get('name', '')),
            owners=[User.from_dict(owner) if hasattr(User, 'from_dict') else owner for owner in data.get('owners', [])] if data.get('owners') else None,
            picture_url=str(data.get('picture_url', '')),
            settings_str=str(data.get('settings_str', '')),
            state=str(data.get('state', '')),
            subscribers=[User.from_dict(subscriber) if hasattr(User, 'from_dict') else subscriber for subscriber in data.get('subscribers', [])] if data.get('subscribers') else None,
            teams=[User.from_dict(team) if hasattr(User, 'from_dict') else team for team in data.get('teams', [])] if data.get('teams') else None,
            updated_at=str(data.get('updated_at', ''))
        )
