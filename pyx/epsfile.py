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

import re
import base, bbox, canvas, path, unit, trafo

def _readbbox(filename):
    """returns bounding box of EPS file filename as 4-tuple (llx, lly, urx, ury)"""

    try:
        file = open(filename, "r")
    except:
        raise IOError, "cannot open EPS file '%s'" % filename

    bbpattern = re.compile( r"""^%%BoundingBox:\s+([+-]?\d+)
                                             \s+([+-]?\d+)
                                             \s+([+-]?\d+)
                                             \s+([+-]?\d+)\s*$""" , re.VERBOSE)

    for line in file.xreadlines():

        if line=="%%EndComments\n": 
            # TODO: BoundingBox-Deklaration kann auch an Ende von Datei
            #       verschoben worden sein...
            #       ...but evaluation of such a bbox directive requires
            #       a parsing of the DSC!
            raise IOError, \
                  "bounding box not found in header of EPS file '%s'" % \
                  filename

        bbmatch = bbpattern.match(line)
        if bbmatch is not None:
            # conversion strings->int
            (llx, lly, urx, ury) = map(int, bbmatch.groups()) 
            return bbox.bbox(llx, lly, urx, ury)
    else:
        raise IOError, \
              "bounding box not found in EPS file '%s'" % filename


class epsfile(base.PSCmd):

    """class for epsfiles"""

    def __init__(self,
                 filename,
                 x = "0 t m", y = "0 t m",
                 width = None, height = None, scale=None,
                 align = "bl",
                 clip = 1,
                 showbbox = 0,
                 translatebbox = 1):
        """inserts epsfile

        inserts EPS file named filename at position (x,y).  If clip is
        set, the result gets clipped to the bbox of the EPS file. If
        translatebbox is not set, the EPS graphics is not translated to
        the corresponding origin. With showbb set, the bbox is drawn.
        
        """

        self.filename    = filename
        self.mybbox      = _readbbox(self.filename)
        
        self._x           = unit.topt(x)
        self._y           = unit.topt(y)

        # determine scaling in x and y direction
        self.scalex = self.scaley = scale

        if (width is not None or height is not None):
            if scale is not None:
                raise ValueError("cannot set both width and/or height and scale simultaneously")
            if height is not None:
                self.scalex = unit.topt(height)/(self.mybbox.urx-self.mybbox.llx)
            if width is not None:
                self.scaley = unit.topt(width)/(self.mybbox.ury-self.mybbox.lly)

            if self.scalex is None:
                self.scalex = self.scaley

            if self.scaley is None:
                self.scaley = self.scalex

        # now, we set the actual width and height of the eps file (after a
        # possible scaling)
        self._width  = (self.mybbox.urx-self.mybbox.llx)
        if self.scalex:
            self._width *= self.scalex
            
        self._height  = (self.mybbox.ury-self.mybbox.lly)
        if self.scaley:
            self._height *= self.scaley

        # take alignment into account
        self.align       = align
        if self.align[0]=="b":
            pass
        elif self.align[0]=="c":
            self._y -= self._height/2.0
        elif self.align[0]=="t":
            self._y -= self._height
        else:
            raise ValueError("vertical alignment can only be b (bottom), c (center), or t (top)")

        if self.align[1]=="l":
            pass
        elif self.align[1]=="c":
            self._x -= self._width/2.0
        elif self.align[1]=="r":
            self._x -= self._width
        else:
            raise ValueError("horizontal alignment can only be l (left), c (center), or r (right)")
        
        self.clip = clip
        self.translatebbox = translatebbox
        self.showbbox = showbbox

        self.trafo = trafo._translate(self._x, self._y)

        if self.scalex is not None:
            self.trafo = self.trafo * trafo._scale(self.scalex, self.scaley)
            
        if translatebbox:
            self.trafo = self.trafo * trafo._translate(-self.mybbox.llx, -self.mybbox.lly)

    def bbox(self):
        return self.mybbox.transform(self.trafo)

    def write(self, file):
        try:
            epsfile=open(self.filename,"r")
        except:
            raise IOError, "cannot open EPS file '%s'" % self.filename 

        file.write("BeginEPSF\n")



        bbrect = self.mybbox.rect().transformed(self.trafo)
        
        if self.showbbox:
            canvas._newpath().write(file)
            bbrect.write(file)
            canvas._stroke().write(file)
            
        if self.clip:
            canvas._newpath().write(file)
            bbrect.write(file)
            canvas._clip().write(file)

        self.trafo.write(file)

        file.write("%%%%BeginDocument: %s\n" % self.filename)
        file.write(epsfile.read()) 
        file.write("%%EndDocument\n")
        file.write("EndEPSF\n")
