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

For example, if you request ``BoardFields.ITEMS``, it's equivalent to requesting ``id name items_count items_page { cursor items { id name } }`` in a GraphQL query.

This page documents all premade field options available across different services.

.. seealso::
    :class:`Fields <monday.Fields>` class documentation for information on implementing custom fields.

.. _fields_section_boards:

Board Fields
~~~~~~~~~~~~

.. autoclass:: monday.BoardFields
    :members:
    :show-inheritance:

.. _fields_section_columns:

Column Fields
~~~~~~~~~~~~~

.. autoclass:: monday.ColumnFields
    :members:
    :show-inheritance:

.. _fields_section_groups:

Group Fields
~~~~~~~~~~~~

.. autoclass:: monday.GroupFields
    :members:
    :show-inheritance:

.. _fields_section_items:

Item Fields
~~~~~~~~~~~

.. autoclass:: monday.ItemFields
    :members:
    :show-inheritance:

.. _fields_section_users:

User Fields
~~~~~~~~~~~

.. autoclass:: monday.UserFields
    :members:
    :show-inheritance:
