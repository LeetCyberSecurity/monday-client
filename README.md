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

## Column Value Classes

For better type safety when updating column values, use the provided input classes:

```python
from monday.types.column_inputs import DateInput, StatusInput, TextInput, NumberInput

await client.items.change_column_values(
    item_id=123456789,
    column_values=[
        DateInput('date_column_id', '2024-01-15', '14:30:00'),
        StatusInput('status_column_id', 'Working on it'),
        TextInput('text_column_id', 'Updated content'),
        NumberInput('number_column_id', 42.5)
    ]
)
```

See the [documentation](https://monday-client.readthedocs.io) for all available column input types.

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

See the [documentation](https://monday-client.readthedocs.io) for advanced logging configuration.

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
pytest --logging=debug
```

See [docs/TESTING.md](docs/TESTING.md) for detailed testing documentation, configuration, and best practices.

## Development

This project uses modern Python development tools:

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

# Run tests
pytest tests/
```

## Contributing

Contributions are welcome! Please open an issue or pull request on [GitHub](https://github.com/LeetCyberSecurity/monday-client) or see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

For questions or support, open an issue on [GitHub Issues](https://github.com/LeetCyberSecurity/monday-client/issues).

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](https://github.com/LeetCyberSecurity/monday-client/blob/main/LICENSE) file for details.
