# Contributing to monday-client

Thank you for your interest in contributing to monday-client! This document provides guidelines and setup instructions for contributors.

## Development Setup

### Installation

For development and testing, install with development dependencies:

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

# Install pre-commit hooks (recommended)
pre-commit install
```

### IDE Extensions (Recommended)

For the best development experience, we recommend installing these VS Code extensions:

- [**Esbonio**](https://docs.esbon.io/en/latest/): Provides  reStructuredText language server support
- [**reStructuredText**](https://docs.lextudio.com/restructuredtext/): Syntax highlighting and basic support for `.rst` files  
- [**reStructuredText Syntax Highlighting**](https://marketplace.visualstudio.com/itemsitemName=trond-snekvik.simple-rst): Enhanced syntax highlighting for RST files
- [**Ruff**](https://docs.astral.sh/ruff/): Fast Python linter and formatter integration
- [**BasedPyright**](https://docs.basedpyright.com/latest/): Type checking and IntelliSense for Python

These extensions are particularly helpful when working with the project's Sphinx documentation in the `docs/` directory and provide real-time feedback for code quality. The project's VS Code settings (`.vscode/settings.json`) are already configured to work optimally with these extensions.

**Note**: The required dependencies for these extensions (`esbonio`, `sphinx`, `rstcheck`, `ruff`, `basedpyright`) are already included in the development dependencies when you install with `pip install -e ".[dev]"`.

### Code Quality Tools

This project uses several tools to maintain code quality. All configurations are in `pyproject.toml`:

- **ruff**: Code formatting, linting, and import sorting
- **basedpyright**: Type checking

### Quick Commands

```bash
# Format code
ruff format monday tests

# Run linting
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

# Clean up cache files
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -delete
find . -type d -name "*.egg-info" -exec rm -rf {} +
```

### Testing

```bash
# Run all tests
pytest tests/

# Run only unit tests
pytest tests/ -m unit

# Run integration tests (requires API key)
pytest tests/ -m "integration and not mutation"

# Run mutation tests (requires API key)
pytest tests/ -m mutation

# Run integration and mutation tests
pytest tests/ -m integration

# Run with custom config
pytest --config /path/to/config.yml

# Run with logging
pytest --logging=debug

# Run with verbose output
pytest -v
```

### Pre-commit Hooks

The project includes pre-commit hooks that automatically run code quality checks before each commit. Install them with:

```bash
pre-commit install
```

This will ensure your code is properly formatted and passes all quality checks before committing.

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write docstrings for public functions and classes
- Keep functions focused and reasonably sized

## Testing Guidelines

- Write unit tests for new functionality
- Integration tests require a valid monday.com API key
- Use the `@pytest.mark.integration` decorator for integration tests
- Use the `@pytest.mark.mutation` decorator for tests that modify data

For detailed testing information, including setup instructions, examples, and troubleshooting, see [docs/TESTING.md](docs/TESTING.md).

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the quality checks: `ruff format monday tests && ruff check monday tests && basedpyright`
5. Run tests: `pytest tests/`
6. Commit your changes (pre-commit hooks will run automatically)
7. Push to your fork
8. Create a pull request

## Issues

When reporting issues, please include:

- Python version
- Operating system
- Error messages and stack traces
- Steps to reproduce the issue
- Expected vs actual behavior

## Questions?

If you have questions about contributing, feel free to open an issue on GitHub.
