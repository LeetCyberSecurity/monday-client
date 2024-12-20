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

Return Types
------------

The return types in this package map to Monday.com's GraphQL API response types. These type definitions are 
specifically designed to document the structure of data returned from API queries and are not intended for 
input parameters or mutation variables.

The mapping follows these conventions:

- ``TypedDict`` classes represent GraphQL objects (``type Object``)
- ``Required[Type]`` indicates a non-nullable GraphQL field (``Type!``)
- ``Literal`` types represent GraphQL enums (``enum State { active archived deleted }``)
- Regular type hints represent nullable GraphQL fields (``Type``)
- ``list[Type]`` represents GraphQL arrays (``[Type]``)

For example, this Python type definition:

.. code-block:: python

   class Item(TypedDict, total=False):
      name: Required[str]                              # GraphQL: name: String!
      updated_at: str                                  # GraphQL: updatedAt: String
      state: Literal['active', 'archived', 'deleted']  # GraphQL: state: State
      subitems: list[Item]                             # GraphQL: subitems: [Item]

Maps to this GraphQL schema:

.. code-block:: text

   type Item {
      name: String!
      updatedAt: String
      state: State
      subitems: [Item]
   }

   enum State {
      active
      archived
      deleted
   }

.. autoclass:: monday.types.Account
   :members:
   :show-inheritance:

.. autoclass:: monday.types.AccountProduct
   :members:
   :show-inheritance:

.. autoclass:: monday.types.ActivityLog
   :members:
   :show-inheritance:

.. autoclass:: monday.types.Asset
   :members:
   :show-inheritance:

.. autoclass:: monday.types.Board
   :members:
   :show-inheritance:

.. autoclass:: monday.types.BoardView
   :members:
   :show-inheritance:

.. autoclass:: monday.types.Column
   :members:
   :show-inheritance:

.. autoclass:: monday.types.ColumnValue
   :members:
   :show-inheritance:

.. autoclass:: monday.types.Group
   :members:
   :show-inheritance:

.. autoclass:: monday.types.Item
   :members:
   :show-inheritance:

.. autoclass:: monday.types.ItemsPage
   :no-members:
   :show-inheritance:

   .. attribute:: cursor
      :type: str

      cursor for retrieving the next page of items

   .. attribute:: items
      :type: Required[list[Item]]

      List of items

.. autoclass:: monday.types.Like
   :members:
   :show-inheritance:

.. autoclass:: monday.types.OutOfOffice
   :members:
   :show-inheritance:

.. autoclass:: monday.types.Plan
   :members:
   :show-inheritance:

.. autoclass:: monday.types.Reply
   :members:
   :show-inheritance:

.. autoclass:: monday.types.Subitem
   :members:
   :show-inheritance:

.. autoclass:: monday.types.Tag
   :members:
   :show-inheritance:

.. autoclass:: monday.types.Team
   :members:
   :show-inheritance:

.. autoclass:: monday.types.UndoData
   :members:
   :show-inheritance:

.. autoclass:: monday.types.Update
   :members:
   :show-inheritance:

.. autoclass:: monday.types.UpdateBoard
   :members:
   :show-inheritance:

.. autoclass:: monday.types.User
   :members:
   :show-inheritance:

.. autoclass:: monday.types.Watcher
   :members:
   :show-inheritance:

.. autoclass:: monday.types.Workspace
   :members:
   :show-inheritance:

.. autoclass:: monday.types.WorkspaceIcon
   :members:
   :show-inheritance:

.. autoclass:: monday.types.WorkspaceSettings
   :members:
   :show-inheritance:
