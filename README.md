# Monday.com API Client

This Python library provides a convenient way to interact with the Monday.com API.

Key features include:
- Automatic handling of API rate limits and query limits
- Easy-to-use methods for common Monday.com operations
- Ability to send fully customizable requests with all Monday.com method arguments and fields available to the user 

## Installation

You can install the library from this private repo using pip:

```bash
pip install git+ssh://git@github.com/LeetCyberSecurity/monday-client
```

## Quick Start

```python
from monday import MondayClient

client = MondayClient(api_key='your_api_key_here')

boards = client.boards.query(board_ids=[1234567890, 1234567891])

items_page = client.items.items_page(board_ids=[1234567890, 1234567891])
```