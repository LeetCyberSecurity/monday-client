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

"""Custom exceptions for the Monday module."""

from typing import Any, Optional


class MondayAPIError(Exception):
    """
    Exception raised when an error occurs during API communication with monday.com.

    Attributes:
        message: Explanation of the error.
        json: JSON data returned by the API, if available.
    """

    def __init__(
        self,
        message,
        json: Optional[dict[str, Any]] = None
    ):
        super().__init__(message)
        self.json = json


class ComplexityLimitExceeded(Exception):
    """
    Exception raised when the complexity limit is exceeded.

    Attributes:
        message: Explanation of the error.
        reset_in: Time in seconds until the complexity limit is reset.
        json: JSON data returned by the API, if available.
    """

    def __init__(
        self,
        message: str,
        reset_in: int,
        json: Optional[dict[str, Any]] = None
    ):
        super().__init__(message)
        self.reset_in = reset_in
        self.json = json


class MutationLimitExceeded(Exception):
    """
    Exception raised when the mutation per minute limit is exceeded.

    Attributes:
        message: Explanation of the error.
        reset_in: Time in seconds until the rate limit is reset.
        json: JSON data returned by the API, if available.
    """

    def __init__(
        self,
        message: str,
        reset_in: int,
        json: Optional[dict[str, Any]] = None
    ):
        super().__init__(message)
        self.reset_in = reset_in
        self.json = json


class PaginationError(Exception):
    """
    Exception raised when item pagination fails.

    Attributes:
        message: Explanation of the error.
    """

    def __init__(
        self,
        message: str
    ):
        super().__init__(message)


class QueryFormatError(Exception):
    """
    Exception raised when a query is improperly formatted.

    Attributes:
        message: Explanation of the error.
        json: JSON data returned by the API, if available.
    """

    def __init__(
        self,
        message: str,
        json: Optional[dict[str, Any]] = None
    ):
        super().__init__(message)
        self.json = json
