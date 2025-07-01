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
Module for handling monday.com subitem-related services.

This module provides a comprehensive set of operations for managing subitems in
monday.com boards.

This module is part of the monday-client package and relies on the MondayClient
for making API requests. It also utilizes various utility functions to ensure proper 
data handling and error checking.

Usage of this module requires proper authentication and initialization of the
MondayClient instance.
"""

import logging
from typing import TYPE_CHECKING, Any, Literal, Optional, Union

from monday.fields.item_fields import ItemFields
from monday.services.utils.error_handlers import check_query_result
from monday.services.utils.fields import Fields
from monday.services.utils.query_builder import build_graphql_query
from monday.types.column import ColumnType
from monday.types.subitem import Subitem, SubitemList

if TYPE_CHECKING:
    from monday.client import MondayClient
    from monday.services.boards import Boards
    from monday.services.items import Items


class Subitems:
    """
    Service class for handling monday.com subitem operations.
    """

    _logger: logging.Logger = logging.getLogger(__name__)

    def __init__(
        self,
        client: 'MondayClient',
        items: 'Items',
        boards: 'Boards'
    ):
        """
        Initialize a Subitems instance with specified parameters.

        Args:
            client: The MondayClient instance to use for API requests.
            items: The Items instance to use for item-related operations.
            boards: The Boards instance to use for board-related operations.
        """
        self.client = client
        self.items = items
        self.boards = boards

    async def query(
        self,
        item_ids: Union[int, list[int]],
        subitem_ids: Optional[Union[int, list[int]]] = None,
        fields: Union[str, Fields] = ItemFields.BASIC,
        **kwargs: Any
    ) -> list[SubitemList]:
        """
        Query items to return metadata about one or multiple subitems.

        Args:
            item_ids: The ID or list of IDs of the specific items containing the subitems to return.
            subitem_ids: The ID or list of IDs of the specific subitems to return.
            fields: Fields to return from the queried subitems.
            **kwargs: Additional keyword arguments for the underlying :meth:`Items.query() <monday.services.Items.query>` call.

        Returns:
            A list of SubitemList dataclass instances containing item IDs and their associated subitems.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> result = await monday_client.subitems.query(
                ...     item_ids=[123456789, 012345678],
                ...     subitem_ids=[987654321, 098765432, 998765432],
                ...     fields='id name state updates { text_body }'
                ... )
                >>> result[0].item_id
                "123456789"
                >>> result[0].subitems[0].id
                "987654321"
                >>> result[0].subitems[0].name
                "subitem"
                >>> result[0].subitems[0].state
                "active"
        """

        fields = Fields(fields)

        if not subitem_ids:
            fields = Fields(f'''
                id subitems 
                {{
                    {str(fields)}   
                }}
            ''')

            query_result = await self.items.query(
                item_ids=item_ids,
                fields=fields,
                **kwargs
            )

            return [SubitemList(item_id=item.id, subitems=item.subitems if item.subitems else []) for item in query_result]

        else:
            subitem_board_query_result = await self.items.query(
                item_ids=item_ids,
                fields='id subitems { id board { id } }',
                **kwargs
            )

            subitem_ids = subitem_ids if isinstance(subitem_ids, list) else [subitem_ids]
            items = []
            for parent_item in subitem_board_query_result:
                if not parent_item.subitems:
                    continue

                parent_subitem_ids = [s for s in subitem_ids if any(int(subitem.id) == int(s) for subitem in parent_item.subitems)]
                if not parent_subitem_ids:
                    continue

                subitem_board_id = int(parent_item.subitems[0].board.id) if parent_item.subitems[0].board else 0
                query_result = await self.boards.get_items(
                    board_ids=subitem_board_id,
                    query_params={'ids': parent_subitem_ids},
                    fields=fields
                )
                # Convert Item instances to Subitem instances
                subitems = []
                if query_result and query_result[0].items:
                    for item in query_result[0].items:
                        if isinstance(item, Subitem):
                            subitems.append(item)
                        else:
                            # Convert Item to Subitem if needed
                            subitems.append(Subitem.from_dict(item.to_dict() if hasattr(item, 'to_dict') else item))

                items.append(SubitemList(item_id=parent_item.id, subitems=subitems))

            return items

    async def create(
        self,
        item_id: int,
        subitem_name: str,
        column_values: Optional[dict[ColumnType, Union[str, dict[str, Any]]]] = None,
        create_labels_if_missing: bool = False,
        fields: Union[str, Fields] = ItemFields.BASIC
    ) -> Subitem:
        """
        Create a new subitem on an item.

        Args:
            item_id: The ID of the item where the subitem will be created.
            item_name: The name of the subitem.
            column_values: Column values for the subitem.
            create_labels_if_missing: Creates status/dropdown labels if they are missing.
            fields: Fields to return from the created subitem.

        Returns:
            Subitem dataclass instance containing info for the created subitem.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> subitem = await monday_client.subitems.create(
                ...     item_id=123456789,
                ...     subitem_name='New Subitem',
                ...     column_values={
                ...         'status': 'Done',
                ...         'text': 'This subitem is done'
                ...     },
                ...     fields='id name column_values (ids: ["status", "text"]) { id text }'
                ... )
                >>> subitem.id
                "123456789"
                >>> subitem.name
                "New Subitem"
                >>> subitem.column_values[0].id
                "status"
                >>> subitem.column_values[0].text
                "Done"
        """

        fields = Fields(fields)

        args = {
            'parent_item_id': item_id,
            'item_name': subitem_name,
            'column_values': column_values,
            'create_labels_if_missing': create_labels_if_missing,
            'fields': fields
        }

        query_string = build_graphql_query(
            'create_subitem',
            'mutation',
            args
        )

        query_result = await self.client.post_request(query_string)

        data = check_query_result(query_result)

        return Subitem.from_dict(data['data']['create_subitem'])
