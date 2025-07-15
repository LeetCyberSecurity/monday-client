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

.. _services_section:

Services
--------

.. attention::

    The services documented below are automatically initialized as part of `MondayClient <monday_client.html>`_ and should be accessed through the `MondayClient <monday_client.html>`_ instance.

.. note::

    The fields parameters in this class's methods directly correspond to monday.com's API GraphQL fields.
    For example, using ``fields='id name owners { id }'`` or ``fields=Fields('id name owners { id }')`` is equivalent to requesting ``id name owners { id }`` in a GraphQL query.

.. seealso::
        Complete documentation of available premade fields in the :ref:`Fields Reference <fields_section_top>`.

.. module:: monday.services

.. _services_section_boards:

Boards
~~~~~~
.. automethod:: monday.services.Boards.query
.. automethod:: monday.services.Boards.get_items
.. automethod:: monday.services.Boards.get_items_by_column_values
.. automethod:: monday.services.Boards.get_column_values
.. automethod:: monday.services.Boards.create
.. automethod:: monday.services.Boards.duplicate
.. automethod:: monday.services.Boards.update
.. automethod:: monday.services.Boards.archive
.. automethod:: monday.services.Boards.delete
.. automethod:: monday.services.Boards.create_column

.. _services_section_groups:

Groups
~~~~~~
.. automethod:: monday.services.Groups.query
.. automethod:: monday.services.Groups.create
.. automethod:: monday.services.Groups.update
.. automethod:: monday.services.Groups.duplicate
.. automethod:: monday.services.Groups.archive
.. automethod:: monday.services.Groups.delete
.. automethod:: monday.services.Groups.get_items_by_name

.. _services_section_items:

Items
~~~~~
.. automethod:: monday.services.Items.query
.. automethod:: monday.services.Items.create
.. automethod:: monday.services.Items.duplicate
.. automethod:: monday.services.Items.move_to_group
.. automethod:: monday.services.Items.move_to_board
.. automethod:: monday.services.Items.archive
.. automethod:: monday.services.Items.delete
.. automethod:: monday.services.Items.clear_updates
.. automethod:: monday.services.Items.get_column_values
.. automethod:: monday.services.Items.change_column_values
.. automethod:: monday.services.Items.get_name
.. automethod:: monday.services.Items.get_id

.. _services_section_subitems:

Subitems
~~~~~~~~
.. automethod:: monday.services.Subitems.query
.. automethod:: monday.services.Subitems.create

.. _services_section_users:

Users
~~~~~
.. automethod:: monday.services.Users.query
