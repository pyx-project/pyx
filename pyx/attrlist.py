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


class AttrlistExcept(base.PyXExcept):

    pass


class nodefault:

    pass


class attrlist:

    def attrcheck(self, attrs, allowonce, allowmulti = []):
        hadonce = []
        for attr in attrs:
            for once in allowonce:
                if isinstance(attr, once):
                    if once in hadonce:
                        raise AttrlistExcept
                    else:
                        hadonce += [once]
                        break
            else:
                for multi in allowmulti:
                    if isinstance(attr, multi):
                        break
                else:
                    raise AttrlistExcept

    def attrgetall(self, attrs, get, default = nodefault()):
        first = 1
        for attr in attrs:
            if isinstance(attr, get):
                if first:
                    result = [attr]
                    first = 0
                else:
                    result.append(attr)
        if first:
            if isinstance(default, nodefault):
                raise AttrlistExcept
            else:
                return default
        return result

    def attrget(self, attrs, get, default = nodefault()):
        try:
            result = self.attrgetall(attrs, get)
        except AttrlistExcept:
            if isinstance(default, nodefault):
                raise AttrlistExcept
            else:
                return default
        if len(result) > 1:
            raise AttrlistExcept
        return result[0]

    def attrgetfirst(self, attrs, get, default = nodefault()):
        try:
            result = self.attrgetall(attrs, get)
        except AttrlistExcept:
            if isinstance(default, nodefault):
                raise AttrlistExcept
            else:
                return default
        return result[0]

    def attrgetlast(self, attrs, get, default = nodefault()):
        try:
            result = self.attrgetall(attrs, get)
        except AttrlistExcept:
            if isinstance(default, nodefault):
                raise AttrlistExcept
            else:
                return default
        return result[-1]


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
    except AttrlistExcept: pass
    try:
        test.attrcheck((c(), A(), A(), c()), (a, b), (A, B))
        print "error"
    except AttrlistExcept: pass
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
    except AttrlistExcept: pass
    if test.attrgetfirst((x1, A(), A(), x2), a) != x1:
        print "error"
    if test.attrgetlast((x1, A(), A(), x2), a) != x2:
        print "error"
    if test.attrget((x1, A(), A()), a, x2) != x1:
        print "error"
    if test.attrget((A(), A()), a, x2) != x2:
        print "error"

