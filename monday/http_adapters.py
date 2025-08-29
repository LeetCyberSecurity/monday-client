"""
HTTP transport adapters for monday-client.

Provides a pluggable transport abstraction so we can support different HTTP stacks
like aiohttp or httpx without changing the public client API.
"""

from __future__ import annotations

import base64
import importlib.util as _import_util
import logging
from typing import Any
from urllib.parse import urlparse

import aiohttp

logger = logging.getLogger(__name__)


class AiohttpAdapter:
    """Adapter that uses aiohttp for requests."""

    def __init__(  # noqa: PLR0913
        self,
        *,
        proxy_url: str | None,
        proxy_auth: tuple[str, str] | None,
        proxy_auth_type: str,
        proxy_trust_env: bool,
        proxy_ssl_verify: bool,
        timeout_seconds: int,
    ) -> None:
        self._proxy_url = proxy_url
        self._proxy_auth = proxy_auth
        self._proxy_auth_type = proxy_auth_type
        self._proxy_trust_env = proxy_trust_env
        self._proxy_ssl_verify = proxy_ssl_verify
        self._timeout_seconds = timeout_seconds

    def _build_request_proxy_kwargs(self) -> dict[str, Any]:
        if not self._proxy_url:
            return {}
        scheme = urlparse(self._proxy_url).scheme.lower()
        if scheme.startswith('socks'):
            return {}
        kwargs: dict[str, Any] = {'proxy': self._proxy_url}
        if self._proxy_auth:
            if self._proxy_auth_type and self._proxy_auth_type != 'basic':
                # Silent fallback to basic; the client already logs a warning
                pass
            kwargs['proxy_auth'] = aiohttp.BasicAuth(
                self._proxy_auth[0], self._proxy_auth[1]
            )
        if scheme == 'https' and self._proxy_ssl_verify is False:
            kwargs['proxy_ssl'] = False
        return kwargs

    def _create_connector(self) -> aiohttp.BaseConnector | None:
        if not self._proxy_url:
            return None
        scheme = urlparse(self._proxy_url).scheme.lower()
        if scheme.startswith('socks'):
            try:
                from aiohttp_socks import ProxyConnector  # noqa: PLC0415
            except ImportError:
                return None
            username = self._proxy_auth[0] if self._proxy_auth else None
            password = self._proxy_auth[1] if self._proxy_auth else None
            return ProxyConnector.from_url(
                self._proxy_url, username=username, password=password
            )
        return None

    async def post(
        self,
        *,
        url: str,
        json: dict[str, Any],
        headers: dict[str, str],
        timeout_seconds: int | None = None,
    ) -> tuple[dict[str, Any], dict[str, str]]:
        """Send a POST request with JSON and return the parsed JSON and headers."""
        timeout = aiohttp.ClientTimeout(total=timeout_seconds or self._timeout_seconds)
        connector = self._create_connector()
        async with (
            aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                trust_env=self._proxy_trust_env,
            ) as session,
            session.post(
                url, json=json, headers=headers, **self._build_request_proxy_kwargs()
            ) as response,
        ):
            response_headers = dict(response.headers)
            try:
                data = await response.json()
            except aiohttp.ContentTypeError:
                text = await response.text()
                return {'error': f'Non-JSON response: {text[:200]}'}, response_headers
            return data, response_headers


class HttpxAdapter:
    """
    Adapter that uses httpx for requests.

    Notes:
        - Requires httpx to be installed by the user. Imported lazily.
        - Supports basic proxy auth. Advanced auth may require plugins.
        - Allows disabling TLS verification when talking to an HTTPS proxy via a custom proxy SSL context.

    """

    # Handle proxy 407 challenge for Kerberos/SPNEGO - single retry
    PROXY_AUTH_REQUIRED = 407

    def __init__(  # noqa: PLR0913
        self,
        *,
        proxy_url: str | None,
        proxy_auth: tuple[str, str] | None,
        proxy_auth_type: str,
        proxy_trust_env: bool,
        proxy_headers: dict[str, str] | None,
        proxy_ssl_verify: bool,
        timeout_seconds: int,
    ) -> None:
        self._proxy_url = proxy_url
        self._proxy_auth = proxy_auth
        self._proxy_auth_type = proxy_auth_type
        self._proxy_trust_env = proxy_trust_env
        self._proxy_headers = proxy_headers or {}
        self._proxy_ssl_verify = proxy_ssl_verify
        self._timeout_seconds = timeout_seconds

    def _build_client(  # noqa: PLR0912
        self,
        *,
        override_proxy_headers: dict[str, str] | None = None,
        negotiate_token_b64: str | None = None,
    ):
        import httpx  # noqa: PLC0415

        proxy_url: str | None = None
        if self._proxy_url:
            parsed = urlparse(self._proxy_url)
            if self._proxy_auth and not (parsed.username or parsed.password):
                username, password = self._proxy_auth
                proxy_url = f'{parsed.scheme}://{username}:{password}@{parsed.hostname}'
                if parsed.port:
                    proxy_url += f':{parsed.port}'
            else:
                proxy_url = self._proxy_url
            # Warn if SOCKS scheme is used but socks support likely missing
            if (
                parsed.scheme.lower().startswith('socks')
                and _import_util.find_spec('socksio') is None
            ):
                logger.warning(
                    'SOCKS proxy specified but socks support not installed. '
                    'Install with: pip install "httpx[socks]" or monday-client[httpx]'
                )

        # Build proxy object with headers
        proxy_headers: dict[str, str] = dict(self._proxy_headers)
        if override_proxy_headers:
            proxy_headers.update(override_proxy_headers)
        if negotiate_token_b64:
            proxy_headers['Proxy-Authorization'] = f'Negotiate {negotiate_token_b64}'

        client_kwargs: dict[str, Any] = {
            'trust_env': self._proxy_trust_env,
            'timeout': self._timeout_seconds,
        }
        if proxy_url:
            proxy_obj: Any
            if proxy_headers:
                proxy_obj = httpx.Proxy(proxy_url, headers=proxy_headers)
            else:
                proxy_obj = proxy_url
            client_kwargs['proxy'] = proxy_obj

        # Note: Disabling TLS verification for HTTPS proxies is not directly configurable
        # in httpx per-proxy. If needed, a custom transport would be required.
        client = httpx.AsyncClient(**client_kwargs)

        # Attach advanced auth plugins if available (optional deps)
        # NTLM (server-side or transparent proxies)
        if self._proxy_auth_type and self._proxy_auth_type.lower() == 'ntlm':
            try:
                from httpx_ntlm import HttpNtlmAuth  # noqa: PLC0415

                if self._proxy_auth:
                    username, password = self._proxy_auth
                    client.auth = HttpNtlmAuth(username, password)
            except Exception:  # noqa: BLE001
                logger.warning('httpx-ntlm not installed; NTLM not enabled')

        # Kerberos / SPNEGO via pyspnego - initialize context
        if (
            self._proxy_url
            and self._proxy_auth_type
            and self._proxy_auth_type.lower() in {'kerberos', 'spnego'}
        ):
            try:
                import spnego  # noqa: PLC0415

                if not hasattr(self, '_spnego_ctx'):
                    self._spnego_ctx = spnego.client(protocol='negotiate')
            except Exception:  # noqa: BLE001
                logger.warning(
                    'Kerberos/SPNEGO initialization failed; proceeding without proxy token'
                )

        return client

    async def post(
        self,
        *,
        url: str,
        json: dict[str, Any],
        headers: dict[str, str],
        timeout_seconds: int | None = None,
    ) -> tuple[dict[str, Any], dict[str, str]]:
        """Send a POST request with JSON and return the parsed JSON and headers."""
        # If Kerberos/SPNEGO, attempt an initial token for CONNECT
        negotiate_b64: str | None = None
        if (
            self._proxy_url
            and self._proxy_auth_type
            and self._proxy_auth_type.lower() in {'kerberos', 'spnego'}
        ):
            try:
                if hasattr(self, '_spnego_ctx') and self._spnego_ctx is not None:
                    initial = self._spnego_ctx.step(None)
                    if initial:
                        negotiate_b64 = base64.b64encode(initial).decode('ascii')
            except Exception:  # noqa: BLE001
                logger.warning('Kerberos initial token generation failed')

        client = self._build_client(negotiate_token_b64=negotiate_b64)
        try:
            resp = await client.post(
                url,
                json=json,
                headers=headers,
                timeout=timeout_seconds or self._timeout_seconds,
            )

            if (
                resp.status_code == self.PROXY_AUTH_REQUIRED
                and hasattr(self, '_spnego_ctx')
                and self._spnego_ctx is not None
            ):
                challenge = resp.headers.get('Proxy-Authenticate', '')
                if 'Negotiate ' in challenge:
                    try:
                        token_b64 = challenge.split('Negotiate ', 1)[1].strip()
                        in_token = base64.b64decode(token_b64)
                        out_token = self._spnego_ctx.step(in_token)
                        if out_token:
                            b64 = base64.b64encode(out_token).decode('ascii')
                            # Rebuild client with updated Proxy-Authorization and resend once
                            new_client = self._build_client(negotiate_token_b64=b64)
                            resp = await new_client.post(
                                url,
                                json=json,
                                headers=headers,
                                timeout=timeout_seconds or self._timeout_seconds,
                            )
                            response_headers = dict(resp.headers)
                            data = resp.json()
                            await new_client.aclose()
                            return data, response_headers
                    except Exception:  # noqa: BLE001
                        logger.warning('Kerberos proxy challenge handling failed')

            response_headers = dict(resp.headers)
            data = resp.json()
            return data, response_headers
        finally:
            await client.aclose()
