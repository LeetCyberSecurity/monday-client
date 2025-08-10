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

"""Tests for monday-client exceptions."""

import pytest

pytestmark = pytest.mark.unit

from monday.exceptions import (
    ComplexityLimitExceeded,
    MondayAPIError,
    MutationLimitExceeded,
    PaginationError,
    QueryFormatError,
)


def test_exception_attributes_set():
    """Test exception classes set attributes (json, reset_in)."""
    e1 = MondayAPIError('msg', json={'a': 1})
    assert e1.json == {'a': 1}

    e2 = ComplexityLimitExceeded('c', reset_in=3, json={'x': 2})
    assert e2.reset_in == 3
    assert e2.json == {'x': 2}

    e3 = MutationLimitExceeded('m', reset_in=5, json=None)
    assert e3.reset_in == 5
    assert e3.json is None

    e4 = PaginationError('p', json={'p': True})
    assert e4.json == {'p': True}

    e5 = QueryFormatError('q', json={'q': 1})
    assert e5.json == {'q': 1}
