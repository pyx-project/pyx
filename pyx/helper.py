#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2002 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2002 André Wobst <wobsta@users.sourceforge.net>
#
# This file is part of PyX (http://pyx.sourceforge.net/).
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


import base


class nodefault: pass


def isstring(arg):
    "arg is string-like (cf. python cookbook 3.2)"
    try: arg + ''
    except: return 0
    return 1


def isnumber(arg):
    "arg is number-like"
    try: arg + 0
    except: return 0
    return 1


def isinteger(arg):
    "arg is integer-like"
    try:
        if type(arg + 0.0) is type(arg):
            return 0
        return 1
    except: return 0


def issequence(arg):
    """arg is sequence-like (e.g. has a len)
       a string is *not* considered to be a sequence"""
    if isstring(arg): return 0
    try: len(arg)
    except: return 0
    return 1


def ensuresequence(arg):
    """return arg or (arg,) depending on the result of issequence,
       None is converted to ()"""
    if isstring(arg): return (arg,)
    if arg is None: return ()
    if issequence(arg): return arg
    return (arg,)


def ensurelist(arg):
    """return list(arg) or [arg] depending on the result of isequence,
       None is converted to []"""
    if isstring(arg): return [arg]
    if arg is None: return []
    if issequence(arg): return list(arg)
    return [arg]

def getitemno(arg, n):
    """get item number n if arg is a sequence (when the sequence
       is not long enough, None is returned), otherweise arg is
       returned"""
    if issequence(arg):
        try: return arg[n]
        except: return None
    else:
        return arg


def issequenceofsequences(arg):
    """check if arg has a sequence or None as it's first entry"""
    return issequence(arg) and len(arg) and (issequence(arg[0]) or arg[0] is None)


def getsequenceno(arg, n):
    """get sequence number n if arg is a sequence of sequences (when
       the sequence is not long enough, None is returned), otherwise
       arg is returned"""
    if issequenceofsequences(arg):
        try: return arg[n]
        except: return None
    else:
        return arg
