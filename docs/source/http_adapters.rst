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


