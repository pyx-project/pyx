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

def mergeattrs(attrs, defaults=[]):
    """perform merging of the attribute list attrs as defined by the
    merge methods of the attributes"""
    newattrs = []
    if attrs is None:
        return None
    # XXX Should we skip merging of the default attributes?
    for a in defaults:
        newattrs = a.merge(newattrs)
    for a in attrs:
        if a is None:
            return None
        # XXX Do we really need this test?
        if isinstance(a, attr):
            newattrs = a.merge(newattrs)
        else:
            raise TypeError("only instances of class attr.attr are allowed")
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
    allowedclasses are present in the attribute list attrs; if not it
    raises a TypeError"""
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

    """an attribute which swallows all but the last of the same type (specified
    by the exlusiveclass argument to the constructor) in an attribute list"""

    def __init__(self, exclusiveclass):
        self.exclusiveclass = exclusiveclass

    def merge(self, attrs):
        attrs = [attr for attr in attrs if not isinstance(attr, self.exclusiveclass)]
        attrs.append(self)
        return attrs


class sortbeforeattr(attr):

    """an attribute which places itself previous to all attributes given
    in the beforetheclasses argument to the constructor"""

    def __init__(self, beforetheclasses):
        self.beforetheclasses = beforetheclasses

    def merge(self, attrs):
        first = 1
        result = []
        try:
            for attr in attrs:
                if first and isinstance(attr, self.beforetheclasses):
                    result.append(self)
                    first = 0
                result.append(attr)
        except TypeError: # workaround for Python 2.1 and older
            for attr in attrs:
                if first:
                    for dependedclass in self.beforetheclasses:
                        if isinstance(attr, dependedclass):
                            result.append(self)
                            first = 0
                            break
                result.append(attr)
        if first:
            result.append(self)
        return result


class sortbeforeexclusiveattr(attr):

    """an attribute which swallows all but the last of the same type (specified
    by the exlusiveclass argument to the constructor) in an attribute list and
    places itself previous to all attributes given in the beforetheclasses
    argument to the constructor"""

    def __init__(self, exclusiveclass, beforetheclasses):
        self.exclusiveclass = exclusiveclass
        self.beforetheclasses = beforetheclasses

    def merge(self, attrs):
        first = 1
        result = []
        try:
            for attr in attrs:
                if first and isinstance(attr, self.beforetheclasses):
                    result.append(self)
                    first = 0
                if not isinstance(attr, self.exclusiveclass):
                    result.append(attr)
        except TypeError: # workaround for Python 2.1 and older
            for attr in attrs:
                if first:
                    for dependedclass in self.beforetheclasses:
                        if isinstance(attr, dependedclass):
                            result.append(self)
                            first = 0
                            break
                if not isinstance(attr, self.exclusiveclass):
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

#
# changeable attrs
#

def select(attrs, index, total):
    """performs select calls for all changeable attributes and
    returns the resulting attribute list
    - attrs should be a list containing attributes and changeable
      attributes
    - index should be an unsigned integer
    - total should be a positive number
    - valid sections fullfill 0<=index<total"""
    result = []
    for a in attrs:
        if isinstance(a, changeattr):
            result.append(a.select(index, total))
        else:
            result.append(a)


class changeattr:

    """changeattr is the base class of all changeable attributes"""

    def select(self, index, total):
        """returns an attribute for a given index out of a total number
        if attributes to be provided
        - index should be an unsigned integer
        - total should be a positive number
        - valid selections fullfill 0 <= index < total
        - the select method may raise a ValueError, when the
          changeable attribute does not allow for a requested
          selection"""

        raise RuntimeError("not implemented")


class changelist(changeattr):

    """a changeable attribute over a list of attribute choises"""

    def __init__(self, attrs, restartable=1):
        """initializes the instance
        - attrs is a list of attributes to cycle
        - restartable is a boolean, allowing to start from
          the beginning after the end was reached; otherwise
          selecting beyond the list returns a None"""
        self.attrs = attrs
        self.restartable = restartable

    def select(self, index, total):
        if self.restartable:
            return self.attrs[index % length(self.attrs)]
        elif index < length(self.attrs):
            return self.attrs[index]

