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
Monday.com API update type definitions and structures.

This module contains dataclasses that represent Monday.com update objects,
including updates (comments) and their relationships to items and users.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from monday.types.asset import Asset
    from monday.types.user import User


@dataclass
class Update:
    """
    Represents a Monday.com update (comment) with its content and metadata.

    This dataclass maps to the Monday.com API update object structure, containing
    fields like body, creator, replies, and associated assets.

    See also:
        https://developer.monday.com/api-reference/reference/updates#fields
    """

    assets: list[Asset] | None = None
    """The update's assets/files"""

    body: str = ''
    """The update's body"""

    created_at: str = ''
    """The update's creation date. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    creator: User | None = None
    """The update's creator"""

    creator_id: str = ''
    """The update's creator unique identifier"""

    id: str = ''
    """The update's unique identifier"""

    item_id: str = ''
    """The update's item unique identifier"""

    parent_id: str = ''
    """The update's parent unique identifier"""

    replies: list['Update'] | None = None
    """The update's replies"""

    text_body: str = ''
    """The update's text body"""

    updated_at: str = ''
    """The update's last update date. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        result = {}

        if self.assets:
            result['assets'] = [asset.to_dict() if hasattr(asset, 'to_dict') else asset for asset in self.assets]
        if self.body:
            result['body'] = self.body
        if self.created_at:
            result['created_at'] = self.created_at
        if self.creator:
            result['creator'] = self.creator.to_dict()
        if self.creator_id:
            result['creator_id'] = self.creator_id
        if self.id:
            result['id'] = self.id
        if self.item_id:
            result['item_id'] = self.item_id
        if self.parent_id:
            result['parent_id'] = self.parent_id
        if self.replies:
            result['replies'] = [reply.to_dict() if hasattr(reply, 'to_dict') else reply for reply in self.replies]
        if self.text_body:
            result['text_body'] = self.text_body
        if self.updated_at:
            result['updated_at'] = self.updated_at

        return result

    @classmethod
    # pylint: disable=import-outside-toplevel
    def from_dict(cls, data: dict[str, Any]) -> Update:
        """Create from dictionary."""
        from monday.types.asset import Asset
        from monday.types.user import User

        return cls(
            assets=[Asset.from_dict(asset) if hasattr(Asset, 'from_dict') else asset for asset in data.get('assets', [])] if data.get('assets') else None,
            body=str(data.get('body', '')),
            created_at=str(data.get('created_at', '')),
            creator=User.from_dict(data['creator']) if data.get('creator') else None,
            creator_id=str(data.get('creator_id', '')),
            id=str(data.get('id', '')),
            item_id=str(data.get('item_id', '')),
            parent_id=str(data.get('parent_id', '')),
            replies=[Update.from_dict(reply) if hasattr(Update, 'from_dict') else reply for reply in data.get('replies', [])] if data.get('replies') else None,
            text_body=str(data.get('text_body', '')),
            updated_at=str(data.get('updated_at', ''))
        )
