.. 
    This file is part of monday-client.

    Copyright (C) 2024 Leet Cyber Security <https://leetcybersecurity.com/>

    monday-client is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    monday-client is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with monday-client. If not, see <https://www.gnu.org/licenses/>.

.. _fields_section_top:

Fields Reference
----------------

The fields used in the MondayClient library directly correspond to the field structure used in monday.com API queries. When you specify fields in this library, they are translated directly into the GraphQL query structure that monday.com's API expects.

For example, if you request ``ITEMS_FIELDS`` for a board, it's equivalent to requesting ``id name items_count items_page { cursor items { id name } }`` in a GraphQL query.

This page documents all premade field options available across different services.

.. seealso::
    :class:`Fields <monday.Fields>` class documentation for information on implementing custom fields.

.. _fields_section_boards:

Boards
~~~~~~

BASIC_FIELDS
^^^^^^^^^^^^
- ``id``: Board's ID
- ``name``: Board's name

DETAILED_FIELDS
^^^^^^^^^^^^^^^
- ``id``: Board's ID
- ``name``: Board's name
- ``board_kind``: The type of board
- ``description``: Board's description

ITEMS_FIELDS
^^^^^^^^^^^^
- ``id``: Board's ID
- ``name``: Board's name
- ``items``: List of all items on the board

    - ``id``: Item's ID
    - ``name``: Item's name

GROUPS_FIELDS
^^^^^^^^^^^^^
- ``id``: Board's ID
- ``name``: Board's name
- ``top_group``: The group at the top of the board

    - ``id``: Group's ID
    - ``title``: Group's title

- ``groups``: The board's visible groups

    - ``id``: Group's ID
    - ``title``: Group's title

USERS_FIELDS
^^^^^^^^^^^^
    - ``id``: Board's ID
    - ``name``: Board's name
    - ``creator``: The board's creator

        - ``id``: User's ID
        - ``email``: User's email
        - ``name``: User's name

    - ``owners``: The board's owners

        - ``id``: User's ID
        - ``email``: User's email
        - ``name``: User's name

    - ``subscribers``: The board's subscribers

        - ``id``: User's ID
        - ``email``: User's email
        - ``name``: User's name

.. seealso::
    `monday.com API Boards fields <https://developer.monday.com/api-reference/reference/boards#fields>`_

.. _fields_section_groups:

Groups
~~~~~~

BASIC_FIELDS
^^^^^^^^^^^^
- ``id``: Group's ID
- ``title``: Group's title

.. seealso::
    `monday.com API Groups fields <https://developer.monday.com/api-reference/reference/groups#fields>`_

.. _fields_section_items:

Items
~~~~~

.. _fields_section_subitems:

Subitems
~~~~~~~~

.. _fields_section_users:

Users
~~~~~
