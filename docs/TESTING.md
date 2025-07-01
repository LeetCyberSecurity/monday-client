# Testing Guide

This document explains the different types of tests available in the monday.com client and how to run them.

## Test Types

### 1. Unit Tests (Default)
Unit tests test individual components in isolation using mocks. They don't require external dependencies or network access.

**Characteristics:**
- Fast execution
- No external dependencies
- Use mocks for API calls
- Test individual functions and classes
- Run by default

**Run with:**
```bash
python -m pytest tests/
```

### 2. Integration Tests
Integration tests make actual API calls to monday.com to verify the client works correctly with the real API.

**Characteristics:**
- Require valid API key
- Make real HTTP requests
- Test end-to-end functionality
- Slower execution
- Can be flaky due to network issues
- **Require explicit marking** - won't run automatically even when API key is set

**Run with:**
```bash
# Set up environment variables
export MONDAY_API_KEY=your_api_key
export MONDAY_TEST_BOARD_ID=123456789

# Run integration tests (requires -m integration flag)
python -m pytest -m integration

# Run specific integration test file
python -m pytest tests/test_integration.py -m integration -v

# Run with verbose output
python -m pytest tests/test_integration.py -m integration -v -s
```

### 3. Performance Tests
Tests that verify the client performs well under various conditions.

**Run with:**
```bash
python -m pytest -m performance
```

### 4. Mutation Tests
Tests that create, update, and delete data on monday.com. These require write permissions and should be run with caution.

**Run with:**
```bash
# Run only mutation tests
python -m pytest -m mutation

# Run integration tests including mutations
python -m pytest -m "integration and mutation"
```

**⚠️ Warning:** Mutation tests will create and delete real data on your monday.com account. Make sure you have a test board set up and understand the implications.

## Running Tests

### Basic Commands

```bash
# Run all unit tests (default)
python -m pytest

# Run with verbose output
python -m pytest -v

# Run specific test file
python -m pytest tests/test_boards.py

# Run specific test function
python -m pytest tests/test_boards.py::test_query

# Run tests matching a pattern
python -m pytest -k "query"
```

### Using Markers

```bash
# Run only unit tests
python -m pytest -m "not integration"

# Run only integration tests
python -m pytest -m integration

# Run integration tests but skip slow ones
python -m pytest -m "integration and not slow"

# Run performance tests
python -m pytest -m performance
```

### Integration Test Setup

1. **Get an API Key:**
   - Go to your monday.com account settings
   - Navigate to Admin → API
   - Generate a new API key

2. **Set Environment Variables:**
   ```bash
   export MONDAY_API_KEY=your_api_key_here
   export MONDAY_TEST_BOARD_ID=your_test_board_id
   ```

3. **Run Integration Tests:**
   ```bash
   # Run all integration tests
   python -m pytest -m integration -v
   
   # Run specific integration test file
   python -m pytest tests/test_integration.py -m integration -v
   
   # Run with verbose output and show print statements
   python -m pytest tests/test_integration.py -m integration -v -s
   ```

## Test Configuration

The test configuration is defined in `pyproject.toml` under `[tool.pytest.ini_options]`:

- **Default behavior:** Runs only unit tests (excludes integration and slow tests)
- **Markers:** Defines different test categories
- **Async support:** Configured for async/await tests
- **Output:** Progress-style output by default

## Writing Tests

### Unit Test Example

```python
import pytest
from unittest.mock import Mock, patch
from monday.services.boards import Boards

@pytest.mark.asyncio
async def test_boards_query():
    """Test boards query with mocked API response."""
    # Mock the API client
    mock_client = Mock()
    mock_client.execute_query.return_value = {
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
import os
from monday import MondayClient

@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_api_call():
    """Test actual API call to monday.com."""
    client = MondayClient(os.getenv('MONDAY_API_KEY'))
    
    # Make real API call
    boards = await client.boards.query(limit=1)
    
    # Verify response structure
    assert isinstance(boards, list)
    if boards:
        assert hasattr(boards[0], 'id')
        assert hasattr(boards[0], 'name')
```

## Best Practices

### For Unit Tests
- Use mocks to isolate the code under test
- Test edge cases and error conditions
- Keep tests fast and reliable
- Use descriptive test names
- Test one thing per test function

### For Integration Tests
- Use real API credentials
- Handle network failures gracefully
- Clean up any test data created
- Don't rely on specific data being present
- Use `pytest.skip()` for tests that can't run

### For Performance Tests
- Set reasonable timeouts
- Test with realistic data sizes
- Measure both success and failure scenarios
- Consider rate limiting

## Continuous Integration

In CI/CD pipelines:

1. **Always run unit tests** - These should be fast and reliable
2. **Optionally run integration tests** - Only if you have API credentials
3. **Skip performance tests** - These are typically run separately

Example GitHub Actions workflow:

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: pip install -e ".[dev]"
      
      - name: Run unit tests
        run: python -m pytest -m "not integration"
      
      - name: Run integration tests
        if: secrets.MONDAY_API_KEY
        env:
          MONDAY_API_KEY: ${{ secrets.MONDAY_API_KEY }}
        run: python -m pytest -m integration
```

## Troubleshooting

### Common Issues

1. **Import errors:** Make sure you're in the project root directory
2. **API key issues:** Verify your API key is valid and has the right permissions
3. **Network timeouts:** Integration tests may fail due to network issues
4. **Rate limiting:** Monday.com has API rate limits that may affect tests

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