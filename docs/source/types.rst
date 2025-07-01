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

.. autoclass:: monday.types.Account
   :members:
   :show-inheritance:

.. autoclass:: monday.types.AccountProduct
   :members:
   :show-inheritance:

.. autoclass:: monday.types.Plan
   :members:
   :show-inheritance:

Asset Types
"""""""""""

.. autoclass:: monday.types.Asset
   :members:
   :show-inheritance:

Board Types
"""""""""""

.. autoclass:: monday.types.Board
   :members:
   :show-inheritance:

.. autoclass:: monday.types.ActivityLog
   :members:
   :show-inheritance:

.. autoclass:: monday.types.BoardView
   :members:
   :show-inheritance:

.. autoclass:: monday.types.UndoData
   :members:
   :show-inheritance:

.. autoclass:: monday.types.UpdateBoard
   :members:
   :show-inheritance:

Column Types
""""""""""""

.. autoclass:: monday.types.Column
   :members:
   :show-inheritance:

.. autoclass:: monday.types.ColumnValue
   :members:
   :show-inheritance:

Group Types
"""""""""""

.. autoclass:: monday.types.Group
   :members:
   :show-inheritance:

.. autoclass:: monday.types.GroupList
   :members:
   :show-inheritance:

Item Types
""""""""""

.. autoclass:: monday.types.Item
   :members:
   :show-inheritance:

.. autoclass:: monday.types.ItemList
   :members:
   :show-inheritance:

Subitem Types
"""""""""""""

.. autoclass:: monday.types.Subitem
   :members:
   :show-inheritance:

.. autoclass:: monday.types.SubitemList
   :members:
   :show-inheritance:

Tag Types
"""""""""

.. autoclass:: monday.types.Tag
   :members:
   :show-inheritance:

Team Types
""""""""""

.. autoclass:: monday.types.Team
   :members:
   :show-inheritance:

Update Types
""""""""""""

.. autoclass:: monday.types.Update
   :members:
   :show-inheritance:

User Types
""""""""""

.. autoclass:: monday.types.User
   :members:
   :show-inheritance:

.. autoclass:: monday.types.OutOfOffice
   :members:
   :show-inheritance:

Workspace Types
"""""""""""""""

.. autoclass:: monday.types.Workspace
   :members:
   :show-inheritance:

Query Types
^^^^^^^^^^^

These dataclasses are used to build complex queries and filter data from the Monday.com API.

For example:

.. code-block:: python

    from monday.services.utils.query_builder import QueryParams, QueryRule, OrderBy
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