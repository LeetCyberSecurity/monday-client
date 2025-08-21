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
Monday.com API column input classes.

This module contains dataclasses that represent input values for different column types
when updating items via the Monday.com API. These classes provide type-safe ways
to set column values in operations like change_column_values.

Each class corresponds to a specific column type and handles the proper formatting
required by the Monday.com API.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, runtime_checkable
from zoneinfo import ZoneInfo

from monday.types.country_codes import get_country_name, is_valid_country_code


@dataclass
class CheckboxInput:
    """
    Represents a checkbox column input value for Monday.com API operations.

    Args:
        column_id: The column's unique identifier
        checked: Whether the checkbox is checked

    Example:
        .. code-block:: python

            checkbox_val = CheckboxInput('unique_column_id', True)

            await client.items.change_column_values(
                item_id=123456789, column_values=checkbox_val
            )

    """

    column_id: str
    """The column's unique identifier"""

    checked: bool
    """Whether the checkbox is checked"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {'checked': self.checked}


@dataclass
class CountryInput:
    """
    Represents a country column input value for Monday.com API operations.

    Args:
        column_id: The column's unique identifier
        country_code: Country code in ISO 3166-1 alpha-2 format (e.g., 'US', 'GB')

    Example:
        .. code-block:: python

            country_val = CountryInput('unique_column_id', 'US')

            await client.items.change_column_values(
                item_id=123456789, column_values=country_val
            )

    """

    column_id: str
    """The column's unique identifier"""

    country_code: str
    """Country code in ISO 3166-1 alpha-2 format"""

    def __post_init__(self) -> None:
        """Validate the country code."""
        if not is_valid_country_code(self.country_code):
            error_msg = f'Invalid country code {self.country_code}'
            raise ValueError(error_msg)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        country_name = get_country_name(self.country_code)
        return {'countryCode': self.country_code, 'countryName': country_name}


@dataclass
class DateInput:
    """
    Represents a date column input value for Monday.com API operations.

    Based on the Monday.com API documentation, date columns can be updated using
    either a simple string format (YYYY-MM-DD) or a JSON format with date and time.

    Args:
        column_id: The column's unique identifier
        date: The date in YYYY-MM-DD format
        time: Optional time in HH:MM:SS format (24-hour)

    Example:
        .. code-block:: python

            # Simple date
            date_val = DateInput('unique_column_id', '2024-01-15')

            # Date with time (use UTC timezone)
            date_val = DateInput('unique_column_id', '2024-01-15', '14:30:00')

            # Use in change_column_values
            await client.items.change_column_values(
                item_id=123456789, column_values=date_val
            )

    """

    column_id: str
    """The column's unique identifier"""

    date: str
    """The date in YYYY-MM-DD format"""

    time: str | None = None
    """Optional time in HH:MM:SS format (24-hour)"""

    def __post_init__(self) -> None:
        """Validate the date and time format."""
        # Validate date format
        try:
            datetime.strptime(self.date, '%Y-%m-%d')  # noqa: DTZ007
        except ValueError as e:
            error_msg = f'Date must be in YYYY-MM-DD format, got {self.date}'
            raise ValueError(error_msg) from e

        # Validate time format if provided
        if self.time is not None:
            try:
                datetime.strptime(self.time, '%H:%M:%S')  # noqa: DTZ007
            except ValueError as e:
                error_msg = f'Time must be in HH:MM:SS format, got {self.time}'
                raise ValueError(error_msg) from e

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        if self.time is not None:
            return {'date': self.date, 'time': self.time}
        return {'date': self.date}


@dataclass
class DropdownInput:
    """
    Represents a dropdown column input value for Monday.com API operations.

    Args:
        column_id: The column's unique identifier
        label: The dropdown option label

    Example:
        .. code-block:: python

            dropdown_val = DropdownInput('unique_column_id', 'Option 1')

            await client.items.change_column_values(
                item_id=123456789, column_values=dropdown_val
            )

    """

    column_id: str
    """The column's unique identifier"""

    label: str | list[str]
    """The dropdown option label or list of labels"""

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary for API requests.

        Monday.com expects dropdown values as an array under the 'labels' key
        (for label text) or 'ids' (for numeric IDs). This helper uses 'labels'
        when strings are provided; to use IDs, pass a dictionary directly.
        """
        labels = self.label if isinstance(self.label, list) else [self.label]
        return {'labels': labels}


@dataclass
class EmailInput:
    """
    Represents an email column input value for Monday.com API operations.

    Args:
        column_id: The column's unique identifier
        email: The email address
        text: The display text (optional, defaults to email)

    Example:
        .. code-block:: python

            email_val = EmailInput(
                'unique_column_id', 'user@example.com', 'Contact User'
            )

            await client.items.change_column_values(
                item_id=123456789, column_values=email_val
            )

    """

    column_id: str
    """The column's unique identifier"""

    email: str
    """The email address"""

    text: str | None = None
    """The display text (optional, defaults to email)"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {'email': self.email, 'text': self.text or self.email}


@dataclass
class HourInput:
    """
    Represents an hour column input value for Monday.com API operations.

    Args:
        column_id: The column's unique identifier
        hour: The hour value (0-23)
        minute: The minute value (0-59)

    Example:
        .. code-block:: python

            hour_val = HourInput('unique_column_id', 14, 30)  # 2:30 PM

            await client.items.change_column_values(
                item_id=123456789, column_values=hour_val
            )

    """

    column_id: str
    """The column's unique identifier"""

    hour: int
    """The hour value (0-23)"""

    minute: int
    """The minute value (0-59)"""

    def __post_init__(self) -> None:
        """Validate the hour and minute values."""
        if not 0 <= self.hour <= 23:  # noqa: PLR2004
            error_msg = f'Hour must be between 0-23, got {self.hour}'
            raise ValueError(error_msg)
        if not 0 <= self.minute <= 59:  # noqa: PLR2004
            error_msg = f'Minute must be between 0-59, got {self.minute}'
            raise ValueError(error_msg)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {'hour': self.hour, 'minute': self.minute}


@dataclass
class LinkInput:
    """
    Represents a link column input value for Monday.com API operations.

    Args:
        column_id: The column's unique identifier
        url: The URL
        text: The display text (optional, defaults to URL)

    Example:
        .. code-block:: python

            link_val = LinkInput(
                'unique_column_id', 'https://example.com', 'Example Website'
            )

            await client.items.change_column_values(
                item_id=123456789, column_values=link_val
            )

    """

    column_id: str
    """The column's unique identifier"""

    url: str
    """The URL"""

    text: str | None = None
    """The display text (optional, defaults to URL)"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        # Ensure both fields are serialized as strings as required by monday.com
        url_value = str(self.url)
        text_value = str(self.text) if self.text is not None else url_value
        return {'url': url_value, 'text': text_value}


@dataclass
class LocationInput:
    """
    Represents a location column input value for Monday.com API operations.

    Args:
        column_id: The column's unique identifier
        address: The address
        latitude: The latitude coordinate
        longitude: The longitude coordinate

    Example:
        .. code-block:: python

            location_val = LocationInput(
                'unique_column_id', '123 Main St', 40.7128, -74.0060
            )

            await client.items.change_column_values(
                item_id=123456789, column_values=location_val
            )

    """

    column_id: str
    """The column's unique identifier"""

    address: str
    """The address"""

    latitude: float
    """The latitude coordinate"""

    longitude: float
    """The longitude coordinate"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {
            'address': self.address,
            'lat': str(self.latitude),
            'lng': str(self.longitude),
        }


@dataclass
class LongTextInput:
    """
    Represents a long text column input value for Monday.com API operations.

    Args:
        column_id: The column's unique identifier
        text: The long text content

    Example:
        .. code-block:: python

            long_text_val = LongTextInput(
                'unique_column_id', 'This is a longer text content...'
            )

            await client.items.change_column_values(
                item_id=123456789, column_values=long_text_val
            )

    """

    column_id: str
    """The column's unique identifier"""

    text: str
    """The long text content"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {'text': self.text}


@dataclass
class NumberInput:
    """
    Represents a number column input value for Monday.com API operations.

    Args:
        column_id: The column's unique identifier
        number: The numeric value

    Example:
        .. code-block:: python

            num_val = NumberInput('unique_column_id', 42.5)

            await client.items.change_column_values(
                item_id=123456789, column_values=num_val
            )

    """

    column_id: str
    """The column's unique identifier"""

    number: float
    """The numeric value"""

    def to_str(self) -> str:
        """Convert to string for API requests."""
        return str(self.number)


@dataclass
class PeopleInput:
    """
    Represents a people column input value for Monday.com API operations.

    Args:
        column_id: The column's unique identifier
        person_ids: List of person IDs to assign
        team_ids: List of team IDs to assign

    Example:
        .. code-block:: python

            people_val = PeopleInput('unique_column_id', person_ids=[123, 456])

            await client.items.change_column_values(
                item_id=123456789, column_values=people_val
            )

    """

    column_id: str
    """The column's unique identifier"""

    person_ids: list[int] | None = None
    """List of person IDs to assign"""

    team_ids: list[int] | None = None
    """List of team IDs to assign"""

    def __post_init__(self) -> None:
        """Validate that at least one type of ID is provided."""
        if not self.person_ids and not self.team_ids:
            error_msg = 'At least one of person_ids or team_ids must be provided'
            raise ValueError(error_msg)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        persons_and_teams = []

        if self.person_ids:
            persons_and_teams.extend(
                {'id': str(person_id), 'kind': 'person'}
                for person_id in self.person_ids
            )

        if self.team_ids:
            persons_and_teams.extend(
                {'id': str(team_id), 'kind': 'team'} for team_id in self.team_ids
            )

        return {'personsAndTeams': persons_and_teams}


@dataclass
class PhoneInput:
    """
    Represents a phone column input value for Monday.com API operations.

    Args:
        column_id: The column's unique identifier
        phone_number: The phone number
        country_code: Country code in ISO 3166-1 alpha-2 format (defaults to 'US')

    Example:
        .. code-block:: python

            phone_val = PhoneInput('unique_column_id', '+1-555-123-4567', 'US')

            await client.items.change_column_values(
                item_id=123456789, column_values=phone_val
            )

    """

    column_id: str
    """The column's unique identifier"""

    phone_number: str
    """The phone number"""

    country_code: str = 'US'
    """Country code in ISO 3166-1 alpha-2 format"""

    def __post_init__(self) -> None:
        """Validate the country code."""
        if not is_valid_country_code(self.country_code):
            error_msg = f'Invalid country code {self.country_code}'
            raise ValueError(error_msg)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {'phone': self.phone_number, 'countryShortName': self.country_code}


@dataclass
class RatingInput:
    """
    Represents a rating column input value for Monday.com API operations.

    Args:
        column_id: The column's unique identifier
        rating: The rating value (0-5)

    Example:
        .. code-block:: python

            rating_val = RatingInput('unique_column_id', 4)

            await client.items.change_column_values(
                item_id=123456789, column_values=rating_val
            )

    """

    column_id: str
    """The column's unique identifier"""

    rating: int
    """The rating value (0-5)"""

    def __post_init__(self) -> None:
        """Validate the rating is within the valid range."""
        if not 0 <= self.rating <= 5:  # noqa: PLR2004
            error_msg = f'Rating must be between 0-5, got {self.rating}'
            raise ValueError(error_msg)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {'rating': self.rating}


@dataclass
class StatusInput:
    """
    Represents a status column input value for Monday.com API operations.
    You can pass either the index or the label value of the status you want to update.
    If the label is a number, send the index instead.

    Args:
        column_id: The column's unique identifier
        label: The status label text or the index value

    Example:
        .. code-block:: python

            status_val = StatusInput('unique_column_id', 'Working on it')

            await client.items.change_column_values(
                item_id=123456789, column_values=status_val
            )

    """

    column_id: str
    """The column's unique identifier"""

    label: str | int
    """The status label text or the index value"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {'label': str(self.label)}


@dataclass
class TagInput:
    """
    Represents a tag column input value for Monday.com API operations.

    Args:
        column_id: The column's unique identifier
        tag_id: The tag ID or list of tag IDs

    Example:
        .. code-block:: python

            tag_val = TagInput('unique_column_id', 'important')

            await client.items.change_column_values(
                item_id=123456789, column_values=tag_val
            )

    """

    column_id: str
    """The column's unique identifier"""

    tag_id: int | list[int]
    """The tag ID or list of tag IDs"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {
            'tag_ids': [str(t) for t in self.tag_id]
            if isinstance(self.tag_id, list)
            else [str(self.tag_id)]
        }


@dataclass
class TextInput:
    """
    Represents a text column input value for Monday.com API operations.

    Args:
        column_id: The column's unique identifier
        text: The text content

    Example:
        .. code-block:: python

            text_val = TextInput('unique_column_id', 'This is some text content')

            await client.items.change_column_values(
                item_id=123456789, column_values=text_val
            )

    """

    column_id: str
    """The column's unique identifier"""

    text: str
    """The text content"""

    def to_str(self) -> str:
        """Convert to string for API requests."""
        return self.text


@dataclass
class TimelineInput:
    """
    Represents a timeline column input value for Monday.com API operations.

    Args:
        column_id: The column's unique identifier
        from_date: Start date in YYYY-MM-DD format
        to_date: End date in YYYY-MM-DD format
        include_time: Whether to include time (defaults to True)

    Example:
        .. code-block:: python

            timeline_val = TimelineInput('unique_column_id', '2024-01-01', '2024-01-31')

            await client.items.change_column_values(
                item_id=123456789, column_values=timeline_val
            )

    """

    column_id: str
    """The column's unique identifier"""

    from_date: str
    """Start date in YYYY-MM-DD format"""

    to_date: str
    """End date in YYYY-MM-DD format"""

    def __post_init__(self) -> None:
        """Validate the date format."""
        try:
            datetime.strptime(self.from_date, '%Y-%m-%d')  # noqa: DTZ007
            datetime.strptime(self.to_date, '%Y-%m-%d')  # noqa: DTZ007
        except ValueError as e:
            error_msg = 'Dates must be in YYYY-MM-DD format'
            raise ValueError(error_msg) from e

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {
            'from': self.from_date,
            'to': self.to_date,
        }


@dataclass
class WeekInput:
    """
    Represents a week column input value for Monday.com API operations.

    Args:
        column_id: The column's unique identifier
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Example:
        .. code-block:: python

            week_val = WeekInput('unique_column_id', '2024-01-01', '2024-01-07')

            await client.items.change_column_values(
                item_id=123456789, column_values=week_val
            )

    """

    column_id: str
    """The column's unique identifier"""

    start_date: str
    """Start date in YYYY-MM-DD format"""

    end_date: str
    """End date in YYYY-MM-DD format"""

    def __post_init__(self) -> None:
        """Validate the date format and that dates are 7 days apart."""
        try:
            start_dt = datetime.strptime(self.start_date, '%Y-%m-%d')  # noqa: DTZ007
            end_dt = datetime.strptime(self.end_date, '%Y-%m-%d')  # noqa: DTZ007
        except ValueError as e:
            error_msg = 'Dates must be in YYYY-MM-DD format'
            raise ValueError(error_msg) from e

        # Calculate the difference in days (inclusive)
        days_diff = (end_dt - start_dt).days + 1
        if days_diff != 7:  # noqa: PLR2004
            error_msg = (
                f'Dates must be exactly 7 days apart (inclusive), got {days_diff} days'
            )
            raise ValueError(error_msg)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {'week': {'startDate': self.start_date, 'endDate': self.end_date}}


@dataclass
class WorldClockInput:
    """
    Represents a world clock column input value for Monday.com API operations.

    Args:
        column_id: The column's unique identifier
        timezone: The timezone in continent/city format (e.g., 'America/New_York', 'Europe/London')

    Example:
        .. code-block:: python

            world_clock_val = WorldClockInput('unique_column_id', 'America/New_York')

            await client.items.change_column_values(
                item_id=123456789, column_values=world_clock_val
            )

    """

    column_id: str
    """The column's unique identifier"""

    timezone: str
    """The timezone in continent/city format"""

    def __post_init__(self) -> None:
        """Validate the timezone is in valid continent/city format."""
        try:
            ZoneInfo(self.timezone)
        except Exception as e:
            error_msg = f'Invalid timezone {self.timezone}. Must be in continent/city format (e.g., America/New_York)'
            raise ValueError(error_msg) from e

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {'timezone': self.timezone}


ColumnInput = (
    CheckboxInput
    | CountryInput
    | DateInput
    | DropdownInput
    | EmailInput
    | HourInput
    | LinkInput
    | LocationInput
    | LongTextInput
    | NumberInput
    | PeopleInput
    | PhoneInput
    | RatingInput
    | StatusInput
    | TagInput
    | TextInput
    | TimelineInput
    | WeekInput
    | WorldClockInput
    | str
    | dict[str, Any]
)
"""
Union type representing all possible column input values for Monday.com API operations.

This type can be used in methods like `change_column_values()` and `create()` to provide
type-safe column values. It includes:

- Specific input classes (DateInput, StatusInput, TextInput, etc.) for type-safe operations
- String values for simple column types
- Dictionary values for complex JSON structures

Example:
    .. code-block:: python

        from monday.types.column_inputs import DateInput, StatusInput, TextInput

        # Type-safe approach using input classes
        column_values: dict[str, ColumnInput] = {
            'date_column_id': DateInput('date_column_id', '2024-01-15'),
            'status_column_id': StatusInput('status_column_id', 'Working on it'),
            'text_column_id': TextInput('text_column_id', 'Some text')
        }

        # Or using simple strings/dicts
        column_values: dict[str, ColumnInput] = {
            'text_column_id': 'Simple text',
            'status_column_id': {'label': 'Done'}
        }
"""


# Protocol-based structural typing for column input objects
@runtime_checkable
class HasToDict(Protocol):
    """Structural protocol for column input objects exposing ``to_dict()``."""

    column_id: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable mapping for the monday.com payload."""
        ...


@runtime_checkable
class HasToStr(Protocol):
    """Structural protocol for column input objects exposing ``to_str()``."""

    column_id: str

    def to_str(self) -> str:
        """Return the string representation expected by monday.com."""
        ...


# Narrow protocol for passing to APIs as a sequence
type ColumnInputObject = HasToDict | HasToStr
"""
Structural type for column input objects accepted by APIs when provided
as a sequence. Any object with a ``column_id`` and either ``to_dict`` or
``to_str`` is supported. This covers all helper input classes like
``DateInput``, ``TextInput``, ``StatusInput``, etc.
"""
