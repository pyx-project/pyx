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

#
# Postscript operators
#

class PSOp:

    """Poscript Operators

    Everything, you can write in a (E)PS file

    """

    def write(self, file):
        """writing into a file is the only routine, a PSOp has to supply"""
        raise NotImplementedError, "cannot call virtual method write()"

    def prolog(self):
        """return list of prolog items"""
        return []

#
# PSCmd class
#

class PSCmd(PSOp):

    """ PSCmd is the base class of all visible elements

    Visible elements are those, that can be embedded in the Canvas
    and posses a bbox.

    """

    def bbox(self):
        raise NotImplementedError, "cannot call virtual method bbox()"

#
# attr class
#

class attr(PSOp):

    """ attr is the base class of all attributes, i.e., colors, decorators,
    styles, text attributes and trafos
    """

    def merge(self, attrs):
        """merge self into list of attrs

        self may either be appended to attrs or inserted at a proper position
        immediately before a dependent attribute. Attributes of the same type
        should be removed, if redundant. Note that it is safe to modify
        attrs."""

        attrs.append(self)
        return attrs


class exclusiveattr(attr):

    def __init__(self, exclusiveclass):
        attr.__init__(self)
        self.exclusiveclass = exclusiveclass

    def merge(self, attrs):
        # remove all previous instances of exclusiveclass
        attrs = [attr for attr in attrs if not isinstance(attr, self.exclusiveclass)]
        attrs.append(self)
        return attrs


class _clear(attr):

    def merge(self, attrs):
        return []

clear = _clear()


class classclear(attr):

    def __init__(self, clearclass):
        _attr.__init__(self)
        self.clearclass = clearclass

    def merge(self, attrs):
        return [attr for attr in attrs if not isinstance(attr, self.clearclass)]

#
# Path style classes
#
# note that as usual in PyX most classes have default instances as members

class PathStyle(PSOp):

    """style modifiers for paths
    """


    pass



#
# PyX Exception class
#

class PyXExcept(Exception):

    """base class for all PyX Exceptions"""

    pass
