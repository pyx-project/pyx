#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2005 André Wobst <wobsta@users.sourceforge.net>
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
from pyx import unit


class _positioner:
    """interface definition of axis tick position methods
    - these methods are used for the postitioning of the ticks
      when painting an axis"""
    # TODO: should we add a local transformation (for label text etc?)
    #       (this might replace tickdirection (and even tickposition?))

#    def basepath(self, axis, axisdata, x1=None, x2=None):
#        """return the basepath as a path
#        - x1 is the start position; if not set, the basepath starts
#          from the beginning of the axis, which might imply a
#          value outside of the graph coordinate range [0; 1]
#        - x2 is analogous to x1, but for the end position"""

    def vbasepath(self, v1=None, v2=None):
        """return the basepath as a path
        - like basepath, but for graph coordinates"""

#    def gridpath(self, axis, axisdata, x):
#        """return the gridpath as a path for a given position x
#        - might return None when no gridpath is available"""

    def vgridpath(self, v):
        """return the gridpath as a path for a given position v
        in graph coordinates
        - might return None when no gridpath is available"""

#    def tickpoint_pt(self, axis, axisdata, x):
#        """return the position at the basepath as a tuple (x, y) in
#        postscript points for the position x"""

#    def tickpoint(self, x):
#        """return the position at the basepath as a tuple (x, y) in
#        in PyX length for the position x"""

    def vtickpoint_pt(self, v):
        "like tickpoint_pt, but for graph coordinates"

    def vtickpoint(self, v):
        "like tickpoint, but for graph coordinates"

#    def tickdirection(self, x):
#        """return the direction of a tick as a tuple (dx, dy) for the
#        position x (the direction points towards the graph)"""

    def vtickdirection(self, v):
        """like tickposition, but for graph coordinates"""


# class _axispos:
#     """implements those parts of _Iaxispos which can be build
#     out of the axis convert method and other _Iaxispos methods
#     - base _Iaxispos methods, which need to be implemented:
#       - vbasepath
#       - vgridpath
#       - vtickpoint_pt
#       - vtickdirection
#     - other methods needed for _Iaxispos are build out of those
#       listed above when this class is inherited"""
# 
#     def __init__(self, convert):
#         """initializes the instance
#         - convert is a convert method from an axis"""
#         self.convert = convert
# 
#     def basepath(self, x1=None, x2=None):
#         if x1 is None:
#             if x2 is None:
#                 return self.vbasepath()
#             else:
#                 return self.vbasepath(v2=self.convert(x2))
#         else:
#             if x2 is None:
#                 return self.vbasepath(v1=self.convert(x1))
#             else:
#                 return self.vbasepath(v1=self.convert(x1), v2=self.convert(x2))
# 
#     def gridpath(self, x):
#         return self.vgridpath(self.convert(x))
# 
#     def tickpoint_pt(self, x):
#         return self.vtickpoint_pt(self.convert(x))
# 
#     def tickpoint(self, x):
#         return self.vtickpoint(self.convert(x))
# 
#     def vtickpoint(self, v):
#         return [x * unit.t_pt for x in self.vtickpoint(v)]
# 
#     def tickdirection(self, x):
#         return self.vtickdirection(self.convert(x))


class pathpositioner(_positioner):
    """axis tick position methods along an arbitrary path"""

    def __init__(self, p, direction=1):
        self.path = p
        self.normpath = p.normpath()
        self.arclen_pt = self.normpath.arclen_pt()
        self.arclen = self.arclen_pt * unit.t_pt
        self.direction = direction

    def vbasepath(self, v1=None, v2=None):
        if v1 is None:
            if v2 is None:
                return self.path
            else:
                return self.normpath.split(self.normpath.arclentoparam(v2 * self.arclen))[0]
        else:
            if v2 is None:
                return self.normpath.split(self.normpath.arclentoparam(v1 * self.arclen))[1]
            else:
                return self.normpath.split(*self.normpath.arclentoparam([v1 * self.arclen, v2 * self.arclen]))[1]

    def vgridpath(self, v):
        return None

    def vtickpoint_pt(self, v):
        return self.normpath.at_pt(self.normpath.arclentoparam(v * self.arclen))

    def vtickdirection(self, v):
        t= self.normpath.tangent(self.normpath.arclentoparam(v * self.arclen))
        tbegin = t.atbegin_pt()
        tend = t.atend_pt()
        dx = tend[0]-tbegin[0]
        dy = tend[1]-tbegin[1]
        norm = math.hypot(dx, dy)
        if self.direction == 1:
            return -dy/norm, dx/norm
        elif self.direction == -1:
            return dy/norm, -dx/norm
        raise RuntimeError("unknown direction")



