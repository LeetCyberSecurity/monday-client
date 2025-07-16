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

from monday import MondayClient

async def main():
    client = MondayClient(api_key='your_api_key_here')

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

### Use predefined field sets for more data

```python
import asyncio

from monday import MondayClient
from monday.fields import BoardFields, ItemFields

async def main():
    client = MondayClient(api_key='your_api_key_here')

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

from monday import MondayClient, QueryParams, QueryRule

async def main():
    client = MondayClient(api_key='your_api_key_here')

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

from monday import MondayClient
from monday.types import DateInput, StatusInput, TextInput

async def main():
    client = MondayClient(api_key='your_api_key_here')

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

The client uses a logger named `monday` for all logging operations. By default, logging is suppressed. To enable logging:

```python
import logging
from monday import MondayClient

# Remove the default NullHandler and add a real handler
monday_logger = logging.getLogger('monday')
for handler in monday_logger.handlers[:]:
    if isinstance(handler, logging.NullHandler):
        monday_logger.removeHandler(handler)

if not monday_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    monday_logger.addHandler(handler)

client = MondayClient('your_api_key')
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
