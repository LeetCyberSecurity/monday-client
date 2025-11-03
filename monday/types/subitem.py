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
Monday.com API subitem type definitions and structures.

This module contains dataclasses that represent Monday.com subitem objects,
including subitems and their relationships to parent items and boards.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from monday.types.asset import Asset
    from monday.types.board import Board
    from monday.types.column import ColumnValue
    from monday.types.group import Group
    from monday.types.item import Item
    from monday.types.update import Update
    from monday.types.user import User


@dataclass
class SubitemList:
    """
    Type definition for a list of subitems associated with a parent item.

    This structure is used by the Subitems.query() method to return subitems
    grouped by their parent item ID.
    """

    item_id: str
    """The ID of the parent item that contains the subitems"""

    subitems: list[Subitem]
    """The list of subitems belonging to the parent item"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {
            'id': self.item_id,
            'subitems': [
                subitem.to_dict() if hasattr(subitem, 'to_dict') else subitem
                for subitem in self.subitems
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SubitemList:
        """Create from dictionary."""
        return cls(
            item_id=str(data.get('id', '')),
            subitems=[
                Subitem.from_dict(subitem) if isinstance(subitem, dict) else subitem
                for subitem in data.get('subitems', [])
            ],
        )


@dataclass
class Subitem:
    """
    Represents a Monday.com subitem with its properties and relationships.

    This dataclass maps to the Monday.com API subitem object structure, containing
    fields like name, state, and associated board/group information.

    See Also:
        https://developer.monday.com/api-reference/reference/subitems#fields

    """

    assets: list['Asset'] | None = None
    """The subitem's assets/files"""

    board: Board | None = None
    """The subitem's board"""

    created_at: str = ''
    """The subitem's creation date. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    column_values: list['ColumnValue'] | None = None
    """The subitem's column values"""

    created_at: str = ''
    """The subitem's creation date. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    creator: 'User' | None = None
    """The subitem's creator"""

    creator_id: str = ''
    """The subitem's creator unique identifier"""

    email: str = ''
    """The subitem's email"""

    group: Group | None = None
    """The subitem's group"""

    id: str = ''
    """The subitem's unique identifier"""

    item_id: str = ''
    """The subitem's parent item unique identifier"""

    linked_items: list['Item'] | None = None
    """The subitem's linked items"""

    parent_item: 'Item' | None = None
    """The subitem's parent item object when requested via fields (e.g., parent_item { id name })"""

    relative_link: str = ''
    """The subitem's relative path"""

    name: str = ''
    """The subitem's name"""

    state: str = ''
    """The subitem's state"""

    updated_at: str = ''
    """The subitem's last update date. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    subitems: list['Item'] | None = None
    """The subitem's subitems (nested items)"""

    subscribers: list['User'] | None = None
    """The subitem's subscribers"""

    updates: list['Update'] | None = None
    """The subitem's updates"""

    url: str = ''
    """The subitem's link"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        result = {}

        if self.assets:
            result['assets'] = [
                asset.to_dict() if hasattr(asset, 'to_dict') else asset
                for asset in self.assets
            ]
        if self.board:
            result['board'] = self.board.to_dict()
        if self.column_values:
            result['column_values'] = [
                cv.to_dict() if hasattr(cv, 'to_dict') else cv
                for cv in self.column_values
            ]
        if self.created_at:
            result['created_at'] = self.created_at
        if self.creator:
            result['creator'] = (
                self.creator.to_dict() if hasattr(self.creator, 'to_dict') else self.creator
            )
        if self.creator_id:
            result['creator_id'] = self.creator_id
        if self.email:
            result['email'] = self.email
        if self.group:
            result['group'] = self.group.to_dict()
        if self.id:
            result['id'] = self.id
        if self.item_id:
            result['item_id'] = self.item_id
        if self.linked_items:
            result['linked_items'] = [
                li.to_dict() if hasattr(li, 'to_dict') else li for li in self.linked_items
            ]
        if self.parent_item:
            # Avoid cycles; only include if present
            result['parent_item'] = (
                self.parent_item.to_dict()
                if hasattr(self.parent_item, 'to_dict')
                else self.parent_item
            )
        if self.name:
            result['name'] = self.name
        if self.relative_link:
            result['relative_link'] = self.relative_link
        if self.state:
            result['state'] = self.state
        if self.updated_at:
            result['updated_at'] = self.updated_at
        if self.subitems:
            result['subitems'] = [
                si.to_dict() if hasattr(si, 'to_dict') else si for si in self.subitems
            ]
        if self.subscribers:
            result['subscribers'] = [
                u.to_dict() if hasattr(u, 'to_dict') else u for u in self.subscribers
            ]
        if self.updates:
            result['updates'] = [
                up.to_dict() if hasattr(up, 'to_dict') else up for up in self.updates
            ]
        if self.url:
            result['url'] = self.url

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Subitem:
        """Create from dictionary."""
        from monday.types.asset import Asset  # noqa: PLC0415
        from monday.types.board import Board  # noqa: PLC0415
        from monday.types.column import ColumnValue  # noqa: PLC0415
        from monday.types.group import Group  # noqa: PLC0415
        from monday.types.item import Item  # noqa: PLC0415
        from monday.types.update import Update  # noqa: PLC0415
        from monday.types.user import User  # noqa: PLC0415

        return cls(
            assets=[
                Asset.from_dict(asset) if hasattr(Asset, 'from_dict') else asset
                for asset in data.get('assets', [])
            ]
            if data.get('assets')
            else None,
            board=Board.from_dict(data['board']) if data.get('board') else None,
            column_values=[
                ColumnValue.from_dict(cv) if hasattr(ColumnValue, 'from_dict') else cv
                for cv in data.get('column_values', [])
            ]
            if data.get('column_values')
            else None,
            created_at=str(data.get('created_at', '')),
            creator=User.from_dict(data['creator']) if data.get('creator') else None,
            creator_id=str(data.get('creator_id', '')),
            email=str(data.get('email', '')),
            group=Group.from_dict(data['group']) if data.get('group') else None,
            id=str(data.get('id', '')),
            item_id=str(data.get('item_id', '')),
            linked_items=[
                Item.from_dict(li) if isinstance(li, dict) else li
                for li in data.get('linked_items', [])
            ]
            if data.get('linked_items')
            else None,
            parent_item=Item.from_dict(data['parent_item'])
            if data.get('parent_item')
            else None,
            name=str(data.get('name', '')),
            relative_link=str(data.get('relative_link', '')),
            state=str(data.get('state', '')),
            updated_at=str(data.get('updated_at', '')),
            subitems=[
                Item.from_dict(si) if isinstance(si, dict) else si
                for si in data.get('subitems', [])
            ]
            if data.get('subitems')
            else None,
            subscribers=[
                User.from_dict(u) if hasattr(User, 'from_dict') else u
                for u in data.get('subscribers', [])
            ]
            if data.get('subscribers')
            else None,
            updates=[
                Update.from_dict(up) if hasattr(Update, 'from_dict') else up
                for up in data.get('updates', [])
            ]
            if data.get('updates')
            else None,
            url=str(data.get('url', '')),
        )
