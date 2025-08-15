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
Configuration system for monday-client.

This module provides configuration classes and providers for managing
monday-client settings from various sources.
"""

import json
import os
import warnings
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from monday.protocols import ConfigProtocol


@dataclass
class Config:
    """
    Configuration for MondayClient.

    This class centralizes all configuration options for the MondayClient,
    focusing on settings that are actually used.
    """

    api_key: str
    """The API key for authenticating with the monday.com API."""

    url: str = 'https://api.monday.com/v2'
    """The endpoint URL for the monday.com API."""

    version: str | None = None
    """The API version to use. If None, will automatically fetch current version."""

    headers: dict[str, Any] = field(default_factory=dict)
    """Additional HTTP headers for API requests."""

    max_retries: int = 4
    """Maximum number of retry attempts."""

    timeout: int = 30
    """Request timeout in seconds."""

    rate_limit_seconds: int = 60
    """Rate limit window in seconds."""

    proxy_url: str | None = None
    """Proxy URL (e.g., 'http://proxy.example.com:8080' or 'socks5://proxy.example.com:1080')."""

    proxy_auth: tuple[str, str] | None = None
    """Proxy authentication as (username, password) tuple for basic authentication."""

    proxy_auth_type: str = 'basic'
    """
    Proxy authentication type.

    Supported values:
    - 'basic': Supported by both transports
    - 'ntlm': Supported by httpx transport (requires httpx-ntlm)
    - 'kerberos' or 'spnego': Supported by httpx transport (requires pyspnego)
    - 'none': No proxy authentication
    """

    proxy_trust_env: bool = False
    """Whether to trust proxy settings from environment variables (HTTP_PROXY, HTTPS_PROXY, etc.)."""

    proxy_headers: dict[str, str] = field(default_factory=dict)
    """Additional headers to send to the proxy server."""

    proxy_ssl_verify: bool = True
    """Whether to verify SSL certificates when connecting through HTTPS proxies."""

    def validate(self) -> None:
        """Validate all configuration values."""
        if not self.api_key:
            error_msg = 'api_key is required'
            raise ValueError(error_msg)

        if self.max_retries < 0:
            error_msg = 'max_retries must be non-negative'
            raise ValueError(error_msg)

        if self.timeout <= 0:
            error_msg = 'timeout must be positive'
            raise ValueError(error_msg)

        if self.rate_limit_seconds <= 0:
            error_msg = 'rate_limit_seconds must be positive'
            raise ValueError(error_msg)

        # Validate proxy authentication type
        valid_proxy_auth_types = {
            'basic',
            'ntlm',  # httpx transport only
            'kerberos',  # httpx transport only
            'spnego',  # httpx transport only
            'none',
        }
        if self.proxy_auth_type not in valid_proxy_auth_types:
            error_msg = f'proxy_auth_type must be one of {valid_proxy_auth_types}'
            raise ValueError(error_msg)

        # Validate proxy authentication consistency
        if (
            self.proxy_auth_type != 'none'
            and self.proxy_auth is None
            and self.proxy_url
        ):
            # Only warn if proxy_url is set but no auth provided for non-none auth types

            warnings.warn(
                f'proxy_auth_type is set to "{self.proxy_auth_type}" but proxy_auth is None. '
                'Consider setting proxy_auth_type to "none" if authentication is not required.',
                UserWarning,
                stacklevel=2,
            )

    @classmethod
    def from_env(cls, prefix: str = 'MONDAY_') -> 'Config':
        """Create configuration from environment variables."""
        # Handle proxy auth from environment
        proxy_auth = None
        proxy_user = os.environ.get(f'{prefix}PROXY_USER')
        proxy_pass = os.environ.get(f'{prefix}PROXY_PASS')
        if proxy_user and proxy_pass:
            proxy_auth = (proxy_user, proxy_pass)

        # Handle proxy headers from environment (JSON format)
        proxy_headers = {}
        proxy_headers_env = os.environ.get(f'{prefix}PROXY_HEADERS')
        if proxy_headers_env:
            try:
                proxy_headers = json.loads(proxy_headers_env)
            except json.JSONDecodeError:
                warnings.warn(
                    f'Invalid JSON in {prefix}PROXY_HEADERS environment variable. Using empty headers.',
                    UserWarning,
                    stacklevel=2,
                )

        return cls(
            api_key=os.environ[f'{prefix}API_KEY'],
            url=os.environ.get(f'{prefix}URL', 'https://api.monday.com/v2'),
            version=os.environ.get(f'{prefix}VERSION'),
            max_retries=int(os.environ.get(f'{prefix}MAX_RETRIES', '4')),
            timeout=int(os.environ.get(f'{prefix}TIMEOUT', '30')),
            rate_limit_seconds=int(os.environ.get(f'{prefix}RATE_LIMIT_SECONDS', '60')),
            proxy_url=os.environ.get(f'{prefix}PROXY_URL'),
            proxy_auth=proxy_auth,
            proxy_auth_type=os.environ.get(f'{prefix}PROXY_AUTH_TYPE', 'basic'),
            proxy_trust_env=os.environ.get(f'{prefix}PROXY_TRUST_ENV', 'false').lower()
            == 'true',
            proxy_headers=proxy_headers,
            proxy_ssl_verify=os.environ.get(f'{prefix}PROXY_SSL_VERIFY', 'true').lower()
            == 'true',
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Config':
        """Create configuration from dictionary."""
        # Handle proxy auth from dict
        proxy_auth = None
        if 'proxy_auth' in data:
            proxy_auth_data = data['proxy_auth']
            if isinstance(proxy_auth_data, (list, tuple)) and len(proxy_auth_data) == 2:  # noqa: PLR2004
                proxy_auth = tuple(proxy_auth_data)

        return cls(
            api_key=data['api_key'],
            url=data.get('url', 'https://api.monday.com/v2'),
            version=data.get('version'),
            headers=data.get('headers', {}),
            max_retries=data.get('max_retries', 4),
            timeout=data.get('timeout', 30),
            rate_limit_seconds=data.get('rate_limit_seconds', 60),
            proxy_url=data.get('proxy_url'),
            proxy_auth=proxy_auth,
            proxy_auth_type=data.get('proxy_auth_type', 'basic'),
            proxy_trust_env=data.get('proxy_trust_env', False),
            proxy_headers=data.get('proxy_headers', {}),
            proxy_ssl_verify=data.get('proxy_ssl_verify', True),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)


class EnvConfig(ConfigProtocol):
    """Load configuration from environment variables."""

    def __init__(self, prefix: str = 'MONDAY_'):
        self.prefix = prefix
        self._config: Config | None = None

    def get_config(self) -> Config:
        """Get configuration from environment variables."""
        if self._config is None:
            self._config = Config.from_env(self.prefix)
        return self._config

    def validate_config(self) -> bool:
        """Validate the configuration."""
        try:
            config = self.get_config()
            config.validate()
        except (ValueError, KeyError):
            return False
        else:
            return True

    def reload_config(self) -> None:
        """Reload configuration from environment."""
        self._config = None

    def get_env_value(self, key: str, default: Any = None) -> Any:
        """Get an environment variable value with optional prefix."""
        # Try with prefix first, then without prefix
        prefixed_key = f'{self.prefix}{key}'.upper()
        value = os.environ.get(prefixed_key)
        if value is not None:
            return value

        # Try without prefix as fallback
        return os.environ.get(key.upper(), default)

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a value from environment variables (alias for get_env_value)."""
        return self.get_env_value(key, default)


class JsonConfig(ConfigProtocol):
    """Load configuration from JSON file."""

    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path)
        self._config: Config | None = None
        self._last_modified: float | None = None
        self._raw_data: dict[str, Any] | None = None

    def get_config(self) -> Config:
        """Get configuration from JSON file."""
        if self._should_reload():
            self._load_config()
        if self._config is None:
            error_msg = 'Failed to load configuration'
            raise ValueError(error_msg)
        return self._config

    def validate_config(self) -> bool:
        """Validate the configuration."""
        try:
            if not self.config_path.exists():
                return False
            config = self.get_config()
            config.validate()
        except (ValueError, json.JSONDecodeError, KeyError):
            return False
        else:
            return True

    def reload_config(self) -> None:
        """Force reload configuration from file."""
        self._config = None
        self._last_modified = None
        self._raw_data = None

    def get_raw_data(self) -> dict[str, Any]:
        """Get raw JSON data for application-specific values."""
        if self._should_reload():
            self._load_config()
        if self._raw_data is None:
            error_msg = 'Failed to load JSON data'
            raise ValueError(error_msg)
        return self._raw_data

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a specific value from the raw JSON data."""
        data = self.get_raw_data()
        return data.get(key, default)

    def _should_reload(self) -> bool:
        """Check if config should be reloaded."""
        if self._config is None:
            return True

        if not self.config_path.exists():
            return False

        current_modified = self.config_path.stat().st_mtime
        return current_modified != self._last_modified

    def _load_config(self) -> None:
        """Load config from file."""
        with self.config_path.open() as f:
            data = json.load(f)

        self._raw_data = data
        self._config = Config.from_dict(data)
        self._last_modified = self.config_path.stat().st_mtime


class MultiSourceConfig(ConfigProtocol):
    """Load configuration from multiple sources with priority."""

    def __init__(self, providers: list[ConfigProtocol]):
        self.providers = providers
        self._config: Config | None = None

    def get_config(self) -> Config:
        """Get merged configuration from all providers."""
        if self._config is None:
            self._merge_configs()
        if self._config is None:
            error_msg = 'Failed to load configuration from any provider'
            raise ValueError(error_msg)
        return self._config

    def validate_config(self) -> bool:
        """Validate the merged configuration."""
        try:
            config = self.get_config()
            config.validate()
        except ValueError:
            return False
        else:
            return True

    def reload_config(self) -> None:
        """Reload all configurations."""
        for provider in self.providers:
            reload_method = getattr(provider, 'reload_config', None)
            if callable(reload_method):
                reload_method()
        self._config = None

    def _merge_configs(self) -> None:
        """Merge configurations from all providers."""
        if not self.providers:
            error_msg = 'No config providers specified'
            raise ValueError(error_msg)

        # Start with first provider
        base_config = self.providers[0].get_config()

        # Merge additional providers (later providers override earlier ones)
        for provider in self.providers[1:]:
            try:
                overlay_config = provider.get_config()
                base_config = self._merge_two_configs(base_config, overlay_config)
            except Exception:  # noqa: BLE001,S112
                continue

        self._config = base_config

    def _merge_two_configs(self, base: Config, overlay: Config) -> Config:
        """Merge two configurations with overlay taking precedence."""
        base_dict = base.to_dict()
        overlay_dict = overlay.to_dict()

        # Merge headers
        if 'headers' in overlay_dict and 'headers' in base_dict:
            merged_headers = {**base_dict['headers'], **overlay_dict['headers']}
            overlay_dict['headers'] = merged_headers

        # Merge dictionaries (overlay takes precedence)
        merged_data = {**base_dict, **overlay_dict}

        return Config.from_dict(merged_data)


try:
    import yaml

    class YamlConfig(ConfigProtocol):
        """Load configuration from YAML file."""

        def __init__(self, config_path: str | Path):
            self.config_path = Path(config_path)
            self._config: Config | None = None
            self._raw_data: dict[str, Any] | None = None

        def get_config(self) -> Config:
            """Get configuration from YAML file."""
            if self._config is None:
                self._load_config()
            if self._config is None:
                error_msg = 'Failed to load YAML configuration'
                raise ValueError(error_msg)
            return self._config

        def validate_config(self) -> bool:
            """Validate the configuration."""
            try:
                if not self.config_path.exists():
                    return False
                config = self.get_config()
                config.validate()
            except (ValueError, yaml.YAMLError, KeyError):
                return False
            else:
                return True

        def reload_config(self) -> None:
            """Reload configuration from file."""
            self._config = None
            self._raw_data = None

        def get_raw_data(self) -> dict[str, Any]:
            """Get raw YAML data for application-specific values."""
            if self._raw_data is None:
                self._load_config()
            if self._raw_data is None:
                error_msg = 'Failed to load YAML data'
                raise ValueError(error_msg)
            return self._raw_data

        def get_value(self, key: str, default: Any = None) -> Any:
            """Get a specific value from the raw YAML data."""
            data = self.get_raw_data()
            return data.get(key, default)

        def _load_config(self) -> None:
            """Load config from YAML file."""
            with self.config_path.open() as f:
                data = yaml.safe_load(f)

            self._raw_data = data
            self._config = Config.from_dict(data)

except ImportError:
    pass
