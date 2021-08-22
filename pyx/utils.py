# -*- encoding: utf-8 -*-
#
#
# Copyright (C) 2017, 2021 Jörg Lehmann <joerg@pyx-project.org>
# Copyright (C) 2017, 2021 André Wobst <wobsta@pyx-project.org>
#
# This file is part of PyX (https://pyx-project.org/).
#
# PyX is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# PyX is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyX; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

def kwsplit(kwargs, parts=None):
    """
    .. testsetup::

       from pyx.utils import * 

    >>> kwsplit({'aaa_bbb': 'ccc'}, ['aaa'])
    {'aaa': {'bbb': 'ccc'}}

    >>> kwsplit({'aaa_bbb': 'ccc', "eee": "fff"}, ['aaa', None])
    {'aaa': {'bbb': 'ccc'}, None: {'eee': 'fff'}}

    >>> kwsplit({'aaa_bbb': 'ccc'})
    {'aaa': {'bbb': 'ccc'}}

    >>> kwsplit({'aaa_bbb': 'ccc', "eee": "fff"})
    {'aaa': {'bbb': 'ccc'}, None: {'eee': 'fff'}}

    >>> kwsplit({'aaa_bbb': 'ccc'}, ['eee'])
    Traceback (most recent call last):
       ...
    ValueError: invalid part name aaa in kwargs'

    """
    result = {} # {part: {} for part in parts}
    for key, value in kwargs.items():
        try:
            part, subkey = key.split('_', 1)
        except ValueError:
            part = None
            subkey = key
        if part not in result:
            if parts is not None and part not in parts:
               raise ValueError('invalid part name %s in kwargs' % part)
            result[part] = {}
        result[part][subkey] = value
    return result
