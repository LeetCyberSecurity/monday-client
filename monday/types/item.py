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
Monday.com API item type definitions and structures.

This module contains dataclasses that represent Monday.com item objects,
including items, item lists, and their relationships to boards and groups.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from monday.types.asset import Asset
    from monday.types.board import Board
    from monday.types.column import ColumnValue
    from monday.types.group import Group
    from monday.types.subitem import Subitem
    from monday.types.update import Update
    from monday.types.user import User


@dataclass
class ItemList:
    """
    Type definition for a list of items associated with a board.

    This structure is used by the Boards.get_items() method to return items
    grouped by their board ID.
    """

    board_id: str
    """The ID of the board that contains the items"""

    items: list[Item]
    """The list of items belonging to the board"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {
            'id': self.board_id,
            'items': [
                item.to_dict() if hasattr(item, 'to_dict') else item
                for item in self.items
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ItemList:
        """Create from dictionary."""
        return cls(
            board_id=str(data.get('id', '')),
            items=[
                Item.from_dict(item) if isinstance(item, dict) else item
                for item in data.get('items', [])
            ],
        )


@dataclass
class Item:
    """
    Represents a Monday.com item (row) with its data and relationships.

    This dataclass maps to the Monday.com API item object structure, containing
    fields like name, column values, updates, and associated board/group information.

    See Also:
        https://developer.monday.com/api-reference/reference/items#fields

    """

    assets: list[Asset] | None = None
    """The item's assets/files"""

    board: Board | None = None
    """The board that contains the item"""

    column_values: list[ColumnValue] | None = None
    """The item's column values"""

    created_at: str = ''
    """The item's creation date. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    creator: User | None = None
    """The item's creator"""

    creator_id: str = ''
    """The unique identifier of the item's creator. Returns ``None`` if the item was created by default on the board."""

    group: Group | None = None
    """The item's group"""

    id: str = ''
    """The item's unique identifier"""

    name: str = ''
    """The item's name"""

    state: str = ''
    """The item's state"""

    subitems: list[Subitem] | None = None
    """The item's subitems"""

    subscribers: list[User] | None = None
    """The item's subscribers"""

    updated_at: str = ''
    """The date the item was last updated. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    updates: list[Update] | None = None
    """The item's updates"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""

        def _convert_list(items: list, converter_name: str = 'to_dict') -> list:
            """Convert list items using their converter method if available."""
            return [
                getattr(item, converter_name)()
                if hasattr(item, converter_name)
                else item
                for item in items
            ]

        data = {
            'assets': _convert_list(self.assets) if self.assets else None,
            'board': self.board.to_dict() if self.board else None,
            'column_values': _convert_list(self.column_values)
            if self.column_values
            else None,
            'created_at': self.created_at,
            'creator': self.creator.to_dict() if self.creator else None,
            'creator_id': self.creator_id,
            'group': self.group.to_dict() if self.group else None,
            'id': self.id,
            'name': self.name,
            'state': self.state,
            'subitems': _convert_list(self.subitems) if self.subitems else None,
            'subscribers': _convert_list(self.subscribers)
            if self.subscribers
            else None,
            'updated_at': self.updated_at,
            'updates': _convert_list(self.updates) if self.updates else None,
        }

        return {k: v for k, v in data.items() if v}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Item:
        """Create from dictionary."""
        from monday.types.asset import Asset  # noqa: PLC0415
        from monday.types.board import Board  # noqa: PLC0415
        from monday.types.column import ColumnValue  # noqa: PLC0415
        from monday.types.group import Group  # noqa: PLC0415
        from monday.types.subitem import Subitem  # noqa: PLC0415
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
            group=Group.from_dict(data['group']) if data.get('group') else None,
            id=str(data.get('id', '')),
            name=str(data.get('name', '')),
            state=str(data.get('state', '')),
            subitems=[
                Subitem.from_dict(subitem) if hasattr(Subitem, 'from_dict') else subitem
                for subitem in data.get('subitems', [])
            ]
            if data.get('subitems')
            else None,
            subscribers=[
                User.from_dict(subscriber) if hasattr(User, 'from_dict') else subscriber
                for subscriber in data.get('subscribers', [])
            ]
            if data.get('subscribers')
            else None,
            updated_at=str(data.get('updated_at', '')),
            updates=[
                Update.from_dict(update) if hasattr(Update, 'from_dict') else update
                for update in data.get('updates', [])
            ]
            if data.get('updates')
            else None,
        )


@dataclass
class ItemsPage:
    """
    Represents a paginated page of Monday.com items with cursor for navigation.

    This dataclass maps to the Monday.com API items page structure, containing
    a list of items and a cursor for retrieving the next page.

    See Also:
        https://developer.monday.com/api-reference/reference/items#fields

    """

    items: list[Any] | None = None
    """List of items"""

    cursor: str = ''
    """cursor for retrieving the next page of items"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        result = {}

        if self.items:
            result['items'] = [
                item.to_dict() if hasattr(item, 'to_dict') else item
                for item in self.items
            ]
        if self.cursor:
            result['cursor'] = self.cursor

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ItemsPage:
        """Create from dictionary."""
        return cls(
            items=[
                Item.from_dict(item) if hasattr(Item, 'from_dict') else item
                for item in data.get('items', [])
            ]
            if data.get('items')
            else None,
            cursor=str(data.get('cursor', '')),
        )


@dataclass
class OrderBy:
    """Structure for ordering items in queries."""

    column_id: str
    """The ID of the column to order by"""

    direction: Literal['asc', 'desc'] = 'asc'
    """The direction to order items. Defaults to 'asc' if not specified"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {'column_id': self.column_id, 'direction': self.direction}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OrderBy:
        """Create from dictionary."""
        return cls(
            column_id=str(data['column_id']), direction=data.get('direction', 'asc')
        )


@dataclass
class QueryRule:
    """Structure for defining item query rules."""

    column_id: str
    """The ID of the column to filter on"""

    compare_value: list[str | int]
    """List of values to compare against"""

    operator: Literal[
        'any_of',
        'not_any_of',
        'is_empty',
        'is_not_empty',
        'greater_than',
        'greater_than_or_equals',
        'lower_than',
        'lower_than_or_equal',
        'between',
        'not_contains_text',
        'contains_text',
        'contains_terms',
        'starts_with',
        'ends_with',
        'within_the_next',
        'within_the_last',
    ] = 'any_of'
    """The comparison operator to use. Defaults to ``any_of`` if not specified"""

    compare_attribute: str = ''
    """The attribute to compare (optional)"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        result = {
            'column_id': self.column_id,
            'compare_value': self.compare_value,
            'operator': self.operator,
        }
        if self.compare_attribute:
            result['compare_attribute'] = self.compare_attribute
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QueryRule:
        """Create from dictionary."""
        # Handle cases where column_id might not be present but compare_attribute is
        column_id = data.get('column_id', '')
        if not column_id and 'compare_attribute' in data:
            # Use compare_attribute as column_id if column_id is not present
            column_id = data['compare_attribute']

        return cls(
            column_id=str(column_id),
            compare_value=data['compare_value'],
            operator=data.get('operator', 'any_of'),
            compare_attribute=data.get('compare_attribute', ''),
        )


@dataclass
class QueryParams:
    """
    Structure for complex item queries.

    Example:
        .. code-block:: python

            query_params = QueryParams(
                rules=[
                    QueryRule(
                        column_id='status',
                        compare_value=['Done', 'In Progress'],
                        operator='any_of',
                    )
                ],
                operator='and',
                order_by=OrderBy(column_id='date', direction='desc'),
            )

    """

    rules: list[QueryRule] = field(default_factory=list)
    """List of query rules to apply"""

    operator: Literal['and', 'or'] = 'and'
    """How to combine multiple rules. Defaults to 'and' if not specified"""

    order_by: OrderBy | None = None
    """Optional ordering configuration"""

    ids: list[int] = field(default_factory=list)
    """The specific item IDs to return. The maximum is 100."""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        result = {
            'rules': [rule.to_dict() for rule in self.rules],
            'operator': self.operator,
        }
        if self.order_by:
            result['order_by'] = self.order_by.to_dict()
        if self.ids:
            result['ids'] = self.ids
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QueryParams:
        """Create from dictionary."""
        return cls(
            rules=[QueryRule.from_dict(rule) for rule in data.get('rules', [])],
            operator=data.get('operator', 'and'),
            order_by=OrderBy.from_dict(data['order_by'])
            if data.get('order_by')
            else None,
            ids=data.get('ids', []),
        )
