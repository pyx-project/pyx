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

import unit

# helper routine for bbox manipulations

def _nmin(x, y):
    """minimum of two values, where None represents +infinity, not -infinity as
    in standard min implementation of python"""
    if x is None: return y
    if y is None: return x
    return min(x,y)

#
# class representing bounding boxes
#

class bbox:

    """class for bounding boxes"""

    def __init__(self, llx=None, lly=None, urx=None, ury=None):
        self.llx=llx
        self.lly=lly
        self.urx=urx
        self.ury=ury
    
    def __add__(self, other):
        """join two bboxes"""

        return bbox(_nmin(self.llx, other.llx), _nmin(self.lly, other.lly),
                    max(self.urx, other.urx), max(self.ury, other.ury))

    def __mul__(self, other):
        """return intersection of two bboxes"""

        return bbox(max(self.llx, other.llx), max(self.lly, other.lly),
                    _nmin(self.urx, other.urx), _nmin(self.ury, other.ury))

    def __str__(self):
        return "%s %s %s %s" % (self.llx, self.lly, self.urx, self.ury)

    def write(self, file):
        file.write("%%%%BoundingBox: %d %d %d %d\n" %
                   (self.llx, self.lly, self.urx, self.ury))
        # TODO: add HighResBBox

    def intersects(self, other):
        """check, if two bboxes intersect eachother"""
        
        return not (self.llx > other.urx or
                    self.lly > other.ury or
                    self.urx < other.llx or
                    self.ury < other.lly)

    def transform(self, trafo):
        """return bbox transformed by trafo"""
        # we have to transform all four corner points of the bbox
        (llx, lly)=trafo._apply(self.llx, self.lly)
        (lrx, lry)=trafo._apply(self.urx, self.lly)
        (urx, ury)=trafo._apply(self.urx, self.ury)
        (ulx, uly)=trafo._apply(self.llx, self.ury)

        # now, by sorting, we obtain the lower left and upper right corner
        # of the new bounding box. 

        return bbox(min(llx, lrx, urx, ulx), min(lly, lry, ury, uly),
                    max(llx, lrx, urx, ulx), max(lly, lry, ury, uly))

    def enhance(self, size):
        """return bbox enhanced in all directions by size"""
        size = unit.topt(unit.length(size, default_type="v"))
        return bbox(self.llx-size, self.lly-size, 
                    self.urx+size, self.ury+size)

    def rect(self):
        """return rectangle corresponding to bbox"""
        import path
        return path._rect(self.llx, self.lly, self.urx-self.llx, self.ury-self.lly)
