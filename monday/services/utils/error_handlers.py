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
from typing import Any

from monday.exceptions import MondayAPIError

logger: logging.Logger = logging.getLogger(__name__)


def check_query_result(
    query_result: dict[str, Any],
    errors_only: bool = False
) -> dict[str, Any]:
    """
    Check if the query result contains an error and raise MondayAPIError if found.

    This function examines the query result dictionary for error indicators and handles them appropriately.

    Args:
        query_result: The response dictionary from a monday.com API query.
        errors_only: Only check for errors, not the presence of the data key.

    Returns:
        The original query_result if no errors are found.

    Raises:
        MondayAPIError: If an error is found in the query result or if the response structure is unexpected.
    """
    error_conditions = [
        lambda x: isinstance(x, dict) and any('error' in k.lower() for k in x),
        lambda x: 'data' not in x and not errors_only,
        lambda x: 'data' in x and any('error' in k.lower() for k in x['data'])
    ]

    for condition in error_conditions:
        if condition(query_result):
            raise MondayAPIError('API request failed', json=query_result)

    return query_result
