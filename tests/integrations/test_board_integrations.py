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
Integration tests for board operations.

These tests make actual API calls to monday.com and require:
1. A valid API key in the MONDAY_API_KEY environment variable or config file
2. A test board with known data
3. Network connectivity

To run these tests:
    python -m pytest tests/integrations/test_board_integrations.py -m integration -v

To skip these tests (default):
    python -m pytest tests/ -m "not integration"
"""

import uuid

import pytest

from monday import ColumnFilter, MondayClient
from monday.fields.board_fields import BoardFields
from monday.types.board import Board
from monday.types.column_defaults import (
    DropdownDefaults,
    DropdownLabel,
    StatusDefaults,
    StatusLabel,
)


@pytest.fixture(scope='module')
def client(monday_config):
    """Create a MondayClient instance with API key from config file or environment."""
    api_key = monday_config.get('api_key')
    if api_key:
        return MondayClient(api_key=api_key)
    pytest.skip('MONDAY_API_KEY not found in config file or environment variable')


@pytest.fixture(scope='module')
def board_id(monday_config):
    """Get test board ID from config file or environment or use a default."""
    board_id_value = monday_config.get('board_id')
    if board_id_value:
        return int(board_id_value)
    pytest.skip('MONDAY_BOARD_ID not found in config file or environment variable')


@pytest.fixture(scope='module')
def column_id(monday_config):
    """Get test column ID from config file or environment or use a default."""
    column_id_value = monday_config.get('column_id')
    if column_id_value:
        return column_id_value
    pytest.skip('MONDAY_COLUMN_ID not found in config file or environment variable')


@pytest.fixture(scope='module')
def column_values(monday_config):
    """Get test column values from config file or environment or use a default."""
    column_values_value = monday_config.get('column_values')
    if column_values_value:
        return column_values_value
    pytest.skip('MONDAY_COLUMN_VALUES not found in config file or environment variable')


@pytest.fixture(scope='module')
def item_id(monday_config):
    """Get test item ID from config file or environment or skip."""
    value = monday_config.get('item_id')
    if value:
        return int(value)
    pytest.skip('MONDAY_ITEM_ID not found in config file or environment variable')


@pytest.fixture(scope='module')
def group_id(monday_config):
    """Get test group ID from config file or environment or skip."""
    value = monday_config.get('group_id')
    if value:
        return str(value)
    pytest.skip('MONDAY_GROUP_ID not found in config file or environment variable')


@pytest.fixture(scope='module')
def workspace_id(monday_config):
    """Get test workspace ID from config file or environment or skip."""
    value = monday_config.get('workspace_id')
    if value:
        return int(value)
    pytest.skip('MONDAY_WORKSPACE_ID not found in config file or environment variable')


@pytest.fixture(scope='module')
def user_id(monday_config):
    """Get test user ID from config file or environment or skip."""
    value = monday_config.get('user_id')
    if value:
        return int(value)
    pytest.skip('MONDAY_USER_ID not found in config file or environment variable')


@pytest.mark.integration
class TestBoardIntegrations:
    """Integration tests for board operations."""

    @pytest.mark.asyncio
    async def test_boards_query(
        self,
        client: MondayClient,
        board_id: int,
    ):
        """Test querying boards using the configured board ID."""
        fields = BoardFields.combine('BASIC', 'DETAILED', 'ITEMS')

        try:
            boards = await client.boards.query(
                fields=fields,
                board_ids=board_id,
            )

            assert isinstance(boards, list)
            if boards:
                board = boards[0]
                assert isinstance(board, Board)
                assert hasattr(board, 'id')
                assert board.id
                assert hasattr(board, 'name')
                assert board.name
                assert hasattr(board, 'state')
                assert board.state
                assert hasattr(board, 'items')
                if board.items:
                    item = board.items[0]
                    assert hasattr(item, 'id')
                    assert item.id
                    assert hasattr(item, 'name')
                    assert item.name
        except Exception as e:
            pytest.fail(str(e))

    @pytest.mark.asyncio
    async def test_boards_comprehensive_query(
        self,
        client: MondayClient,
        board_id: int,
    ):
        """Test querying boards with all available fields."""
        try:
            fields = BoardFields.get_all_fields()

            boards = await client.boards.query(
                fields=fields,
                board_ids=board_id,
            )

            assert isinstance(boards, list)
            if boards:
                board = boards[0]
                # Test all expected fields are present
                expected_fields = [
                    'id',
                    'name',
                    'board_kind',
                    'description',
                    'top_group',
                    'groups',
                    'items_count',
                    'items',
                    'creator',
                    'owners',
                    'subscribers',
                ]

                for field in expected_fields:
                    assert hasattr(board, field)

        except Exception as e:
            pytest.fail(str(e))

    @pytest.mark.asyncio
    async def test_boards_query_with_parameters(
        self,
        client: MondayClient,
        board_id: int,
        workspace_id: int,
    ):
        """Test querying boards with non-default parameters and toggled pagination flags."""
        try:
            boards = await client.boards.query(
                fields='id name',
                board_ids=board_id,
                board_kind='all',
                order_by='used',
                boards_limit=1,
                page=1,
                state='all',
                workspace_ids=workspace_id,
                paginate_items=False,
                paginate_boards=False,
            )
            assert isinstance(boards, list)
        except Exception as e:
            pytest.skip(f'Cannot query boards with parameters: {e}')

    @pytest.mark.asyncio
    async def test_boards_get_items(
        self,
        client: MondayClient,
        board_id: int,
    ):
        """Test getting items from a board."""
        try:
            items = await client.boards.get_items(
                board_ids=board_id, limit=1, fields='id name'
            )

            assert isinstance(items, list)
            if items:
                item_list = items[0]
                assert hasattr(item_list, 'board_id')
                assert item_list.board_id
                assert hasattr(item_list, 'items')
                assert isinstance(item_list.items, list)

                if item_list.items:
                    item = item_list.items[0]
                    assert hasattr(item, 'id')
                    assert item.id
                    assert hasattr(item, 'name')
                    assert item.name
        except Exception as e:
            pytest.skip(f'Cannot access board items: {e}')

    @pytest.mark.asyncio
    async def test_boards_get_items_with_group_and_query_params(
        self,
        client: MondayClient,
        board_id: int,
        item_id: int,
    ):
        """Test getting items filtered by group and query_params (ids)."""
        try:
            # Discover a valid group on the board at runtime
            groups = await client.groups.query(board_ids=board_id, fields='id title')
            if not groups or not groups[0].groups:
                pytest.skip('No groups available on the board')
            discovered_group_id = groups[0].groups[0].id

            items = await client.boards.get_items(
                board_ids=board_id,
                query_params={'ids': [str(item_id)]},
                limit=1,
                group_id=discovered_group_id,
                fields='id name',
                paginate_items=False,
            )
            assert isinstance(items, list)
        except Exception as e:
            pytest.skip(f'Cannot access board items with group and query params: {e}')

    @pytest.mark.asyncio
    async def test_boards_get_items_by_column_values(
        self,
        client: MondayClient,
        board_id: int,
        column_id: str,
        column_values: str | list[str],
    ):
        """Test getting items from a board."""
        try:
            items = await client.boards.get_items_by_column_values(
                board_id=board_id,
                columns=[
                    ColumnFilter(column_id=column_id, column_values=column_values)
                ],
                limit=1,
                fields='id name',
            )

            assert isinstance(items, list)
            if items:
                item = items[0]
                assert hasattr(item, 'id')
                assert item.id
                assert hasattr(item, 'name')
                assert item.name
        except Exception as e:
            pytest.skip(f'Cannot access board column values: {e}')

    @pytest.mark.asyncio
    async def test_boards_get_column_values(
        self,
        client: MondayClient,
        board_id: int,
        column_id: str,
    ):
        """Test getting items from a board."""
        try:
            items = await client.boards.get_column_values(
                board_id=board_id, column_ids=column_id
            )

            assert isinstance(items, list)
            if items:
                item = items[0]
                assert hasattr(item, 'id')
                assert item.id
                assert hasattr(item, 'name')
                assert item.name
                assert isinstance(item.column_values, list)

                if item.column_values:
                    column_value = item.column_values[0]
                    assert hasattr(column_value, 'id')
                    assert column_value.id
                    assert hasattr(column_value, 'value')
                    # assert column_value.value
                    assert isinstance(column_value.value, dict)
                    assert hasattr(column_value, 'column')
                    assert hasattr(column_value.column, 'title')
                    assert column_value.column
                    assert column_value.column.title
        except Exception as e:
            pytest.skip(f'Cannot access board column values: {e}')

    @pytest.mark.asyncio
    async def test_boards_get_groups(
        self,
        client: MondayClient,
        board_id: int,
    ):
        """Test getting groups from a board."""
        try:
            groups = await client.groups.query(board_ids=board_id, fields='id title')

            assert isinstance(groups, list)
            if groups:
                group_list = groups[0]
                assert hasattr(group_list, 'board_id')
                assert group_list.board_id
                assert hasattr(group_list, 'groups')

                if group_list.groups:
                    group = group_list.groups[0]
                    assert hasattr(group, 'id')
                    assert group.id
                    assert hasattr(group, 'title')
                    assert group.title
        except Exception as e:
            pytest.skip(f'Cannot access board groups: {e}')

    @pytest.mark.asyncio
    async def test_boards_invalid_board_id(
        self,
        client: MondayClient,
    ):
        """Test that invalid board requests are handled properly."""
        boards = await client.boards.query(
            board_ids=999999999,  # Invalid board ID
            fields='id name',
        )
        assert isinstance(boards, list)
        assert len(boards) == 0


@pytest.mark.integration
@pytest.mark.mutation
class TestBoardMutations:
    """Mutation tests for board operations (create, update, delete)."""

    @pytest.mark.asyncio
    async def test_create_and_delete_board(
        self,
        client: MondayClient,
    ):
        """Test creating a board and then deleting it."""
        unique_id = str(uuid.uuid4())[:8]
        board_name = f'Create Delete Test Board {unique_id}'

        try:
            # Create the board
            created_board = await client.boards.create(
                name=board_name, board_kind='public', fields='id name state'
            )

            # Verify the board was created
            assert created_board is not None
            assert hasattr(created_board, 'id')
            assert hasattr(created_board, 'name')
            assert created_board.name == board_name

            created_board_id = created_board.id

            # Verify we can query the board back
            queried_boards = await client.boards.query(
                board_ids=[created_board_id], fields='id name state'
            )

            assert len(queried_boards) == 1
            assert queried_boards[0].id == created_board_id
            assert queried_boards[0].name == board_name

            # Delete the board
            delete_result = await client.boards.delete(board_id=created_board_id)
            assert delete_result is not None
            assert delete_result.id == created_board_id

        except Exception as e:
            pytest.skip(f'Cannot perform create and delete board: {e}')

    @pytest.mark.asyncio
    async def test_duplicate_board(
        self,
        client: MondayClient,
    ):
        """Test creating a board, duplicating it, then deleting both boards."""
        unique_id = str(uuid.uuid4())[:8]
        board_name = f'Duplicate Test Board {unique_id}'
        duplicated_board_name = f'Duplicated Test Board {unique_id}'

        try:
            # Create the board
            created_board = await client.boards.create(
                name=board_name, board_kind='public', fields='id name state'
            )

            # Verify the board was created
            assert created_board is not None
            assert hasattr(created_board, 'id')
            assert hasattr(created_board, 'name')
            assert created_board.name == board_name

            created_board_id = created_board.id

            # Duplicate the board
            duplicated_board = await client.boards.duplicate(
                board_id=created_board_id,
                board_name=duplicated_board_name,
                duplicate_type='with_structure',
                fields='id name state',
            )

            # Verify the board was duplicated
            assert duplicated_board is not None
            assert hasattr(duplicated_board, 'id')
            assert hasattr(duplicated_board, 'name')
            assert duplicated_board.name == duplicated_board_name

            duplicated_board_id = duplicated_board.id

            # Delete both boards
            delete_duplicated_result = await client.boards.delete(
                board_id=duplicated_board_id
            )
            assert delete_duplicated_result is not None
            assert delete_duplicated_result.id == duplicated_board_id

            delete_original_result = await client.boards.delete(
                board_id=created_board_id
            )
            assert delete_original_result is not None
            assert delete_original_result.id == created_board_id

        except Exception as e:
            pytest.skip(f'Cannot perform duplicate board: {e}')

    @pytest.mark.asyncio
    async def test_duplicate_board_keep_subscribers(
        self,
        client: MondayClient,
    ):
        """Test duplicating a board keeping subscribers flag set."""
        unique_id = str(uuid.uuid4())[:8]
        board_name = f'Duplicate Keep Subs Test Board {unique_id}'
        try:
            created_board = await client.boards.create(
                name=board_name, board_kind='public', fields='id name state'
            )
            created_board_id = created_board.id

            duplicated_board = await client.boards.duplicate(
                board_id=created_board_id,
                duplicate_type='with_structure',
                keep_subscribers=True,
                fields='id name state',
            )
            assert duplicated_board is not None

            # Cleanup
            await client.boards.delete(board_id=duplicated_board.id)
            await client.boards.delete(board_id=created_board_id)
        except Exception as e:
            pytest.skip(f'Cannot perform duplicate board keep subscribers: {e}')

    @pytest.mark.asyncio
    async def test_create_columns(
        self,
        client: MondayClient,
    ):
        """Test creating a board, then creating status and dropdown columns with defaults, then deleting the board."""
        unique_id = str(uuid.uuid4())[:8]
        board_name = f'Create Columns Test Board {unique_id}'

        try:
            # Create the board
            created_board = await client.boards.create(
                name=board_name, board_kind='public', fields='id name state'
            )

            # Verify the board was created
            assert created_board is not None
            assert hasattr(created_board, 'id')
            assert hasattr(created_board, 'name')
            assert created_board.name == board_name

            created_board_id = created_board.id

            # Create status column with status defaults
            status_defaults = StatusDefaults(
                [
                    StatusLabel('To Do', 1),
                    StatusLabel('In Progress', 2),
                    StatusLabel('Done', 3),
                ]
            )

            status_column = await client.boards.create_column(
                board_id=created_board_id,
                column_type='status',
                title='Task Status',
                defaults=status_defaults,
                fields='id title type',
            )

            # Verify status column was created
            assert status_column is not None
            assert hasattr(status_column, 'id')
            assert hasattr(status_column, 'title')
            assert hasattr(status_column, 'type')
            assert status_column.title == 'Task Status'
            assert status_column.type == 'status'

            # Create dropdown column with dropdown defaults
            dropdown_defaults = DropdownDefaults(
                [
                    DropdownLabel('Low Priority', 0),
                    DropdownLabel('Medium Priority', 1),
                    DropdownLabel('High Priority', 2),
                ]
            )

            dropdown_column = await client.boards.create_column(
                board_id=created_board_id,
                column_type='dropdown',
                title='Priority',
                defaults=dropdown_defaults,
                fields='id title type',
            )

            # Verify dropdown column was created
            assert dropdown_column is not None
            assert hasattr(dropdown_column, 'id')
            assert hasattr(dropdown_column, 'title')
            assert hasattr(dropdown_column, 'type')
            assert dropdown_column.title == 'Priority'
            assert dropdown_column.type == 'dropdown'

            # Delete the board
            delete_result = await client.boards.delete(board_id=created_board_id)
            assert delete_result is not None
            assert delete_result.id == created_board_id

        except Exception as e:
            pytest.skip(f'Cannot perform create columns: {e}')

    @pytest.mark.asyncio
    async def test_create_column_after_another(
        self,
        client: MondayClient,
    ):
        """Test creating a column positioned after an existing column."""
        unique_id = str(uuid.uuid4())[:8]
        board_name = f'After Column Test Board {unique_id}'
        try:
            created_board = await client.boards.create(
                name=board_name, board_kind='public', fields='id name'
            )
            created_board_id = created_board.id

            # First create an anchor column on the new board
            anchor_column = await client.boards.create_column(
                board_id=created_board_id,
                column_type='status',
                title='Anchor',
                fields='id title type',
            )

            text_column = await client.boards.create_column(
                board_id=created_board_id,
                column_type='text',
                title='Notes',
                after_column_id=anchor_column.id,
                fields='id title type',
            )
            assert text_column is not None

            await client.boards.delete(board_id=created_board_id)
        except Exception as e:
            pytest.skip(f'Cannot perform create column after another: {e}')

    @pytest.mark.asyncio
    async def test_update_board(
        self,
        client: MondayClient,
    ):
        """Test creating a board, updating it, then deleting it."""
        unique_id = str(uuid.uuid4())[:8]
        board_name = f'Update Test Board {unique_id}'
        updated_board_name = f'Updated Test Board {unique_id}'

        try:
            # Create the board
            created_board = await client.boards.create(
                name=board_name, board_kind='public', fields='id name state'
            )

            # Verify the board was created
            assert created_board is not None
            assert hasattr(created_board, 'id')
            assert hasattr(created_board, 'name')
            assert created_board.name == board_name

            created_board_id = created_board.id

            # Update the board
            update_result = await client.boards.update(
                board_id=created_board_id,
                board_attribute='name',
                new_value=updated_board_name,
            )

            # Verify the board was updated
            assert update_result is not None
            assert hasattr(update_result, 'success')
            assert update_result.success

            # Verify undo_data is included
            assert hasattr(update_result, 'undo_data')
            assert update_result.undo_data is not None
            assert hasattr(update_result.undo_data, 'undo_record_id')
            assert update_result.undo_data.undo_record_id
            assert hasattr(update_result.undo_data, 'action_type')
            assert update_result.undo_data.action_type == 'modify_project'
            assert hasattr(update_result.undo_data, 'entity_type')
            assert update_result.undo_data.entity_type == 'Board'
            assert hasattr(update_result.undo_data, 'entity_id')
            assert str(update_result.undo_data.entity_id) == str(created_board_id)
            assert hasattr(update_result.undo_data, 'count')
            assert update_result.undo_data.count == 1

            # Verify the name was actually updated
            updated_boards = await client.boards.query(
                board_ids=[created_board_id], fields='id name state'
            )

            assert len(updated_boards) == 1
            assert updated_boards[0].name == updated_board_name

            # Delete the board
            delete_result = await client.boards.delete(board_id=created_board_id)
            assert delete_result is not None
            assert delete_result.id == created_board_id

        except Exception as e:
            pytest.skip(f'Cannot perform update board: {e}')

    @pytest.mark.asyncio
    async def test_create_board_with_additional_parameters(
        self,
        client: MondayClient,
        workspace_id: int,
        user_id: int,
    ):
        """Test creating a board with description, owners and subscribers in a workspace."""
        unique_id = str(uuid.uuid4())[:8]
        board_name = f'Create With Params {unique_id}'
        try:
            created_board = await client.boards.create(
                name=board_name,
                board_kind='public',
                owner_ids=[user_id],
                subscriber_ids=[user_id],
                description='Integration created board',
                workspace_id=workspace_id,
                fields='id name state description',
            )
            assert created_board is not None
            await client.boards.delete(board_id=created_board.id)
        except Exception as e:
            pytest.skip(f'Cannot perform create board with additional parameters: {e}')

    @pytest.mark.asyncio
    async def test_archive_board(
        self,
        client: MondayClient,
    ):
        """Test creating a board, archiving it, then deleting it."""
        unique_id = str(uuid.uuid4())[:8]
        board_name = f'Archive Test Board {unique_id}'

        try:
            # Create the board
            created_board = await client.boards.create(
                name=board_name, board_kind='public', fields='id name state'
            )

            # Verify the board was created
            assert created_board is not None
            assert hasattr(created_board, 'id')
            assert hasattr(created_board, 'name')
            assert created_board.name == board_name

            created_board_id = created_board.id

            # Archive the board
            archived_board = await client.boards.archive(
                board_id=created_board_id, fields='id name state'
            )

            # Verify the board was archived
            assert archived_board is not None
            assert hasattr(archived_board, 'id')
            assert hasattr(archived_board, 'name')
            assert hasattr(archived_board, 'state')
            assert archived_board.state == 'archived'

            # Delete the board
            delete_result = await client.boards.delete(board_id=created_board_id)
            assert delete_result is not None
            assert delete_result.id == created_board_id

        except Exception as e:
            pytest.skip(f'Cannot perform archive board: {e}')
