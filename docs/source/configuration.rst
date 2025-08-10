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

.. _configuration:

Configuration
=============

The monday-client library provides a flexible configuration system that supports multiple sources and methods for managing client settings. This page covers all configuration options, from basic setup to advanced proxy configurations.

.. contents:: Table of Contents
    :depth: 3
    :local:

Overview
--------

The configuration system is built around the :class:`~monday.config.Config` dataclass and various configuration providers. You can configure the client using:

1. **Direct instantiation** with :class:`~monday.config.Config` objects (recommended)
2. **Environment variables** via :class:`~monday.config.EnvConfig`
3. **JSON files** via :class:`~monday.config.JsonConfig`
4. **YAML files** via :class:`~monday.config.YamlConfig` (requires PyYAML)
5. **Multiple sources** via :class:`~monday.config.MultiSourceConfig`

Configuration Options
---------------------

Core Settings
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 15 10 55

   * - Setting
     - Type
     - Default
     - Description
   * - ``api_key``
     - ``str``
     - **Required**
     - Your monday.com API key for authentication
   * - ``url``
     - ``str``
     - ``https://api.monday.com/v2``
     - The monday.com API endpoint URL
   * - ``version``
     - ``str | None``
     - ``None``
     - API version to use (auto-fetches current if None)
   * - ``headers``
     - ``dict[str, Any]``
     - ``{}``
     - Additional HTTP headers for API requests
   * - ``max_retries``
     - ``int``
     - ``4``
     - Maximum number of retry attempts for requests
   * - ``timeout``
     - ``int``
     - ``30``
     - Request timeout in seconds
   * - ``rate_limit_seconds``
     - ``int``
     - ``60``
     - Rate limit window in seconds

Proxy Settings
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 15 10 55

   * - Setting
     - Type
     - Default
     - Description
   * - ``proxy_url``
     - ``str | None``
     - ``None``
     - Proxy server URL (HTTP/HTTPS/SOCKS5)
   * - ``proxy_auth``
     - ``tuple[str, str] | None``
     - ``None``
     - Proxy authentication as (username, password)
   * - ``proxy_auth_type``
     - ``str``
     - ``'basic'``
     - Aiohttp transport: only 'basic'. Httpx transport: 'basic', 'ntlm', 'kerberos'/'spnego' with extra dependencies.
   * - ``proxy_trust_env``
     - ``bool``
     - ``False``
     - Trust system proxy environment variables
   * - ``proxy_headers``
     - ``dict[str, str]``
     - ``{}``
     - Supported with httpx transport (sent on CONNECT). Ignored with aiohttp transport.
   * - ``proxy_ssl_verify``
     - ``bool``
     - ``True``
     - Verify SSL certificates for HTTPS proxies. Applies to the ``aiohttp`` transport. The ``httpx`` transport does not support per-proxy TLS verification toggling and this setting is ignored there.

Basic Usage
-----------

Direct Configuration
~~~~~~~~~~~~~~~~~~~~

The recommended approach is to use the :class:`~monday.config.Config` class directly:

.. code-block:: python

    from monday import MondayClient, Config

    # Basic configuration
    config = Config(api_key='your_api_key_here')
    client = MondayClient(config)

    # Advanced configuration
    config = Config(
        api_key='your_api_key_here',
        timeout=60,
        max_retries=6,
        headers={'User-Agent': 'MyApp/1.0'}
    )
    client = MondayClient(config)

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Use :class:`~monday.config.EnvConfig` to load configuration from environment variables:

.. code-block:: python

    from monday import MondayClient, EnvConfig

    # Load from environment variables with MONDAY_ prefix
    env_config = EnvConfig()
    client = MondayClient(env_config.get_config())

    # Custom prefix
    env_config = EnvConfig(prefix='MYAPP_MONDAY_')
    client = MondayClient(env_config.get_config())

**Environment Variable Names:**

.. code-block:: bash

    # Core settings
    export MONDAY_API_KEY="your_api_key_here"
    export MONDAY_URL="https://api.monday.com/v2"
    export MONDAY_VERSION="2024-01"
    export MONDAY_MAX_RETRIES="4"
    export MONDAY_TIMEOUT="30"
    export MONDAY_RATE_LIMIT_SECONDS="60"

    # Proxy settings
    export MONDAY_PROXY_URL="http://proxy.company.com:8080"
    export MONDAY_PROXY_USER="username"
    export MONDAY_PROXY_PASS="password"
    export MONDAY_PROXY_AUTH_TYPE="basic"
    export MONDAY_PROXY_TRUST_ENV="false"
    # Optional (used by httpx transport only). JSON string of headers sent to the proxy (on CONNECT):
    export MONDAY_PROXY_HEADERS='{"X-Proxy-Trace": "on"}'
    export MONDAY_PROXY_SSL_VERIFY="true"

File-Based Configuration
~~~~~~~~~~~~~~~~~~~~~~~~

JSON Configuration
^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from monday import MondayClient, JsonConfig

    # Load from JSON file
    json_config = JsonConfig('config.json')
    client = MondayClient(json_config.get_config())

**Example config.json:**

.. code-block:: json

    {
        "api_key": "your_api_key_here",
        "timeout": 60,
        "max_retries": 6,
        "headers": {
            "User-Agent": "MyApp/1.0"
        },
        "proxy_url": "http://proxy.company.com:8080",
        "proxy_auth": ["username", "password"],
        "proxy_auth_type": "basic"
    }

YAML Configuration
^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from monday import MondayClient, YamlConfig

    # Load from YAML file (requires PyYAML: pip install pyyaml)
    yaml_config = YamlConfig('config.yaml')
    client = MondayClient(yaml_config.get_config())

**Example config.yaml:**

.. code-block:: yaml

    api_key: "your_api_key_here"
    timeout: 60
    max_retries: 6
    headers:
        User-Agent: "MyApp/1.0"
    proxy_url: "http://proxy.company.com:8080"
    proxy_auth:
        - "username"
        - "password"
    proxy_auth_type: "basic"

Multi-Source Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~

Combine multiple configuration sources with priority ordering:

.. code-block:: python

    from monday import MondayClient, MultiSourceConfig, JsonConfig, EnvConfig

    # Environment variables override JSON file settings
    multi_config = MultiSourceConfig([
        JsonConfig('config.json'),      # Base configuration
        EnvConfig()                     # Environment overrides
    ])

    client = MondayClient(multi_config.get_config())

Transports
----------

The client supports two async HTTP transports: ``aiohttp`` (default) and ``httpx``.

- **Use aiohttp (default)**: general usage with minimal dependencies and solid performance. SOCKS requires ``aiohttp-socks``.
- **Use httpx**: when you need enterprise proxy features such as custom ``proxy_headers`` and advanced proxy authentication (NTLM, Kerberos/SPNEGO). SOCKS requires the ``httpx[socks]`` extra.

Select a transport explicitly:

.. code-block:: python

    from monday import MondayClient, Config

    config = Config(api_key='your_api_key_here')
    client = MondayClient(config, transport='httpx')  # or 'aiohttp' (default)

.. note::

    Disabling or altering TLS verification for HTTPS proxies is not supported per-proxy in ``httpx``; ``proxy_ssl_verify`` only affects the ``aiohttp`` transport.

Proxy Configuration
-------------------

The monday-client supports various proxy configurations for enterprise environments.

.. note::
    - SOCKS support (aiohttp): install ``aiohttp-socks``: ``pip install monday-client[proxy]``
    - SOCKS support (httpx): install ``httpx`` extras: ``pip install 'httpx[socks]'``
    - Enterprise proxy auth (httpx): install ``httpx-ntlm`` for NTLM and ``pyspnego`` for Kerberos/SPNEGO

Supported Proxy Types
~~~~~~~~~~~~~~~~~~~~~

- **HTTP/HTTPS proxies**: ``http://proxy.company.com:8080``
- **SOCKS5 proxies**: ``socks5://proxy.company.com:1080``
- **Authenticated proxies**: Any type with username/password

Basic Proxy Setup
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from monday import MondayClient, Config

    config = Config(
        api_key='your_api_key_here',
        proxy_url='http://proxy.company.com:8080'
    )
    client = MondayClient(config)

Authenticated Proxy (Aiohttp)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from monday import MondayClient, Config

    config = Config(
        api_key='your_api_key_here',
        proxy_url='http://proxy.company.com:8080',
        proxy_auth=('username', 'password'),
        proxy_auth_type='basic'  # aiohttp supports basic proxy auth
    )
    client = MondayClient(config)

SOCKS5 Proxy
~~~~~~~~~~~~

.. code-block:: python

    from monday import MondayClient, Config

    config = Config(
        api_key='your_api_key_here',
        proxy_url='socks5://proxy.company.com:1080',
        proxy_auth=('username', 'password')
    )
    client = MondayClient(config)

System Proxy Environment
~~~~~~~~~~~~~~~~~~~~~~~~

To use system proxy environment variables (``HTTP_PROXY``, ``HTTPS_PROXY``, etc.):

.. code-block:: python

    from monday import MondayClient, Config

    config = Config(
        api_key='your_api_key_here',
        proxy_trust_env=True
    )
    client = MondayClient(config)

Advanced Proxy Configuration (Httpx)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from monday import MondayClient, Config

    config = Config(
        api_key='your_api_key_here',
        proxy_url='https://proxy.company.com:8080',
        proxy_headers={
            'X-Forwarded-For': '192.168.1.100',
            'X-Custom-Header': 'value'
        },
    )
    client = MondayClient(config, transport='httpx')

NTLM Proxy Authentication (Httpx)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Requires ``httpx-ntlm``:

.. code-block:: bash

    pip install httpx httpx-ntlm

Example:

.. code-block:: python

    from monday import MondayClient, Config

    config = Config(
        api_key='your_api_key_here',
        proxy_url='http://proxy.company.com:8080',
        proxy_auth=('DOMAIN\\username', 'password'),
        proxy_auth_type='ntlm',
    )
    client = MondayClient(config, transport='httpx')

Kerberos / SPNEGO Proxy Authentication (Httpx)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Requires ``pyspnego`` and a valid Kerberos credential (for example, via ``kinit`` on Unix or SSPI on Windows):

.. code-block:: bash

    pip install httpx pyspnego

Example:

.. code-block:: python

    from monday import MondayClient, Config

    config = Config(
        api_key='your_api_key_here',
        proxy_url='http://proxy.company.com:8080',
        proxy_auth_type='kerberos',  # or 'spnego'
    )
    client = MondayClient(config, transport='httpx')

Validation and Error Handling
------------------------------

All configuration objects provide validation methods:

.. code-block:: python

    from monday import Config, JsonConfig, EnvConfig

    # Validate direct config
    config = Config(api_key='test')
    try:
        config.validate()
        print("Configuration is valid")
    except ValueError as e:
        print(f"Configuration error: {e}")

    # Validate file-based config
    json_config = JsonConfig('config.json')
    if json_config.validate_config():
        print("JSON configuration is valid")
    else:
        print("JSON configuration is invalid")

    # Validate environment config
    env_config = EnvConfig()
    if env_config.validate_config():
        print("Environment configuration is valid")
    else:
        print("Environment configuration is invalid")

Configuration Reloading
-----------------------

Some configuration providers support dynamic reloading:

.. code-block:: python

    from monday import JsonConfig, EnvConfig

    # File-based configs auto-reload when file changes
    json_config = JsonConfig('config.json')
    config1 = json_config.get_config()

    # ... modify config.json ...

    config2 = json_config.get_config()  # Automatically reloaded

    # Force reload
    json_config.reload_config()

    # Environment configs can be manually reloaded
    env_config = EnvConfig()
    env_config.reload_config()  # Re-reads environment variables

Best Practices
--------------

1. **Use Config objects**: The :class:`~monday.config.Config` class provides type safety and validation.

2. **Environment-specific configs**: Use different configuration sources for different environments:

    .. code-block:: python

        import os
        from monday import MondayClient, Config, JsonConfig, EnvConfig

        if os.environ.get('PRODUCTION'):
            # Production: use environment variables
            config_provider = EnvConfig()
        else:
            # Development: use JSON file
            config_provider = JsonConfig('dev_config.json')

        client = MondayClient(config_provider.get_config())

3. **Secure credential storage**: Never commit API keys or proxy credentials to version control.

4. **Proxy authentication**: Store proxy credentials securely and use environment variables in production.

5. **Validation**: Always validate configuration before using it in production:

    .. code-block:: python

        from monday import Config

        config = Config(api_key=api_key, timeout=timeout)
        config.validate()  # Raises ValueError if invalid
        client = MondayClient(config)

Troubleshooting
---------------

Common Configuration Issues
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Missing API Key**
    Ensure ``MONDAY_API_KEY`` environment variable is set or ``api_key`` is provided in config.

**Proxy Connection Failures**
    - Verify proxy URL format (``http://``, ``https://``, ``socks5://``)
    - Check proxy authentication credentials
    - Ensure ``aiohttp-socks`` is installed for SOCKS5 support

**File Not Found Errors**
    Verify configuration file paths and permissions.

**Invalid JSON/YAML**
    Validate configuration file syntax using a JSON/YAML validator.

Debugging Configuration
~~~~~~~~~~~~~~~~~~~~~~~

Enable logging to debug configuration issues:

.. code-block:: python

    import logging
    from monday import MondayClient, Config

    # Enable debug logging
    logging.basicConfig(level=logging.DEBUG)
    monday_logger = logging.getLogger('monday')
    monday_logger.setLevel(logging.DEBUG)

    config = Config(api_key='your_api_key_here')
    client = MondayClient(config)

.. seealso::

    - :doc:`usage` - Basic usage examples
    - :doc:`monday_client` - MondayClient API reference
    - :doc:`exceptions` - Error handling and exceptions

API Reference
-------------

Configuration Classes
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: monday.config.Config
    :members:
    :show-inheritance:

.. autoclass:: monday.config.EnvConfig
    :members:
    :show-inheritance:

.. autoclass:: monday.config.JsonConfig
    :members:
    :show-inheritance:

.. autoclass:: monday.config.MultiSourceConfig
    :members:
    :show-inheritance:

.. autoclass:: monday.config.YamlConfig
    :members:
    :show-inheritance:
