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
Module containing predefined field sets for monday.com group operations.

This module provides a collection of commonly used field combinations when
querying monday.com groups, making it easier to maintain consistent field
sets across group operations.
"""

from monday.services.utils.fields import Fields


class GroupFields:
    """
    Collection of predefined field sets for group operations.

    See also:
        `monday.com API Group fields <https://developer.monday.com/api-reference/reference/groups#fields>`_
    """

    BASIC = Fields('id title')
    """Returns the following fields:
    
    - id: Group's ID
    - title: Group's title
    """
