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

class bbox_pt:
    
    """class for bounding boxes

    This variant requires points in the constructor, and is used for internal
    purposes."""

    def __init__(self, llx_pt, lly_pt, urx_pt, ury_pt):
        self.llx_pt = llx_pt
        self.lly_pt = lly_pt
        self.urx_pt = urx_pt
        self.ury_pt = ury_pt

    def __add__(self, other):
        """join two bboxes"""
        return bbox_pt(min(self.llx_pt, other.llx_pt), min(self.lly_pt, other.lly_pt),
                     max(self.urx_pt, other.urx_pt), max(self.ury_pt, other.ury_pt))

    def __iadd__(self, other):
        """join two bboxes inplace"""
        self.llx_pt = min(self.llx_pt, other.llx_pt)
        self.lly_pt = min(self.lly_pt, other.lly_pt)
        self.urx_pt = max(self.urx_pt, other.urx_pt)
        self.ury_pt = max(self.ury_pt, other.ury_pt)
        return self

    def __mul__(self, other):
        """return intersection of two bboxes"""
        return bbox_pt(max(self.llx_pt, other.llx_pt), max(self.lly_pt, other.lly_pt),
                     min(self.urx_pt, other.urx_pt), min(self.ury_pt, other.ury_pt))

    def __imul__(self, other):
        """intersect two bboxes in place"""
        self.llx_pt = max(self.llx_pt, other.llx_pt)
        self.lly_pt = max(self.lly_pt, other.lly_pt)
        self.urx_pt = min(self.urx_pt, other.urx_pt)
        self.ury_pt = min(self.ury_pt, other.ury_pt)
        return self

    def __str__(self):
        return "%s %s %s %s" % (self.llx_pt, self.lly_pt, self.urx_pt, self.ury_pt)

    def outputPS(self, file):
        file.write("%%%%BoundingBox: %d %d %d %d\n" %
                   (math.floor(self.llx_pt), math.floor(self.lly_pt),
                    math.ceil(self.urx_pt), math.ceil(self.ury_pt)))
        file.write("%%%%HiResBoundingBox: %g %g %g %g\n" %
                   (self.llx_pt, self.lly_pt, self.urx_pt, self.ury_pt))

    def outputPDF(self, file):
        file.write("[%d %d %d %d]\n" %
                   (math.floor(self.llx_pt), math.floor(self.lly_pt),
                    math.ceil(self.urx_pt), math.ceil(self.ury_pt)))

    def intersects(self, other):
        """check, if two bboxes intersect eachother"""
        return not (self.llx_pt > other.urx_pt or
                    self.lly_pt > other.ury_pt or
                    self.urx_pt < other.llx_pt or
                    self.ury_pt < other.lly_pt)

    def transform(self, trafo):
        """transform bbox in place by trafo"""
        # we have to transform all four corner points of the bbox
        llx_pt, lly_pt = trafo._apply(self.llx_pt, self.lly_pt)
        lrx, lry = trafo._apply(self.urx_pt, self.lly_pt)
        urx_pt, ury_pt = trafo._apply(self.urx_pt, self.ury_pt)
        ulx, uly = trafo._apply(self.llx_pt, self.ury_pt)

        # Now, by sorting, we obtain the lower left and upper right corner
        # of the new bounding box.
        self.llx_pt = min(llx_pt, lrx, urx_pt, ulx)
        self.lly_pt = min(lly_pt, lry, ury_pt, uly)
        self.urx_pt = max(llx_pt, lrx, urx_pt, ulx)
        self.ury_pt = max(lly_pt, lry, ury_pt, uly)

    def transformed(self, trafo):
        """return bbox transformed by trafo"""
        # we have to transform all four corner points of the bbox
        llx_pt, lly_pt = trafo._apply(self.llx_pt, self.lly_pt)
        lrx, lry = trafo._apply(self.urx_pt, self.lly_pt)
        urx_pt, ury_pt = trafo._apply(self.urx_pt, self.ury_pt)
        ulx, uly = trafo._apply(self.llx_pt, self.ury_pt)

        # Now, by sorting, we obtain the lower left and upper right corner
        # of the new bounding box. 
        return bbox_pt(min(llx_pt, lrx, urx_pt, ulx), min(lly_pt, lry, ury_pt, uly),
                     max(llx_pt, lrx, urx_pt, ulx), max(lly_pt, lry, ury_pt, uly))

    def enlarge(self, all=0, bottom=None, left=None, top=None, right=None):
        """enlarge bbox in place

        all is used, if bottom, left, top and/or right are not given.

        """
        bottom_pt = left_pt = top_pt = right_pt = unit.topt(all)
        if bottom is not None:
           bottom_pt = unit.topt(bottom)
        if left is not None:
           left_pt = unit.topt(left)
        if top is not None:
           top_pt = unit.topt(top)
        if right is not None:
           right_pt = unit.topt(right)
        self.llx_pt -= left_pt
        self.lly_pt -= bottom_pt
        self.urx_pt += right_pt
        self.ury_pt += top_pt

    def enlarged(self, all=0, bottom=None, left=None, top=None, right=None):
        """return bbox enlarged

        all is used, if bottom, left, top and/or right are not given.

        """
        bottom_pt = left_pt = top_pt = right_pt = unit.topt(all)
        if bottom is not None:
           bottom_pt = unit.topt(bottom)
        if left is not None:
           left_pt = unit.topt(left)
        if top is not None:
           top_pt = unit.topt(top)
        if right is not None:
           right_pt = unit.topt(right)
        return bbox_pt(self.llx_pt-left_pt, self.lly_pt-bottom_pt, self.urx_pt+right_pt, self.ury_pt+top_pt)

    def rect(self):
        """return rectangle corresponding to bbox"""
        import path
        return path.rect_pt(self.llx_pt, self.lly_pt, self.urx_pt-self.llx_pt, self.ury_pt-self.lly_pt)

    path = rect

    def height(self):
        """return height of bbox"""
        return (self.ury_pt-self.lly_pt) * unit.t_pt

    def width(self):
        """return width of bbox"""
        return (self.urx_pt-self.llx_pt) * unit.t_pt

    def top(self):
        """return top coordinate of bbox"""
        return self.ury_pt * unit.t_pt

    def bottom(self):
        """return bottom coordinate of bbox"""
        return self.lly_pt * unit.t_pt

    def left(self):
        """return left coordinate of bbox"""
        return self.llx_pt * unit.t_pt

    def right(self):
        """return right coordinate of bbox"""
        return self.urx_pt * unit.t_pt

    def center(self):
        """return coordinates of the center of the bbox"""
        return 0.5 * (self.llx_pt+self.urx_pt) * unit.t_pt, 0.5 * (self.lly_pt+self.ury_pt) * unit.t_pt


class bbox(bbox_pt):

    """class for bounding boxes"""

    def __init__(self, llx_pt, lly_pt, urx_pt, ury_pt):
        llx_pt = unit.topt(llx_pt)
        lly_pt = unit.topt(lly_pt)
        urx_pt = unit.topt(urx_pt)
        ury_pt = unit.topt(ury_pt)
        bbox_pt.__init__(self, llx_pt, lly_pt, urx_pt, ury_pt)
