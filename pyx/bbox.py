#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2002-2004 Jörg Lehmann <joergl@users.sourceforge.net>
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
import unit

#
# classes representing bounding boxes
#

class _bbox:
    
    """class for bounding boxes

    This variant requires points in the constructor, and is used for internal
    purposes."""

    def __init__(self, llx, lly, urx, ury):
        self.llx = llx
        self.lly = lly
        self.urx = urx
        self.ury = ury

    def __add__(self, other):
        """join two bboxes"""
        return _bbox(min(self.llx, other.llx), min(self.lly, other.lly),
                     max(self.urx, other.urx), max(self.ury, other.ury))

    def __iadd__(self, other):
        """join two bboxes inplace"""
        self.llx = min(self.llx, other.llx)
        self.lly = min(self.lly, other.lly)
        self.urx = max(self.urx, other.urx)
        self.ury = max(self.ury, other.ury)
        return self

    def __mul__(self, other):
        """return intersection of two bboxes"""
        return _bbox(max(self.llx, other.llx), max(self.lly, other.lly),
                     min(self.urx, other.urx), min(self.ury, other.ury))

    def __imul__(self, other):
        """intersect two bboxes in place"""
        self.llx = max(self.llx, other.llx)
        self.lly = max(self.lly, other.lly)
        self.urx = min(self.urx, other.urx)
        self.ury = min(self.ury, other.ury)
        return self

    def __str__(self):
        return "%s %s %s %s" % (self.llx, self.lly, self.urx, self.ury)

    def outputPS(self, file):
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

    def transform(self, trafo):
        """transform bbox in place by trafo"""
        # we have to transform all four corner points of the bbox
        llx, lly = trafo._apply(self.llx, self.lly)
        lrx, lry = trafo._apply(self.urx, self.lly)
        urx, ury = trafo._apply(self.urx, self.ury)
        ulx, uly = trafo._apply(self.llx, self.ury)

        # Now, by sorting, we obtain the lower left and upper right corner
        # of the new bounding box.
        self.llx = min(llx, lrx, urx, ulx)
        self.lly = min(lly, lry, ury, uly)
        self.urx = max(llx, lrx, urx, ulx)
        self.ury = max(lly, lry, ury, uly)

    def transformed(self, trafo):
        """return bbox transformed by trafo"""
        # we have to transform all four corner points of the bbox
        llx, lly = trafo._apply(self.llx, self.lly)
        lrx, lry = trafo._apply(self.urx, self.lly)
        urx, ury = trafo._apply(self.urx, self.ury)
        ulx, uly = trafo._apply(self.llx, self.ury)

        # Now, by sorting, we obtain the lower left and upper right corner
        # of the new bounding box. 
        return _bbox(min(llx, lrx, urx, ulx), min(lly, lry, ury, uly),
                     max(llx, lrx, urx, ulx), max(lly, lry, ury, uly))

    def enlarged(self, all=0, bottom=None, left=None, top=None, right=None):
        """enlarge bbox in place

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
        self.llx -= _left
        self.lly -= _bottom
        self.urx += _right
        self.ury += top

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

    def __init__(self, llx, lly, urx, ury):
        llx = unit.topt(llx)
        lly = unit.topt(lly)
        urx = unit.topt(urx)
        ury = unit.topt(ury)
        _bbox.__init__(self, llx, lly, urx, ury)

