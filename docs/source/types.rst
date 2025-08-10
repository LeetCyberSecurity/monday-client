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

Types
-----

The types in this package are implemented as Python dataclasses that model the structure of Monday.com's GraphQL API responses and query parameters.

Data Types
^^^^^^^^^^

These dataclasses represent the structure of data returned from the Monday.com API.

For example:

.. code-block:: python

   @dataclass
   class Item:
      name: str = ''
      updated_at: str = ''
      state: str = ''
      subitems: list[Subitem] | None = None

You can access the attributes directly:

.. rstcheck: ignore-next-code-block
.. code-block:: python

   # Get item data from API
   items = await monday_client.items.query(item_ids=[123456789])

   for item in items:
      print(f"Item: {item.name}")
      print(f"Last updated: {item.updated_at}")
      print(f"State: {item.state}")

      if item.subitems:
         print(f"Has {len(item.subitems)} subitems")
         for subitem in item.subitems:
            print(f"  - {subitem.name}")

Account Types
"""""""""""""

.. autoclass:: monday.types.account.Account
   :members:
   :show-inheritance:

.. autoclass:: monday.types.account.AccountProduct
   :members:
   :show-inheritance:

.. autoclass:: monday.types.account.Plan
   :members:
   :show-inheritance:

Asset Types
"""""""""""

.. autoclass:: monday.types.asset.Asset
   :members:
   :show-inheritance:

Board Types
"""""""""""

.. autoclass:: monday.types.board.Board
   :members:
   :show-inheritance:

.. autoclass:: monday.types.board.ActivityLog
   :members:
   :show-inheritance:

.. autoclass:: monday.types.board.BoardView
   :members:
   :show-inheritance:

.. autoclass:: monday.types.board.UndoData
   :members:
   :show-inheritance:

.. autoclass:: monday.types.board.UpdateBoard
   :members:
   :show-inheritance:

Column Types
""""""""""""

.. autoclass:: monday.types.column.Column
   :members:
   :show-inheritance:

.. autoclass:: monday.types.column.ColumnValue
   :members:
   :show-inheritance:

.. autoclass:: monday.types.column.ColumnFilter
   :members:
   :show-inheritance:

.. py:data:: monday.types.column.ColumnType
   :type: Literal

   Literal of supported column type names used throughout the API.

Group Types
"""""""""""

.. autoclass:: monday.types.group.Group
   :members:
   :show-inheritance:

.. autoclass:: monday.types.group.GroupList
   :members:
   :show-inheritance:

Item Types
""""""""""

.. note::
   Items can be filtered and queried using :class:`QueryParams` and :class:`QueryRule`. See :ref:`Query Types <query_types>` for details.

.. autoclass:: monday.types.item.Item
   :members:
   :show-inheritance:

.. autoclass:: monday.types.item.ItemList
   :members:
   :show-inheritance:

.. autoclass:: monday.types.item.ItemsPage
   :members:
   :show-inheritance:

.. autoclass:: monday.types.item.OrderBy
   :members:
   :show-inheritance:

.. autoclass:: monday.types.item.QueryRule
   :members:
   :show-inheritance:

.. autoclass:: monday.types.item.QueryParams
   :members:
   :show-inheritance:

   .. note::
      For examples of how to use QueryParams to filter items, see :ref:`Filtering and Querying Items <usage_filtering_and_querying_items>` in the Usage documentation.

Subitem Types
"""""""""""""

.. autoclass:: monday.types.subitem.Subitem
   :members:
   :show-inheritance:

.. autoclass:: monday.types.subitem.SubitemList
   :members:
   :show-inheritance:

Tag Types
"""""""""

.. autoclass:: monday.types.tag.Tag
   :members:
   :show-inheritance:

Team Types
""""""""""

.. autoclass:: monday.types.team.Team
   :members:
   :show-inheritance:

Update Types
""""""""""""

.. autoclass:: monday.types.update.Update
   :members:
   :show-inheritance:

User Types
""""""""""

.. autoclass:: monday.types.user.User
   :members:
   :show-inheritance:

.. autoclass:: monday.types.user.OutOfOffice
   :members:
   :show-inheritance:

Workspace Types
"""""""""""""""

.. autoclass:: monday.types.workspace.Workspace
   :members:
   :show-inheritance:

.. _column_input_types:

Column Input Types
""""""""""""""""""

These dataclasses provide type-safe ways to set column values when updating items via the Monday.com API.

For example:

.. rstcheck: ignore-next-code-block
.. code-block:: python

   from monday.types.column_inputs import DateInput, StatusInput, TextInput, NumberInput

   # Update multiple column values at once
   await client.items.change_column_values(
      item_id=123456789,
      column_values=[
         DateInput('date_column_id', '2024-01-15', '14:30:00'),
         StatusInput('status_column_id', 'Working on it'),
         TextInput('text_column_id', 'Updated content'),
         NumberInput('number_column_id', 42.5)
      ]
   )

.. autoclass:: monday.types.column_inputs.CheckboxInput
   :members:
   :show-inheritance:

.. autoclass:: monday.types.column_inputs.CountryInput
   :members:
   :show-inheritance:

.. autoclass:: monday.types.column_inputs.DateInput
   :members:
   :show-inheritance:

.. autoclass:: monday.types.column_inputs.DropdownInput
   :members:
   :show-inheritance:

.. autoclass:: monday.types.column_inputs.EmailInput
   :members:
   :show-inheritance:

.. autoclass:: monday.types.column_inputs.HourInput
   :members:
   :show-inheritance:

.. autoclass:: monday.types.column_inputs.LinkInput
   :members:
   :show-inheritance:

.. autoclass:: monday.types.column_inputs.LocationInput
   :members:
   :show-inheritance:

.. autoclass:: monday.types.column_inputs.LongTextInput
   :members:
   :show-inheritance:

.. autoclass:: monday.types.column_inputs.NumberInput
   :members:
   :show-inheritance:

.. autoclass:: monday.types.column_inputs.PeopleInput
   :members:
   :show-inheritance:

.. autoclass:: monday.types.column_inputs.PhoneInput
   :members:
   :show-inheritance:

.. autoclass:: monday.types.column_inputs.RatingInput
   :members:
   :show-inheritance:

.. autoclass:: monday.types.column_inputs.StatusInput
   :members:
   :show-inheritance:

.. autoclass:: monday.types.column_inputs.TagInput
   :members:
   :show-inheritance:

.. autoclass:: monday.types.column_inputs.TextInput
   :members:
   :show-inheritance:

.. autoclass:: monday.types.column_inputs.TimelineInput
   :members:
   :show-inheritance:

.. autoclass:: monday.types.column_inputs.WeekInput
   :members:
   :show-inheritance:

.. autoclass:: monday.types.column_inputs.WorldClockInput
   :members:
   :show-inheritance:

Column Default Types
""""""""""""""""""""

These dataclasses are used to define default values when creating columns.

.. autoclass:: monday.types.column_defaults.StatusDefaults
   :members:
   :show-inheritance:

.. autoclass:: monday.types.column_defaults.StatusLabel
   :members:
   :show-inheritance:

.. autoclass:: monday.types.column_defaults.DropdownDefaults
   :members:
   :show-inheritance:

.. autoclass:: monday.types.column_defaults.DropdownLabel
   :members:
   :show-inheritance:

.. _query_types:

Query Types
^^^^^^^^^^^

These dataclasses are used to build complex queries and filter data from the Monday.com API. They are primarily used with the :meth:`boards.get_items() <monday.services.boards.Boards.get_items>` method to filter items based on column values, dates, text content, and other criteria.

For basic usage examples, see :ref:`Filtering and Querying Items <usage_filtering_and_querying_items>` in the Usage documentation.

For example:

.. rstcheck: ignore-next-code-block
.. code-block:: python

   from monday.types.item import QueryParams, QueryRule, OrderBy
   # Create a query to find items with status "Done" or "In Progress"
   query_params = QueryParams(
      rules=[
         QueryRule(
            column_id='status',
            compare_value=['Done', 'In Progress'],
            operator='any_of'
         )
      ],
      operator='and',
      order_by=OrderBy(
         column_id='date',
         direction='desc'
      )
   )
   # Use the query parameters
   items = await monday_client.items.query(query_params=query_params)
