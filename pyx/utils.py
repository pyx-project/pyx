# -*- encoding: utf-8 -*-
#
#
# Copyright (C) 2017, 2021, 2022 Jörg Lehmann <joerg@pyx-project.org>
# Copyright (C) 2017, 2021, 2022 André Wobst <wobsta@pyx-project.org>
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

def kwsplit(kwargs, parts=None, allow_only_split=False):
    """
    .. testsetup::

       from pyx.utils import * 

    >>> kwsplit({"aaa": "bbb"})
    ({}, {'aaa': 'bbb'})

    >>> kwsplit({"aaa": "bbb"}, allow_only_split=True)
    Traceback (most recent call last):
    ...
    ValueError: Invalid kwargs: {'aaa': 'bbb'}

    >>> kwsplit({"aaa": "bbb"}, ["ccc"])
    ({}, {'aaa': 'bbb'})

    >>> kwsplit({"aaa": "bbb"}, ["aaa"])
    ({}, {'aaa': 'bbb'})

    >>> kwsplit({"aaa_bbb": "ccc"})
    ({'aaa': {'bbb': 'ccc'}}, {})

    >>> kwsplit({"aaa_bbb": "ccc"}, ["aaa"])
    ({'aaa': {'bbb': 'ccc'}}, {})

    >>> kwsplit({"aaa_bbb": "ccc"}, ["ddd"])
    ({}, {'aaa_bbb': 'ccc'})

    >>> kwsplit({"aaa_bbb": "ccc", "ddd_eee": "fff", "ggg": "hhh"})
    ({'aaa': {'bbb': 'ccc'}, 'ddd': {'eee': 'fff'}}, {'ggg': 'hhh'})

    >>> kwsplit({"aaa_bbb": "ccc", "ddd_eee": "fff", "ggg": "hhh"}, ["aaa"])
    ({'aaa': {'bbb': 'ccc'}}, {'ddd_eee': 'fff', 'ggg': 'hhh'})

    """
    split = {}
    rest = {}
    for key, value in kwargs.items():
        try:
            part, subkey = key.split("_", 1)
        except ValueError:
            rest[key] = value
        else:
            if parts is None or part in parts:
                if part not in split:
                    split[part] = {}
                split[part][subkey] = value
            else:
                rest[key] = value
    if allow_only_split and rest:
        raise ValueError("Invalid kwargs: %s" % rest)
    return split, rest


def merge_members_kwargs(obj, kwargs_updates, member_names):
    """return merge obj's member variables member_names and obj.kwargs with dictionary kwargs"""

    new_kwargs = {}
    for name in member_names:
        new_kwargs[name] = getattr(obj, name)

    for kwargs in kwargs_updates:
        new_kwargs.update(kwargs)
    return new_kwargs
