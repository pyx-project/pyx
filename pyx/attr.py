#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2003 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2003 Michael Schindler <m-schindler@users.sourceforge.net>
# Copyright (C) 2003 André Wobst <wobsta@users.sourceforge.net>
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


#
# some helper functions for the attribute handling
#

def mergeattrs(attrs):
    """perform merging of the attribute list attrs as defined by the
    merge methods of the attributes"""
    newattrs = []
    for attr in attrs:
        newattrs = attr.merge(newattrs)
    return newattrs


def getattrs(attrs, getclasses):
    """return all attributes in the attribute list attrs, which are
    instances of one of the classes in getclasses"""
    result = []
    try:
        for attr in attrs:
            if isinstance(attr, getclasses):
                result.append(attr)
    except TypeError: # workaround for Python 2.1 and older
        for attr in attrs:
            for getclass in getclasses:
                if isinstance(attr, getclass):
                    result.append(attr)
                    break
    return result


def checkattrs(attrs, allowedclasses):
    """check whether only attributes which are instances of classes in
    allowedclasses are present in the attribute list attrs"""
    if len(attrs) != len(getattrs(attrs, allowedclasses)):
        for attr1, attr2 in zip(attrs, getattrs(attrs, allowedclasses)):
            if attr1 is not attr2:
                raise TypeError("instance %r not allowed" % attr1)
        else:
            raise TypeError("instance %r not allowed" % attrs[len(getattrs(attrs, allowedclasses))])

#
# attr class and simple descendants
#

class attr:

    """ attr is the base class of all attributes, i.e., colors, decorators,
    styles, text attributes and trafos"""

    def merge(self, attrs):
        """merge self into list of attrs

        self may either be appended to attrs or inserted at a proper position
        immediately before a dependent attribute. Attributes of the same type
        should be removed, if redundant. Note that it is safe to modify
        attrs."""

        attrs.append(self)
        return attrs


class exclusiveattr(attr):

    """an attribute which swallows all but the last of the same type in an
    attribute list"""

    def __init__(self, exclusiveclass):
        self.exclusiveclass = exclusiveclass

    def merge(self, attrs):
        attrs = [attr for attr in attrs if not isinstance(attr, self.exclusiveclass)]
        attrs.append(self)
        return attrs


class sortattr(attr):

    """an attribute which places itself previous to all attributes given
    in the dependedclasses argument to the constructor"""

    def __init__(self, dependedclasses):
        self.dependedclasses = dependedclasses

    def merge(self, attrs):
        first = 1
        result = []
        try:
            for attr in attrs:
                if first and isinstance(attr, self.dependedclasses):
                    result.append(self)
                    first = 0
                result.append(attr)
        except TypeError: # workaround for Python 2.1 and older
            for attr in attrs:
                if first:
                    for dependedclass in self.dependedclasses:
                        if isinstance(attr, dependedclass):
                            result.append(self)
                            first = 0
                            break
                result.append(attr)
        if first:
            result.append(self)
        return result


class clearclass(attr):

    """a special attribute which allows to remove all predecessing attributes of
    the same type in an attribute list"""

    def __init__(self, clearclass):
        self.clearclass = clearclass

    def merge(self, attrs):
        return [attr for attr in attrs if not isinstance(attr, self.clearclass)]


# XXX is _clear a good choice?

class _clear(attr):

    """a special attribute which removes all predecessing attributes
    in an attribute list"""

    def merge(self, attrs):
        return []

# we define the attribute "clear", an instance of "_clear",
# which can be used to remove all predecessing attributes
# in an attribute list

clear = _clear()

