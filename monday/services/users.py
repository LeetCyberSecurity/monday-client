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
Module for handling monday.com user operations.

This module provides a comprehensive set of functions and classes for interacting
with monday.com users.

This module is part of the monday-client package and relies on the MondayClient
for making API requests. It also utilizes various utility functions to ensure proper 
data handling and error checking.

Usage of this module requires proper authentication and initialization of the
MondayClient instance.
"""

import logging
from typing import TYPE_CHECKING, Any, Literal, Optional, Union

from monday.services.utils import build_graphql_query, check_query_result

if TYPE_CHECKING:
    from monday import MondayClient


class Users:
    """
    Service class for handling monday.com user operations.
    """

    _logger: logging.Logger = logging.getLogger(__name__)

    def __init__(
        self,
        client: 'MondayClient'
    ):
        """
        Initialize a Users instance with specified parameters.

        Args:
            client: The MondayClient instance to use for API requests.
        """
        self.client: 'MondayClient' = client

    async def query(
        self,
        emails: Optional[Union[str, list[str]]] = None,
        ids: Optional[Union[int, list[int]]] = None,
        name: Optional[str] = None,
        kind: Literal['all', 'guests', 'non_guests', 'non_pending'] = 'all',
        newest_first: bool = False,
        non_active: bool = False,
        limit: int = 50,
        page: int = 1,
        paginate: bool = True,
        fields: str = 'id'
    ) -> list[dict[str, Any]]:
        """
        Query users to return metadata about one or multiple users.

        Args:
            emails: The specific user emails to return.
            ids: The IDs of the specific users to return.
            name: A fuzzy search of users by name.
            kind: The kind of users to search by.
            newest_first: Lists the most recently created users at the top.
            non_active: Returns non-active users.
            limit: The number of users to get per page.
            page: The page number to start from.
            paginate: Whether to paginate results or just return the first page.
            fields: Fields to return from the queried users.

        Returns:
            List of dictionaries containing info for the queried users.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                >>> from monday import MondayClient
                >>> monday_client = MondayClient('your_api_key')
                >>> await monday_client.users.query(
                ...     emails=[
                ...         'user1@domain.com',
                ...         'user2@domain.com'
                ...     ],
                ...     fields='id name'
                ... )
                [
                    {
                        "id": "12345678",
                        "name": "User One"
                    },
                    {
                        "id": "01234567",
                        "name": "User Two"
                    }
                ]
        """
        args = {
            'emails': emails,
            'ids': ids,
            'name': name,
            'kind': kind,
            'newest_first': newest_first,
            'non_active': non_active,
            'limit': limit,
            'page': page,
            'fields': fields
        }

        query_string = build_graphql_query(
            'users',
            'query',
            args
        )

        users_data = []
        last_response = None

        while True:
            query_result = await self.client.post_request(query_string)
            data = check_query_result(query_result)

            current_users = data['data']['users']
            if not current_users:
                break

            if current_users == last_response:
                self._logger.debug('Received duplicate page of users, stopping pagination')
                break

            users_data.extend(current_users)
            last_response = current_users

            if len(current_users) < limit:
                self._logger.debug('Received fewer results than limit, reached last page')
                break

            if not paginate:
                break

            args['page'] += 1
            query_string = build_graphql_query('users', 'query', args)

        # Unique the users by ID before returning
        seen_ids = set()
        unique_users = []
        for user in users_data:
            if user['id'] not in seen_ids:
                seen_ids.add(user['id'])
                unique_users.append(user)

        return unique_users
