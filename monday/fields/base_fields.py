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
Base class for field collections in monday-client.

This module provides a base class that contains common functionality
for combining and retrieving field sets across different field collections.
"""

from monday.services.utils.fields import Fields


class BaseFields:
    """
    Base class providing common functionality for field collections.

    This class provides methods for combining field sets and retrieving
    all available fields from field collection classes.
    """

    @classmethod
    def combine(cls, *field_sets: str) -> Fields:
        """
        Dynamically combine multiple field sets from a field collection.

        Args:
            *field_sets: Names of field sets to combine (e.g., 'BASIC', 'DETAILED')

        Returns:
            Combined Fields instance

        Example:
            >>> fields = BoardFields.combine('BASIC', 'GROUPS', 'USERS')
            >>> print(fields)
            'id name top_group { id title } groups { id title } creator { id email name } owners { id email name } subscribers { id email name }'

        """
        combined_fields = []
        for field_set_name in field_sets:
            if hasattr(cls, field_set_name):
                field_set = getattr(cls, field_set_name)
                combined_fields.append(str(field_set))
            else:
                error_msg = f'Unknown field set: {field_set_name}'
                raise ValueError(error_msg)

        return Fields(' '.join(combined_fields))

    @classmethod
    def get_all_fields(cls) -> Fields:
        """
        Get all available fields from a field collection.

        Automatically discovers all field sets defined as class attributes
        that are instances of Fields.

        Returns:
            Combined Fields instance with all field sets

        Example:
            >>> fields = BoardFields.get_all_fields()
            >>> print(fields)
            'id name board_kind description top_group { id title } groups { id title } items_count items_page { cursor items { id name } } creator { id email name } owners { id email name } subscribers { id email name }'

        """
        field_sets = []
        for attr_name, attr_value in cls.__dict__.items():
            # Skip private attributes and methods
            if attr_name.startswith('_'):
                continue
            # Check if it's a Fields instance
            if isinstance(attr_value, Fields):
                field_sets.append(attr_name)

        return cls.combine(*field_sets)
