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
Type definitions for monday.com Webhooks.

This module provides dataclasses representing webhook objects.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class Webhook:
    """Represents a monday.com Webhook object."""

    id: str = ''
    event: str = ''
    board_id: str = ''
    config: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API interactions."""
        result: dict[str, Any] = {}
        if self.id:
            result['id'] = self.id
        if self.event:
            result['event'] = self.event
        if self.board_id:
            result['board_id'] = self.board_id
        if self.config is not None:
            result['config'] = self.config
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Webhook:
        """Create a Webhook from a dictionary payload."""
        raw_config = data.get('config')
        config_obj: dict[str, Any] | None
        if isinstance(raw_config, str):
            try:
                config_obj = json.loads(raw_config)
            except (json.JSONDecodeError, TypeError):
                config_obj = None
        elif isinstance(raw_config, dict):
            config_obj = raw_config
        else:
            config_obj = None

        return cls(
            id=str(data.get('id', '')),
            event=str(data.get('event', '')),
            board_id=str(data.get('board_id', '')),
            config=config_obj,
        )
