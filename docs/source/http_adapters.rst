.. This file is part of monday-client.

.. index:: HTTP Adapters

HTTP Adapters
-------------

The monday-client supports pluggable async HTTP transports so you can choose the
stack that best fits your environment without changing your application code.

- ``aiohttp`` (default): solid performance with minimal dependencies.
- ``httpx``: enterprise proxy features such as custom ``proxy_headers`` and
  advanced proxy authentication (NTLM, Kerberos/SPNEGO) via optional extras.

Selecting a transport
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from monday import MondayClient, Config

   config = Config(api_key='your_api_key_here')
   client = MondayClient(config, transport='httpx')  # or 'aiohttp' (default)

Proxy capabilities (summary)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **AiohttpAdapter**: HTTP/HTTPS proxies, optional SOCKS via ``aiohttp-socks``,
  basic auth with ``proxy_auth``. ``proxy_ssl_verify`` can disable TLS
  verification when talking to an HTTPS proxy.
- **HttpxAdapter**: HTTP/HTTPS proxies, optional SOCKS via ``httpx[socks]``,
  custom ``proxy_headers`` (useful for CONNECT), optional NTLM via
  ``httpx-ntlm`` and Kerberos/SPNEGO via ``pyspnego``.

API Reference
~~~~~~~~~~~~~

.. autoclass:: monday.http_adapters.AiohttpAdapter
   :members:
   :show-inheritance:

.. autoclass:: monday.http_adapters.HttpxAdapter
   :members:
   :show-inheritance:


