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
Type definitions for monday.com API update related structures.
"""

from typing import TYPE_CHECKING, Literal, Required, TypedDict

from monday.types.asset import Asset
from monday.types.user import User

if TYPE_CHECKING:
    from monday.types.item import Item


class Like(TypedDict, total=False):
    """
    Type definitions for monday.com API like structures.

    These types correspond to Monday.com's like fields as documented in their API reference:
    https://developer.monday.com/api-reference/reference/other-types#like
    """

    created_at: str
    """The like's creation date. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    creator: User
    """The user that liked the update"""

    creator_id: str
    """The unique identifier of the like's creator"""

    id: Required[str]
    """The like's unique identifier"""

    reaction_type: Literal[
        'Clap',
        'Happy',
        'Like',
        'Love',
        'PlusOne',
        'Rocks',
        'Trophy',
        'Wow'
    ]
    """The reaction type"""

    updated_at: str
    """The like's last updated date. Returned as ``YYYY-MM-DDTHH:MM:SS``"""


class Reply(TypedDict, total=False):
    """
    Type definitions for monday.com API reply structures.

    These types correspond to Monday.com's reply fields as documented in their API reference:
    https://developer.monday.com/api-reference/reference/other-types#reply
    """

    body: Required[str]
    """The reply's HTML-formatted body"""

    created_at: str
    """The reply's creation date. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    creator: User
    """The reply's creator"""

    creator_id: str
    """The unique identifier of the reply's creator"""

    id: Required[str]
    """The reply's unique identifier"""

    kind: Required[str]
    """The reply's kind"""

    likes: Required[list[Like]]
    """The reply's likes"""

    pinned_to_top: Required[list[int]]
    """The reply's pin to top data"""

    text_body: str
    """The reply's text body"""

    updated_at: str
    """The reply's last updated date. Returned as ``YYYY-MM-DDTHH:MM:SS``"""


class Watcher(TypedDict, total=False):
    """
    Type definitions for monday.com API watcher/viewer structures.

    These types correspond to Monday.com's watcher/viewer fields as documented in their API reference:
    https://developer.monday.com/api-reference/reference/viewers#fields
    """

    medium: Required[Literal['email', 'mobile', 'web']]
    """The medium the user's viewed the update from"""

    user: User
    """The user who viewed the update"""

    user_id: Required[str]
    """The unique identifier of the user who viewed the update"""


class Update(TypedDict, total=False):
    """
    Type definitions for monday.com API update structures.

    These types correspond to Monday.com's update fields as documented in their API reference:
    https://developer.monday.com/api-reference/reference/updates#fields
    """

    assets: list[Asset]
    """The update's assets/files"""

    body: Required[str]
    """The update's HTML-formatted body"""

    created_at: str
    """The update's creation date. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    creator: User
    """The update's creator"""

    creator_id: str
    """The unique identifier of the update's creator"""

    edited_at: Required[str]
    """The update's creation date. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    id: Required[str]
    """The update's unique identifier"""

    item: 'Item'
    """The update's :class:`Item <monday.types.Item>`"""

    item_id: str
    """The update's item ID"""

    likes: Required[list[Like]]
    """The update's likes"""

    pinned_to_top: Required[list[int]]
    """The update's pin to top data"""

    replies: list[Reply]
    """The update's replies"""

    text_body: str
    """The update's text body"""

    updated_at: str
    """The date the update was last edited"""

    watchers: Required[Watcher]
    """The update's viewers"""
