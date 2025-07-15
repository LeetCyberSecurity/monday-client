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
Monday.com API column creation defaults and configurations.

This module contains dataclasses that represent the default settings and
configurations for creating different types of columns in Monday.com boards.

Each column type has specific configuration options that can be set during creation.
These dataclasses provide type-safe ways to configure column defaults.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class DropdownDefaults:
    """Default configuration for dropdown columns."""

    options: list[DropdownLabel]
    """List of dropdown options to create"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        labels = []
        used_indices = set()

        # First pass: collect all explicitly set indices
        for option in self.options:
            if option.index is not None:
                used_indices.add(option.index)

        # Second pass: build labels with auto-increment for None indices
        next_index = 0
        for option in self.options:
            if option.index is None:
                # Find the next available index
                while next_index in used_indices:
                    next_index += 1
                used_indices.add(next_index)
                labels.append({'id': next_index, 'name': option.text})
                next_index += 1
            else:
                labels.append({'id': option.index, 'name': option.text})

        return {'settings': {'labels': labels}}


@dataclass
class StatusDefaults:
    """Default configuration for status columns."""

    labels: list[StatusLabel]
    """List of status labels to create"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {'labels': {label.index: label.text for label in self.labels}}


@dataclass
class DropdownLabel:
    """Represents a dropdown option with its properties."""

    text: str
    """The option text"""

    index: int | None = None
    """The option index (auto-assigned if None)"""


@dataclass
class StatusLabel:
    """Represents a status label with its properties."""

    text: str
    """The label text"""

    index: int
    """
    The label index which corresponds to its color (ranges: 0-19, 101-110, 151-160).
    See `Monday.com status colors <https://view.monday.com/1073554546-ad9f20a427a16e67ded630108994c11b?r=use1>`_ for index to color mappings.
    """

    def __post_init__(self) -> None:
        """Validate the index is within the valid ranges."""
        valid_ranges = [(0, 19), (101, 110), (151, 160)]
        is_valid = any(low <= self.index <= high for low, high in valid_ranges)
        if not is_valid:
            error_msg = f'Status label index must be in ranges 0-19, 101-110, or 151-160, got {self.index}'
            raise ValueError(error_msg)


ColumnDefaults = StatusDefaults | DropdownDefaults
