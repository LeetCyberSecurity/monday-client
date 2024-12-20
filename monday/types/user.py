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
Type definitions for monday.com API user related structures.
"""

from __future__ import annotations

from typing import Literal, Required, TypedDict

from monday.types.account import Account
from monday.types.team import Team


class User(TypedDict, total=False):
    """
    Type definitions for monday.com API user structures.

    These types correspond to Monday.com's user fields as documented in their API reference:
    https://developer.monday.com/api-reference/reference/users#fields
    """

    account: Required[Account]
    """The user's account"""

    birthday: str
    """The user's date of birth. Returned as ``YYYY-MM-DD``"""

    country_code: str
    """The user's country code"""

    created_at: str
    """The user's creation date. Returned as ``YYYY-MM-DD``"""

    current_language: str
    """The user's language"""

    email: Required[str]
    """The user's email"""

    enabled: Required[bool]
    """Returns ``True`` if the user is enabled"""

    id: Required[str]
    """The user's unique identifier"""

    is_admin: bool
    """Returns ``True`` if the user is an admin"""

    is_guest: bool
    """Returns ``True`` if the user is a guest"""

    is_pending: bool
    """Returns ``True`` if the user didn't confirm their email yet"""

    is_view_only: bool
    """Returns ``True`` if the user is only a viewer"""

    is_verified: bool
    """Returns ``True`` if the user verified their email"""

    join_date: str
    """The date the user joined the account. Returned as ``YYYY-MM-DD``"""

    last_activity: str
    """The last date and time the user was active. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    location: str
    """The user's location"""

    mobile_phone: str
    """The user's mobile phone number"""

    name: Required[str]
    """The user's name"""

    out_of_office: OutOfOffice
    """The user's out-of-office status"""

    phone: str
    """The user's phone number"""

    photo_original: str
    """Returns the URL of the user's uploaded photo in its original size"""

    photo_small: str
    """Returns the URL of the user's uploaded photo in a small size (150x150 px)"""

    photo_thumb: str
    """Returns the URL of the user's uploaded photo in a small thumbnail size (50x50 px)"""

    photo_tiny: str
    """Returns the URL of the user's uploaded photo in tiny size (30x30 px)"""

    sign_up_product_kind: str
    """The product the user first signed up to"""

    teams: list[Team]
    """The user's teams"""

    time_zone_identifier: str
    """The user's timezone identifier"""

    title: str
    """The user's title"""

    url: Required[str]
    """The user's profile URL"""

    utc_hours_diff: int
    """The user's UTC hours difference"""


class OutOfOffice(TypedDict, total=False):
    """Type definition for monday.com API user out of office settings"""

    active: bool
    """Returns ``True`` if the out of office status is in effect"""

    disable_notifications: bool
    """Returns ``True`` if the user has notifications disabled"""

    end_date: str
    """Out of office end date. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    start_date: str
    """Out of office start date. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    type: Literal[
        'family_time',
        'focus_mode',
        'on_break',
        'out_of_office',
        'out_sick',
        'working_from_home',
        'working_outside'
    ]
    """Out of office type"""
