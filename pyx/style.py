#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2002-2004 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2003-2004 Michael Schindler <m-schindler@users.sourceforge.net>
# Copyright (C) 2002-2004 André Wobst <wobsta@users.sourceforge.net>
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

class strokestyle(base.canvasitem): pass

class fillstyle(base.canvasitem): pass

#
# common stroke styles
#


class linecap(attr.exclusiveattr, strokestyle):

    """linecap of paths"""

    def __init__(self, value=0):
        attr.exclusiveattr.__init__(self, linecap)
        self.value = value

    def outputPS(self, file):
        file.write("%d setlinecap\n" % self.value)

    def outputPDF(self, file):
        file.write("%d J\n" % self.value)

linecap.butt = linecap(0)
linecap.round = linecap(1)
linecap.square = linecap(2)
linecap.clear = attr.clearclass(linecap)


class linejoin(attr.exclusiveattr, strokestyle):

    """linejoin of paths"""

    def __init__(self, value=0):
        attr.exclusiveattr.__init__(self, linejoin)
        self.value = value

    def outputPS(self, file):
        file.write("%d setlinejoin\n" % self.value)

    def outputPDF(self, file):
        file.write("%d j\n" % self.value)

linejoin.miter = linejoin(0)
linejoin.round = linejoin(1)
linejoin.bevel = linejoin(2)
linejoin.clear = attr.clearclass(linejoin)


class miterlimit(attr.exclusiveattr, strokestyle):

    """miterlimit of paths"""

    def __init__(self, value=10.0):
        attr.exclusiveattr.__init__(self, miterlimit)
        self.value = value

    def outputPS(self, file):
        file.write("%f setmiterlimit\n" % self.value)

    def outoutPDF(self, file):
        file.write("%f M\n" % self.value)

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

    def outputPS(self, file):
        if self.rellengths:
            sep = " currentlinewidth mul "
        else:
            sep = " "
        patternstring = sep.join(["%f" % element for element in self.pattern])
        file.write("[%s] %d setdash\n" % (patternstring, self.offset))

    def outputPDF(self, file):
        if self.rellengths:
            raise RuntimeError("rellengths currently not supported in pdf output")
        file.write("[%s] %d d\n" % (" ".join(["%f" % element for element in self.pattern]), self.offset))

dash.clear = attr.clearclass(dash)


class linestyle(attr.exclusiveattr, strokestyle):

    """linestyle (linecap together with dash) of paths"""

    def __init__(self, c=linecap.butt, d=dash([])):
        # XXX better, but at the moment not supported by attr.exlusiveattr would be:
        # XXX   attr.exclusiveattr.__init__(self, [linestyle, linecap, dash])
        attr.exclusiveattr.__init__(self, linestyle)
        self.c = c
        self.d = d

    def outputPS(self, file):
        self.c.outputPS(file)
        self.d.outputPS(file)

    def outputPDF(self, file):
        self.c.outputPDF(file)
        self.d.outputPDF(file)

linestyle.solid = linestyle(linecap.butt, dash([]))
linestyle.dashed = linestyle(linecap.butt, dash([2]))
linestyle.dotted = linestyle(linecap.round, dash([0, 2]))
linestyle.dashdotted = linestyle(linecap.round, dash([0, 2, 2, 2]))
linestyle.clear = attr.clearclass(linestyle)


class linewidth(unit.length, attr.sortbeforeexclusiveattr, strokestyle):

    """linewidth of paths"""

    def __init__(self, l):
        unit.length.__init__(self, 0)
        self.t = l.t
        self.u = l.u
        self.v = l.v
        self.w = l.w
        self.x = l.x
        attr.sortbeforeexclusiveattr.__init__(self, linewidth, [dash, linestyle])

    def outputPS(self, file):
        file.write("%f setlinewidth\n" % unit.topt(self))

    def outputPDF(self, file):
        file.write("%f w\n" % unit.topt(self))

_base = 0.02 * unit.w_cm

linewidth.THIN = linewidth(_base/math.sqrt(32))
linewidth.THIn = linewidth(_base/math.sqrt(16))
linewidth.THin = linewidth(_base/math.sqrt(8))
linewidth.Thin = linewidth(_base/math.sqrt(4))
linewidth.thin = linewidth(_base/math.sqrt(2))
linewidth.normal = linewidth(_base)
linewidth.thick = linewidth(_base*math.sqrt(2))
linewidth.Thick = linewidth(_base*math.sqrt(4))
linewidth.THick = linewidth(_base*math.sqrt(8))
linewidth.THIck = linewidth(_base*math.sqrt(16))
linewidth.THICk = linewidth(_base*math.sqrt(32))
linewidth.THICK = linewidth(_base*math.sqrt(64))
linewidth.clear = attr.clearclass(linewidth)
