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

"""Utility functions for handling errors in Monday API interactions."""

import logging
from typing import Any, Dict, Type, TypeVar

from pydantic import BaseModel, ValidationError

from ...exceptions import MondayAPIError

T = TypeVar('T', bound=BaseModel)

logger = logging.getLogger(__name__)


def check_query_result(query_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if the query result contains an error and raise MondayAPIError if found.

    This function examines the query result dictionary for error indicators and handles them appropriately.

    Args:
        query_result: The response dictionary from a Monday.com API query.

    Returns:
        The original query_result if no errors are found.

    Raises:
        MondayAPIError: If an error is found in the query result or if the response structure is unexpected.

    Example:
        result = check_query_result(api_response)
    """
    try:
        if isinstance(query_result, dict) and any('error' in key.lower() for key in query_result.keys()):
            raise MondayAPIError("API request failed", json_data=query_result)
        if 'data' not in query_result:
            raise MondayAPIError("Unexpected API response", json_data=query_result)
        return query_result
    except MondayAPIError as e:
        logger.error('MondayAPIError occurred: %s Data: %s', str(e), e.json)
        raise


def check_schema(schema: Type[T], **kwargs) -> T:
    """
    Validate input data against a given Pydantic schema.

    This function attempts to create an instance of the provided schema using the given keyword arguments.
    If validation fails, it raises a ValueError with detailed error messages.

    Args:
        schema: A Pydantic model class to validate against. This should be a subclass of BaseModel
                          that defines the expected structure and validation rules for the input data.
                          Examples include CreateBoardInput, DuplicateBoardInput, QueryBoardInput, etc.
        **kwargs: Keyword arguments representing the data to be validated.
                  These should match the fields defined in the schema class.

    Returns:
        An instance of the schema class if validation succeeds.

    Raises:
        ValueError: If the input data fails validation, with detailed error messages.

    Example:
        validated_data = check_schema(UserSchema, name="John Doe", age=30)
    """
    try:
        input_data = schema(**kwargs)
    except ValidationError as e:
        error_messages = [
            f"{' -> '.join(str(loc) for loc in m['loc'])}: {m['msg'].strip()}"
            for m in e.errors()
        ]
        raise ValueError("Validation error\n" + "\n".join(error_messages)) from None
    return input_data
