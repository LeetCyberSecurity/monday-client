# monday.com API Client

[![Documentation Status](https://readthedocs.org/projects/monday-client/badge/?version=latest)](https://monday-client.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/monday-client.svg)](https://pypi.org/project/monday-client/)
[![Python Versions](https://img.shields.io/pypi/pyversions/monday-client.svg)](https://pypi.org/project/monday-client/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![GitHub issues](https://img.shields.io/github/issues/LeetCyberSecurity/monday-client.svg)](https://github.com/LeetCyberSecurity/monday-client/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/LeetCyberSecurity/monday-client.svg)](https://github.com/LeetCyberSecurity/monday-client/commits/main)

This Python library provides an **asynchronous** client to interact with the [monday.com API](https://developer.monday.com/api-reference/reference/about-the-api-reference).

## Documentation

For detailed documentation, visit the [official documentation site](https://monday-client.readthedocs.io).

## Key Features

- **Asynchronous API calls** using `asyncio` and `aiohttp` for efficient I/O operations
- **Automatic handling of API rate limits and query limits** following monday.com's rate limit policies
- **Built-in retry logic** for handling rate limit exceptions, ensuring smooth operation without manual intervention
- **Type-safe column value updates** with dedicated input classes for all column types
- **Advanced filtering and querying** with QueryParams and QueryRule support
- **Fully customizable requests** with all monday.com method arguments and fields available

## Installation

```bash
pip install monday-client
```

## Usage

```python
import asyncio

from monday import MondayClient, Config

async def main():
    # Recommended: Using configuration object
    config = Config(api_key='your_api_key_here')
    client = MondayClient(config)

    # Alternative: Using individual parameters  
    # client = MondayClient(api_key='your_api_key_here')

    # Query boards and items
    boards = await client.boards.query(board_ids=[987654321, 876543210])
    items = await client.items.query(item_ids=[123456789, 123456780])

    # Access dataclass attributes
    for board in boards:
        print(f'Board: {board.name} (ID: {board.id})')

    for item in items:
        print(f'Item: {item.name} (ID: {item.id})')

asyncio.run(main())
```

## Configuration

The monday-client supports flexible configuration through the `Config` class and various configuration providers:

### Environment Variables

```python
import os
from monday import MondayClient, EnvConfig

# Set environment variables
os.environ['MONDAY_API_KEY'] = 'your_api_key_here'
os.environ['MONDAY_TIMEOUT'] = '60'

# Load from environment
env_config = EnvConfig()
client = MondayClient(env_config.get_config())
```

### Configuration Files

```python
from monday import MondayClient, JsonConfig

# Load from JSON file
json_config = JsonConfig('config.json')
client = MondayClient(json_config.get_config())
```

For comprehensive configuration options, including proxy settings, multi-source configurations, and advanced features, see the [Configuration Documentation](https://monday-client.readthedocs.io/en/latest/configuration.html).

### Use predefined field sets for more data

```python
import asyncio

from monday import MondayClient, Config
from monday.fields import BoardFields, ItemFields

async def main():
    config = Config(api_key='your_api_key_here')
    client = MondayClient(config)

    # Get detailed board information
    detailed_boards = await client.boards.query(
        board_ids=[987654321, 876543210],
        fields=BoardFields.DETAILED  # Includes: id name state board_kind description
    )

    # Get boards with items
    boards_with_items = await client.boards.query(
        board_ids=[987654321, 876543210],
        fields=BoardFields.ITEMS  # Includes: id name items_count items_page
    )

asyncio.run(main())
```

See [Fields Reference](https://monday-client.readthedocs.io/en/latest/fields.html) in the documentation for more info.

You can also use custom field strings for specific needs:

```python
custom_boards = await client.boards.query(
    board_ids=[987654321],
    fields='id name state type url items_count update { body }'
)

custom_items = await client.items.query(
    item_ids=[123456789],
    fields='id name created_at updated_at column_values { id text }'
)
```

### Use QueryParams and QueryRule to filter data

```python
import asyncio

from monday import MondayClient, Config, QueryParams, QueryRule

async def main():
    config = Config(api_key='your_api_key_here')
    client = MondayClient(config)

    # Filter items with status "Done" or "In Progress"
    query_params = QueryParams(
        rules=[
            QueryRule(
                column_id='status',
                compare_value=['Done', 'In Progress'],
                operator='any_of'
            )
        ],
        operator='and'
    )

    item_lists = await client.boards.get_items(
        board_ids=[987654321, 876543210],
        query_params=query_params,
        fields='id name column_values { id text column { title } } '
    )

    # Access dataclass attributes from filtered results
    for item_list in item_lists:
        print(f'Board {item_list.board_id}:')
        for item in item_list.items:
            print(f'  - {item.name} (ID: {item.id})')

asyncio.run(main())
```

### Use type-safe input classes to update column values

```python
import asyncio

from monday import MondayClient, Config
from monday.types import DateInput, StatusInput, TextInput

async def main():
    config = Config(api_key='your_api_key_here')
    client = MondayClient(config)

    # Create a new item
    new_item = await client.items.create(
        board_id=987654321,
        item_name='New Task',
        group_id='topics'
    )

    await client.items.change_column_values(
        item_id=new_item.id,
        column_values=[
            StatusInput('status', 'Working on it'),
            TextInput('text', 'Task description'),
            DateInput('date', '2024-01-15', '14:30:00')
        ]
    )

asyncio.run(main())
```

### Asynchronous Operations

All methods provided by the `MondayClient` are asynchronous and should be awaited. This allows for efficient concurrent execution of API calls.

### Rate Limiting and Retry Logic

The client automatically handles rate limiting in compliance with monday.com's API policies. When a rate limit is reached, the client will wait for the specified reset time before retrying the request. This ensures that your application doesn't need to manually handle rate limit exceptions and can operate smoothly.

### Error Handling

Custom exceptions are defined for handling specific error cases:

- `MondayAPIError`: Raised when an error occurs during API communication with monday.com
- `PaginationError`: Raised when item pagination fails during a request
- `QueryFormatError`: Raised when there is a query formatting error
- `ComplexityLimitExceeded`: Raised when the complexity limit and max retries are exceeded
- `MutationLimitExceeded`: Raised when the mutation limit and max retries are exceeded

### Logging

The client uses a logger named `monday` for all logging operations. By default, logging is suppressed to follow Python library best practices.

#### Quick Setup

For simple logging during development or testing:

```python
from monday import MondayClient, enable_logging

# Enable logging with default settings
enable_logging()

client = MondayClient(api_key='your_api_key')
# Now you'll see Monday client logs
```

#### Advanced Configuration

For production applications, integrate with your existing logging configuration:

```python
import logging.config
from monday import configure_for_external_logging

# Prepare Monday client for external configuration
configure_for_external_logging()

# Add Monday client to your logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'standard'},
    },
    'loggers': {
        'myapp': {'level': 'DEBUG', 'handlers': ['console']},
        'monday': {'level': 'INFO', 'handlers': ['console']},  # Add this line
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
client = MondayClient(api_key='your_api_key')
```

#### Other Options

```python
from monday import enable_logging, disable_logging, set_log_level

# Enable with specific level and format
enable_logging(level='DEBUG', format_string='%(name)s: %(message)s')

# Change level at runtime
set_log_level('WARNING')

# Disable when done
disable_logging()
```

## Testing

This project uses `pytest` for testing and `ruff` for code quality. For development and testing, install with development dependencies:

```bash
pip install -e ".[dev]"
```

### Quick Test Commands

```bash
# Run all tests
pytest tests/

# Run only unit tests
pytest tests/ -m unit

# Run integration tests (requires API key)
pytest tests/ -m "integration and not mutation"

# Run mutation tests (requires API key)
pytest tests/ -m mutation

# Run with logging
pytest tests/ --logging=debug
```

See [docs/TESTING.md](docs/TESTING.md) for detailed testing documentation, configuration, and best practices.

## Development

This project uses these Python development tools:

- **ruff**: Fast Python linter and formatter (replaces autopep8, isort, pylint)
- **basedpyright**: Type checking
- **pre-commit**: Git hooks for code quality

### Quick Development Commands

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Linux/macOS)
source .venv/bin/activate
# Or on Windows
# .venv\Scripts\activate

# Install development dependencies
pip install --upgrade pip setuptools wheel
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Format and lint code
ruff format monday tests
ruff check monday tests

# Fix code automatically
ruff check --fix monday tests
ruff format monday tests

# Run type checking
basedpyright

# Run all quality checks
ruff format monday tests
ruff check monday tests
basedpyright
```

## Contributing

Contributions are welcome! Please open an issue or pull request on [GitHub](https://github.com/LeetCyberSecurity/monday-client) or see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

For questions or support, open an issue on [GitHub Issues](https://github.com/LeetCyberSecurity/monday-client/issues).

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](https://github.com/LeetCyberSecurity/monday-client/blob/main/LICENSE) file for details.
