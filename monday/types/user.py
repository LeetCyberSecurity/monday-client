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
Monday.com API user type definitions and structures.

This module contains dataclasses that represent Monday.com user objects,
including user profiles, out-of-office settings, and account information.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from monday.types.account import Account
from monday.types.team import Team


@dataclass
class OutOfOffice:
    """Type definition for monday.com API user out of office settings"""

    active: bool = False
    """Returns ``True`` if the out of office status is in effect"""

    disable_notifications: bool = False
    """Returns ``True`` if the user has notifications disabled"""

    end_date: str = ''
    """Out of office end date. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    start_date: str = ''
    """Out of office start date. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    type: Literal[
        'family_time',
        'focus_mode',
        'on_break',
        'out_of_office',
        'out_sick',
        'working_from_home',
        'working_outside'
    ] | None = None
    """Out of office type"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        result = {}

        if self.active:
            result['active'] = self.active
        if self.disable_notifications:
            result['disable_notifications'] = self.disable_notifications
        if self.end_date:
            result['end_date'] = self.end_date
        if self.start_date:
            result['start_date'] = self.start_date
        if self.type:
            result['type'] = self.type

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OutOfOffice:
        """Create from dictionary."""
        return cls(
            active=data.get('active', False),
            disable_notifications=data.get('disable_notifications', False),
            end_date=str(data.get('end_date', '')),
            start_date=str(data.get('start_date', '')),
            type=data.get('type')
        )


@dataclass
class User:
    """
    Represents a Monday.com user with their profile and account information.

    This dataclass maps to the Monday.com API user object structure, containing
    fields like name, email, profile photos, teams, and account settings.

    See also:
        https://developer.monday.com/api-reference/reference/users#fields
    """

    account: Account | None = None
    """The user's account"""

    birthday: str = ''
    """The user's date of birth. Returned as ``YYYY-MM-DD``"""

    country_code: str = ''
    """The user's country code"""

    created_at: str = ''
    """The user's creation date. Returned as ``YYYY-MM-DD``"""

    current_language: str = ''
    """The user's language"""

    email: str = ''
    """The user's email"""

    enabled: bool = False
    """Returns ``True`` if the user is enabled"""

    id: str = ''
    """The user's unique identifier"""

    is_admin: bool = False
    """Returns ``True`` if the user is an admin"""

    is_guest: bool = False
    """Returns ``True`` if the user is a guest"""

    is_pending: bool = False
    """Returns ``True`` if the user didn't confirm their email yet"""

    is_view_only: bool = False
    """Returns ``True`` if the user is only a viewer"""

    is_verified: bool = False
    """Returns ``True`` if the user verified their email"""

    join_date: str = ''
    """The date the user joined the account. Returned as ``YYYY-MM-DD``"""

    last_activity: str = ''
    """The last date and time the user was active. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    location: str = ''
    """The user's location"""

    mobile_phone: str = ''
    """The user's mobile phone number"""

    name: str = ''
    """The user's name"""

    out_of_office: OutOfOffice | None = None
    """The user's out-of-office status"""

    phone: str = ''
    """The user's phone number"""

    photo_original: str = ''
    """Returns the URL of the user's uploaded photo in its original size"""

    photo_small: str = ''
    """Returns the URL of the user's uploaded photo in a small size (150x150 px)"""

    photo_thumb: str = ''
    """Returns the URL of the user's uploaded photo in a small thumbnail size (50x50 px)"""

    photo_tiny: str = ''
    """Returns the URL of the user's uploaded photo in tiny size (30x30 px)"""

    sign_up_product_kind: str = ''
    """The product the user first signed up to"""

    teams: list[Team] | None = None
    """The user's teams"""

    time_zone_identifier: str = ''
    """The user's timezone identifier"""

    title: str = ''
    """The user's title"""

    url: str = ''
    """The user's profile URL"""

    utc_hours_diff: int = 0
    """The user's UTC hours difference"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        result = {}

        if self.account:
            result['account'] = self.account.to_dict()
        if self.birthday:
            result['birthday'] = self.birthday
        if self.country_code:
            result['country_code'] = self.country_code
        if self.created_at:
            result['created_at'] = self.created_at
        if self.current_language:
            result['current_language'] = self.current_language
        if self.email:
            result['email'] = self.email
        if self.enabled:
            result['enabled'] = self.enabled
        if self.id:
            result['id'] = self.id
        if self.is_admin:
            result['is_admin'] = self.is_admin
        if self.is_guest:
            result['is_guest'] = self.is_guest
        if self.is_pending:
            result['is_pending'] = self.is_pending
        if self.is_view_only:
            result['is_view_only'] = self.is_view_only
        if self.is_verified:
            result['is_verified'] = self.is_verified
        if self.join_date:
            result['join_date'] = self.join_date
        if self.last_activity:
            result['last_activity'] = self.last_activity
        if self.location:
            result['location'] = self.location
        if self.mobile_phone:
            result['mobile_phone'] = self.mobile_phone
        if self.name:
            result['name'] = self.name
        if self.out_of_office:
            result['out_of_office'] = self.out_of_office.to_dict()
        if self.phone:
            result['phone'] = self.phone
        if self.photo_original:
            result['photo_original'] = self.photo_original
        if self.photo_small:
            result['photo_small'] = self.photo_small
        if self.photo_thumb:
            result['photo_thumb'] = self.photo_thumb
        if self.photo_tiny:
            result['photo_tiny'] = self.photo_tiny
        if self.sign_up_product_kind:
            result['sign_up_product_kind'] = self.sign_up_product_kind
        if self.teams:
            result['teams'] = [team.to_dict() if hasattr(team, 'to_dict') else team for team in self.teams]
        if self.time_zone_identifier:
            result['time_zone_identifier'] = self.time_zone_identifier
        if self.title:
            result['title'] = self.title
        if self.url:
            result['url'] = self.url
        if self.utc_hours_diff:
            result['utc_hours_diff'] = self.utc_hours_diff

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> User:
        """Create from dictionary."""
        return cls(
            account=Account.from_dict(data['account']) if data.get('account') else None,
            birthday=str(data.get('birthday', '')),
            country_code=str(data.get('country_code', '')),
            created_at=str(data.get('created_at', '')),
            current_language=str(data.get('current_language', '')),
            email=str(data.get('email', '')),
            enabled=data.get('enabled', False),
            id=str(data.get('id', '')),
            is_admin=data.get('is_admin', False),
            is_guest=data.get('is_guest', False),
            is_pending=data.get('is_pending', False),
            is_view_only=data.get('is_view_only', False),
            is_verified=data.get('is_verified', False),
            join_date=str(data.get('join_date', '')),
            last_activity=str(data.get('last_activity', '')),
            location=str(data.get('location', '')),
            mobile_phone=str(data.get('mobile_phone', '')),
            name=str(data.get('name', '')),
            out_of_office=OutOfOffice.from_dict(data['out_of_office']) if data.get('out_of_office') else None,
            phone=str(data.get('phone', '')),
            photo_original=str(data.get('photo_original', '')),
            photo_small=str(data.get('photo_small', '')),
            photo_thumb=str(data.get('photo_thumb', '')),
            photo_tiny=str(data.get('photo_tiny', '')),
            sign_up_product_kind=str(data.get('sign_up_product_kind', '')),
            teams=[Team.from_dict(team) if hasattr(Team, 'from_dict') else team for team in data.get('teams', [])] if data.get('teams') else None,
            time_zone_identifier=str(data.get('time_zone_identifier', '')),
            title=str(data.get('title', '')),
            url=str(data.get('url', '')),
            utc_hours_diff=int(data.get('utc_hours_diff', 0))
        )
