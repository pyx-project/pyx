#!/usr/bin/env python
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



class AttrError(base.PyXExcept): pass


def checkattr(attrs, allowonce=(), allowmulti=()):
    """checks the sequence attrs for occurencies of instances
       the classes provided as a tuple to allowonce are allowed only once
       the classes provided as a tuple to allowonce are allowed multiple times"""
    hadonce = []
    for attr in attrs:
        for once in allowonce:
            if isinstance(attr, once):
                if once in hadonce:
                    raise AttrError("only a single instance of %r allowed" % once)
                else:
                    hadonce += [once]
                    break
        else:
            for multi in allowmulti:
                if isinstance(attr, multi):
                    break
            else:
                raise AttrError("%r not allowed" % attr)

def getattrs(attrs, get, default=nodefault):
    """creates a list of instances of class get out of the sequence attrs
       when no instances are found it returns default when set (whatever it is)
       when no instances are found it raises AttrError when default is not set"""
    first = 1
    for attr in attrs:
        if isinstance(attr, get):
            if first:
                result = [attr]
                first = 0
            else:
                result.append(attr)
    if first:
        if default is nodefault:
            raise AttrError
        else:
            return default
    return result

def countattrs(attrs, check):
    "count the occurancies of instances of class get out of the sequence attrs"
    return len(getattrs(attrs, check, ()))

def getattr(attrs, get, default=nodefault):
    """get the instance of class get out of the sequence attrs
       when no instance is found it returns default when set (whatever it is)
       when no instance is found it raises AttrError when default is not set
       when no multiple instances are found it always raises AttrError"""
    try:
        result = getattrs(attrs, get)
    except AttrError:
        if default is nodefault:
            raise AttrError
        else:
            return default
    if len(result) > 1:
        raise AttrError
    return result[0]

def getfirstattr(attrs, get, default=nodefault):
    """get the first instance of class get out of the sequence attrs
       when no instances are found it returns default when set (whatever it is)
       when no instances are found it raises AttrError when default is not set"""
    try:
        result = getattrs(attrs, get)
    except AttrError:
        if default is nodefault:
            raise AttrError
        else:
            return default
    return result[0]

def getlastattr(attrs, get, default=nodefault):
    """get the last instance of class get out of the sequence attrs
       when no instances are found it returns default when set (whatever it is)
       when no instances are found it raises AttrError when default is not set"""
    try:
        result = getattrs(attrs, get)
    except AttrError:
        if default is nodefault:
            raise AttrError
        else:
            return default
    return result[-1]

def delattr(attrs, remove):
    """create a new list of instances out of the sequence attrs
       where all instances of class remove are removed"""
    result = []
    for attr in attrs:
        if not isinstance(attr, remove):
            result.append(attr)
    return result


if __name__=="__main__":
    class a: pass
    class b: pass
    class c(b): pass
    class A: pass
    class B: pass
    class C(B): pass
    checkattr((a(), A(), A()), (a, b), (A, B))
    checkattr((c(), A(), A()), (a, b), (A, B))
    try:
        checkattr((a(), A(), A(), a()), (a, b), (A, B))
        print "error"
    except AttrError: pass
    try:
        checkattr((c(), A(), A(), c()), (a, b), (A, B))
        print "error"
    except AttrError: pass
    x1, x2 = a(), a()
    if getattrs((x1, A(), A()), a) != [x1]:
        print "error"
    if getattrs((x1, A(), A(), x2), a) != [x1, x2]:
        print "error"
    if getattr((x1, A(), A()), a) != x1:
        print "error"
    try:
        getattr((x1, A(), A(), x2), a)
        print "error"
    except AttrError: pass
    if getfirstattr((x1, A(), A(), x2), a) != x1:
        print "error"
    if getlastattr((x1, A(), A(), x2), a) != x2:
        print "error"
    if getattr((x1, A(), A()), a, x2) != x1:
        print "error"
    if getattr((A(), A()), a, x2) != x2:
        print "error"

