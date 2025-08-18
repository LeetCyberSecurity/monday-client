# Testing Guide

This document explains the different types of tests available in the monday.com client and how to run them.

## Test Types

### 1. Unit Tests

Unit tests test individual components in isolation using mocks. They don't require external dependencies or network access.

**Characteristics:**

- Fast execution
- No external dependencies
- Use mocks for API calls
- Test individual functions and classes

**Run with:** See the [Running Tests](#running-tests) section below.

### 2. Integration Tests

Integration tests make actual API calls to monday.com to verify the client works correctly with the real API.

**Characteristics:**

- All [API-based test characteristics](#api-based-test-characteristics) below
- Read-only operations (no data modification)

**Run with:** See the [Running Tests](#running-tests) section below.

**Setup required:** See the [Integration Test Setup](#integration-test-setup) section below.

### 3. Mutation Tests

Tests that create, update, and delete data on monday.com. These require write permissions and should be run with caution.

**Characteristics:**

- All [API-based test characteristics](#api-based-test-characteristics) below
- **Modify data** - create, update, and delete operations
- Require write permissions
- **⚠️ Will create and delete real data** - use with caution

**Run with:** See the [Running Tests](#running-tests) section below.

**Setup required:** See the [Integration Test Setup](#integration-test-setup) section below.

**⚠️ Warning:** Mutation tests will create and delete real data on your monday.com account. Make sure you have a test board set up and understand the implications.

### API-based Test Characteristics

The following characteristics apply to both Integration Tests and Mutation Tests:

- Require valid API key
- Make real HTTP requests
- Test end-to-end functionality
- Slower execution
- Can be flaky due to network issues
- **Require explicit marking** - won't run automatically even when API key is set

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_boards.py

# Run specific test function
pytest tests/test_boards.py::test_query

# Run tests matching a pattern
pytest -k "query"
```

### Using Markers

```bash
# Run only unit tests
pytest tests/ -m unit

# Run only integration tests (excluding mutations)
pytest tests/ -m "integration and not mutation"

# Run mutation tests
pytest tests/ -m mutation

# Run all integration tests (including mutations)
pytest tests/ -m integration

# Run all tests (ignore markers)
pytest tests/
```

### Integration Test Setup

1. **Get an API Key:**
   - Go to your monday.com account settings
   - Navigate to Admin → API
   - Generate a new API key

2. **Set Environment Variables:**

   ```bash
   export MONDAY_API_KEY=your_api_key_here
   export MONDAY_BOARD_ID=your_test_board_id
   export MONDAY_ITEM_ID=your_test_item_id
   export MONDAY_USER_ID=your_test_user_id
   # For webhook mutation tests, provide a URL that echoes the URL verification challenge
   export MONDAY_WEBHOOK_TARGET_URL=https://your-domain.example/webhooks/monday
   ```

3. **Or Use Configuration File (Recommended):**

   ```bash
   # Copy the example configuration
   cp tests/integrations/config.example.yml tests/integrations/config.yml

   # Edit with your values
   # tests/integrations/config.yml
   monday:
     api_key: "your_actual_api_key_here"
     board_id: "123456789"
     item_id: "123456789"
     user_id: "123456789"
     webhook_target_url: "https://your-domain.example/webhooks/monday"
     # webhook_target_url must respond to monday's URL verification challenge
     # by echoing the provided JSON {"challenge": "..."} per monday docs.
     # See: https://developer.monday.com/api-reference/reference/webhooks#url-verification
   ```

4. **Run Integration Tests:**

   ```bash
   # Run all integration tests (excluding mutations)
   pytest tests/ -m "integration and not mutation"

   # Run specific integration test files
   pytest tests/integrations/test_board_integrations.py -m integration -v
   pytest tests/integrations/test_item_integrations.py -m integration -v
   pytest tests/integrations/test_user_integrations.py -m integration -v
   ```

## Test Configuration

The test configuration is defined in `pyproject.toml` under `[tool.pytest.ini_options]`:

- **Default behavior:** Runs all tests (no marker filter)
- **Markers:** Defines different test categories (unit, integration, mutation)
- **Async support:** Configured for async/await tests with `asyncio_mode = "auto"`
- **Output:** Progress-style output by default

## Code Quality

This project uses modern Python development tools:

- **ruff**: Fast Python linter and formatter (replaces autopep8, isort, pylint)
- **basedpyright**: Type checking
- **pre-commit**: Git hooks for code quality

### Code Quality Commands

```bash
# Format code
ruff format monday tests

# Lint code
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

## Test Organization

- **Unit tests**: Located in `tests/` directory (e.g., `test_boards.py`, `test_items.py`)
- **Integration tests**: Located in `tests/integrations/` directory
- **Test configuration**: `tests/conftest.py` contains shared fixtures and configuration

## Writing Tests

### Unit Test Example

```python
import pytest
from unittest.mock import AsyncMock
from monday.services.boards import Boards

@pytest.mark.asyncio
@pytest.mark.unit
async def test_boards_query():
    """Test boards query with mocked API response."""
    # Mock the API client
    mock_client = AsyncMock()
    mock_client.post_request.return_value = {
        'data': {
            'boards': [{'id': '1', 'name': 'Test Board'}]
        }
    }

    boards = Boards(mock_client)
    result = await boards.query(board_ids=1)

    assert len(result) == 1
    assert result[0].id == '1'
    assert result[0].name == 'Test Board'
```

### Integration Test Example

```python
import pytest
from monday import MondayClient

@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_api_call(client):
    """Test actual API call to monday.com."""
    # Make real API call
    boards = await client.boards.query(limit=1)

    # Verify response structure
    assert isinstance(boards, list)
    if boards:
        assert hasattr(boards[0], 'id')
        assert hasattr(boards[0], 'name')
```

### Mutation Test Example

```python
import pytest
from monday import MondayClient

@pytest.mark.integration
@pytest.mark.mutation
@pytest.mark.asyncio
async def test_create_and_delete_board(client):
    """Test creating a board and then deleting it."""
    # Create board
    board = await client.boards.create(name="Test Board")
    assert board.name == "Test Board"

    # Delete board
    result = await client.boards.delete(board_id=board.id)
    assert result.state == "deleted"
```

## Test Markers

The project uses the following pytest markers:

- `@pytest.mark.unit` - Unit tests (default, no external dependencies)
- `@pytest.mark.integration` - Integration tests (require API key and network)
- `@pytest.mark.mutation` - Mutation tests (create, update, delete data)
- `@pytest.mark.asyncio` - Async tests (automatically applied to async test functions)

### Marker Usage Rules

1. **All tests must have the `unit` marker** (except integration/mutation tests)
2. **Async tests must have both `asyncio` and `unit` markers**
3. **Integration tests must have the `integration` marker**
4. **Mutation tests must have both `integration` and `mutation` markers**

Example:

```python
# Sync unit test
@pytest.mark.unit
def test_sync_function():
    pass

# Async unit test
@pytest.mark.asyncio
@pytest.mark.unit
async def test_async_function():
    pass

# Integration test
@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration():
    pass

# Mutation test
@pytest.mark.integration
@pytest.mark.mutation
@pytest.mark.asyncio
async def test_mutation():
    pass
```

## Best Practices

### For Unit Tests

- Use mocks to isolate the code under test
- Test edge cases and error conditions
- Keep tests fast and reliable
- Use descriptive test names
- Test one thing per test function
- Always use `@pytest.mark.unit` marker

### For Integration Tests

- Use real API credentials
- Handle network failures gracefully
- Clean up any test data created
- Don't rely on specific data being present
- Use `pytest.skip()` for tests that can't run
- Always use `@pytest.mark.integration` marker

### For Mutation Tests

- Always clean up test data
- Use descriptive test names that indicate data creation/deletion
- Test in isolation when possible
- Use both `@pytest.mark.integration` and `@pytest.mark.mutation` markers
- Be aware of rate limits and API quotas

## Continuous Integration

In CI/CD pipelines:

1. **Always run unit tests** - These should be fast and reliable
2. **Optionally run integration tests** - Only if you have API credentials
3. **Skip mutation tests** - These are typically run separately or in staging environments

Example GitHub Actions workflow:

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Run code quality checks
        run: |
          ruff check monday tests
          ruff format --check monday tests
          basedpyright

      - name: Run all tests
        run: python -m pytest

      - name: Run integration tests
        if: secrets.MONDAY_API_KEY
        env:
          MONDAY_API_KEY: ${{ secrets.MONDAY_API_KEY }}
          MONDAY_TEST_BOARD_ID: ${{ secrets.MONDAY_TEST_BOARD_ID }}
        run: python -m pytest -m integration
```

## Troubleshooting

### Common Issues

1. **Import errors:** Make sure you're in the project root directory
2. **API key issues:** Verify your API key is valid and has the right permissions
3. **Network timeouts:** Integration tests may fail due to network issues
4. **Rate limiting:** Monday.com has API rate limits that may affect tests
5. **Marker errors:** Ensure all tests have appropriate markers

### Debug Mode

Run tests with more verbose output:

```bash
python -m pytest -v -s --tb=long
```

### Test Coverage

To check test coverage (requires `pytest-cov`):

```bash
pip install pytest-cov
python -m pytest --cov=monday --cov-report=html
```

This will generate an HTML coverage report in `htmlcov/index.html`.

### Logging During Tests

To enable logging during test runs:

```bash
python -m pytest --logging=info
```

This will show monday-client logs during test execution.
