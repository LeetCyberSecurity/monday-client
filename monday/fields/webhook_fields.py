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
Field presets for monday.com Webhook operations.
"""

from monday.fields.base_fields import BaseFields
from monday.services.utils.fields import Fields


class WebhookFields(BaseFields):
    """Predefined selection sets for webhook queries/mutations."""

    BASIC = Fields('id event board_id config')
    """
    Returns the following fields:

    - id: Webhook ID
    - event: Subscribed event type
    - board_id: Board ID of the webhook
    - config: Webhook configuration JSON (string)
    """
