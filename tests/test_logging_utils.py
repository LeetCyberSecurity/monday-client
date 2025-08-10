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

"""Tests for monday-client logging utilities."""

import pytest

pytestmark = pytest.mark.unit

import logging

from monday.logging_utils import (
    configure_for_external_logging,
    disable_logging,
    enable_logging,
    get_logger,
    is_logging_enabled,
    set_log_level,
)


def test_enable_disable_logging_roundtrip():
    """Test enabling/disabling logging toggles handlers and levels."""
    logger = get_logger()

    # Start disabled
    disable_logging()
    assert not is_logging_enabled()
    assert any(isinstance(h, logging.NullHandler) for h in logger.handlers)

    # Enable and check state
    enable_logging(level='INFO')
    assert is_logging_enabled()
    assert not any(isinstance(h, logging.NullHandler) for h in logger.handlers)
    assert logger.level == logging.INFO

    # Change level
    set_log_level('DEBUG')
    assert logger.level == logging.DEBUG


def test_configure_for_external_logging():
    """Test external logging config removes NullHandler and sets NOTSET."""
    # Ensure a clean state
    disable_logging()
    configure_for_external_logging()
    logger = get_logger()

    # No NullHandler, level NOTSET, allow external config
    assert not any(isinstance(h, logging.NullHandler) for h in logger.handlers)
    assert logger.level == logging.NOTSET
