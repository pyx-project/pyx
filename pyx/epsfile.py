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

class epsfile(base.PSCmd):

    """class for epsfiles"""

    def __init__(self,
                 filename,
                 x = "0 t m", y = "0 t m",
                 clip = 1,
                 translatebb = 1,
                 showbb = 0):
        """inserts epsfile

        inserts EPS file named filename at position (x,y).  If clip is
        set, the result gets clipped to the bbox of the EPS file. If
        translatebb is not set, the EPS graphics is not translated to
        the corresponding origin. With showbb set, the bbox is drawn.
        
        """
        self.x           = unit.topt(x)
        self.y           = unit.topt(y)
        self.filename    = filename
        self.clip        = clip
        self.translatebb = translatebb
        self.showbb      = showbb
        self.mybbox      = self._readbbox(translatebb)

    def _readbbox(self, translatebb):
        """returns bounding box of EPS file filename as 4-tuple (llx, lly, urx, ury)"""
        
        try:
            file = open(self.filename, "r")
        except:
            raise IOError, "cannot open EPS file '%s'" % self.filename

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
                      self.filename
            
            bbmatch = bbpattern.match(line)
            if bbmatch is not None:
                # conversion strings->int
                (llx, lly, urx, ury) = map(int, bbmatch.groups()) 
                if translatebb:
                    (llx, lly, urx, ury) = (0, 0, urx - llx, ury - lly)
                return bbox.bbox(llx, lly, urx, ury)
        else:
            raise IOError, \
                  "bounding box not found in EPS file '%s'" % self.filename

    def bbox(self):
        return self.mybbox

    def write(self, file):
        try:
            epsfile=open(self.filename,"r")
        except:
            raise IOError, "cannot open EPS file '%s'" % self.filename 

        file.write("BeginEPSF\n")
        
        trafo._translation(self.x, self.y).write(file)
        
        if self.translatebb:
            trafo._translation(-self.mybbox.llx, -self.mybbox.lly).write(file)

        bbrect = path._rect(self.mybbox.llx,
                            self.mybbox.lly, 
                            self.mybbox.urx-self.mybbox.llx,
                            self.mybbox.ury-self.mybbox.lly)
        
        if self.showbb:
            canvas._newpath().write(file)
            bbrect.write(file)
            canvas._stroke().write(file)
            
        if self.clip:
            canvas._newpath().write(file)
            bbrect.write(file)
            canvas._clip().write(file)

        file.write("%%%%BeginDocument: %s\n" % self.filename)
        file.write(epsfile.read()) 
        file.write("%%EndDocument\n")
        file.write("EndEPSF\n")
