"""Custom exceptions for the Monday module."""

from typing import Any, Dict, Optional


class ComplexityLimitExceeded(Exception):
    """
    Exception raised when the complexity limit is exceeded.

    Attributes:
        message (str): Explanation of the error.
        reset_in (int): Time in seconds until the complexity limit is reset.
    """

    def __init__(self, message: str, reset_in: int):
        super().__init__(message)
        self.reset_in = reset_in


class MondayAPIError(Exception):
    """
    Exception raised when an error occurs during API communication with Monday.com.

    Attributes:
        message (str): Explanation of the error.
        json_data (Dict[str, Any], optional): JSON data returned by the API, if available.
    """

    def __init__(self, message, json_data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.json: Optional[Dict[str, Any]] = json_data


class MutationLimitExceeded(Exception):
    """
    Exception raised when the mutation per minute limit is exceeded.

    Attributes:
        message (str): Explanation of the error.
        reset_in (int): Time in seconds until the rate limit is reset.
    """

    def __init__(self, message: str, reset_in: int):
        super().__init__(message)
        self.reset_in = reset_in


class PaginationError(Exception):
    """
    Exception raised when item pagination fails.

    Attributes:
        message (str): Explanation of the error.
    """

    def __init__(self, message: str):
        super().__init__(message)


class QueryFormatError(Exception):
    """
    Exception raised when a query is improperly formatted.

    Attributes:
        message (str): Explanation of the error.
    """

    def __init__(self, message: str):
        super().__init__(message)
