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

"""Monday API client"""

__version__ = '0.1.87'
__authors__ = [{'name': 'Dan Hollis', 'email': 'dh@leetsys.com'}]

import asyncio
import threading
from collections.abc import Awaitable, Callable
from contextlib import suppress
from typing import Any

from monday.client import MondayClient
from monday.config import (Config, EnvConfig, JsonConfig, MultiSourceConfig,
                           YamlConfig)
from monday.fields.board_fields import BoardFields
from monday.fields.column_fields import ColumnFields
from monday.fields.group_fields import GroupFields
from monday.fields.item_fields import ItemFields
from monday.fields.user_fields import UserFields
from monday.fields.webhook_fields import WebhookFields
from monday.logging_utils import (configure_for_external_logging,
                                  disable_logging, enable_logging, get_logger,
                                  is_logging_enabled, set_log_level)
from monday.services.utils.fields import Fields
from monday.sync_client import SyncMondayClient
from monday.types.account import Account, AccountProduct, Plan
from monday.types.asset import Asset
from monday.types.board import (ActivityLog, Board, BoardView, UndoData,
                                UpdateBoard)
from monday.types.column import Column, ColumnFilter, ColumnType, ColumnValue
from monday.types.column_defaults import (DropdownDefaults, DropdownLabel,
                                          StatusDefaults, StatusLabel)
from monday.types.column_inputs import (CheckboxInput, ColumnInput,
                                        CountryInput, DateInput, DropdownInput,
                                        EmailInput, HourInput, LinkInput,
                                        LocationInput, LongTextInput,
                                        NumberInput, PeopleInput, PhoneInput,
                                        RatingInput, StatusInput, TagInput,
                                        TextInput, TimelineInput, WeekInput,
                                        WorldClockInput)
from monday.types.group import Group, GroupList
from monday.types.item import (Item, ItemList, ItemsPage, OrderBy, QueryParams,
                               QueryRule)
from monday.types.subitem import Subitem, SubitemList
from monday.types.tag import Tag
from monday.types.team import Team
from monday.types.update import Update
from monday.types.user import OutOfOffice, User
from monday.types.webhook import Webhook
from monday.types.workspace import Workspace


class _TmpRunner:
    """Minimal background event loop runner used by :func:`run_sync`."""

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._started = threading.Event()
        self._thread.start()
        self._started.wait()

    def _run(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._started.set()
        self._loop.run_forever()

    def run[T](self, aw: Awaitable[T]) -> T:
        async def _runner() -> T:
            return await aw

        fut = asyncio.run_coroutine_threadsafe(_runner(), self._loop)
        return fut.result()

    def shutdown(self) -> None:
        try:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=2)
        finally:
            with suppress(Exception):
                self._loop.close()


def sync(
    config: Config | None = None,
    **kwargs: Any,
) -> SyncMondayClient:
    """
    Create a synchronous Monday client.

    This is a convenience factory for :class:`SyncMondayClient` for users not
    using asyncio.

    Args:
        config: Optional :class:`Config` object.
        **kwargs: Keyword arguments forwarded to :class:`SyncMondayClient` such as
            ``api_key``, ``url``, ``version``, ``headers``, ``max_retries``,
            and ``transport``.

    Returns:
        A ready-to-use :class:`SyncMondayClient` instance.

    """
    return SyncMondayClient(config, **kwargs)


def run_sync[T](awaitable: Awaitable[T]) -> T:
    """
    Run a coroutine/awaitable to completion in a temporary background loop.

    Useful for one-off calls when you have an async function but are in a
    synchronous context.

    Example:
        >>> async def fetch():
        ...     return 42
        >>> run_sync(fetch())
        42

    Note:
        If you need to call multiple async functions efficiently, prefer
        constructing a :class:`SyncMondayClient` and reusing its background
        loop, as this helper spins up a fresh loop each time.

    """
    runner = _TmpRunner()
    try:
        return runner.run(awaitable)
    finally:
        runner.shutdown()


def to_sync[**P, T](fn: Callable[P, Awaitable[T]]) -> Callable[P, T]:
    """
    Convert an async function into a blocking callable using ``run_sync``.

    Example:
        >>> async def fetch():
        ...     return 42
        >>> fetch_sync = to_sync(fetch)
        >>> fetch_sync()
        42

    """

    def _wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
        return run_sync(fn(*args, **kwargs))

    return _wrapped


__all__ = [
    'Account',
    'AccountProduct',
    'ActivityLog',
    'Asset',
    'Board',
    'BoardFields',
    'BoardView',
    'CheckboxInput',
    'Column',
    'ColumnFields',
    'ColumnFilter',
    'ColumnInput',
    'ColumnType',
    'ColumnValue',
    'Config',
    'CountryInput',
    'DateInput',
    'DropdownDefaults',
    'DropdownInput',
    'DropdownLabel',
    'EmailInput',
    'EnvConfig',
    'Fields',
    'Group',
    'GroupFields',
    'GroupList',
    'HourInput',
    'Item',
    'ItemFields',
    'ItemList',
    'ItemsPage',
    'JsonConfig',
    'LinkInput',
    'LocationInput',
    'LongTextInput',
    'MondayClient',
    'MultiSourceConfig',
    'NumberInput',
    'OrderBy',
    'OutOfOffice',
    'PeopleInput',
    'PhoneInput',
    'Plan',
    'QueryParams',
    'QueryRule',
    'RatingInput',
    'StatusDefaults',
    'StatusInput',
    'StatusLabel',
    'Subitem',
    'SubitemList',
    'SyncMondayClient',
    'Tag',
    'TagInput',
    'Team',
    'TextInput',
    'TimelineInput',
    'UndoData',
    'Update',
    'UpdateBoard',
    'User',
    'UserFields',
    'Webhook',
    'WebhookFields',
    'WeekInput',
    'Workspace',
    'WorldClockInput',
    'YamlConfig',
    'configure_for_external_logging',
    'disable_logging',
    'enable_logging',
    'get_logger',
    'is_logging_enabled',
    'run_sync',
    'set_log_level',
    'sync',
    'to_sync',
]
