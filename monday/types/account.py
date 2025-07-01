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
Monday.com API account type definitions and structures.

This module contains dataclasses that represent Monday.com account objects,
including accounts, plans, and account products with their settings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class Plan:
    """
    Represents a Monday.com account plan with its limits and features.

    This dataclass maps to the Monday.com API plan object structure, containing
    fields like max users, period, tier, and version.

    See also:
        https://developer.monday.com/api-reference/reference/plan#fields
    """

    max_users: int = 0
    """The maximum number of users allowed on the plan. This will be ``0`` for free and developer accounts"""

    period: str = ''
    """The plan's time period"""

    tier: str = ''
    """The plan's tier"""

    version: int = 0
    """The plan's version"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        result = {}
        if self.max_users:
            result['max_users'] = self.max_users
        if self.period:
            result['period'] = self.period
        if self.tier:
            result['tier'] = self.tier
        if self.version:
            result['version'] = self.version
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Plan:
        """Create from dictionary."""
        return cls(
            max_users=int(data.get('max_users', 0)),
            period=str(data.get('period', '')),
            tier=str(data.get('tier', '')),
            version=int(data.get('version', 0))
        )


@dataclass
class AccountProduct:
    """
    Represents a Monday.com account product with its configuration.

    This dataclass maps to the Monday.com API account product object structure, containing
    fields like kind, default workspace, and unique identifier.

    See also:
        https://developer.monday.com/api-reference/reference/other-types#account-product
    """

    id: str = ''
    """The unique identifier of the account product"""

    default_workspace_id: str = ''
    """The account product's default workspace ID"""

    kind: Literal[
        'core',
        'crm',
        'forms',
        'marketing',
        'projectManagement',
        'project_management',
        'service',
        'software',
        'whiteboard'
    ] | None = None
    """The account product"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        result = {}
        if self.id:
            result['id'] = self.id
        if self.default_workspace_id:
            result['default_workspace_id'] = self.default_workspace_id
        if self.kind:
            result['kind'] = self.kind
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AccountProduct:
        """Create from dictionary."""
        return cls(
            id=data.get('id', ''),
            default_workspace_id=str(data.get('default_workspace_id', '')),
            kind=data.get('kind')
        )


@dataclass
class Account:
    """
    Represents a Monday.com account with its settings and plan information.

    This dataclass maps to the Monday.com API account object structure, containing
    fields like name, plan, products, and account settings.

    See also:
        https://developer.monday.com/api-reference/reference/account#fields
    """

    active_members_count: int = 0
    """The number of active users in the account - includes active users across all products who are not guests or viewers"""

    country_code: str = ''
    """The account's two-letter country code in ISO3166 format. The result is based on the location of the first account admin"""

    first_day_of_the_week: Literal['monday', 'sunday'] | None = None
    """The first day of the week for the account"""

    id: str = ''
    """The account's unique identifier"""

    logo: str = ''
    """The account's logo"""

    name: str = ''
    """The account's name"""

    plan: Plan | None = None
    """The account's payment plan. Returns ``None`` for accounts with the multi-product infrastructure"""

    products: AccountProduct | None = None
    """The account's active products"""

    show_timeline_weekends: bool | None = None
    """Returns ``True`` if weekends appear in the timeline"""

    sign_up_product_kind: str = ''
    """The product the account first signed up to"""

    slug: str = ''
    """The account's slug"""

    tier: str = ''
    """The account's tier. For accounts with multiple products, this will return the highest tier across all products"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        result = {}

        if self.active_members_count:
            result['active_members_count'] = self.active_members_count
        if self.country_code:
            result['country_code'] = self.country_code
        if self.first_day_of_the_week:
            result['first_day_of_the_week'] = self.first_day_of_the_week
        if self.id:
            result['id'] = self.id
        if self.logo:
            result['logo'] = self.logo
        if self.name:
            result['name'] = self.name
        if self.plan:
            result['plan'] = self.plan.to_dict()
        if self.products:
            result['products'] = self.products.to_dict()
        if self.show_timeline_weekends:
            result['show_timeline_weekends'] = self.show_timeline_weekends
        if self.sign_up_product_kind:
            result['sign_up_product_kind'] = self.sign_up_product_kind
        if self.slug:
            result['slug'] = self.slug
        if self.tier:
            result['tier'] = self.tier

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Account:
        """Create from dictionary."""
        return cls(
            active_members_count=int(data.get('active_members_count', 0)),
            country_code=str(data.get('country_code', '')),
            first_day_of_the_week=data.get('first_day_of_the_week'),
            id=str(data.get('id', '')),
            logo=str(data.get('logo', '')),
            name=str(data.get('name', '')),
            plan=Plan.from_dict(data['plan']) if data.get('plan') else None,
            products=AccountProduct.from_dict(data['products']) if data.get('products') else None,
            show_timeline_weekends=data.get('show_timeline_weekends'),
            sign_up_product_kind=data.get('sign_up_product_kind', ''),
            slug=data.get('slug', ''),
            tier=data.get('tier', '')
        )
