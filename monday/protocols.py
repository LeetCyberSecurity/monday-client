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

"""Protocols for dependency injection in monday-client."""

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from monday.config import Config


class HTTPClient(Protocol):
    """Protocol defining the interface for HTTP clients used by monday services."""

    async def post_request(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute a POST request to the monday.com API.

        Args:
            query: The GraphQL query string to execute
            variables: Optional GraphQL variables to include with the query

        Returns:
            Response data from the API

        Raises:
            Various exceptions for different error conditions

        """
        ...


class MondayClientProtocol(HTTPClient, Protocol):
    """
    Extended protocol for MondayClient that includes additional properties
    that services might need.
    """

    @property
    def api_key(self) -> str:
        """The API key used for authentication."""
        ...

    @property
    def url(self) -> str:
        """The API endpoint URL."""
        ...

    @property
    def version(self) -> str | None:
        """The API version being used."""
        ...

    @property
    def headers(self) -> dict[str, Any]:
        """HTTP headers used for requests."""
        ...

    @property
    def max_retries(self) -> int:
        """Maximum number of retry attempts."""
        ...


class ConfigProtocol(Protocol):
    """Protocol for configuration providers."""

    def get_config(self) -> 'Config':
        """Get the Monday configuration."""
        ...

    def reload_config(self) -> None:  # pragma: no cover - optional
        """Reload configuration from its source (optional)."""
        ...

    def validate_config(self) -> bool:  # pragma: no cover - optional
        """Validate the configuration (optional)."""
        ...


class TransportAdapter(Protocol):
    """
    Protocol for pluggable HTTP transport adapters.

    Note:
        Only ``post()`` is required by current adapters. Other methods shown here are optional
        and may be unimplemented by specific transports.

    """

    async def post(
        self,
        *,
        url: str,
        json: dict[str, Any],
        headers: dict[str, str],
        timeout_seconds: int,
    ) -> tuple[dict[str, Any], dict[str, str]]:
        """Execute a POST request and return JSON body and response headers."""
        ...

    def validate_config(self) -> bool:  # pragma: no cover - optional
        """Validate the configuration (optional)."""
        ...

    def reload_config(self) -> None:  # pragma: no cover - optional
        """Reload configuration from source (optional)."""
        ...
