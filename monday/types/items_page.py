"""Common type definitions shared between multiple modules."""

from typing import TYPE_CHECKING, Required, TypedDict

if TYPE_CHECKING:
    from monday.types.item import Item


class ItemsPage(TypedDict, total=False):
    """Type definition for ItemsPage structure."""

    items: Required[list['Item']]
    """List of items"""

    cursor: str
    """cursor for retrieving the next page of items"""
