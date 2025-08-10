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

"""Tests for configuration system."""

import contextlib
import json
import os
import tempfile
import warnings
from pathlib import Path
from unittest.mock import patch

import pytest

from monday.config import Config, EnvConfig, JsonConfig, MultiSourceConfig


@pytest.mark.unit
class TestConfig:
    """Test the base Config class."""

    def test_config_minimal_creation(self):
        """Test creating config with minimal required parameters."""
        config = Config(api_key='test_key')

        assert config.api_key == 'test_key'
        assert config.url == 'https://api.monday.com/v2'
        assert config.version is None
        assert config.headers == {}
        assert config.max_retries == 4
        assert config.timeout == 30
        assert config.rate_limit_seconds == 60
        assert config.proxy_url is None
        assert config.proxy_auth is None
        assert config.proxy_auth_type == 'basic'
        assert config.proxy_trust_env is False
        assert config.proxy_headers == {}
        assert config.proxy_ssl_verify is True

    def test_config_full_creation(self):
        """Test creating config with all parameters."""
        headers = {'Custom-Header': 'value'}
        proxy_headers = {'Proxy-Header': 'proxy_value'}
        proxy_auth = ('user', 'pass')

        config = Config(
            api_key='test_key',
            url='https://custom.api.com/v3',
            version='2023-10',
            headers=headers,
            max_retries=10,
            timeout=60,
            rate_limit_seconds=120,
            proxy_url='http://proxy.example.com:8080',
            proxy_auth=proxy_auth,
            proxy_auth_type='basic',
            proxy_trust_env=True,
            proxy_headers=proxy_headers,
            proxy_ssl_verify=False,
        )

        assert config.api_key == 'test_key'
        assert config.url == 'https://custom.api.com/v3'
        assert config.version == '2023-10'
        assert config.headers == headers
        assert config.max_retries == 10
        assert config.timeout == 60
        assert config.rate_limit_seconds == 120
        assert config.proxy_url == 'http://proxy.example.com:8080'
        assert config.proxy_auth == proxy_auth
        assert config.proxy_auth_type == 'basic'
        assert config.proxy_trust_env is True
        assert config.proxy_headers == proxy_headers
        assert config.proxy_ssl_verify is False

    def test_config_validation_valid(self):
        """Test config validation with valid values."""
        config = Config(api_key='test_key')
        config.validate()  # Should not raise

    def test_config_validation_empty_api_key(self):
        """Test config validation with empty api_key."""
        config = Config(api_key='')
        with pytest.raises(ValueError, match='api_key is required'):
            config.validate()

    def test_config_validation_negative_max_retries(self):
        """Test config validation with negative max_retries."""
        config = Config(api_key='test_key', max_retries=-1)
        with pytest.raises(ValueError, match='max_retries must be non-negative'):
            config.validate()

    def test_config_validation_zero_timeout(self):
        """Test config validation with zero timeout."""
        config = Config(api_key='test_key', timeout=0)
        with pytest.raises(ValueError, match='timeout must be positive'):
            config.validate()

    def test_config_validation_negative_timeout(self):
        """Test config validation with negative timeout."""
        config = Config(api_key='test_key', timeout=-10)
        with pytest.raises(ValueError, match='timeout must be positive'):
            config.validate()

    def test_config_validation_zero_rate_limit(self):
        """Test config validation with zero rate_limit_seconds."""
        config = Config(api_key='test_key', rate_limit_seconds=0)
        with pytest.raises(ValueError, match='rate_limit_seconds must be positive'):
            config.validate()

    def test_config_validation_negative_rate_limit(self):
        """Test config validation with negative rate_limit_seconds."""
        config = Config(api_key='test_key', rate_limit_seconds=-60)
        with pytest.raises(ValueError, match='rate_limit_seconds must be positive'):
            config.validate()

    def test_config_validation_invalid_proxy_auth_type(self):
        """Test config validation with invalid proxy_auth_type."""
        config = Config(api_key='test_key', proxy_auth_type='invalid')
        with pytest.raises(ValueError, match='proxy_auth_type must be one of'):
            config.validate()

    def test_config_validation_valid_proxy_auth_types(self):
        """Test config validation with all valid proxy_auth_types."""
        valid_types = ['basic', 'ntlm', 'kerberos', 'spnego', 'none']
        for auth_type in valid_types:
            config = Config(api_key='test_key', proxy_auth_type=auth_type)
            config.validate()  # Should not raise

    def test_config_validation_proxy_auth_warning(self):
        """Test config validation shows warning for proxy auth mismatch."""
        config = Config(
            api_key='test_key',
            proxy_url='http://proxy.example.com:8080',
            proxy_auth_type='basic',
            proxy_auth=None,
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            config.validate()

            assert len(w) == 1
            assert 'proxy_auth_type is set to "basic" but proxy_auth is None' in str(
                w[0].message
            )
            assert w[0].category is UserWarning

    def test_config_validation_no_proxy_auth_warning_when_none_type(self):
        """Test config validation doesn't warn when proxy_auth_type is 'none'."""
        config = Config(
            api_key='test_key',
            proxy_url='http://proxy.example.com:8080',
            proxy_auth_type='none',
            proxy_auth=None,
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            config.validate()

            assert len(w) == 0

    def test_config_validation_no_proxy_auth_warning_when_no_proxy_url(self):
        """Test config validation doesn't warn when proxy_url is None."""
        config = Config(
            api_key='test_key',
            proxy_url=None,
            proxy_auth_type='basic',
            proxy_auth=None,
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            config.validate()

            assert len(w) == 0

    def test_config_from_env_minimal(self):
        """Test creating config from environment variables with minimal settings."""
        env = {
            'MONDAY_API_KEY': 'env_api_key',
        }

        with patch.dict(os.environ, env, clear=False):
            config = Config.from_env()

        assert config.api_key == 'env_api_key'
        assert config.url == 'https://api.monday.com/v2'
        assert config.version is None
        assert config.max_retries == 4
        assert config.timeout == 30
        assert config.rate_limit_seconds == 60

    def test_config_from_env_full(self):
        """Test creating config from environment variables with all settings."""
        env = {
            'MONDAY_API_KEY': 'env_api_key',
            'MONDAY_URL': 'https://env.api.com/v3',
            'MONDAY_VERSION': '2023-10',
            'MONDAY_MAX_RETRIES': '8',
            'MONDAY_TIMEOUT': '90',
            'MONDAY_RATE_LIMIT_SECONDS': '120',
            'MONDAY_PROXY_URL': 'http://env-proxy.example.com:8080',
            'MONDAY_PROXY_USER': 'env_user',
            'MONDAY_PROXY_PASS': 'env_pass',
            'MONDAY_PROXY_AUTH_TYPE': 'basic',
            'MONDAY_PROXY_TRUST_ENV': 'true',
            'MONDAY_PROXY_HEADERS': '{"Env-Header": "env_value"}',
            'MONDAY_PROXY_SSL_VERIFY': 'false',
        }

        with patch.dict(os.environ, env, clear=False):
            config = Config.from_env()

        assert config.api_key == 'env_api_key'
        assert config.url == 'https://env.api.com/v3'
        assert config.version == '2023-10'
        assert config.max_retries == 8
        assert config.timeout == 90
        assert config.rate_limit_seconds == 120
        assert config.proxy_url == 'http://env-proxy.example.com:8080'
        assert config.proxy_auth == ('env_user', 'env_pass')
        assert config.proxy_auth_type == 'basic'
        assert config.proxy_trust_env is True
        assert config.proxy_headers == {'Env-Header': 'env_value'}
        assert config.proxy_ssl_verify is False

    def test_config_from_env_custom_prefix(self):
        """Test creating config from environment variables with custom prefix."""
        env = {
            'CUSTOM_API_KEY': 'custom_api_key',
            'CUSTOM_URL': 'https://custom.api.com/v2',
            'CUSTOM_PROXY_USER': 'custom_user',
            'CUSTOM_PROXY_PASS': 'custom_pass',
        }

        with patch.dict(os.environ, env, clear=False):
            config = Config.from_env(prefix='CUSTOM_')

        assert config.api_key == 'custom_api_key'
        assert config.url == 'https://custom.api.com/v2'
        assert config.proxy_auth == ('custom_user', 'custom_pass')

    def test_config_from_env_proxy_auth_partial(self):
        """Test creating config from environment with only proxy username."""
        env = {
            'MONDAY_API_KEY': 'env_api_key',
            'MONDAY_PROXY_USER': 'env_user',
            # Missing MONDAY_PROXY_PASS
        }

        with patch.dict(os.environ, env, clear=False):
            config = Config.from_env()

        assert config.proxy_auth is None

    def test_config_from_env_invalid_proxy_headers_json(self):
        """Test creating config from environment with invalid proxy headers JSON."""
        env = {
            'MONDAY_API_KEY': 'env_api_key',
            'MONDAY_PROXY_HEADERS': 'invalid-json',
        }

        with (
            patch.dict(os.environ, env, clear=False),
            warnings.catch_warnings(record=True) as w,
        ):
            warnings.simplefilter('always')
            config = Config.from_env()

            assert len(w) == 1
            assert 'Invalid JSON in MONDAY_PROXY_HEADERS' in str(w[0].message)
            assert config.proxy_headers == {}

    def test_config_from_env_boolean_values(self):
        """Test creating config from environment with various boolean values."""
        test_cases = [
            ('true', True),
            ('TRUE', True),
            ('True', True),
            ('false', False),
            ('FALSE', False),
            ('False', False),
            ('1', False),  # Only 'true' (case-insensitive) should be True
            ('yes', False),
            ('', False),
        ]

        for env_value, expected in test_cases:
            env = {
                'MONDAY_API_KEY': 'env_api_key',
                'MONDAY_PROXY_TRUST_ENV': env_value,
                'MONDAY_PROXY_SSL_VERIFY': env_value,
            }

            with patch.dict(os.environ, env, clear=False):
                config = Config.from_env()

                assert config.proxy_trust_env is expected, (
                    f'Failed for proxy_trust_env with value "{env_value}"'
                )
                assert config.proxy_ssl_verify is expected, (
                    f'Failed for proxy_ssl_verify with value "{env_value}"'
                )

    def test_config_from_dict_minimal(self):
        """Test creating config from dictionary with minimal settings."""
        data = {'api_key': 'dict_api_key'}

        config = Config.from_dict(data)

        assert config.api_key == 'dict_api_key'
        assert config.url == 'https://api.monday.com/v2'
        assert config.version is None
        assert config.headers == {}

    def test_config_from_dict_full(self):
        """Test creating config from dictionary with all settings."""
        data = {
            'api_key': 'dict_api_key',
            'url': 'https://dict.api.com/v3',
            'version': '2023-10',
            'headers': {'Dict-Header': 'dict_value'},
            'max_retries': 12,
            'timeout': 120,
            'rate_limit_seconds': 180,
            'proxy_url': 'http://dict-proxy.example.com:8080',
            'proxy_auth': ['dict_user', 'dict_pass'],
            'proxy_auth_type': 'ntlm',
            'proxy_trust_env': True,
            'proxy_headers': {'Dict-Proxy-Header': 'dict_proxy_value'},
            'proxy_ssl_verify': False,
        }

        config = Config.from_dict(data)

        assert config.api_key == 'dict_api_key'
        assert config.url == 'https://dict.api.com/v3'
        assert config.version == '2023-10'
        assert config.headers == {'Dict-Header': 'dict_value'}
        assert config.max_retries == 12
        assert config.timeout == 120
        assert config.rate_limit_seconds == 180
        assert config.proxy_url == 'http://dict-proxy.example.com:8080'
        assert config.proxy_auth == ('dict_user', 'dict_pass')
        assert config.proxy_auth_type == 'ntlm'
        assert config.proxy_trust_env is True
        assert config.proxy_headers == {'Dict-Proxy-Header': 'dict_proxy_value'}
        assert config.proxy_ssl_verify is False

    def test_config_from_dict_proxy_auth_tuple(self):
        """Test creating config from dictionary with proxy_auth as tuple."""
        data = {
            'api_key': 'dict_api_key',
            'proxy_auth': ('tuple_user', 'tuple_pass'),
        }

        config = Config.from_dict(data)
        assert config.proxy_auth == ('tuple_user', 'tuple_pass')

    def test_config_from_dict_proxy_auth_invalid(self):
        """Test creating config from dictionary with invalid proxy_auth."""
        invalid_auths = [
            'string_auth',
            ['single_item'],
            ['too', 'many', 'items'],
            123,
            None,
        ]

        for invalid_auth in invalid_auths:
            data = {
                'api_key': 'dict_api_key',
                'proxy_auth': invalid_auth,
            }

            config = Config.from_dict(data)
            assert config.proxy_auth is None

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        headers = {'Custom-Header': 'value'}
        proxy_headers = {'Proxy-Header': 'proxy_value'}
        proxy_auth = ('user', 'pass')

        config = Config(
            api_key='test_key',
            url='https://test.api.com/v3',
            version='2023-10',
            headers=headers,
            max_retries=8,
            timeout=90,
            rate_limit_seconds=120,
            proxy_url='http://test-proxy.example.com:8080',
            proxy_auth=proxy_auth,
            proxy_auth_type='basic',
            proxy_trust_env=True,
            proxy_headers=proxy_headers,
            proxy_ssl_verify=False,
        )

        result = config.to_dict()

        expected = {
            'api_key': 'test_key',
            'url': 'https://test.api.com/v3',
            'version': '2023-10',
            'headers': headers,
            'max_retries': 8,
            'timeout': 90,
            'rate_limit_seconds': 120,
            'proxy_url': 'http://test-proxy.example.com:8080',
            'proxy_auth': proxy_auth,
            'proxy_auth_type': 'basic',
            'proxy_trust_env': True,
            'proxy_headers': proxy_headers,
            'proxy_ssl_verify': False,
        }

        assert result == expected

    def test_config_round_trip_dict(self):
        """Test config round-trip through dictionary conversion."""
        original_config = Config(
            api_key='round_trip_key',
            url='https://roundtrip.api.com/v2',
            version='2023-08',
            headers={'RT-Header': 'rt_value'},
            max_retries=6,
            timeout=45,
            rate_limit_seconds=90,
            proxy_url='http://rt-proxy.example.com:3128',
            proxy_auth=('rt_user', 'rt_pass'),
            proxy_auth_type='basic',
            proxy_trust_env=False,
            proxy_headers={'RT-Proxy-Header': 'rt_proxy_value'},
            proxy_ssl_verify=True,
        )

        # Convert to dict and back
        config_dict = original_config.to_dict()
        restored_config = Config.from_dict(config_dict)

        # Compare all attributes
        assert restored_config.api_key == original_config.api_key
        assert restored_config.url == original_config.url
        assert restored_config.version == original_config.version
        assert restored_config.headers == original_config.headers
        assert restored_config.max_retries == original_config.max_retries
        assert restored_config.timeout == original_config.timeout
        assert restored_config.rate_limit_seconds == original_config.rate_limit_seconds
        assert restored_config.proxy_url == original_config.proxy_url
        assert restored_config.proxy_auth == original_config.proxy_auth
        assert restored_config.proxy_auth_type == original_config.proxy_auth_type
        assert restored_config.proxy_trust_env == original_config.proxy_trust_env
        assert restored_config.proxy_headers == original_config.proxy_headers
        assert restored_config.proxy_ssl_verify == original_config.proxy_ssl_verify


@pytest.mark.unit
class TestEnvConfig:
    """Test the EnvConfig provider."""

    def test_env_config_creation(self):
        """Test creating EnvConfig with default prefix."""
        env_config = EnvConfig()
        assert env_config.prefix == 'MONDAY_'
        assert env_config._config is None

    def test_env_config_creation_custom_prefix(self):
        """Test creating EnvConfig with custom prefix."""
        env_config = EnvConfig(prefix='CUSTOM_')
        assert env_config.prefix == 'CUSTOM_'

    def test_env_config_get_config(self):
        """Test getting config from EnvConfig."""
        env = {'MONDAY_API_KEY': 'env_test_key'}

        with patch.dict(os.environ, env, clear=False):
            env_config = EnvConfig()
            config = env_config.get_config()

            assert config.api_key == 'env_test_key'

    def test_env_config_get_config_caching(self):
        """Test that EnvConfig caches the config."""
        env = {'MONDAY_API_KEY': 'cached_key'}

        with patch.dict(os.environ, env, clear=False):
            env_config = EnvConfig()

            # First call
            config1 = env_config.get_config()

            # Second call should return the same object
            config2 = env_config.get_config()

            assert config1 is config2

    def test_env_config_validate_valid(self):
        """Test validating valid EnvConfig."""
        env = {'MONDAY_API_KEY': 'valid_key'}

        with patch.dict(os.environ, env, clear=False):
            env_config = EnvConfig()
            assert env_config.validate_config() is True

    def test_env_config_validate_missing_key(self):
        """Test validating EnvConfig with missing API key."""
        # Ensure MONDAY_API_KEY is not set
        env = {}

        with patch.dict(os.environ, env, clear=True):
            env_config = EnvConfig()
            assert env_config.validate_config() is False

    def test_env_config_validate_invalid_values(self):
        """Test validating EnvConfig with invalid values."""
        env = {
            'MONDAY_API_KEY': 'valid_key',
            'MONDAY_MAX_RETRIES': '-1',  # Invalid
        }

        with patch.dict(os.environ, env, clear=False):
            env_config = EnvConfig()
            assert env_config.validate_config() is False

    def test_env_config_reload(self):
        """Test reloading EnvConfig."""
        initial_env = {'MONDAY_API_KEY': 'initial_key'}

        with patch.dict(os.environ, initial_env, clear=False):
            env_config = EnvConfig()
            initial_config = env_config.get_config()
            assert initial_config.api_key == 'initial_key'

        # Change environment and reload
        updated_env = {'MONDAY_API_KEY': 'updated_key'}

        with patch.dict(os.environ, updated_env, clear=False):
            env_config.reload_config()
            updated_config = env_config.get_config()
            assert updated_config.api_key == 'updated_key'

    def test_env_config_custom_prefix(self):
        """Test EnvConfig with custom prefix."""
        env = {'CUSTOM_API_KEY': 'custom_prefix_key'}

        with patch.dict(os.environ, env, clear=False):
            env_config = EnvConfig(prefix='CUSTOM_')
            config = env_config.get_config()

            assert config.api_key == 'custom_prefix_key'


@pytest.mark.unit
class TestJsonConfig:
    """Test the JsonConfig provider."""

    def test_json_config_creation(self):
        """Test creating JsonConfig."""
        json_config = JsonConfig('/path/to/config.json')
        assert json_config.config_path == Path('/path/to/config.json')
        assert json_config._config is None
        assert json_config._last_modified is None

    def test_json_config_get_config_valid_file(self):
        """Test getting config from valid JSON file."""
        config_data = {
            'api_key': 'json_test_key',
            'url': 'https://json.api.com/v2',
            'max_retries': 8,
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            json_config = JsonConfig(temp_path)
            config = json_config.get_config()

            assert config.api_key == 'json_test_key'
            assert config.url == 'https://json.api.com/v2'
            assert config.max_retries == 8
        finally:
            Path(temp_path).unlink()

    def test_json_config_get_config_missing_file(self):
        """Test getting config from missing JSON file."""
        json_config = JsonConfig('/nonexistent/file.json')

        with pytest.raises(FileNotFoundError):
            json_config.get_config()

    def test_json_config_get_config_invalid_json(self):
        """Test getting config from invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('invalid json content')
            temp_path = f.name

        try:
            json_config = JsonConfig(temp_path)

            with pytest.raises(json.JSONDecodeError):
                json_config.get_config()
        finally:
            Path(temp_path).unlink()

    def test_json_config_validate_valid_file(self):
        """Test validating valid JSON config file."""
        config_data = {'api_key': 'valid_json_key'}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            json_config = JsonConfig(temp_path)
            assert json_config.validate_config() is True
        finally:
            Path(temp_path).unlink()

    def test_json_config_validate_missing_file(self):
        """Test validating missing JSON config file."""
        json_config = JsonConfig('/nonexistent/file.json')
        assert json_config.validate_config() is False

    def test_json_config_validate_invalid_json(self):
        """Test validating invalid JSON config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('invalid json')
            temp_path = f.name

        try:
            json_config = JsonConfig(temp_path)
            assert json_config.validate_config() is False
        finally:
            Path(temp_path).unlink()

    def test_json_config_validate_invalid_config_values(self):
        """Test validating JSON file with invalid config values."""
        config_data = {'api_key': ''}  # Empty API key is invalid

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            json_config = JsonConfig(temp_path)
            assert json_config.validate_config() is False
        finally:
            Path(temp_path).unlink()

    def test_json_config_reload(self):
        """Test reloading JSON config."""
        initial_data = {'api_key': 'initial_json_key'}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(initial_data, f)
            temp_path = f.name

        try:
            json_config = JsonConfig(temp_path)
            initial_config = json_config.get_config()
            assert initial_config.api_key == 'initial_json_key'

            # Update file and reload
            updated_data = {'api_key': 'updated_json_key'}
            with Path(temp_path).open('w') as f:
                json.dump(updated_data, f)

            json_config.reload_config()
            updated_config = json_config.get_config()
            assert updated_config.api_key == 'updated_json_key'
        finally:
            Path(temp_path).unlink()

    def test_json_config_file_modification_detection(self):
        """Test that JsonConfig detects file modifications."""
        initial_data = {'api_key': 'initial_key'}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(initial_data, f)
            temp_path = f.name

        try:
            json_config = JsonConfig(temp_path)

            # Load initial config
            initial_config = json_config.get_config()
            assert initial_config.api_key == 'initial_key'

            # Modify file (this changes the modification time)
            import time

            time.sleep(0.1)  # Ensure modification time is different
            updated_data = {'api_key': 'modified_key'}
            with Path(temp_path).open('w') as f:
                json.dump(updated_data, f)

            # Get config again - should reload automatically
            modified_config = json_config.get_config()
            assert modified_config.api_key == 'modified_key'
        finally:
            Path(temp_path).unlink()

    def test_json_config_caching_when_unchanged(self):
        """Test that JsonConfig caches config when file is unchanged."""
        config_data = {'api_key': 'cached_key'}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            json_config = JsonConfig(temp_path)

            # First call
            config1 = json_config.get_config()

            # Second call should return cached config (same object)
            config2 = json_config.get_config()

            assert config1 is config2
        finally:
            Path(temp_path).unlink()

    def test_json_config_pathlib_path(self):
        """Test JsonConfig with pathlib.Path."""
        config_data = {'api_key': 'pathlib_key'}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            json_config = JsonConfig(temp_path)
            config = json_config.get_config()

            assert config.api_key == 'pathlib_key'
        finally:
            temp_path.unlink()


@pytest.mark.unit
class TestMultiSourceConfig:
    """Test the MultiSourceConfig provider."""

    def test_multi_source_config_creation(self):
        """Test creating MultiSourceConfig."""
        providers = []
        multi_config = MultiSourceConfig(providers)

        assert multi_config.providers == providers
        assert multi_config._config is None

    def test_multi_source_config_no_providers(self):
        """Test MultiSourceConfig with no providers."""
        multi_config = MultiSourceConfig([])

        with pytest.raises(ValueError, match='No config providers specified'):
            multi_config.get_config()

    def test_multi_source_config_single_provider(self):
        """Test MultiSourceConfig with single provider."""
        # Create environment config
        env = {'MONDAY_API_KEY': 'single_provider_key'}

        with patch.dict(os.environ, env, clear=False):
            env_config = EnvConfig()
            multi_config = MultiSourceConfig([env_config])

            config = multi_config.get_config()
            assert config.api_key == 'single_provider_key'

    def test_multi_source_config_multiple_providers_merge(self):
        """Test MultiSourceConfig merging multiple providers."""
        # Create JSON config
        json_data = {
            'api_key': 'json_key',
            'url': 'https://json.api.com/v2',
            'max_retries': 10,
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_data, f)
            json_path = f.name

        # Create environment config that overrides some values
        env = {
            'MONDAY_API_KEY': 'env_key',  # Should override JSON
            'MONDAY_TIMEOUT': '60',  # Should add to JSON config
        }

        try:
            with patch.dict(os.environ, env, clear=False):
                json_config = JsonConfig(json_path)
                env_config = EnvConfig()

                # JSON first, then env (env should override)
                multi_config = MultiSourceConfig([json_config, env_config])
                config = multi_config.get_config()

                assert config.api_key == 'env_key'  # From env (override)
                assert (
                    config.url == 'https://api.monday.com/v2'
                )  # Default from env_config
                assert (
                    config.max_retries == 4
                )  # Default from env_config (overrides JSON)
                assert config.timeout == 60  # From env
        finally:
            Path(json_path).unlink()

    def test_multi_source_config_header_merging(self):
        """Test MultiSourceConfig merging headers correctly."""
        # First provider with headers
        json_data = {
            'api_key': 'json_key',
            'headers': {
                'JSON-Header': 'json_value',
                'Shared-Header': 'json_shared',
            },
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_data, f)
            json_path = f.name

        # Second provider with different headers
        json_data2 = {
            'api_key': 'json2_key',
            'headers': {
                'JSON2-Header': 'json2_value',
                'Shared-Header': 'json2_shared',  # Should override
            },
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f2:
            json.dump(json_data2, f2)
            json_path2 = f2.name

        try:
            json_config1 = JsonConfig(json_path)
            json_config2 = JsonConfig(json_path2)

            multi_config = MultiSourceConfig([json_config1, json_config2])
            config = multi_config.get_config()

            expected_headers = {
                'JSON-Header': 'json_value',
                'JSON2-Header': 'json2_value',
                'Shared-Header': 'json2_shared',  # Override from second provider
            }

            assert config.headers == expected_headers
        finally:
            Path(json_path).unlink()
            Path(json_path2).unlink()

    def test_multi_source_config_provider_failure(self):
        """Test MultiSourceConfig handling provider failures."""
        # Create valid environment config
        env = {'MONDAY_API_KEY': 'fallback_key'}

        with patch.dict(os.environ, env, clear=False):
            # Create failing JSON config (nonexistent file)
            failing_json_config = JsonConfig('/nonexistent/file.json')

            # Create working env config
            env_config = EnvConfig()

            # Working provider first, failing provider second (fails silently)
            multi_config = MultiSourceConfig([env_config, failing_json_config])

            # Should still work with the env config
            config = multi_config.get_config()
            assert config.api_key == 'fallback_key'

    def test_multi_source_config_all_providers_fail(self):
        """Test MultiSourceConfig when all providers fail."""
        # Create multiple failing configs
        failing_json1 = JsonConfig('/nonexistent/file1.json')

        # Use environment config with missing API key
        with patch.dict(os.environ, {}, clear=True):
            # First provider must succeed, second can fail
            multi_config = MultiSourceConfig([failing_json1])

            with pytest.raises(FileNotFoundError):
                multi_config.get_config()

    def test_multi_source_config_validate(self):
        """Test MultiSourceConfig validation."""
        env = {'MONDAY_API_KEY': 'valid_key'}

        with patch.dict(os.environ, env, clear=False):
            env_config = EnvConfig()
            multi_config = MultiSourceConfig([env_config])

            assert multi_config.validate_config() is True

    def test_multi_source_config_validate_invalid(self):
        """Test MultiSourceConfig validation with invalid config."""
        env = {'MONDAY_API_KEY': ''}  # Empty API key is invalid

        with patch.dict(os.environ, env, clear=False):
            env_config = EnvConfig()
            multi_config = MultiSourceConfig([env_config])

            assert multi_config.validate_config() is False

    def test_multi_source_config_reload(self):
        """Test MultiSourceConfig reload."""
        initial_env = {'MONDAY_API_KEY': 'initial_multi_key'}

        with patch.dict(os.environ, initial_env, clear=False):
            env_config = EnvConfig()
            multi_config = MultiSourceConfig([env_config])

            initial_config = multi_config.get_config()
            assert initial_config.api_key == 'initial_multi_key'

        # Change environment and reload
        updated_env = {'MONDAY_API_KEY': 'updated_multi_key'}

        with patch.dict(os.environ, updated_env, clear=False):
            multi_config.reload_config()
            updated_config = multi_config.get_config()
            assert updated_config.api_key == 'updated_multi_key'

    def test_multi_source_config_complex_merge(self):
        """Test complex merging scenario with all config options."""
        # Base JSON config with most settings
        base_data = {
            'api_key': 'base_key',
            'url': 'https://base.api.com/v2',
            'version': '2023-01',
            'headers': {'Base-Header': 'base_value'},
            'max_retries': 5,
            'timeout': 45,
            'rate_limit_seconds': 90,
            'proxy_url': 'http://base-proxy.com:8080',
            'proxy_auth': ['base_user', 'base_pass'],
            'proxy_auth_type': 'basic',
            'proxy_trust_env': False,
            'proxy_headers': {'Base-Proxy-Header': 'base_proxy_value'},
            'proxy_ssl_verify': True,
        }

        # Override JSON config with some different settings
        override_data = {
            'api_key': 'override_key',  # Override
            'version': '2023-10',  # Override
            'headers': {  # Merge
                'Override-Header': 'override_value',
                'Base-Header': 'overridden_base_value',  # Override specific header
            },
            'timeout': 120,  # Override
            'proxy_auth_type': 'basic',  # Override
            'proxy_headers': {  # Merge
                'Override-Proxy-Header': 'override_proxy_value',
            },
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f1:
            json.dump(base_data, f1)
            base_path = f1.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f2:
            json.dump(override_data, f2)
            override_path = f2.name

        try:
            base_config = JsonConfig(base_path)
            override_config = JsonConfig(override_path)

            multi_config = MultiSourceConfig([base_config, override_config])
            config = multi_config.get_config()

            # Check merged values
            assert config.api_key == 'override_key'
            assert (
                config.url == 'https://api.monday.com/v2'
            )  # Default from Config.from_dict
            assert config.version == '2023-10'  # Override
            assert (
                config.max_retries == 4
            )  # Default from Config.from_dict (override config)
            assert config.timeout == 120  # Override
            assert (
                config.rate_limit_seconds == 60
            )  # Default from Config.from_dict (override config)
            assert (
                config.proxy_url is None
            )  # Default from Config.from_dict (override config)
            assert (
                config.proxy_auth is None
            )  # Default from Config.from_dict (override config)
            assert config.proxy_auth_type == 'basic'  # Override
            assert (
                config.proxy_trust_env is False
            )  # Default from Config.from_dict (override config)
            assert (
                config.proxy_ssl_verify is True
            )  # Default from Config.from_dict (override config)

            # Check merged headers
            expected_headers = {
                'Base-Header': 'overridden_base_value',  # Overridden
                'Override-Header': 'override_value',  # Added
            }
            assert config.headers == expected_headers

            # Check merged proxy headers (only override headers remain)
            expected_proxy_headers = {
                'Override-Proxy-Header': 'override_proxy_value',  # From override config
            }
            assert config.proxy_headers == expected_proxy_headers

        finally:
            Path(base_path).unlink()
            Path(override_path).unlink()


@pytest.mark.unit
@pytest.mark.skipif(
    pytest.importorskip('yaml', reason='yaml not available') is None,
    reason='yaml not available',
)
class TestYamlConfig:
    """Test the YamlConfig provider (if yaml is available)."""

    def test_yaml_config_creation(self):
        """Test creating YamlConfig."""
        # Import here to avoid issues if yaml is not available
        from monday.config import YamlConfig

        yaml_config = YamlConfig('/path/to/config.yaml')
        assert yaml_config.config_path == Path('/path/to/config.yaml')
        assert yaml_config._config is None

    def test_yaml_config_get_config_valid_file(self):
        """Test getting config from valid YAML file."""
        import yaml

        from monday.config import YamlConfig

        config_data = {
            'api_key': 'yaml_test_key',
            'url': 'https://yaml.api.com/v2',
            'max_retries': 8,
            'headers': {'YAML-Header': 'yaml_value'},
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            yaml_config = YamlConfig(temp_path)
            config = yaml_config.get_config()

            assert config.api_key == 'yaml_test_key'
            assert config.url == 'https://yaml.api.com/v2'
            assert config.max_retries == 8
            assert config.headers == {'YAML-Header': 'yaml_value'}
        finally:
            Path(temp_path).unlink()

    def test_yaml_config_validate_valid_file(self):
        """Test validating valid YAML config file."""
        import yaml

        from monday.config import YamlConfig

        config_data = {'api_key': 'valid_yaml_key'}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            yaml_config = YamlConfig(temp_path)
            assert yaml_config.validate_config() is True
        finally:
            Path(temp_path).unlink()

    def test_yaml_config_validate_missing_file(self):
        """Test validating missing YAML config file."""
        from monday.config import YamlConfig

        yaml_config = YamlConfig('/nonexistent/file.yaml')
        assert yaml_config.validate_config() is False

    def test_yaml_config_validate_invalid_yaml(self):
        """Test validating invalid YAML config file."""
        from monday.config import YamlConfig

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('invalid: yaml: content:')  # Invalid YAML syntax
            temp_path = f.name

        try:
            yaml_config = YamlConfig(temp_path)
            assert yaml_config.validate_config() is False
        finally:
            Path(temp_path).unlink()

    def test_yaml_config_reload(self):
        """Test reloading YAML config."""
        import yaml

        from monday.config import YamlConfig

        initial_data = {'api_key': 'initial_yaml_key'}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(initial_data, f)
            temp_path = f.name

        try:
            yaml_config = YamlConfig(temp_path)
            initial_config = yaml_config.get_config()
            assert initial_config.api_key == 'initial_yaml_key'

            # Update file and reload
            updated_data = {'api_key': 'updated_yaml_key'}
            with Path(temp_path).open('w') as f:
                yaml.dump(updated_data, f)

            yaml_config.reload_config()
            updated_config = yaml_config.get_config()
            assert updated_config.api_key == 'updated_yaml_key'
        finally:
            Path(temp_path).unlink()

    def test_yaml_config_pathlib_path(self):
        """Test YamlConfig with pathlib.Path."""
        import yaml

        from monday.config import YamlConfig

        config_data = {'api_key': 'yaml_pathlib_key'}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            yaml_config = YamlConfig(temp_path)
            config = yaml_config.get_config()

            assert config.api_key == 'yaml_pathlib_key'
        finally:
            temp_path.unlink()

    def test_yaml_config_comprehensive_options(self):
        """Test YamlConfig with all configuration options."""
        import yaml

        from monday.config import YamlConfig

        # Test with all possible config options
        config_data = {
            'api_key': 'yaml_comprehensive_key',
            'url': 'https://yaml-comprehensive.api.com/v3',
            'version': '2023-yaml',
            'headers': {
                'YAML-Auth': 'yaml_token',
                'YAML-Client': 'yaml_client_v1',
            },
            'max_retries': 15,
            'timeout': 180,
            'rate_limit_seconds': 300,
            'proxy_url': 'http://yaml-proxy.example.com:9090',
            'proxy_auth': ['yaml_proxy_user', 'yaml_proxy_pass'],
            'proxy_auth_type': 'basic',
            'proxy_trust_env': True,
            'proxy_headers': {
                'YAML-Proxy-Auth': 'yaml_proxy_token',
                'YAML-Proxy-Client': 'yaml_proxy_client',
            },
            'proxy_ssl_verify': False,
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            yaml_config = YamlConfig(temp_path)
            config = yaml_config.get_config()

            # Verify all config options are loaded correctly
            assert config.api_key == 'yaml_comprehensive_key'
            assert config.url == 'https://yaml-comprehensive.api.com/v3'
            assert config.version == '2023-yaml'
            assert config.headers == {
                'YAML-Auth': 'yaml_token',
                'YAML-Client': 'yaml_client_v1',
            }
            assert config.max_retries == 15
            assert config.timeout == 180
            assert config.rate_limit_seconds == 300
            assert config.proxy_url == 'http://yaml-proxy.example.com:9090'
            assert config.proxy_auth == ('yaml_proxy_user', 'yaml_proxy_pass')
            assert config.proxy_auth_type == 'basic'
            assert config.proxy_trust_env is True
            assert config.proxy_headers == {
                'YAML-Proxy-Auth': 'yaml_proxy_token',
                'YAML-Proxy-Client': 'yaml_proxy_client',
            }
            assert config.proxy_ssl_verify is False
        finally:
            Path(temp_path).unlink()

    def test_yaml_config_get_config_missing_file(self):
        """Test getting config from missing YAML file."""
        from monday.config import YamlConfig

        yaml_config = YamlConfig('/nonexistent/file.yaml')

        with pytest.raises(FileNotFoundError):
            yaml_config.get_config()

    def test_yaml_config_get_config_invalid_yaml_syntax(self):
        """Test getting config from YAML file with syntax errors."""
        import yaml

        from monday.config import YamlConfig

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('invalid: yaml: [unclosed list')  # Invalid YAML syntax
            temp_path = f.name

        try:
            yaml_config = YamlConfig(temp_path)

            with pytest.raises(yaml.YAMLError):
                yaml_config.get_config()
        finally:
            Path(temp_path).unlink()

    def test_yaml_config_validate_invalid_config_values(self):
        """Test validating YAML file with invalid config values."""
        import yaml

        from monday.config import YamlConfig

        config_data = {'api_key': ''}  # Empty API key is invalid

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            yaml_config = YamlConfig(temp_path)
            assert yaml_config.validate_config() is False
        finally:
            Path(temp_path).unlink()

    def test_yaml_config_file_modification_detection(self):
        """Test that YamlConfig can handle file modifications (no auto-reload like JsonConfig)."""
        import yaml

        from monday.config import YamlConfig

        initial_data = {'api_key': 'initial_yaml_key'}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(initial_data, f)
            temp_path = f.name

        try:
            yaml_config = YamlConfig(temp_path)

            # Load initial config
            initial_config = yaml_config.get_config()
            assert initial_config.api_key == 'initial_yaml_key'

            # Modify file
            import time

            time.sleep(0.1)  # Ensure modification time is different
            updated_data = {'api_key': 'modified_yaml_key'}
            with Path(temp_path).open('w') as f:
                yaml.dump(updated_data, f)

            # YamlConfig doesn't auto-reload, so should still return cached config
            cached_config = yaml_config.get_config()
            assert cached_config.api_key == 'initial_yaml_key'

            # But after explicit reload, should get new config
            yaml_config.reload_config()
            reloaded_config = yaml_config.get_config()
            assert reloaded_config.api_key == 'modified_yaml_key'
        finally:
            Path(temp_path).unlink()

    def test_yaml_config_caching_behavior(self):
        """Test that YamlConfig caches config properly."""
        import yaml

        from monday.config import YamlConfig

        config_data = {'api_key': 'cached_yaml_key'}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            yaml_config = YamlConfig(temp_path)

            # First call
            config1 = yaml_config.get_config()

            # Second call should return cached config (same object)
            config2 = yaml_config.get_config()

            assert config1 is config2
        finally:
            Path(temp_path).unlink()

    def test_yaml_config_complex_data_types(self):
        """Test YamlConfig with complex YAML data types."""
        import yaml

        from monday.config import YamlConfig

        # Test with various YAML data types
        config_data = {
            'api_key': 'yaml_complex_key',
            'headers': {
                'string_header': 'simple_string',
                'number_header': 42,
                'boolean_header': True,
                'null_header': None,
                'list_header': ['item1', 'item2', 'item3'],
                'nested_dict': {
                    'nested_key': 'nested_value',
                    'nested_number': 123,
                },
            },
            'max_retries': 7,
            'timeout': 120,
            'proxy_trust_env': False,
            'proxy_ssl_verify': True,
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            yaml_config = YamlConfig(temp_path)
            config = yaml_config.get_config()

            # Verify complex data types are preserved
            assert config.api_key == 'yaml_complex_key'
            assert config.headers['string_header'] == 'simple_string'
            assert config.headers['number_header'] == 42
            assert config.headers['boolean_header'] is True
            assert config.headers['null_header'] is None
            assert config.headers['list_header'] == ['item1', 'item2', 'item3']
            assert config.headers['nested_dict'] == {
                'nested_key': 'nested_value',
                'nested_number': 123,
            }
            assert config.max_retries == 7
            assert config.timeout == 120
            assert config.proxy_trust_env is False
            assert config.proxy_ssl_verify is True
        finally:
            Path(temp_path).unlink()


@pytest.mark.unit
class TestConfigIntegration:
    """Integration tests for the config system."""

    def test_config_providers_in_multisource(self):
        """Test all config provider types working together in MultiSourceConfig."""
        # Check if YAML is available
        try:
            import yaml

            yaml_available = True
        except ImportError:
            yaml_available = False

        providers = []
        temp_files = []

        try:
            # JSON config as base
            json_data = {
                'api_key': 'json_base_key',
                'url': 'https://json.api.com/v2',
                'max_retries': 3,
                'headers': {'JSON-Header': 'json_value'},
            }

            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False
            ) as f:
                json.dump(json_data, f)
                json_path = f.name
                temp_files.append(json_path)

            providers.append(JsonConfig(json_path))

            # Add YAML config if available
            if yaml_available:
                import yaml

                from monday.config import YamlConfig

                yaml_data = {
                    'api_key': 'yaml_override_key',
                    'timeout': 90,
                    'headers': {'YAML-Header': 'yaml_value'},
                }

                with tempfile.NamedTemporaryFile(
                    mode='w', suffix='.yaml', delete=False
                ) as f:
                    yaml.dump(yaml_data, f)
                    yaml_path = f.name
                    temp_files.append(yaml_path)

                providers.append(YamlConfig(yaml_path))

            # Environment config as final override
            env = {
                'MONDAY_API_KEY': 'env_final_key',
                'MONDAY_VERSION': '2023-12',
            }

            with patch.dict(os.environ, env, clear=False):
                providers.append(EnvConfig())

                multi_config = MultiSourceConfig(providers)
                config = multi_config.get_config()

                # Env should override everything
                assert config.api_key == 'env_final_key'
                assert config.version == '2023-12'

                # JSON base values should be preserved (but may be overridden by defaults)
                assert config.url == 'https://api.monday.com/v2'
                assert config.max_retries == 4  # Default from env config overrides JSON

                # YAML values should override JSON (if YAML is available)
                if yaml_available:
                    assert (
                        config.timeout == 30
                    )  # Default from env config overrides YAML
                    expected_headers = {
                        'JSON-Header': 'json_value',
                        'YAML-Header': 'yaml_value',
                    }
                    assert config.headers == expected_headers
                else:
                    assert config.headers == {'JSON-Header': 'json_value'}

        finally:
            # Clean up temp files
            for temp_file in temp_files:
                with contextlib.suppress(OSError):
                    Path(temp_file).unlink()

    def test_config_edge_cases(self):
        """Test edge cases and error conditions."""
        # Test Config with empty strings and special values
        config = Config(
            api_key='test_key',
            url='',  # Empty URL
            version='',  # Empty version
            headers={},  # Empty headers
            proxy_url='',  # Empty proxy URL
        )

        # Empty strings should be preserved
        assert config.url == ''
        assert config.version == ''
        assert config.proxy_url == ''

        # Test validation with edge case values
        config_edge = Config(
            api_key='test_key',
            max_retries=0,  # Minimum valid value
            timeout=1,  # Minimum valid value
            rate_limit_seconds=1,  # Minimum valid value
        )

        config_edge.validate()  # Should not raise

    def test_config_type_conversion(self):
        """Test type conversion in Config.from_env() and Config.from_dict()."""
        # Test from_env with string numbers
        env = {
            'MONDAY_API_KEY': 'test_key',
            'MONDAY_MAX_RETRIES': '999',
            'MONDAY_TIMEOUT': '3600',
            'MONDAY_RATE_LIMIT_SECONDS': '1800',
        }

        with patch.dict(os.environ, env, clear=False):
            config = Config.from_env()

            assert isinstance(config.max_retries, int)
            assert isinstance(config.timeout, int)
            assert isinstance(config.rate_limit_seconds, int)
            assert config.max_retries == 999
            assert config.timeout == 3600
            assert config.rate_limit_seconds == 1800

    def test_config_comprehensive_field_coverage(self):
        """Test that all config fields are properly handled in all scenarios."""
        # Test with every single config field set to non-default values
        all_fields_config = Config(
            api_key='comprehensive_key',
            url='https://comprehensive.api.com/v3',
            version='2023-comprehensive',
            headers={'Comprehensive-Header': 'comprehensive_value'},
            max_retries=99,
            timeout=999,
            rate_limit_seconds=9999,
            proxy_url='http://comprehensive-proxy.example.com:9999',
            proxy_auth=('comprehensive_user', 'comprehensive_pass'),
            proxy_auth_type='ntlm',
            proxy_trust_env=True,
            proxy_headers={'Comprehensive-Proxy-Header': 'comprehensive_proxy_value'},
            proxy_ssl_verify=False,
        )

        # Validate
        all_fields_config.validate()

        # Convert to dict and back
        config_dict = all_fields_config.to_dict()
        restored_config = Config.from_dict(config_dict)

        # Verify every field matches
        for field_name in [
            'api_key',
            'url',
            'version',
            'headers',
            'max_retries',
            'timeout',
            'rate_limit_seconds',
            'proxy_url',
            'proxy_auth',
            'proxy_auth_type',
            'proxy_trust_env',
            'proxy_headers',
            'proxy_ssl_verify',
        ]:
            original_value = getattr(all_fields_config, field_name)
            restored_value = getattr(restored_config, field_name)
            assert original_value == restored_value, (
                f'Field {field_name} mismatch: {original_value} != {restored_value}'
            )
