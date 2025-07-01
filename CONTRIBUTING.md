# Contributing to monday-client

Thank you for your interest in contributing to monday-client! Your help is greatly appreciated. This guide will help you get started.

## Introduction

monday-client is an open source Python library for interacting with the monday.com API. We welcome contributions of all kinds, including bug reports, feature requests, code improvements, and documentation updates.

## How to Contribute

- **Reporting Issues:**
  - Please use [GitHub Issues](https://github.com/LeetCyberSecurity/monday-client/issues) to report bugs or request features.
  - Include as much detail as possible (steps to reproduce, environment, etc.).

- **Submitting Pull Requests:**
  - Fork the repository and create your branch from `main`.
  - Write clear, concise commit messages.
  - Ensure your code passes all tests and follows the coding standards.
  - Open a pull request with a clear description of your changes.

## Coding Standards

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code style.
- Use type hints where appropriate.
- Write clear and concise docstrings for all public classes, methods, and functions.
- Keep code readable and well-organized.

## Testing

- All code should be covered by unit tests using `pytest`.
- Run tests with:
  ```bash
  python -m pytest
  ```
- For integration/mutation tests, see the [README](README.md) for details.

## Documentation

- Update or add docstrings as needed.
- If you change the public API, update the documentation in the `docs/` directory.
- Build the docs locally with:
  ```bash
  cd docs
  make html
  ```

## Code of Conduct

Please be respectful and considerate in all interactions. For more details, see the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).

## Contact

For questions, open an issue or contact the maintainers via [GitHub Issues](https://github.com/LeetCyberSecurity/monday-client/issues). 