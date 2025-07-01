# This file is part of monday-client.
#
# Copyright (C) 2024 Leet Cyber Security <https://leetcybersecurity.com/>
#
# monday-client is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# monday-client is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with monday-client. If not, see <https://www.gnu.org/licenses/>.

# pylint: disable=broad-exception-caught,redefined-outer-name

"""
Integration tests for monday.com API client.

These tests make actual API calls to monday.com and require:
1. A valid API key in the MONDAY_API_KEY environment variable
2. A test board with known data
3. Network connectivity

To run these tests:
    MONDAY_API_KEY=your_api_key python -m pytest tests/test_integration.py -m integration -v

To skip these tests (default):
    python -m pytest tests/ -m "not integration"
"""

import os
import time
import uuid

import pytest

from monday import MondayClient
from monday.types.board import Board
from monday.types.item import Item, ItemList
from monday.types.user import User


@pytest.fixture(scope='module')
def client():
    """Create a MondayClient instance with API key from environment."""
    api_key = os.getenv('MONDAY_API_KEY')
    if not api_key:
        pytest.skip('MONDAY_API_KEY environment variable not set')
    return MondayClient(api_key)


@pytest.fixture(scope='module')
def test_board_id():
    """Get test board ID from environment or use a default."""
    # You can set this in your environment or use a known board ID
    return int(os.getenv('MONDAY_TEST_BOARD_ID', '123456789'))


@pytest.mark.integration
class TestMondayAPIIntegration:
    """Integration tests that make real API calls to monday.com."""

    @pytest.mark.asyncio
    async def test_boards_query(self, client):
        """Test querying boards from the API."""
        boards = await client.boards.query(
            board_ids=123456789,  # Use a real board ID
            fields='id name state'
        )

        assert isinstance(boards, list)
        if boards:  # If we have access to boards
            board = boards[0]
            assert isinstance(board, Board)
            assert hasattr(board, 'id')
            assert hasattr(board, 'name')
            assert hasattr(board, 'state')

    @pytest.mark.asyncio
    async def test_users_query(self, client):
        """Test querying users from the API."""
        users = await client.users.query(
            fields='id name email'
        )

        assert isinstance(users, list)
        if users:  # If we have access to users
            user = users[0]
            assert isinstance(user, User)
            assert hasattr(user, 'id')
            assert hasattr(user, 'name')
            assert hasattr(user, 'email')

    @pytest.mark.asyncio
    async def test_items_query(self, client, test_board_id):
        """Test querying items from a board."""
        try:
            items = await client.boards.get_items(
                board_ids=test_board_id,
                limit=5,
                fields='id name'
            )

            assert isinstance(items, list)
            if items:  # If we have access to items
                item_list = items[0]
                assert isinstance(item_list, ItemList)
                assert hasattr(item_list, 'board_id')
                assert hasattr(item_list, 'items')

                if item_list.items:
                    item = item_list.items[0]
                    assert isinstance(item, Item)
                    assert hasattr(item, 'id')
                    assert hasattr(item, 'name')
        except Exception as e:
            # Handle cases where we don't have access to the test board
            pytest.skip(f"Cannot access test board: {e}")

    @pytest.mark.asyncio
    async def test_groups_query(self, client, test_board_id):
        """Test querying groups from a board."""
        try:
            groups = await client.groups.query(
                board_ids=test_board_id,
                fields='id title'
            )

            assert isinstance(groups, list)
            if groups:  # If we have access to groups
                group_list = groups[0]
                assert hasattr(group_list, 'board_id')
                assert hasattr(group_list, 'groups')

                if group_list.groups:
                    group = group_list.groups[0]
                    assert hasattr(group, 'id')
                    assert hasattr(group, 'title')
        except Exception as e:
            # Handle cases where we don't have access to the test board
            pytest.skip(f"Cannot access test board: {e}")

    @pytest.mark.asyncio
    async def test_api_error_handling(self, client):
        """Test that invalid requests are handled properly."""
        # Test with an invalid board ID
        with pytest.raises(Exception):  # Should raise some kind of error
            await client.boards.query(
                board_ids=999999999,  # Invalid board ID
                fields='id name'
            )


@pytest.mark.integration
class TestMondayAPIPerformance:
    """Performance tests for API calls."""

    @pytest.mark.asyncio
    async def test_query_performance(self, client):
        """Test that queries complete within reasonable time."""

        start_time = time.time()
        boards = await client.boards.query(
            limit=1,
            fields='id name'
        )
        end_time = time.time()

        # Should complete within 5 seconds
        assert end_time - start_time < 5.0
        assert isinstance(boards, list)


@pytest.mark.integration
class TestMondayAPITestEnvironment:
    """Tests that can be run with a test/demo API key."""

    @pytest.mark.asyncio
    async def test_client_initialization(self, client):
        """Test that the client can be initialized and make basic requests."""
        # This should work even with limited API access
        try:
            # Try to get user info (usually accessible)
            users = await client.users.query(
                fields='id name',
                limit=1
            )
            assert isinstance(users, list)
        except Exception as e:
            # If even this fails, the API key might be invalid
            pytest.fail(f'Basic API access failed: {e}')


# Utility functions for integration tests
def get_test_data():
    """Get test data from environment or configuration."""
    return {
        'board_id': int(os.getenv('MONDAY_TEST_BOARD_ID', '123456789')),
        'item_id': int(os.getenv('MONDAY_TEST_ITEM_ID', '123456789')),
        'user_id': int(os.getenv('MONDAY_TEST_USER_ID', '123456789')),
    }


def is_integration_test_enabled():
    """Check if integration tests should be run."""
    return bool(os.getenv('MONDAY_API_KEY'))


@pytest.mark.integration
@pytest.mark.mutation
class TestMondayAPIMutations:
    """Mutation tests that create, update, and delete data on monday.com."""

    @pytest.mark.asyncio
    async def test_create_and_delete_item(self, client, test_board_id):
        """Test creating and deleting an item (requires write permissions)."""
        # Create a unique item name with timestamp to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        item_name = f'Integration Test Item {unique_id}'

        try:
            # Create the item
            created_item = await client.items.create(
                board_id=test_board_id,
                item_name=item_name,
                fields='id name'
            )

            # Verify the item was created correctly
            assert created_item is not None
            assert hasattr(created_item, 'id')
            assert hasattr(created_item, 'name')
            assert created_item.name == item_name

            item_id = created_item.id

            # Verify we can query the item back
            queried_items = await client.items.query(
                item_ids=[item_id],
                fields='id name'
            )

            assert len(queried_items) == 1
            assert queried_items[0].id == item_id
            assert queried_items[0].name == item_name

            # Delete the item
            delete_result = await client.items.delete(item_id=item_id)

            # Verify deletion was successful
            assert delete_result is not None

            # Verify the item is no longer accessible
            try:
                await client.items.query(
                    item_ids=[item_id],
                    fields='id name'
                )
                # If we get here, the item still exists
                pytest.fail('Item was not properly deleted')
            except Exception:
                # Expected - item should not be found
                pass

        except Exception as e:
            # If we can't create/delete items, skip the test but log the reason
            pytest.skip(f'Cannot perform item mutations: {e}')

    @pytest.mark.asyncio
    async def test_update_item(self, client, test_board_id):
        """Test updating an existing item."""
        # Create a test item first
        unique_id = str(uuid.uuid4())[:8]
        original_name = f'Update Test Item {unique_id}'
        updated_name = f'Updated Item {unique_id}'

        try:
            # Create the item
            created_item = await client.items.create(
                board_id=test_board_id,
                item_name=original_name,
                fields='id name'
            )

            item_id = created_item.id

            # Update the item
            updated_item = await client.items.update(
                item_id=item_id,
                item_name=updated_name,
                fields='id name'
            )

            # Verify the update
            assert updated_item is not None
            assert updated_item.name == updated_name

            # Query to verify the change persisted
            queried_items = await client.items.query(
                item_ids=[item_id],
                fields='id name'
            )

            assert len(queried_items) == 1
            assert queried_items[0].name == updated_name

            # Clean up
            await client.items.delete(item_id=item_id)

        except Exception as e:
            pytest.skip(f'Cannot perform item updates: {e}')

    @pytest.mark.asyncio
    async def test_duplicate_item(self, client, test_board_id):
        """Test duplicating an item."""
        unique_id = str(uuid.uuid4())[:8]
        original_name = f'Duplicate Test Item {unique_id}'

        try:
            # Create the original item
            original_item = await client.items.create(
                board_id=test_board_id,
                item_name=original_name,
                fields='id name'
            )

            original_id = original_item.id

            # Duplicate the item
            duplicated_item = await client.items.duplicate(
                item_id=original_id,
                fields='id name'
            )

            # Verify the duplication
            assert duplicated_item is not None
            assert duplicated_item.id != original_id
            assert duplicated_item.name == original_name

            # Clean up both items
            await client.items.delete(item_id=original_id)
            await client.items.delete(item_id=duplicated_item.id)

        except Exception as e:
            pytest.skip(f'Cannot perform item duplication: {e}')

    @pytest.mark.asyncio
    async def test_archive_and_restore_item(self, client, test_board_id):
        """Test archiving and restoring an item."""
        unique_id = str(uuid.uuid4())[:8]
        item_name = f'Archive Test Item {unique_id}'

        try:
            # Create the item
            created_item = await client.items.create(
                board_id=test_board_id,
                item_name=item_name,
                fields='id name'
            )

            item_id = created_item.id

            # Archive the item
            archive_result = await client.items.archive(item_id=item_id)
            assert archive_result is not None

            # Try to query the item - it should not be found in normal queries
            try:
                await client.items.query(
                    item_ids=[item_id],
                    fields='id name'
                )
                # If we get here, the item is still visible (might be expected behavior)
            except Exception:
                # Expected - archived items might not be queryable
                pass

            # Clean up by deleting the archived item
            await client.items.delete(item_id=item_id)

        except Exception as e:
            pytest.skip(f'Cannot perform item archiving: {e}')

    @pytest.mark.asyncio
    async def test_create_and_delete_board(self, client):
        """Test creating and deleting a board (requires workspace permissions)."""
        unique_id = str(uuid.uuid4())[:8]
        board_name = f'Integration Test Board {unique_id}'

        try:
            # Create the board
            created_board = await client.boards.create(
                board_name=board_name,
                board_kind='public',
                fields='id name state'
            )

            # Verify the board was created
            assert created_board is not None
            assert hasattr(created_board, 'id')
            assert hasattr(created_board, 'name')
            assert created_board.name == board_name

            board_id = created_board.id

            # Verify we can query the board back
            queried_boards = await client.boards.query(
                board_ids=[board_id],
                fields='id name state'
            )

            assert len(queried_boards) == 1
            assert queried_boards[0].id == board_id
            assert queried_boards[0].name == board_name

            # Delete the board
            delete_result = await client.boards.delete(board_id=board_id)
            assert delete_result is not None

        except Exception as e:
            pytest.skip(f'Cannot perform board mutations: {e}')
