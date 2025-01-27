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
Type definitions for monday.com API asset related structures.
"""

from typing import Required, TypedDict

from monday.types.user import User


class Asset(TypedDict, total=False):
    """
    Type definitions for monday.com API asset structures.

    These types correspond to Monday.com's asset fields as documented in their API reference:
    https://developer.monday.com/api-reference/reference/assets#fields
    """

    created_at: str
    """The asset's creation date. Returned as ``YYYY-MM-DDTHH:MM:SS``"""

    file_extension: Required[str]
    """The asset's extension"""

    file_size: Required[int]
    """The asset's size in bytes"""

    id: Required[str]
    """The asset's unique identifier"""

    name: Required[str]
    """The asset's name"""

    original_geometry: str
    """The asset's original geometry"""

    public_url: Required[str]
    """The asset's public URL (valid for 1 hour). Accessing this link will allow users without a monday.com user profile to see the file directly while the link is valid."""

    uploaded_by: Required[User]
    """The user who uploaded the asset. This field will not return anything if the asset is a duplicate of something generated by a system."""

    url: Required[str]
    """The asset's URL. This will only be available to users who have access to the file as part of your account. If the asset is stored on a private or shareable board, it will also need to be part of the board in question."""

    url_thumbnail: str
    """The URL to view the asset in thumbnail mode. Only available for images."""