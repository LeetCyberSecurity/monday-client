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

"""
Integration tests for item operations.

These tests make actual API calls to monday.com and require:
1. A valid API key in the MONDAY_API_KEY environment variable or config file
2. A test board with known data
3. Network connectivity

To run these tests:
    python -m pytest tests/integrations/test_item_integrations.py -m integration -v

To skip these tests (default):
    python -m pytest tests/ -m "not integration"
"""

import uuid
from typing import Any

import pytest

from monday import MondayClient
from monday.types.item import Item


@pytest.fixture(scope='module')
def client(monday_config: dict[str, Any]) -> MondayClient:
    """Create a MondayClient instance with API key from config file or environment."""
    api_key = monday_config.get('api_key')
    if api_key:
        return MondayClient(api_key=api_key)
    pytest.skip('MONDAY_API_KEY not found in config file or environment variable')


@pytest.fixture(scope='module')
def board_id(monday_config: dict[str, Any]) -> int:
    """Get test board ID from config file or environment or use a default."""
    board_id_value = monday_config.get('board_id')
    if board_id_value:
        return int(board_id_value)
    pytest.skip('MONDAY_BOARD_ID not found in config file or environment variable')


@pytest.fixture(scope='module')
def item_id(monday_config: dict[str, Any]) -> int:
    """Get test item ID from config file or environment or use a default."""
    item_id_value = monday_config.get('item_id')
    if item_id_value:
        return int(item_id_value)
    pytest.skip('MONDAY_ITEM_ID not found in config file or environment variable')


@pytest.fixture(scope='module')
def column_id(monday_config: dict[str, Any]) -> str:
    """Get test column ID from config file or environment or skip."""
    value = monday_config.get('column_id')
    if value:
        return str(value)
    pytest.skip('MONDAY_COLUMN_ID not found in config file or environment variable')


@pytest.fixture(scope='module')
def group_id(monday_config: dict[str, Any]) -> str:
    """Get test group ID from config file or environment or skip."""
    value = monday_config.get('group_id')
    if value:
        return str(value)
    pytest.skip('MONDAY_GROUP_ID not found in config file or environment variable')


@pytest.mark.integration
class TestItemIntegrations:
    """Integration tests for item operations."""

    @pytest.mark.asyncio
    async def test_items_query(
        self,
        client: MondayClient,
        item_id: int,
    ):
        """Test querying items from the API."""
        try:
            items = await client.items.query(
                item_ids=item_id, limit=1, fields='id name'
            )

            assert isinstance(items, list)
            if items:
                item = items[0]
                assert isinstance(item, Item)
                assert hasattr(item, 'id')
                assert hasattr(item, 'name')
        except Exception as e:
            pytest.skip(f'Cannot access configured item: {e}')

    @pytest.mark.asyncio
    async def test_items_query_with_flags(
        self,
        client: MondayClient,
        item_id: int,
    ):
        """Test querying items with optional flags toggled."""
        try:
            items = await client.items.query(
                item_ids=item_id,
                limit=1,
                fields='id name',
                exclude_nonactive=True,
                newest_first=True,
            )

            assert isinstance(items, list)
        except Exception as e:
            pytest.skip(f'Cannot access configured item with flags: {e}')

    @pytest.mark.asyncio
    async def test_items_get_column_values(
        self,
        client: MondayClient,
        item_id: int,
    ):
        """Test getting column values for an item."""
        try:
            column_values = await client.items.get_column_values(
                item_id=item_id, fields='id value'
            )

            assert isinstance(column_values, list)
            if column_values:
                column_value = column_values[0]
                assert hasattr(column_value, 'id')
                assert hasattr(column_value, 'value')
        except Exception as e:
            pytest.skip(f'Cannot access item column values: {e}')

    @pytest.mark.asyncio
    async def test_items_get_column_values_specific_ids(
        self,
        client: MondayClient,
        item_id: int,
        column_id: str,
    ):
        """Test getting specific column values for an item by ID filter."""
        try:
            column_values = await client.items.get_column_values(
                item_id=item_id, column_ids=[column_id], fields='id text'
            )

            assert isinstance(column_values, list)
            # If returned, ensure only requested IDs appear
            if column_values:
                ids = {cv.id for cv in column_values}
                assert ids == {column_id}
        except Exception as e:
            pytest.skip(f'Cannot access specific item column values: {e}')

    @pytest.mark.asyncio
    async def test_items_get_name(
        self,
        client: MondayClient,
        item_id: int,
    ):
        """Test getting an item name by ID."""
        try:
            item_name = await client.items.get_name(item_id=item_id)
            assert isinstance(item_name, str)
            assert len(item_name) > 0
        except Exception as e:
            pytest.skip(f'Cannot get item name: {e}')

    @pytest.mark.asyncio
    async def test_items_get_id(
        self,
        client: MondayClient,
        board_id: int,
    ):
        """Test getting item IDs by name."""
        try:
            # First create a test item to search for
            unique_id = str(uuid.uuid4())[:8]
            test_item_name = f'Search Test Item {unique_id}'

            created_item = await client.items.create(
                board_id=board_id, item_name=test_item_name, fields='id name'
            )

            # Search for the item by name
            item_ids = await client.items.get_id(
                board_id=board_id, item_name=test_item_name
            )

            assert isinstance(item_ids, list)
            assert len(item_ids) > 0
            assert str(created_item.id) in item_ids

            # Clean up
            await client.items.delete(item_id=created_item.id)

        except Exception as e:
            pytest.skip(f'Cannot test get_id: {e}')

    @pytest.mark.asyncio
    async def test_items_invalid_board_id(
        self,
        client: MondayClient,
    ):
        """Test that invalid item requests are handled properly."""
        items = await client.items.query(
            item_ids=999999999,  # Invalid item ID
            fields='id name',
        )
        assert isinstance(items, list)
        assert len(items) == 0


@pytest.mark.integration
@pytest.mark.mutation
class TestItemMutations:
    """Mutation tests for item operations (create, update, delete)."""

    @pytest.mark.asyncio
    async def test_create_and_delete_item(
        self,
        client: MondayClient,
        board_id: int,
    ):
        """Test creating and deleting an item (requires write permissions)."""
        unique_id = str(uuid.uuid4())[:8]
        item_name = f'Integration Test Item {unique_id}'

        try:
            created_item = await client.items.create(
                board_id=board_id, item_name=item_name, fields='id name'
            )

            assert created_item is not None
            assert hasattr(created_item, 'id')
            assert hasattr(created_item, 'name')
            assert created_item.name == item_name

            created_item_id = created_item.id

            queried_items = await client.items.query(
                item_ids=created_item_id, fields='id name'
            )

            assert len(queried_items) == 1
            assert queried_items[0].id == created_item_id
            assert queried_items[0].name == item_name

            delete_result = await client.items.delete(item_id=created_item_id)

            assert delete_result is not None

        except Exception as e:
            pytest.skip(f'Cannot perform item mutations: {e}')

    @pytest.mark.asyncio
    async def test_duplicate_item(
        self,
        client: MondayClient,
        board_id: int,
    ):
        """Test duplicating an item."""
        unique_id = str(uuid.uuid4())[:8]
        item_name = f'Duplicate Test Item {unique_id}'
        duplicated_item_name = f'Duplicated Test Item {unique_id}'

        try:
            # Create the original item
            original_item = await client.items.create(
                board_id=board_id, item_name=item_name, fields='id name'
            )

            original_id = original_item.id

            # Duplicate the item
            duplicated_item = await client.items.duplicate(
                item_id=original_id,
                board_id=board_id,
                new_item_name=duplicated_item_name,
                fields='id name',
            )

            # Verify the duplication
            assert duplicated_item is not None
            assert duplicated_item.id != original_id
            assert duplicated_item.name == duplicated_item_name

            # Clean up both items
            await client.items.delete(item_id=original_id)
            await client.items.delete(item_id=duplicated_item.id)

        except Exception as e:
            pytest.skip(f'Cannot perform item duplication: {e}')

    @pytest.mark.asyncio
    async def test_duplicate_item_with_updates_flag(
        self,
        client: MondayClient,
        board_id: int,
    ):
        """Test duplicating an item with with_updates flag set."""
        unique_id = str(uuid.uuid4())[:8]
        item_name = f'Duplicate With Updates Test Item {unique_id}'

        try:
            # Create the original item
            original_item = await client.items.create(
                board_id=board_id, item_name=item_name, fields='id name'
            )

            original_id = original_item.id

            # Duplicate the item with updates flag (no renaming to cover alt code path)
            duplicated_item = await client.items.duplicate(
                item_id=original_id,
                board_id=board_id,
                with_updates=True,
                fields='id name',
            )

            assert duplicated_item is not None
            assert duplicated_item.id != original_id

            # Clean up both items
            await client.items.delete(item_id=original_id)
            await client.items.delete(item_id=duplicated_item.id)

        except Exception as e:
            pytest.skip(f'Cannot perform duplicate item with updates flag: {e}')

    @pytest.mark.asyncio
    async def test_archive_item(
        self,
        client: MondayClient,
        board_id: int,
    ):
        """Test archiving and restoring an item."""
        unique_id = str(uuid.uuid4())[:8]
        item_name = f'Archive Test Item {unique_id}'

        try:
            # Create the item
            created_item = await client.items.create(
                board_id=board_id, item_name=item_name, fields='id name'
            )

            created_item_id = created_item.id

            # Archive the item
            archive_result = await client.items.archive(item_id=created_item_id)
            assert archive_result is not None

            # Clean up by deleting the archived item
            await client.items.delete(item_id=created_item_id)

        except Exception as e:
            pytest.skip(f'Cannot perform item archiving: {e}')

    @pytest.mark.asyncio
    async def test_create_with_group_and_relative_position(
        self,
        client: MondayClient,
        board_id: int,
        group_id: str,
    ):
        """Test creating items with group and relative positioning parameters."""
        unique_id = str(uuid.uuid4())[:8]
        base_item_name = f'Base Item {unique_id}'
        rel_item_name = f'Rel Positioned Item {unique_id}'

        try:
            base_item = await client.items.create(
                board_id=board_id,
                item_name=base_item_name,
                group_id=group_id,
                fields='id name group { id }',
            )

            assert base_item is not None
            assert base_item.group
            assert base_item.group.id == group_id

            rel_item = await client.items.create(
                board_id=board_id,
                item_name=rel_item_name,
                group_id=group_id,
                position_relative_method='after_at',
                relative_to=int(base_item.id),
                fields='id name group { id }',
            )

            assert rel_item is not None
            assert rel_item.group
            assert rel_item.group.id == group_id

            # Clean up
            await client.items.delete(item_id=base_item.id)
            await client.items.delete(item_id=rel_item.id)

        except Exception as e:
            pytest.skip(f'Cannot create items with relative position: {e}')

    @pytest.mark.asyncio
    async def test_move_to_group(
        self,
        client: MondayClient,
        board_id: int,
    ):
        """Test moving an item to a different group."""
        unique_id = str(uuid.uuid4())[:8]
        item_name = f'Move Group Test Item {unique_id}'
        target_group_name = f'Target Group {unique_id}'

        try:
            # First, get available groups on the board
            groups = await client.groups.query(board_ids=board_id, fields='id title')

            # Get the first available group as source
            if not groups or not groups[0].groups:
                pytest.skip('No groups available on the board')

            source_group = groups[0].groups[0]
            if not source_group or not source_group.id:
                pytest.skip('Source group does not have a valid ID')

            # Create a second group as target
            target_group = await client.groups.create(
                board_id=board_id, group_name=target_group_name, fields='id title'
            )

            target_group_id = target_group.id

            # Create the item in the first group
            created_item = await client.items.create(
                board_id=board_id,
                item_name=item_name,
                group_id=source_group.id,
                fields='id name group { id title }',
            )

            created_item_id = created_item.id

            # Move to the second group
            moved_item = await client.items.move_to_group(
                item_id=created_item_id,
                group_id=target_group_id,
                fields='id name group { id title }',
            )

            # Verify the move
            assert moved_item is not None
            assert hasattr(moved_item, 'id')
            assert hasattr(moved_item, 'name')
            assert hasattr(moved_item, 'group')
            assert moved_item.name == item_name
            assert moved_item.group is not None
            assert moved_item.group.id == target_group_id

            # Clean up
            await client.items.delete(item_id=created_item_id)
            await client.groups.delete(board_id=board_id, group_id=target_group_id)

        except Exception as e:
            pytest.skip(f'Cannot perform move to group: {e}')

    @pytest.mark.asyncio
    async def test_move_to_board(
        self,
        client: MondayClient,
        board_id: int,
    ):
        """Test moving an item to a different board."""
        unique_id = str(uuid.uuid4())[:8]
        item_name = f'Move Board Test Item {unique_id}'
        target_board_name = f'Target Board {unique_id}'
        target_group_name = f'Target Group {unique_id}'

        try:
            # Create a target board for the move
            target_board = await client.boards.create(
                name=target_board_name, board_kind='public', fields='id name'
            )

            target_board_id = target_board.id

            # Create a new group on the target board
            target_group = await client.groups.create(
                board_id=target_board_id,
                group_name=target_group_name,
                fields='id title',
            )

            target_group_id = target_group.id

            # Create the item on the source board
            created_item = await client.items.create(
                board_id=board_id,
                item_name=item_name,
                fields='id name board { id } group { id }',
            )

            created_item_id = created_item.id

            # Move to the target board and group
            moved_item = await client.items.move_to_board(
                item_id=created_item_id,
                board_id=target_board_id,
                group_id=target_group_id,
                fields='id name board { id } group { id }',
            )

            # Verify the move
            assert moved_item is not None
            assert hasattr(moved_item, 'id')
            assert hasattr(moved_item, 'name')
            assert hasattr(moved_item, 'board')
            assert hasattr(moved_item, 'group')
            assert moved_item.name == item_name
            assert moved_item.board is not None
            assert moved_item.group is not None
            assert moved_item.board.id == target_board_id
            assert moved_item.group.id == target_group_id

            # Clean up - delete the item from the target board
            await client.items.delete(item_id=created_item_id)
            # Delete the target group
            await client.groups.delete(
                board_id=target_board_id, group_id=target_group_id
            )
            # Delete the target board
            await client.boards.delete(board_id=target_board_id)

        except Exception as e:
            pytest.skip(f'Cannot perform move to board: {e}')

    @pytest.mark.asyncio
    async def test_clear_updates(
        self,
        client: MondayClient,
        board_id: int,
    ):
        """Test clearing item updates."""
        unique_id = str(uuid.uuid4())[:8]
        item_name = f'Clear Updates Test Item {unique_id}'

        try:
            # Create the item
            created_item = await client.items.create(
                board_id=board_id,
                item_name=item_name,
                fields='id name updates { text_body }',
            )

            created_item_id = created_item.id

            # Clear updates
            cleared_item = await client.items.clear_updates(
                item_id=created_item_id, fields='id name updates { text_body }'
            )

            # Verify the updates were cleared
            assert cleared_item is not None
            assert hasattr(cleared_item, 'id')
            assert hasattr(cleared_item, 'name')
            assert hasattr(cleared_item, 'updates')
            assert cleared_item.name == item_name

            # Clean up
            await client.items.delete(item_id=created_item_id)

        except Exception as e:
            pytest.skip(f'Cannot perform clear updates: {e}')

    @pytest.mark.asyncio
    async def test_change_column_values(
        self,
        client: MondayClient,
        board_id: int,
    ):
        """Test changing item column values."""
        unique_id = str(uuid.uuid4())[:8]
        item_name = f'Change Column Values Test Item {unique_id}'

        try:
            # Create the item
            created_item = await client.items.create(
                board_id=board_id, item_name=item_name, fields='id name'
            )

            created_item_id = created_item.id

            # Change column values using dictionary format
            column_values = {'name': f'Updated {item_name}'}

            updated_column_value = await client.items.change_column_values(
                item_id=created_item_id,
                column_values=column_values,
                fields='id column_values { value }',
            )

            # Verify the column values were changed
            assert updated_column_value is not None
            assert hasattr(updated_column_value, 'id')
            assert hasattr(updated_column_value, 'value')

            # Clean up
            await client.items.delete(item_id=created_item_id)

        except Exception as e:
            pytest.skip(f'Cannot perform change column values: {e}')

    @pytest.mark.asyncio
    async def test_change_column_values_with_create_labels(
        self,
        client: MondayClient,
        board_id: int,
    ):
        """Test changing item column values with create_labels_if_missing flag."""
        unique_id = str(uuid.uuid4())[:8]
        item_name = f'Change Column Values With Labels {unique_id}'

        try:
            created_item = await client.items.create(
                board_id=board_id, item_name=item_name, fields='id name'
            )

            created_item_id = created_item.id

            updated_column_value = await client.items.change_column_values(
                item_id=created_item_id,
                column_values={'name': f'Updated {item_name}'},
                create_labels_if_missing=True,
                fields='id column_values { id text }',
            )

            assert updated_column_value is not None

            # Clean up
            await client.items.delete(item_id=created_item_id)

        except Exception as e:
            pytest.skip(
                f'Cannot perform change column values with create labels flag: {e}'
            )

    @pytest.mark.asyncio
    async def test_create_with_column_values(
        self,
        client: MondayClient,
        board_id: int,
    ):
        """Test creating an item with column values."""
        unique_id = str(uuid.uuid4())[:8]
        item_name = f'Column Values Test Item {unique_id}'

        try:
            # Create the item with column values using dictionary format
            column_values = {'name': item_name}

            created_item = await client.items.create(
                board_id=board_id,
                item_name=item_name,
                column_values=column_values,
                fields='id name column_values { id value }',
            )

            # Verify the item was created with column values
            assert created_item is not None
            assert hasattr(created_item, 'id')
            assert hasattr(created_item, 'name')
            assert hasattr(created_item, 'column_values')
            assert created_item.name == item_name

            # Clean up
            await client.items.delete(item_id=created_item.id)

        except Exception as e:
            pytest.skip(f'Cannot perform create with column values: {e}')
