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
Type definitions for monday.com API workspace related structures.
"""

from __future__ import annotations

from typing import Literal, Required, TypedDict

from monday.types.account import AccountProduct
from monday.types.team import Team
from monday.types.user import User


class Workspace(TypedDict, total=False):
    """
    Type definitions for monday.com API workspace structures.

    These types correspond to Monday.com's workspace fields as documented in their API reference:
    https://developer.monday.com/api-reference/reference/workspaces#fields
    """

    account_product: AccountProduct
    """The account product that contains the workspace"""

    created_at: str
    """The workspace's creation date. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    description: str
    """The workspace's description"""

    id: str
    """The workspace's unique identifier"""

    is_default_workspace: bool
    """Returns ``True`` if a workspace is the default workspace of the product or account"""

    kind: Literal['closed', 'open']
    """The workspace's kind"""

    name: Required[str]
    """The workspace's name"""

    owners_subscribers: list[User]
    """The workspace's owners"""

    settings: WorkspaceSettings
    """The workspace's settings"""

    state: Literal['active', 'archived', 'deleted']
    """The state of the workspace"""

    team_owners_subscribers: list[Required[Team]]
    """The workspace's team owners"""

    teams_subscribers: list[Team]
    """The teams subscribed to the workspace"""

    users_subscribers: list[User]
    """The users subscribed to the workspace"""


class WorkspaceSettings(TypedDict, total=False):
    """
    Type definitions for monday.com API workspace settings structures.

    These types correspond to Monday.com's workspace settings fields as documented in their API reference:
    https://developer.monday.com/api-reference/reference/other-types#workspace-settings
    """

    icon: WorkspaceIcon
    """The workspace's icon"""


class WorkspaceIcon(TypedDict, total=False):
    """
    Type definitions for monday.com API workspace icon structures.

    These types correspond to Monday.com's workspace icon fields as documented in their API reference:
    https://developer.monday.com/api-reference/reference/other-types#workspace-icon
    """

    color: str
    """The hex value of the icon's color. Used as a background for the image"""

    image: str
    """The temporary public image URL (valid for one hour)"""
