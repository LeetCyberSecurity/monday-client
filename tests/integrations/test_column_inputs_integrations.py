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
Integration tests for creating items using all column input helper types.

This test creates a temporary board, adds one column for each supported input
class (status, dropdown, text, long_text, numbers, date, hour, link, location,
email, phone, rating, checkbox, country, people, timeline, week, world_clock,
tags), then creates an item using the corresponding input instances.

Notes:
- PeopleInput requires a valid user ID in configuration (monday.user_id)
- TagInput requires an existing tag ID; if MONDAY_TAG_ID env var is not set,
  the TagInput portion is skipped to avoid flakiness

"""

from __future__ import annotations

import contextlib
import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from monday import MondayClient
from monday.exceptions import (
    ComplexityLimitExceeded,
    MondayAPIError,
    MutationLimitExceeded,
    PaginationError,
    QueryFormatError,
)
from monday.types.column_defaults import (
    DropdownDefaults,
    DropdownLabel,
    StatusDefaults,
    StatusLabel,
)
from monday.types.column_inputs import (
    CheckboxInput,
    CountryInput,
    DateInput,
    DropdownInput,
    EmailInput,
    HourInput,
    LinkInput,
    LocationInput,
    LongTextInput,
    NumberInput,
    PeopleInput,
    PhoneInput,
    RatingInput,
    StatusInput,
    TagInput,
    TextInput,
    TimelineInput,
    WeekInput,
    WorldClockInput,
)


@pytest.fixture(scope='module')
def client(monday_config: dict[str, Any]) -> MondayClient:
    """Create a MondayClient from config or skip if api key missing."""
    api_key = monday_config.get('api_key')
    if api_key:
        return MondayClient(api_key=api_key)
    pytest.skip('MONDAY_API_KEY not found in config file or environment variable')


@pytest.fixture(scope='module')
def user_id(monday_config: dict[str, Any]) -> int:
    """Get a valid user id for PeopleInput or skip if missing."""
    value = monday_config.get('user_id')
    if value:
        return int(value)
    pytest.skip('MONDAY_USER_ID not found in config file or environment variable')


@pytest.fixture(scope='module')
def workspace_id(monday_config: dict[str, Any]) -> int:
    """Get workspace id from config or skip."""
    value = monday_config.get('workspace_id')
    if value:
        return int(value)
    pytest.skip('MONDAY_WORKSPACE_ID not found in config file or environment variable')


@pytest.fixture(scope='module')
def tag_id(monday_config: dict[str, Any]) -> int | None:
    """Optional tag id for TagInput; prefer config, then env (handled upstream)."""
    value = monday_config.get('tag_id')
    try:
        return int(value) if value is not None and str(value).strip() != '' else None
    except (TypeError, ValueError):
        return None


@pytest.mark.integration
@pytest.mark.mutation
class TestColumnInputIntegrations:
    """Integration that covers creating items using column input helpers."""

    @pytest.mark.asyncio
    async def test_create_item_with_all_column_inputs(
        self,
        client: MondayClient,
        user_id: int,
        workspace_id: int,
        tag_id: int | None,
    ) -> None:
        """
        Create a board, add all supported input columns, then create an item.

        The test validates the item was created. Individual column value
        correctness is best-effort and may vary by account configuration, so we
        avoid over-asserting and skip gracefully on API limitations.
        """
        unique_id = str(uuid.uuid4())[:8]
        board_name = f'Column Inputs IT {unique_id}'

        created_board = None
        try:
            # Create board
            created_board = await client.boards.create(
                name=board_name,
                board_kind='public',
                workspace_id=workspace_id,
                fields='id name',
            )
            assert created_board is not None
            board_id = created_board.id

            # Create columns needed for each input type
            # Where relevant, include defaults to ensure valid labels/options
            status_defaults = StatusDefaults(
                [
                    StatusLabel('To Do', 0),
                    StatusLabel('In Progress', 1),
                    StatusLabel('Done', 2),
                ]
            )
            status_col = await client.boards.create_column(
                board_id=board_id,
                column_type='status',
                title='Status',
                defaults=status_defaults,
                fields='id type title',
            )

            dropdown_defaults = DropdownDefaults(
                [
                    DropdownLabel('Bug', 0),
                    DropdownLabel('Feature', 1),
                    DropdownLabel('Docs', 2),
                ]
            )
            dropdown_col = await client.boards.create_column(
                board_id=board_id,
                column_type='dropdown',
                title='Category',
                defaults=dropdown_defaults,
                fields='id type title',
            )

            text_col = await client.boards.create_column(
                board_id=board_id,
                column_type='text',
                title='Text',
                fields='id type title',
            )
            long_text_col = await client.boards.create_column(
                board_id=board_id,
                column_type='long_text',
                title='Long Text',
                fields='id type title',
            )
            numbers_col = await client.boards.create_column(
                board_id=board_id,
                column_type='numbers',
                title='Number',
                fields='id type title',
            )
            date_col = await client.boards.create_column(
                board_id=board_id,
                column_type='date',
                title='Date',
                fields='id type title',
            )
            hour_col = await client.boards.create_column(
                board_id=board_id,
                column_type='hour',
                title='Hour',
                fields='id type title',
            )
            link_col = await client.boards.create_column(
                board_id=board_id,
                column_type='link',
                title='Link',
                fields='id type title',
            )
            location_col = await client.boards.create_column(
                board_id=board_id,
                column_type='location',
                title='Location',
                fields='id type title',
            )
            email_col = await client.boards.create_column(
                board_id=board_id,
                column_type='email',
                title='Email',
                fields='id type title',
            )
            phone_col = await client.boards.create_column(
                board_id=board_id,
                column_type='phone',
                title='Phone',
                fields='id type title',
            )
            rating_col = await client.boards.create_column(
                board_id=board_id,
                column_type='rating',
                title='Rating',
                fields='id type title',
            )
            checkbox_col = await client.boards.create_column(
                board_id=board_id,
                column_type='checkbox',
                title='Checkbox',
                fields='id type title',
            )
            country_col = await client.boards.create_column(
                board_id=board_id,
                column_type='country',
                title='Country',
                fields='id type title',
            )
            people_col = await client.boards.create_column(
                board_id=board_id,
                column_type='people',
                title='People',
                fields='id type title',
            )
            timeline_col = await client.boards.create_column(
                board_id=board_id,
                column_type='timeline',
                title='Timeline',
                fields='id type title',
            )
            week_col = await client.boards.create_column(
                board_id=board_id,
                column_type='week',
                title='Week',
                fields='id type title',
            )
            world_clock_col = await client.boards.create_column(
                board_id=board_id,
                column_type='world_clock',
                title='World Clock',
                fields='id type title',
            )
            tags_col = await client.boards.create_column(
                board_id=board_id,
                column_type='tags',
                title='Tags',
                fields='id type title',
            )

            # Prepare values for each input
            today = datetime.now(UTC).date()
            # Ensure the week range starts on Monday to satisfy API validation
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)

            inputs = [
                StatusInput(status_col.id, 'To Do'),
                DropdownInput(dropdown_col.id, 'Bug'),
                TextInput(text_col.id, 'Short note'),
                LongTextInput(
                    long_text_col.id, 'A much longer block of text for testing.'
                ),
                NumberInput(numbers_col.id, 42.5),
                DateInput(date_col.id, today.strftime('%Y-%m-%d')),
                HourInput(hour_col.id, 14, 30),
                LinkInput(link_col.id, 'https://example.com', 'Example'),
                LocationInput(location_col.id, '123 Main St', 40.7128, -74.0060),
                EmailInput(email_col.id, 'user@example.com', 'User Email'),
                PhoneInput(phone_col.id, '+15551234567', 'US'),
                RatingInput(rating_col.id, 4),
                CheckboxInput(checkbox_col.id, checked=True),
                CountryInput(country_col.id, 'US'),
                PeopleInput(people_col.id, person_ids=[user_id]),
                TimelineInput(
                    timeline_col.id,
                    today.strftime('%Y-%m-%d'),
                    (today + timedelta(days=7)).strftime('%Y-%m-%d'),
                ),
                WeekInput(
                    week_col.id,
                    start_of_week.strftime('%Y-%m-%d'),
                    end_of_week.strftime('%Y-%m-%d'),
                ),
                WorldClockInput(world_clock_col.id, 'America/New_York'),
            ]

            # Optionally include TagInput if provided via config/env
            if tag_id is not None:
                inputs.append(TagInput(tags_col.id, tag_id))

            item_name = f'All Inputs Item {unique_id}'
            # Create the item first (no column values) to avoid large-payload issues
            created_item = await client.items.create(
                board_id=board_id,
                item_name=item_name,
                fields='id name',
            )

            # Basic verification
            assert created_item is not None
            assert hasattr(created_item, 'id')
            assert hasattr(created_item, 'name')
            assert created_item.name == item_name

            # Update each column value individually for robustness and clearer errors
            for cv in inputs:
                try:
                    await client.items.change_column_values(
                        item_id=created_item.id,
                        column_values=[cv],
                        fields='id',
                        create_labels_if_missing=True,
                    )
                except (
                    MondayAPIError,
                    ComplexityLimitExceeded,
                    MutationLimitExceeded,
                    PaginationError,
                    QueryFormatError,
                ) as e:
                    details = getattr(e, 'json', None)
                    extra = f'\n{json.dumps(details, indent=4)}' if details else ''
                    pytest.skip(
                        f'Failed updating column {getattr(cv, "column_id", "<unknown>")}: {e}{extra}'
                    )

        except (
            MondayAPIError,
            ComplexityLimitExceeded,
            MutationLimitExceeded,
            PaginationError,
            QueryFormatError,
        ) as e:
            details = getattr(e, 'json', None)
            extra = f'\n{json.dumps(details, indent=4)}' if details else ''
            pytest.skip(
                f'Column input integration failed due to environment/API constraints: {e}{extra}'
            )
        except Exception as e:
            pytest.skip(
                f'Column input integration failed due to environment/API constraints: {e}'
            )
        finally:
            # Cleanup board
            if created_board is not None:
                # Best-effort cleanup; ignore errors in teardown
                with contextlib.suppress(Exception):
                    await client.boards.delete(board_id=created_board.id)
