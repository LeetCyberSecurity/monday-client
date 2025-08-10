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

"""Tests for monday-client error handlers."""

import pytest

pytestmark = pytest.mark.unit

from monday.exceptions import (
    ComplexityLimitExceeded,
    MondayAPIError,
    MutationLimitExceeded,
    QueryFormatError,
)
from monday.services.utils.error_handlers import ErrorHandler


def test_handle_graphql_errors_complexity_exception():
    """Test mapping of ComplexityException to ComplexityLimitExceeded with reset_in."""
    handler = ErrorHandler(rate_limit_seconds=5)
    response = {
        'errors': [
            {
                'message': 'Complexity limit exceeded',
                'extensions': {'code': 'ComplexityException', 'reset_in': 3},
            }
        ]
    }
    with pytest.raises(ComplexityLimitExceeded) as exc:
        handler.handle_graphql_errors(response, {}, 'query { x }')
    assert exc.value.reset_in == 3


def test_handle_graphql_errors_rate_limit_uses_retry_after():
    """Test RateLimitExceeded uses Retry-After to set reset_in."""
    handler = ErrorHandler(rate_limit_seconds=5)
    response = {
        'errors': [
            {
                'message': 'Rate limited',
                'extensions': {'code': 'RateLimitExceeded'},
            }
        ]
    }
    with pytest.raises(MutationLimitExceeded) as exc:
        handler.handle_graphql_errors(response, {'Retry-After': '7'}, 'query { x }')
    assert exc.value.reset_in == 7


def test_handle_graphql_errors_query_format_error():
    """Test QueryFormatError is raised for bad query."""
    handler = ErrorHandler()
    response = {
        'errors': [
            {
                'message': 'Bad query',
                'extensions': {'code': 'QueryFormatError'},
            }
        ]
    }
    with pytest.raises(QueryFormatError):
        handler.handle_graphql_errors(response, {}, 'query {')


def test_handle_graphql_errors_unhandled():
    """Test unhandled error wraps as MondayAPIError."""
    handler = ErrorHandler()
    response = {'errors': [{'message': 'Something else', 'extensions': {'code': 'X'}}]}
    with pytest.raises(MondayAPIError) as exc:
        handler.handle_graphql_errors(response, {}, 'query { x }')
    assert 'Unhandled monday.com API error' in str(exc.value)
