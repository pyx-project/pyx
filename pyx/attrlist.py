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

# TODO: - testsuite
#       - documentation (docstrings)


import base, helper


class AttrlistError(base.PyXExcept):

    pass


class attrlist:

    # TODO: could be improved??? (read python cookbook carefully)

    def attrcheck(self, attrs, allowonce=(), allowmulti=()):
        hadonce = []
        for attr in attrs:
            for once in allowonce:
                if isinstance(attr, once):
                    if once in hadonce:
                        raise AttrlistError
                    else:
                        hadonce += [once]
                        break
            else:
                for multi in allowmulti:
                    if isinstance(attr, multi):
                        break
                else:
                    raise AttrlistError

    def attrgetall(self, attrs, get, default=helper._nodefault):
        first = 1
        for attr in attrs:
            if isinstance(attr, get):
                if first:
                    result = [attr]
                    first = 0
                else:
                    result.append(attr)
        if first:
            if default is helper._nodefault:
                raise AttrlistError
            else:
                return default
        return result

    def attrcount(self, attrs, check):
        return len(self.attrgetall(attrs, check, ()))

    def attrget(self, attrs, get, default=helper._nodefault):
        try:
            result = self.attrgetall(attrs, get)
        except AttrlistError:
            if default is helper._nodefault:
                raise AttrlistError
            else:
                return default
        if len(result) > 1:
            raise AttrlistError
        return result[0]

    def attrgetfirst(self, attrs, get, default=helper._nodefault):
        try:
            result = self.attrgetall(attrs, get)
        except AttrlistError:
            if default is helper._nodefault:
                raise AttrlistError
            else:
                return default
        return result[0]

    def attrgetlast(self, attrs, get, default=helper._nodefault):
        try:
            result = self.attrgetall(attrs, get)
        except AttrlistError:
            if default is helper._nodefault:
                raise AttrlistError
            else:
                return default
        return result[-1]

    def attrdel(self, attrs, remove):
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
    test = attrlist()
    test.attrcheck((a(), A(), A()), (a, b), (A, B))
    test.attrcheck((c(), A(), A()), (a, b), (A, B))
    try:
        test.attrcheck((a(), A(), A(), a()), (a, b), (A, B))
        print "error"
    except AttrlistError: pass
    try:
        test.attrcheck((c(), A(), A(), c()), (a, b), (A, B))
        print "error"
    except AttrlistError: pass
    x1, x2 = a(), a()
    if test.attrgetall((x1, A(), A()), a) != [x1]:
        print "error"
    if test.attrgetall((x1, A(), A(), x2), a) != [x1, x2]:
        print "error"
    if test.attrget((x1, A(), A()), a) != x1:
        print "error"
    try:
        test.attrget((x1, A(), A(), x2), a)
        print "error"
    except AttrlistError: pass
    if test.attrgetfirst((x1, A(), A(), x2), a) != x1:
        print "error"
    if test.attrgetlast((x1, A(), A(), x2), a) != x2:
        print "error"
    if test.attrget((x1, A(), A()), a, x2) != x1:
        print "error"
    if test.attrget((A(), A()), a, x2) != x2:
        print "error"

