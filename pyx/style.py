#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2002, 2003 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2003 Michael Schindler <m-schindler@users.sourceforge.net>
# Copyright (C) 2002, 2003 André Wobst <wobsta@users.sourceforge.net>
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

import math
import attr, unit, base

#
# base classes for stroke and fill styles
#

class strokestyle(base.PSOp): pass

class fillstyle(base.PSOp): pass

#
# common stroke styles
#


class linecap(attr.exclusiveattr, strokestyle):

    """linecap of paths"""

    def __init__(self, value=0):
        attr.exclusiveattr.__init__(self, linecap)
        self.value = value

    def write(self, file):
        file.write("%d setlinecap\n" % self.value)

linecap.butt = linecap(0)
linecap.round = linecap(1)
linecap.square = linecap(2)
linecap.clear = attr.clearclass(linecap)


class linejoin(attr.exclusiveattr, strokestyle):

    """linejoin of paths"""

    def __init__(self, value=0):
        attr.exclusiveattr.__init__(self, linejoin)
        self.value = value

    def write(self, file):
        file.write("%d setlinejoin\n" % self.value)

linejoin.miter = linejoin(0)
linejoin.round = linejoin(1)
linejoin.bevel = linejoin(2)
linejoin.clear = attr.clearclass(linejoin)


class miterlimit(attr.exclusiveattr, strokestyle):

    """miterlimit of paths"""

    def __init__(self, value=10.0):
        attr.exclusiveattr.__init__(self, miterlimit)
        self.value = value

    def write(self, file):
        file.write("%f setmiterlimit\n" % self.value)

miterlimit.lessthan180deg = miterlimit(1/math.sin(math.pi*180/360))
miterlimit.lessthan90deg = miterlimit(1/math.sin(math.pi*90/360))
miterlimit.lessthan60deg = miterlimit(1/math.sin(math.pi*60/360))
miterlimit.lessthan45deg = miterlimit(1/math.sin(math.pi*45/360))
miterlimit.lessthan11deg = miterlimit(10) # the default, approximately 11.4783 degress
miterlimit.clear = attr.clearclass(miterlimit)


class dash(attr.exclusiveattr, strokestyle):

    """dash of paths"""

    def __init__(self, pattern=[], offset=0, rellengths=0):
        """set pattern with offset.

        If rellengths is True, interpret all dash lengths relative to current linewidth.
        """
        attr.exclusiveattr.__init__(self, dash)
        self.pattern = pattern
        self.offset = offset
        self.rellengths = rellengths

    def write(self, file):
        if self.rellengths:
            sep = " currentlinewidth mul "
        else:
            sep = " "
        patternstring = sep.join(["%g" % element for element in self.pattern])
        file.write("[%s] %d setdash\n" % (patternstring, self.offset))

dash.clear = attr.clearclass(dash)


class linestyle(attr.exclusiveattr, strokestyle):

    """linestyle (linecap together with dash) of paths"""

    def __init__(self, c=linecap.butt, d=dash([])):
        # XXX better, but at the moment not supported by attr.exlusiveattr would be:
        # XXX   attr.exclusiveattr.__init__(self, [linestyle, linecap, dash])
        attr.exclusiveattr.__init__(self, linestyle)
        self.c = c
        self.d = d

    def write(self, file):
        self.c.write(file)
        self.d.write(file)

linestyle.solid = linestyle(linecap.butt, dash([]))
linestyle.dashed = linestyle(linecap.butt, dash([2]))
linestyle.dotted = linestyle(linecap.round, dash([0, 3]))
linestyle.dashdotted = linestyle(linecap.round, dash([0, 3, 3, 3]))
linestyle.clear = attr.clearclass(linestyle)


class linewidth(unit.length, attr.exclusiveattr, attr.sortbeforeattr, strokestyle):

    """linewidth of paths"""

    def __init__(self, l="0 cm"):
        unit.length.__init__(self, l=l, default_type="w")
        attr.exclusiveattr.__init__(self, linewidth)
        attr.sortbeforeattr.__init__(self, [dash, linestyle])

    def merge(self, attrs):
        return attr.sortbeforeattr.merge(self, attr.exclusiveattr.merge(self, attrs)[:-1])

    def write(self, file):
        file.write("%f setlinewidth\n" % unit.topt(self))

_base = 0.02

linewidth.THIN = linewidth("%f cm" % (_base/math.sqrt(32)))
linewidth.THIn = linewidth("%f cm" % (_base/math.sqrt(16)))
linewidth.THin = linewidth("%f cm" % (_base/math.sqrt(8)))
linewidth.Thin = linewidth("%f cm" % (_base/math.sqrt(4)))
linewidth.thin = linewidth("%f cm" % (_base/math.sqrt(2)))
linewidth.normal = linewidth("%f cm" % _base)
linewidth.thick = linewidth("%f cm" % (_base*math.sqrt(2)))
linewidth.Thick = linewidth("%f cm" % (_base*math.sqrt(4)))
linewidth.THick = linewidth("%f cm" % (_base*math.sqrt(8)))
linewidth.THIck = linewidth("%f cm" % (_base*math.sqrt(16)))
linewidth.THICk = linewidth("%f cm" % (_base*math.sqrt(32)))
linewidth.THICK = linewidth("%f cm" % (_base*math.sqrt(64)))
linewidth.clear = attr.clearclass(linewidth)
