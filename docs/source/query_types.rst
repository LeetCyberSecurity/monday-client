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

Query Types
-----------

The query types in this package map to Monday.com's GraphQL API query field and argument types.

The mapping follows these conventions:

- ``TypedDict`` classes represent GraphQL objects (``type Object``)
- ``Required[Type]`` indicates a non-nullable GraphQL field (``Type!``)
- ``Literal`` types represent GraphQL enums (``enum State { active archived deleted }``)
- Regular type hints represent nullable GraphQL fields (``Type``)
- ``list[Type]`` represents GraphQL arrays (``[Type]``)

For example, this Python type definition:

.. code-block:: python

    class OrderBy(TypedDict, total=False):
        column_id: Required[str]           # GraphQL: column_id: String!
        direction: Literal['asc', 'desc']  # GraphQL: direction: ItemsOrderByDirection

Maps to this GraphQL schema:

.. code-block:: text

    type OrderBy {
        column_id: String!
        direction: ItemsOrderByDirection
    }

    enum ItemsOrderByDirection {
        asc
        desc
    }

.. autoclass:: monday.types.ColumnFilter
    :members:
    :show-inheritance:

.. autoclass:: monday.types.ColumnValueDict
    :members:
    :show-inheritance:

.. autoclass:: monday.types.OrderBy
    :members:
    :show-inheritance:

.. autoclass:: monday.types.PersonOrTeam
    :members:
    :show-inheritance:

.. autoclass:: monday.types.QueryParams
    :members:
    :show-inheritance:

.. autoclass:: monday.types.QueryRule
    :members:
    :show-inheritance: