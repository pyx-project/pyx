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

import base, trafo, unit, canvas

# PostScript-procedure definitions
# cf. file: 5002.EPSF_Spec_v3.0.pdf     

_PSProlog = """/BeginEPSF {
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
} bind def
/EndEPSF {
  count op_count sub {pop} repeat % Clean up stacks
  countdictstack dict_count sub {end} repeat
  b4_Inc_state restore
} bind def"""

# known paperformats as tuple(width, height)

_paperformats = { "a4"      : ("210 t mm",  "297 t mm"), 
                  "a3"      : ("297 t mm",  "420 t mm"), 
                  "a2"      : ("420 t mm",  "594 t mm"), 
                  "a1"      : ("594 t mm",  "840 t mm"), 
                  "a0"      : ("840 t mm", "1188 t mm"), 
                  "a0b"     : ("910 t mm", "1350 t mm"), 
                  "letter"  : ("8.5 t in",   "11 t in"),
                  "legal"   : ("8.5 t in",   "14 t in")}

#
# PSCmd class
#

class PSCmd(base.PSOp):

    """ PSCmd is the base class of all visible elements

    Visible elements, are those, that can be embedded in the Canvas
    and posses a bbox. Furthermore, they can write themselves to
    an open file and to an EPS file
    
    """
    
    def bbox(self):
       raise NotImplementedError, "cannot call virtual method bbox()"
       
    def write(self, file):
        raise NotImplementedError, "cannot call virtual method write()"

    def writetofile(self, filename, paperformat=None, rotated=0, fittosize=0, margin="1 t cm"):
        """write canvas to EPS file

        If paperformat is set to a known paperformat, the output will be centered on 
        the page (and optionally rotated)

        If fittosize is set as well, then the output is scaled to the size of the
        page (minus margin).

        """


        try:
            file = open(filename + ".eps", "w")
        except IOError:
            assert 0, "cannot open output file"                 # TODO: Fehlerbehandlung...

        abbox=self.bbox()
        ctrafo=None     # global transformation of canvas

        if rotated:
            ctrafo = trafo._rotate(90,
                                   0.5*(abbox.llx+abbox.urx),
                                   0.5*(abbox.lly+abbox.ury))

        if paperformat:
            # center (optionally rotated) output on page
            try:
                width, height = _paperformats[paperformat]
                width = unit.topt(width)
                height = unit.topt(height)
            except KeyError:
                raise KeyError, "unknown paperformat '%s'" % paperformat

            if not ctrafo:
                ctrafo=trafo.trafo()

            ctrafo = ctrafo._translate(0.5*(width -(abbox.urx-abbox.llx))-
                                       abbox.llx, 
                                       0.5*(height-(abbox.ury-abbox.lly))-
                                       abbox.lly)
            
            if fittosize:
                # scale output to pagesize - margins
                margin=unit.topt(margin)

                if rotated:
                    sfactor = min((height-2*margin)/(abbox.urx-abbox.llx), 
                                  (width-2*margin)/(abbox.ury-abbox.lly))
                else:
                    sfactor = min((width-2*margin)/(abbox.urx-abbox.llx), 
                                  (height-2*margin)/(abbox.ury-abbox.lly))
                    
                ctrafo = ctrafo._scale(sfactor, sfactor, 0.5*width, 0.5*height)
                          
                
        elif fittosize:
            assert 0, "must specify paper size for fittosize" # TODO: exception...

        # if there has been a global transformation, adjust the bounding box
        # accordingly
        if ctrafo:
            abbox = abbox.transform(ctrafo) 

        file.write("%!PS-Adobe-3.0 EPSF 3.0\n")
        abbox.write(file)
        file.write("%%Creator: pyx 0.0.1\n") 
        file.write("%%%%Title: %s.eps\n" % filename) 
        # file.write("%%CreationDate: %s" % ) 
        file.write("%%EndComments\n") 
        file.write("%%BeginProlog\n") 
        file.write(_PSProlog)
        file.write("\n%%EndProlog\n") 

        # now apply a potential global transformation
        if ctrafo: ctrafo.write(file)   

        file.write("%f setlinewidth\n" % unit.topt(canvas.linewidth.normal))
        
        # here comes the actual content
        self.write(file)
        
        file.write("showpage\n")
        file.write("%%Trailer\n")
        file.write("%%EOF\n")

