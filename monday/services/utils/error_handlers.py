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

from monday.exceptions import (
    ComplexityLimitExceeded,
    MondayAPIError,
    MutationLimitExceeded,
    QueryFormatError,
)

logger: logging.Logger = logging.getLogger(__name__)


def check_query_result(
    query_result: dict[str, Any], *, errors_only: bool = False
) -> dict[str, Any]:
    """
    Check if the query result contains an error and raise MondayAPIError if found.

    This function examines the query result dictionary for error indicators and handles them appropriately.
    Supports the GraphQL-compliant error format.

    Args:
        query_result: The response dictionary from a monday.com API query.
        errors_only: Only check for errors, not the presence of the data key.

    Returns:
        The original query_result if no errors are found.

    Raises:
        MondayAPIError: If an error is found in the query result or if the response structure is unexpected.

    """
    # Check for GraphQL-compliant error format
    if query_result.get('errors'):
        error_messages = [
            e.get('message', 'Unknown error') for e in query_result['errors']
        ]
        raise MondayAPIError(
            message=f'API request failed: {"; ".join(error_messages)}',
            json=query_result,
        )

    # Check for missing data key (unless errors_only is True)
    if not errors_only and 'data' not in query_result:
        raise MondayAPIError(message='API request failed', json=query_result)

    return query_result


class ErrorHandler:
    """Centralized error handler for Monday.com API errors."""

    def __init__(self, rate_limit_seconds: int = 60):
        self.rate_limit_seconds = rate_limit_seconds

    def handle_graphql_errors(
        self,
        response_data: dict[str, Any],
        response_headers: dict[str, str],
        query: str,
    ) -> None:
        """Handle GraphQL-compliant error format (2025-01+)."""
        response_data['query'] = ' '.join(query.split())

        for error in response_data['errors']:
            self._handle_single_graphql_error(error, response_data, response_headers)

        # If we get here, it's an unhandled error
        error_messages = [
            e.get('message', 'Unknown error') for e in response_data['errors']
        ]
        raise MondayAPIError(
            message=f'Unhandled monday.com API error: {"; ".join(error_messages)}',
            json=response_data,
        )

    def get_retry_after_seconds(
        self, response_headers: dict[str, str], default_seconds: int
    ) -> int:
        """Extract retry delay from Retry-After header or return default."""
        retry_after = response_headers.get('Retry-After')
        if retry_after:
            try:
                retry_seconds = int(retry_after)
                logger.warning(
                    'Using Retry-After header value: %d seconds', retry_seconds
                )
            except ValueError:
                logger.warning(
                    'Invalid Retry-After header value: %s, using default %d seconds',
                    retry_after,
                    default_seconds,
                )
                return default_seconds
            else:
                return retry_seconds
        return default_seconds

    def _handle_single_graphql_error(
        self,
        error: dict[str, Any],
        response_data: dict[str, Any],
        response_headers: dict[str, str],
    ) -> None:
        """Handle a single GraphQL error."""
        error_code = error.get('extensions', {}).get('code')
        error_message = error.get('message', 'Unknown error')

        error_handlers = {
            'ComplexityException': lambda: self._handle_complexity_exception(
                error, response_data
            ),
            'ComplexityBudgetExhausted': lambda: self._handle_complexity_budget_exhausted(
                error.get('extensions', {}), response_data
            ),
            'RateLimitExceeded': lambda: self._handle_rate_limit(
                response_headers, response_data
            ),
            'QueryFormatError': lambda: self._raise_query_format_error(
                error_message, response_data
            ),
        }

        handler = error_handlers.get(error_code)
        if handler:
            handler()

    def _handle_complexity_exception(
        self,
        error: dict[str, Any],
        response_data: dict[str, Any],
    ) -> None:
        """Handle complexity exception from GraphQL errors."""
        extensions = error.get('extensions', {})
        reset_in = extensions.get('reset_in', self.rate_limit_seconds)

        raise ComplexityLimitExceeded(
            message=f'Complexity limit exceeded: {error.get("message", "Unknown error")}',
            reset_in=reset_in,
            json=response_data,
        )

    def _handle_complexity_budget_exhausted(
        self,
        extensions: dict[str, Any],
        response_data: dict[str, Any],
    ) -> None:
        """Handle complexity budget exhausted error."""
        reset_in = extensions.get('reset_in', self.rate_limit_seconds)

        raise ComplexityLimitExceeded(
            message='Complexity budget exhausted',
            reset_in=reset_in,
            json=response_data,
        )

    def _handle_rate_limit(
        self,
        response_headers: dict[str, str],
        response_data: dict[str, Any],
    ) -> None:
        """Handle rate limit exceeded error."""
        reset_in = self.get_retry_after_seconds(
            response_headers, self.rate_limit_seconds
        )

        raise MutationLimitExceeded(
            message='Mutation rate limit exceeded',
            reset_in=reset_in,
            json=response_data,
        )

    def _raise_query_format_error(
        self, error_message: str, response_data: dict[str, Any]
    ) -> None:
        """Raise query format error."""
        raise QueryFormatError(
            message=f'Query format error: {error_message}',
            json=response_data,
        )
