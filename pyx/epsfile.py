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

import string
import base, bbox, prolog, pykpathsea, unit, trafo

# PostScript-procedure definitions (cf. 5002.EPSF_Spec_v3.0.pdf)
# with important correction in EndEPSF:
#   end operator is missing in the spec!

_BeginEPSF = prolog.definition("BeginEPSF", """{
  /b4_Inc_state save def
  /dict_count countdictstack def
  /op_count count 1 sub def
  userdict begin
  /showpage { } def
  0 setgray 0 setlinecap
  1 setlinewidth 0 setlinejoin
  10 setmiterlimit [ ] 0 setdash newpath
  /languagelevel where
  {pop languagelevel
  1 ne
    {false setstrokeadjust false setoverprint
    } if
  } if
} bind""")

_EndEPSF = prolog.definition("EndEPSF", """{
  end
  count op_count sub {pop} repeat
  countdictstack dict_count sub {end} repeat
  b4_Inc_state restore
} bind""")

def _readbbox(filename):
    """returns bounding box of EPS file filename"""

    file = open(filename, "r")

    # readline
    def readlinewithexception():
        line = file.readline()
        if not len(line):
            raise IOError("unexpected end of file")
        return line

    # check the %! header comment
    if not readlinewithexception().startswith("%!"):
        raise IOError("file doesn't start with a '%!' header comment")

    bboxatend = 0
    # parse the header (use the first BoundingBox)
    while 1:
        line = readlinewithexception()
        if line.startswith("%%BoundingBox:") and not bboxatend:
            values = line.split(":", 1)[1].split()
            if values == ["(atend)"]:
                bboxatend = 1
            else:
                if len(values) != 4:
                    raise IOError("invalid number of bounding box values")
                return bbox.bbox_pt(*map(int, values))
        elif (line.rstrip() == "%%EndComments" or
              (line[0] != "%" and line[1] not in string.whitespace)): # implicit end of comments section
            break
    if not bboxatend:
        raise IOError("no bounding box information found")

    # parse the body
    nesting = 0 # allow for nested documents
    while 1:
        line = readlinewithexception()
        if line.startswith("%%BeginData:"):
            values = line.split(":", 1)[1].split()
            if len(values) > 3:
                raise IOError("invalid number of arguments")
            if len(values) == 3:
                if values[2] == "Lines":
                    for i in xrange(int(values[0])):
                        readlinewithexception()
                elif values[2] != "Bytes":
                    raise IOError("invalid bytesorlines-value")
                else:
                    file.read(int(values[0]))
            else:
                file.read(int(values[0]))
            line = readlinewithexception()
            # ignore tailing whitespace/newline for binary data
            if (len(values) < 3 or values[2] != "Lines") and not len(line.strip()):
                line = readlinewithexception()
            if line.rstrip() != "%%EndData":
                raise IOError("missing EndData")
        elif line.startswith("%%BeginBinary:"):
            file.read(int(line.split(":", 1)[1]))
            line = readlinewithexception()
            # ignore tailing whitespace/newline
            if not len(line.strip()):
                line = readlinewithexception()
            if line.rstrip() != "%%EndBinary":
                raise IOError("missing EndBinary")
        elif line.startswith("%%BeginDocument:"):
            nesting += 1
        elif line.rstrip() == "%%EndDocument":
            if nesting < 1:
                raise IOError("unmatched EndDocument")
            nesting -= 1
        elif not nesting and line.rstrip() == "%%Trailer":
            break

    usebbox = None
    # parse the trailer (use the last BoundingBox)
    while 1:
        line = file.readline()
        if line.startswith("%%BoundingBox:"):
            values = line.split(":", 1)[1].split()
            if len(values) != 4:
                raise IOError("invalid number of bounding box values")
            usebbox = bbox.bbox_pt(*map(int, values))
        elif not len(line):
            break
    if usebbox is None:
        raise IOError("missing bounding box information in document trailer")
    return usebbox


class epsfile(base.canvasitem):

    """class for epsfiles"""

    def __init__(self,
                 x, y, filename,
                 width=None, height=None, scale=None, align="bl",
                 clip=1, translatebbox=1, bbox=None,
                 kpsearch=0):
        """inserts epsfile

        Object for an EPS file named filename at position (x,y). Width, height,
        scale and aligment can be adjusted by the corresponding parameters. If
        clip is set, the result gets clipped to the bbox of the EPS file. If
        translatebbox is not set, the EPS graphics is not translated to the
        corresponding origin. If bbox is not None, it overrides the bounding
        box in the epsfile itself. If kpsearch is set then filename is searched
        using the kpathsea library.
        """

        self.x_pt = unit.topt(x)
        self.y_pt = unit.topt(y)
        if kpsearch:
            self.filename = pykpathsea.find_file(filename, pykpathsea.kpse_pict_format)
        else:
            self.filename = filename
        self.mybbox = bbox or _readbbox(self.filename)

        # determine scaling in x and y direction
        self.scalex = self.scaley = scale

        if width is not None or height is not None:
            if scale is not None:
                raise ValueError("cannot set both width and/or height and scale simultaneously")
            if height is not None:
                self.scaley = unit.topt(height)/(self.mybbox.ury_pt-self.mybbox.lly_pt)
            if width is not None:
                self.scalex = unit.topt(width)/(self.mybbox.urx_pt-self.mybbox.llx_pt)

            if self.scalex is None:
                self.scalex = self.scaley
            if self.scaley is None:
                self.scaley = self.scalex

        # set the actual width and height of the eps file (after a
        # possible scaling)
        self.width_pt  = self.mybbox.urx_pt-self.mybbox.llx_pt
        if self.scalex:
            self.width_pt *= self.scalex

        self.height_pt = self.mybbox.ury_pt-self.mybbox.lly_pt
        if self.scaley:
            self.height_pt *= self.scaley

        # take alignment into account
        self.align       = align
        if self.align[0]=="b":
            pass
        elif self.align[0]=="c":
            self.y_pt -= self.height_pt/2.0
        elif self.align[0]=="t":
            self.y_pt -= self.height_pt
        else:
            raise ValueError("vertical alignment can only be b (bottom), c (center), or t (top)")

        if self.align[1]=="l":
            pass
        elif self.align[1]=="c":
            self.x_pt -= self.width_pt/2.0
        elif self.align[1]=="r":
            self.x_pt -= self.width_pt
        else:
            raise ValueError("horizontal alignment can only be l (left), c (center), or r (right)")

        self.clip = clip
        self.translatebbox = translatebbox

        self.trafo = trafo.translate_pt(self.x_pt, self.y_pt)

        if self.scalex is not None:
            self.trafo = self.trafo * trafo.scale_pt(self.scalex, self.scaley)

        if translatebbox:
            self.trafo = self.trafo * trafo.translate_pt(-self.mybbox.llx_pt, -self.mybbox.lly_pt)

    def bbox(self):
        return self.mybbox.transformed(self.trafo)

    def prolog(self):
        return [_BeginEPSF, _EndEPSF]

    def outputPS(self, file):
        try:
            epsfile=open(self.filename,"r")
        except:
            raise IOError, "cannot open EPS file '%s'" % self.filename 

        file.write("BeginEPSF\n")

        bbrect = self.mybbox.rect().transformed(self.trafo)

        if self.clip:
            file.write("newpath\n")
            bbrect.outputPS(file)
            file.write("clip\n")

        self.trafo.outputPS(file)

        file.write("%%%%BeginDocument: %s\n" % self.filename)
        file.write(epsfile.read()) 
        file.write("%%EndDocument\n")
        file.write("EndEPSF\n")
