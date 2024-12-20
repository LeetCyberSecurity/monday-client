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
Type definitions for monday.com API account related structures.
"""

from __future__ import annotations

from typing import Literal, Required, TypedDict


class Account(TypedDict, total=False):
    """
    Type definitions for monday.com API account structures.

    These types correspond to Monday.com's account fields as documented in their API reference:
    https://developer.monday.com/api-reference/reference/account#fields
    """

    active_members_count: int
    """The number of active users in the account - includes active users across all products who are not guests or viewers"""

    country_code: str
    """The account's two-letter country code in ISO3166 format. The result is based on the location of the first account admin"""

    first_day_of_the_week: Literal['monday', 'sunday']
    """The first day of the week for the account"""

    id: Required[str]
    """The account's unique identifier"""

    logo: str
    """The account's logo"""

    name: Required[str]
    """The account's name"""

    plan: Plan
    """The account's payment plan. Returns ``None`` for accounts with the multi-product infrastructure"""

    products: AccountProduct
    """The account's active products"""

    show_timeline_weekends: bool
    """Returns ``True`` if weekends appear in the timeline"""

    sign_up_product_kind: str
    """The product the account first signed up to"""

    slug: Required[str]
    """The account's slug"""

    tier: str
    """The account's tier. For accounts with multiple products, this will return the highest tier across all products"""


class AccountProduct(TypedDict, total=False):
    """
    Type definitions for monday.com API account product structures.

    These types correspond to Monday.com's account product fields as documented in their API reference:
    https://developer.monday.com/api-reference/reference/other-types#account-product
    """

    id: int
    """The unique identifier of the account product"""

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
    ]
    """The account product"""


class Plan(TypedDict, total=False):
    """
    Type definitions for monday.com API account plan structures.

    These types correspond to Monday.com's account plan fields as documented in their API reference:
    https://developer.monday.com/api-reference/reference/plan#fields
    """

    max_users: Required[int]
    """The maximum number of users allowed on the plan. This will be ``0`` for free and developer accounts"""

    period: str
    """The plan's time period"""

    tier: str
    """The plan's tier"""

    version: int
    """The plan's version"""
