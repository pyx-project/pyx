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

# TODO: - it would be nice to have a real bbox.transform
#       - what about __iadd__, ...

import math
import unit

# helper routine for bbox manipulations

def _nmin(*args):
    """minimum of a list of values, where None represents +infinity, not -infinity as
    in standard min implementation of python"""
    args = [x for x in args if x is not None]
    if len(args):
        return min(args)
    else:
        return None

def _nmax(*args):
    """maximum of a list of values, where None represents +infinity, not -infinity as
    in standard max implementation of python 2.0"""
    args = [x for x in args if x is not None]
    if len(args):
        return max(args)
    else:
        return None

#
# classes representing bounding boxes
#

class _bbox:
    
    """class for bounding boxes

    This variant requires points in the constructor, and is used for internal
    purposes."""

    def __init__(self, llx=None, lly=None, urx=None, ury=None):
        self.llx = llx
        self.lly = lly
        self.urx = urx
        self.ury = ury

    def __add__(self, other):
        """join two bboxes"""

        return _bbox(_nmin(self.llx, other.llx), _nmin(self.lly, other.lly),
                     _nmax(self.urx, other.urx), _nmax(self.ury, other.ury))

    def __mul__(self, other):
        """return intersection of two bboxes"""

        return _bbox(_nmax(self.llx, other.llx), _nmax(self.lly, other.lly),
                     _nmin(self.urx, other.urx), _nmin(self.ury, other.ury))

    def __str__(self):
        return "%s %s %s %s" % (self.llx, self.lly, self.urx, self.ury)

    def write(self, file):
        file.write("%%%%BoundingBox: %d %d %d %d\n" %
                   (math.floor(self.llx), math.floor(self.lly),
                    math.ceil(self.urx), math.ceil(self.ury)))
        file.write("%%%%HiResBoundingBox: %g %g %g %g\n" %
                   (self.llx, self.lly, self.urx, self.ury))

    def intersects(self, other):
        """check, if two bboxes intersect eachother"""

        return not (self.llx > other.urx or
                    self.lly > other.ury or
                    self.urx < other.llx or
                    self.ury < other.lly)

    def transformed(self, trafo):
        """return bbox transformed by trafo"""
        # we have to transform all four corner points of the bbox
        # method correctly handles bboxes with None entries at the corners
        if None not in (self.llx, self.lly):
            llx, lly = trafo._apply(self.llx, self.lly)
        else:
            llx = lly = None
        if None not in (self.urx, self.lly):
            lrx, lry = trafo._apply(self.urx, self.lly)
        else:
            lrx = lry = None
        if None not in (self.urx, self.ury):
            urx, ury = trafo._apply(self.urx, self.ury)
        else:
            urx = ury = None
        if None not in (self.llx, self.ury):
            ulx, uly = trafo._apply(self.llx, self.ury)
        else:
            ulx = uly = None

        # now, by sorting, we obtain the lower left and upper right corner
        # of the new bounding box. 

        return _bbox(_nmin(llx, lrx, urx, ulx), _nmin(lly, lry, ury, uly),
                     _nmax(llx, lrx, urx, ulx), _nmax(lly, lry, ury, uly))

    def enlarged(self, all=0, bottom=None, left=None, top=None, right=None):
        """return bbox enlarged

        all is used, if bottom, left, top and/or right are not given.

        """
        _bottom = _left = _top = _right = unit.topt(unit.length(all, default_type="v"))
        if bottom is not None:
           _bottom = unit.topt(unit.length(bottom, default_type="v"))
        if left is not None:
           _left = unit.topt(unit.length(left, default_type="v"))
        if top is not None:
           _top = unit.topt(unit.length(top, default_type="v"))
        if right is not None:
           _right = unit.topt(unit.length(right, default_type="v"))
        return _bbox(self.llx-_left, self.lly-_bottom, self.urx+_right, self.ury+_top)

    def rect(self):
        """return rectangle corresponding to bbox"""
        import path
        return path.rect_pt(self.llx, self.lly, self.urx-self.llx, self.ury-self.lly)

    path = rect

    def height(self):
        """return height of bbox"""
        return unit.t_pt(self.ury-self.lly)

    def width(self):
        """return width of bbox"""
        return unit.t_pt(self.urx-self.llx)

    def top(self):
        """return top coordinate of bbox"""
        return unit.t_pt(self.ury)

    def bottom(self):
        """return bottom coordinate of bbox"""
        return unit.t_pt(self.lly)

    def left(self):
        """return left coordinate of bbox"""
        return unit.t_pt(self.llx)

    def right(self):
        """return right coordinate of bbox"""
        return unit.t_pt(self.urx)


class bbox(_bbox):

    """class for bounding boxes"""

    def __init__(self, llx=None, lly=None, urx=None, ury=None):
        if llx is not None:
            llx = unit.topt(llx)
        if lly is not None:
            lly = unit.topt(lly)
        if urx is not None:
            urx = unit.topt(urx)
        if ury is not None:
            ury = unit.topt(ury)
        _bbox.__init__(self, llx, lly, urx, ury)

