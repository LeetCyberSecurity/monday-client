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
Client module for interacting with the monday.com API.

This module provides a comprehensive client for interacting with the monday.com GraphQL API.
It includes the MondayClient class, which handles authentication, rate limiting, pagination,
and various API operations.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any

import aiohttp

from monday.config import Config
from monday.exceptions import (ComplexityLimitExceeded, MondayAPIError,
                               MutationLimitExceeded, QueryFormatError)
from monday.http_adapters import AiohttpAdapter, HttpxAdapter
from monday.services.boards import Boards
from monday.services.groups import Groups
from monday.services.items import Items
from monday.services.subitems import Subitems
from monday.services.users import Users
from monday.services.utils.error_handlers import (ErrorHandler,
                                                  check_query_result)
from monday.services.webhooks import Webhooks


class MondayClient:
    """
    Client for interacting with the monday.com API.
    This client handles API requests, rate limiting, and pagination for monday.com's GraphQL API.

    Logging:
        Each module in this library uses a module-level logger under the
        ``monday.*`` namespace (for example, ``monday.client``). These
        loggers propagate to the root library logger ``monday``. Configure
        logging either by working with the ``monday`` logger directly or by
        using helpers in :mod:`monday.logging_utils`.

    Usage:
        .. code-block:: python

            # Recommended: Using configuration object
            >>> from monday import MondayClient, Config
            >>> config = Config(api_key='your_api_key')
            >>> monday_client = MondayClient(config)
            >>> monday_client.boards.query(board_ids=987654321)

            # Alternative: Using individual parameters
            >>> monday_client = MondayClient(api_key='your_api_key')
            >>> monday_client.boards.query(board_ids=987654321)

    Args:
        config: Config instance containing all client settings (recommended approach).
        api_key: The API key for authenticating with the monday.com API (alternative approach).
        url: The endpoint URL for the monday.com API.
        version: The monday.com API version to use.
        headers: Additional HTTP headers used for API requests.
        max_retries: Maximum amount of retry attempts before raising an error.

    """

    logger: logging.Logger = logging.getLogger(__name__)
    """
    Module logger used by this class (e.g., ``monday.client``).

    Note:
        By default, a ``NullHandler`` is attached to the root ``monday`` logger
        to suppress output. To enable logs quickly in development, call:

        .. code-block:: python

            from monday import enable_logging
            enable_logging()  # Enable with default settings

        To integrate with an existing logging configuration, call:

        .. code-block:: python

            import logging.config
            from monday import configure_for_external_logging

            configure_for_external_logging()
            logging.config.dictConfig({
                'version': 1,
                'handlers': {'console': {'class': 'logging.StreamHandler'}},
                'loggers': {'monday': {'level': 'INFO', 'handlers': ['console']}},
            })

        Other helpers:

        .. code-block:: python

            from monday import set_log_level, disable_logging
            set_log_level('DEBUG')  # Change level
            disable_logging()       # Turn off completely
    """

    def __init__(  # noqa: PLR0913
        self,
        config: Config | None = None,
        *,
        api_key: str | None = None,
        url: str = 'https://api.monday.com/v2',
        version: str | None = None,
        headers: dict[str, Any] | None = None,
        max_retries: int = 4,
        transport: str = 'aiohttp',
    ):
        """
        Initialize the MondayClient with either a configuration object or individual parameters.

        Args:
            config: Config instance containing all client settings.
            api_key: The API key for authenticating with the monday.com API.
            url: The endpoint URL for the monday.com API.
            version: The monday.com API version to use. If None, will automatically fetch the current version.
            headers: Additional HTTP headers used for API requests.
            max_retries: Maximum amount of retry attempts before raising an error.
            transport: HTTP transport to use: 'aiohttp' (default) or 'httpx'.

        Raises:
            ValueError: If neither config nor api_key is provided, or if both config and individual parameters are provided.

        """
        self._validate_init_params(config, api_key)

        if config is not None:
            self._setup_from_config(config)
        else:
            self._setup_from_params(api_key, url, version, headers, max_retries)

        # Initialize transport adapter
        if transport == 'httpx':
            self._adapter = HttpxAdapter(
                proxy_url=self.proxy_url,
                proxy_auth=self.proxy_auth,
                proxy_auth_type=self.proxy_auth_type,
                proxy_trust_env=self.proxy_trust_env,
                proxy_headers=self.proxy_headers,
                proxy_ssl_verify=self.proxy_ssl_verify,
                timeout_seconds=self.timeout,
            )
        else:
            self._adapter = AiohttpAdapter(
                proxy_url=self.proxy_url,
                proxy_auth=self.proxy_auth,
                proxy_auth_type=self.proxy_auth_type,
                proxy_trust_env=self.proxy_trust_env,
                proxy_ssl_verify=self.proxy_ssl_verify,
                timeout_seconds=self.timeout,
            )

        # Task-local header overrides for concurrency-safe per-call credentials
        self._headers_override: ContextVar[dict[str, Any] | None] = ContextVar(
            'headers_override', default=None
        )

        self._initialize_services()

    @asynccontextmanager
    async def use_api_key(self, api_key: str):
        """
        Temporarily override the Authorization header for awaited calls within the context.

        Example:
            async with client.use_api_key('integration_oauth_token'):
                await client.webhooks.create(...)

        """
        token = self._headers_override.set({'Authorization': api_key})
        try:
            yield self
        finally:
            self._headers_override.reset(token)

    @asynccontextmanager
    async def use_headers(self, headers: dict[str, Any]):
        """
        Temporarily override arbitrary headers for awaited calls within the context.

        Example:
            async with client.use_headers({'Authorization': 'token2', 'API-Version': '2025-01'}):
                await client.users.query(...)

        """
        token = self._headers_override.set(headers)
        try:
            yield self
        finally:
            self._headers_override.reset(token)

    async def post_request(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Executes an asynchronous post request to the monday.com API with rate limiting and retry logic.

        Args:
            query: The GraphQL query string to be executed.
            variables: Optional GraphQL variables to include with the query.

        Returns:
            A dictionary containing the response data from the API.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds monday.com's complexity limits.
            MutationLimitExceeded: When the API rate limit is exceeded.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.
            aiohttp.ClientError: When there's a client-side network or connection error.

        Example:
            .. code-block:: python

                # Using config object (recommended)
                >>> from monday import MondayClient, Config
                >>> config = Config(api_key='your_api_key')
                >>> monday_client = MondayClient(config)
                >>> await monday_client.post_request(
                ...      query='query { boards (ids: 987654321) { id name } }'
                ... )

                # Using individual parameters (alternative)
                >>> monday_client = MondayClient(api_key='your_api_key')
                >>> await monday_client.post_request(
                ...      query='query { boards (ids: 987654321) { id name } }'
                ... )
                {
                    "data": {
                        "boards": [
                            {
                                "id": "987654321",
                                "name": "Board 1"
                            }
                        ]
                    },
                    "account_id": 1234567
                }

        Note:
            This is a low-level method that directly executes GraphQL queries. In most cases, you should use the higher-level
            methods provided by the :ref:`service classes <services_section>` instead, as they handle query construction
            and provide a more user-friendly interface.

        """
        # Ensure version is set before making any requests
        await self._ensure_version_set()

        response_data = None
        for attempt in range(self.max_retries):
            response_headers = {}

            try:
                response_data, response_headers = await self._execute_request(
                    query, variables
                )
                self._handle_api_errors(response_data, response_headers, query)
            except (ComplexityLimitExceeded, MutationLimitExceeded) as e:
                if attempt < self.max_retries - 1:
                    self.logger.warning(
                        'Attempt %d failed: %s. Retrying...', attempt + 1, str(e)
                    )
                    await asyncio.sleep(e.reset_in)
                else:
                    self.logger.exception('Max retries reached. Last error: ')
                    e.args = (f'Max retries ({self.max_retries}) reached',)
                    raise
            except (MondayAPIError, QueryFormatError):
                self.logger.exception('Attempt %d failed', attempt + 1)
                raise
            except aiohttp.ClientError as e:
                if attempt < self.max_retries - 1:
                    # Check for Retry-After header even for client errors
                    retry_seconds = self._error_handler.get_retry_after_seconds(
                        response_headers, self._rate_limit_seconds
                    )
                    self.logger.warning(
                        'Attempt %d failed due to aiohttp.ClientError: %s. Retrying after %d seconds...',
                        attempt + 1,
                        str(e),
                        retry_seconds,
                    )
                    await asyncio.sleep(retry_seconds)
                else:
                    self.logger.exception(
                        'Max retries reached. Last error (aiohttp.ClientError)'
                    )
                    e.args = (f'Max retries ({self.max_retries}) reached',)
                    raise
            except Exception as e:  # Fallback for other transport errors (e.g., httpx)
                if attempt >= self.max_retries - 1:
                    self.logger.exception('Max retries reached. Last network error')
                    raise
                retry_seconds = self._error_handler.get_retry_after_seconds(
                    response_headers, self._rate_limit_seconds
                )
                self.logger.warning(
                    'Attempt %d failed due to network error: %s. Retrying after %d seconds...',
                    attempt + 1,
                    str(e),
                    retry_seconds,
                )
                await asyncio.sleep(retry_seconds)
            else:
                # Always check for legacy errors before returning
                check_query_result(response_data)
                return response_data

        return {'error': f'Max retries reached: {response_data}'}

    def _validate_init_params(self, config: Config | None, api_key: str | None) -> None:
        """Validate initialization parameters."""
        if config is not None and api_key is not None:
            error_msg = 'Cannot specify both config and individual parameters'
            raise ValueError(error_msg)

        if config is None and api_key is None:
            error_msg = 'Either config or api_key must be provided'
            raise ValueError(error_msg)

    def _setup_from_config(self, config: Config) -> None:
        """Setup client from config object."""
        if not isinstance(config, Config):
            error_msg = f'Expected Config, got {type(config).__name__}'
            raise TypeError(error_msg)
        config.validate()

        self.url = config.url
        self.api_key = config.api_key
        self.version = config.version
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': config.api_key,
            **config.headers,
        }
        self.max_retries = int(config.max_retries)
        self._rate_limit_seconds = config.rate_limit_seconds
        self.timeout = config.timeout
        self.proxy_url = config.proxy_url
        self.proxy_auth = config.proxy_auth
        self.proxy_auth_type = config.proxy_auth_type
        self.proxy_trust_env = config.proxy_trust_env
        self.proxy_headers = config.proxy_headers
        self.proxy_ssl_verify = config.proxy_ssl_verify

    def _setup_from_params(
        self,
        api_key: str | None,
        url: str,
        version: str | None,
        headers: dict[str, Any] | None,
        max_retries: int,
    ) -> None:
        """Setup client from individual parameters."""
        if api_key is None:
            error_msg = 'api_key cannot be None'
            raise ValueError(error_msg)

        self.url = url
        self.api_key = api_key
        self.version = version
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': api_key,
            **(headers or {}),
        }
        self.max_retries = int(max_retries)
        self._rate_limit_seconds = 60
        self.timeout = 30
        self.proxy_url = None
        self.proxy_auth = None
        self.proxy_auth_type = 'basic'
        self.proxy_trust_env = False
        self.proxy_headers = {}
        self.proxy_ssl_verify = True

    def _initialize_services(self) -> None:
        """Initialize service instances and error handler."""
        # Initialize service instances
        self.boards = Boards(self)
        """
        Service for board-related operations

        Type: `Boards <services.html#boards>`_
        """
        self.items = Items(self, self.boards)
        """
        Service for item-related operations

        Type: `Items <services.html#items>`_
        """
        self.subitems = Subitems(self, self.items, self.boards)
        """
        Service for subitem-related operations

        Type: `Subitems <services.html#subitems>`_
        """
        self.groups = Groups(self, self.boards)
        """
        Service for group-related operations

        Type: `Groups <services.html#groups>`_
        """
        self.users = Users(self)
        """
        Service for user-related operations

        Type: `Users <services.html#users>`_
        """

        self.webhooks = Webhooks(self)
        """
        Service for webhook-related operations

        Type: `Webhooks <services.html#webhooks>`_
        """

        self._query_errors = {'argumentLiteralsIncompatible'}
        self._error_handler = ErrorHandler(self._rate_limit_seconds)

    def _handle_api_errors(
        self,
        response_data: dict[str, Any],
        response_headers: dict[str, str],
        query: str,
    ) -> None:
        """
        Handle API errors and raise appropriate exceptions.

        Args:
            response_data: The response data from the API.
            response_headers: HTTP response headers from the API.
            query: The original GraphQL query.

        Raises:
            ComplexityLimitExceeded: When the API request exceeds complexity limits.
            MutationLimitExceeded: When the API rate limit is exceeded.
            QueryFormatError: When the GraphQL query format is invalid.
            MondayAPIError: When an unhandled monday.com API error occurs.

        """
        # Handle GraphQL-compliant error format
        if response_data.get('errors'):
            self._error_handler.handle_graphql_errors(
                response_data, response_headers, query
            )

    async def _ensure_version_set(self) -> None:
        """
        Ensure the API version is set, fetching the current version if needed.
        """
        if self.version is None:
            self.version = await self._get_current_version()
            self.headers['API-Version'] = self.version

    async def _get_current_version(self) -> str:
        """
        Fetch the current monday.com API version.

        Returns:
            The current API version string.

        Raises:
            MondayAPIError: If unable to fetch the current version.

        """
        # Use a temporary session without version header to query versions
        temp_headers = {
            'Content-Type': 'application/json',
            'Authorization': self.api_key,
        }

        query = """
        query {
            versions {
                kind
                value
                display_name
            }
        }
        """

        error_msg: str | None = None
        current_version_str: str | None = None
        data: dict[str, Any] | None = None

        try:
            data, _ = await self._adapter.post(
                url=self.url,
                json={'query': query},
                headers=temp_headers,
                timeout_seconds=self.timeout,
            )
            if 'errors' in data:
                error_msg = f'Failed to fetch API versions: {data["errors"]}'

            versions = data.get('data', {}).get('versions', [])
            current_version = next(
                (v['value'] for v in versions if v['kind'] == 'current'), None
            )

            if not current_version and error_msg is None:
                error_msg = 'No current version found in API response'

            if error_msg is None:
                current_version_str = str(current_version)
            self.logger.info(
                'Using current monday.com API version: %s', current_version_str
            )

        except Exception as e:
            raise MondayAPIError(
                message=f'Network error while fetching API version: {e}'
            ) from e

        if error_msg is not None:
            raise MondayAPIError(message=error_msg, json=data or {})

        return current_version_str or ''

    async def _execute_request(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> tuple[dict[str, Any], dict[str, str]]:
        """
        Executes a single API request.

        Args:
            query: The GraphQL query to be executed.
            variables: Optional GraphQL variables to include with the query.

        Returns:
            A tuple containing (JSON response from the API, HTTP response headers).

        Raises:
            aiohttp.ClientError: If there's a client-side error during the request.

        """
        payload: dict[str, Any] = {'query': query}
        if variables:
            payload['variables'] = variables

        # Merge task-local header overrides (if any) in a concurrency-safe way
        override_headers = self._headers_override.get()
        effective_headers: dict[str, Any] = (
            self.headers
            if not override_headers
            else {**self.headers, **override_headers}
        )

        response_data, response_headers = await self._adapter.post(
            url=self.url,
            json=payload,
            headers=effective_headers,
            timeout_seconds=self.timeout,
        )
        return response_data, response_headers


logging.getLogger('monday').addHandler(logging.NullHandler())
