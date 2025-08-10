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

.. index:: MondayClient

MondayClient
------------

.. autoclass:: monday.client.MondayClient
   :members: logger, post_request
   :show-inheritance:

Services
~~~~~~~~

The MondayClient provides access to various services for interacting with different aspects of the Monday.com API:

.. py:attribute:: MondayClient.boards
   :no-index:

   Service for board-related operations.

   Type: :ref:`Boards <services_section_boards>`

.. py:attribute:: MondayClient.items
   :no-index:

   Service for item-related operations.

   Type: :ref:`Items <services_section_items>`

.. py:attribute:: MondayClient.subitems
   :no-index:

   Service for subitem-related operations.

   Type: :ref:`Subitems <services_section_subitems>`

.. py:attribute:: MondayClient.groups
   :no-index:

   Service for group-related operations.

   Type: :ref:`Groups <services_section_groups>`

.. py:attribute:: MondayClient.users
   :no-index:

   Service for user-related operations.

   Type: :ref:`Users <services_section_users>`
