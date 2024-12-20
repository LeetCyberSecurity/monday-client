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
Module containing predefined field sets for monday.com board operations.

This module provides a collection of commonly used field combinations when
querying monday.com boards, making it easier to maintain consistent field
sets across board operations.
"""

from monday.services.utils.fields import Fields


class BoardFields:
    """
    Collection of predefined field sets for board operations.

    See also:
        `monday.com API Board fields <https://developer.monday.com/api-reference/reference/boards#fields>`_
    """

    BASIC: Fields = Fields('id name')
    """Returns the following fields:

    - id: Board's ID
    - name: Board's name
    """

    DETAILED: Fields = Fields('id name board_kind description')
    """Returns the following fields:

    - id: Board's ID
    - name: Board's name
    - board_kind: The type of board
    - description: Board's description
    """

    GROUPS: Fields = Fields('id name top_group { id title } groups { id title }')
    """Returns the following fields:

    - id: Board's ID
    - name: Board's name
    - top_group: The group at the top of the board

        - id: Group's ID
        - title: Group's title
    - groups: The board's visible groups

        - id: Group's ID
        - title: Group's title
    """

    ITEMS: Fields = Fields('id name items_count items_page { cursor items { id name } }')
    """Returns the following fields:

    - id: Board's ID
    - name: Board's name
    - items_count: The number of items on the board
    - items: List of all items on the board

        - id: Item's ID
        - name: Item's name
    """

    USERS: Fields = Fields('id name creator { id email name } owners { id email name } subscribers { id email name }')
    """Returns the following fields:

    - id: Board's ID
    - name: Board's name
    - creator: The board's creator

        - id: User's ID
        - email: User's email
        - name: User's name
    - owners: The board's owners

        - id: User's ID
        - email: User's email
        - name: User's name
    - subscribers: The board's subscribers

        - id: User's ID
        - email: User's email
        - name: User's name
    """
