# monday.com API Client

[![Documentation Status](https://readthedocs.org/projects/monday-client/badge/?version=latest)](https://monday-client.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/monday-client.svg)](https://badge.fury.io/py/monday-client)
[![Python Versions](https://img.shields.io/pypi/pyversions/monday-client.svg)](https://pypi.org/project/monday-client/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![GitHub issues](https://img.shields.io/github/issues/LeetCyberSecurity/monday-client.svg)](https://github.com/LeetCyberSecurity/monday-client/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/LeetCyberSecurity/monday-client.svg)](https://github.com/LeetCyberSecurity/monday-client/commits/main)

This Python library provides an **asynchronous** client to interact with the [monday.com API](https://developer.monday.com/api-reference/reference/about-the-api-reference).

## Documentation

For detailed documentation, visit the [official documentation site](https://monday-client.readthedocs.io).

## Key Features

- **Asynchronous API calls** using `asyncio` and `aiohttp` for efficient I/O operations.
- **Automatic handling of API rate limits and query limits** following monday.com's rate limit policies.
- **Built-in retry logic** for handling rate limit exceptions, ensuring smooth operation without manual intervention.
- **Easy-to-use methods** for common monday.com operations.
- **Fully customizable requests** with all monday.com method arguments and fields available to the user.

## Installation

```bash
pip install monday-client
```

## Quick Start

```python
import asyncio

from monday import MondayClient

async def main():
    monday_client = MondayClient(api_key='your_api_key_here')
    boards = await monday_client.boards.query(board_ids=[987654321, 876543210])
    items = await monday_client.items.query(item_ids=[123456789, 123456780])

asyncio.run(main())
```


## Usage

### Asynchronous Operations

All methods provided by the `MondayClient` are asynchronous and should be awaited. This allows for efficient concurrent execution of API calls.

### Rate Limiting and Retry Logic

The client automatically handles rate limiting in compliance with monday.com's API policies. When a rate limit is reached, the client will wait for the specified reset time before retrying the request. This ensures that your application doesn't need to manually handle rate limit exceptions and can operate smoothly.

### Error Handling

Custom exceptions are defined for handling specific error cases:

- `MondayAPIError`: Raised when an error occurs during API communication with monday.com.
- `PaginationError`: Raised when item pagination fails during a request.
- `QueryFormatError`: Raised when there is a query formatting error.
- `ComplexityLimitExceeded`: Raised when the complexity limit and max retries are exceeded.
- `MutationLimitExceeded`: Raised when the mutation limit and max retries are exceeded.

### Logging

The client uses a logger named `monday_client` for all logging operations. By default, a `NullHandler` is added to suppress logging output. To enable logging, you can configure the logger in your application:

```python
import logging

logger = logging.getLogger('monday_client')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
```

Or update an already existing logging config:
```python
import logging.config

logging_config = config['logging']

logging_config['loggers'].update({
    'monday_client': {
        'handlers': ['file', 'console'],  # Use the same handlers as your main logger
        'level': 'INFO',  # Set appropriate level
        'propagate': False
    }
})

logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)
```

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](https://github.com/LeetCyberSecurity/monday-client/blob/main/LICENSE) file for details.