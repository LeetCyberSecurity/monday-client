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
Module for handling Monday.com user operations.

This module provides a comprehensive set of functions and classes for interacting
with Monday.com users. It encapsulates various operations such as querying, adding,
and deleting users.

Key features:
- Query users with customizable fields and pagination

The Users class in this module serves as the main interface for these operations,
providing methods that correspond to different Monday.com API endpoints related to users.

This module is part of the monday-client package and relies on the MondayClient
for making API requests. It also utilizes various utility functions and schema
validators to ensure proper data handling and error checking.

Usage of this module requires proper authentication and initialization of the
MondayClient instance.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Union

from .schemas.users.query_user_schema import QueryUserInput
from .utils.error_handlers import check_query_result, check_schema

if TYPE_CHECKING:
    from ..client import MondayClient


class Users:
    """
    Handles operations related to Monday.com users.

    This class provides a comprehensive set of methods for interacting with users
    on Monday.com. It encapsulates functionality for creating, querying, modifying,
    and deleting users, as well as managing their properties and relationships.

    Each method in this class corresponds to a specific Monday.com API endpoint,
    providing a pythonic interface for user-related operations.

    Note:
        This class requires an initialized MondayClient instance for making API requests.
    """

    logger: logging.Logger = logging.getLogger(__name__)

    def __init__(self, client: 'MondayClient'):
        """
        Initialize a Users instance with specified parameters.

        Args:
            client: The MondayClient instance to use for API requests.
        """
        self.client: 'MondayClient' = client

    async def query(
        self,
        fields: str = 'id email',
        emails: Optional[Union[str, List[str]]] = None,
        ids: Optional[Union[int, List[int]]] = None,
        name: Optional[str] = None,
        kind: Literal['all', 'guests', 'non_guests', 'non_pending'] = 'all',
        newest_first: bool = False,
        non_active: bool = False,
        limit: int = 50,
        page: int = 1,
        paginate: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Query users to return metadata about one or multiple users.

        Args:
            fields: Fields to return from the users query.
            emails: The specific user emails to return.
            ids: The IDs of the specific users to return.
            name: A fuzzy search of users by name.
            kind: The kind of users to search by.
            newest_first: Lists the most recently created users at the top.
            non_active: Returns non-active users.
            limit: The number of users to get per page.
            page: The page number to start from.
            paginate: Whether to paginate results or just return the first page.

        Returns:
            List of dictionaries containing queried user data.

        Raises:
            MondayAPIError: If API request fails or returns unexpected format.
            ValueError: If input parameters are invalid.
        """
        input_data = check_schema(
            QueryUserInput,
            fields=fields,
            emails=emails,
            ids=ids,
            name=name,
            kind=kind,
            newest_first=newest_first,
            non_active=non_active,
            limit=limit,
            page=page,
            paginate=paginate
        )

        page = input_data.page
        users_data = []
        while True:
            query_string = self._build_users_query_string(input_data, page)

            query_result = await self.client.post_request(query_string)

            data = check_query_result(query_result)

            if not data['data']['users']:
                break

            users_data.extend(data['data']['users'])

            if not paginate:
                break

            page += 1

        return users_data

    def _build_users_query_string(self, input_data: QueryUserInput, page: Optional[int] = None) -> str:
        """
        Build GraphQL query string for user queries.

        Args:
            input_data: User query input data.
            page: Page number for pagination.

        Returns:
            Formatted GraphQL query string for querying users.
        """
        input_data.emails = [f'"{i}"' for i in input_data.emails] if input_data.emails else None
        args = {
            'emails': f"[{', '.join(input_data.emails)}]" if input_data.emails else None,
            'ids': f"[{', '.join(map(str, input_data.ids))}]" if input_data.ids else None,
            'name': f'"{input_data.name}"' if input_data.name else None,
            'kind': input_data.kind,
            'newest_first': str(input_data.newest_first).lower(),
            'non_active': str(input_data.non_active).lower(),
            'limit': input_data.limit,
            'page': page,
        }
        args_str = ', '.join(f"{k}: {v}" for k, v in args.items() if v is not None)

        return f"""
            query {{
                users ({args_str}) {{
                    {input_data.fields}
                }}
            }}
        """
