#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2005 Jörg Lehmann <joergl@users.sourceforge.net>
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

import sys
import pswriter, pdfwriter, trafo, unit


class paperformat:

    def __init__(self, width, height, name=None):
        self.width = width
        self.height = height
        self.name = name

paperformat.A4 = paperformat(210 * unit.t_mm, 297  * unit.t_mm, "A4")
paperformat.A3 = paperformat(297 * unit.t_mm, 420  * unit.t_mm, "A3")
paperformat.A2 = paperformat(420 * unit.t_mm, 594  * unit.t_mm, "A2")
paperformat.A1 = paperformat(594 * unit.t_mm, 840  * unit.t_mm, "A1")
paperformat.A0 = paperformat(840 * unit.t_mm, 1188 * unit.t_mm, "A0")
paperformat.A0b = paperformat(910 * unit.t_mm, 1370 * unit.t_mm, None) # dedicated to our friends in Augsburg
paperformat.Letter = paperformat(8.5 * unit.t_inch, 11 * unit.t_inch, "Letter")
paperformat.Legal = paperformat(8.5 * unit.t_inch, 14 * unit.t_inch, "Legal")

def _paperformatfromstring(name):
    return getattr(paperformat, name.capitalize())


class page:

    def __init__(self, canvas, pagename=None, paperformat=paperformat.A4, rotated=0, centered=1, fittosize=0, 
                 margin=1 * unit.t_cm, bboxenlarge=1 * unit.t_pt, bbox=None):
        self.canvas = canvas
        self.pagename = pagename
        # support for depricated string specification of paper formats
        try:
            paperformat + ""
        except:
            self.paperformat = paperformat
        else:
            self.paperformat = _paperformatfromstring(paperformat)
            sys.stderr.write("*** PyX Warning: specification of paperformat by string is depricated, use document.paperformat.%s instead\n" % paperformat.capitalize())
            
        self.rotated = rotated
        self.centered = centered
        self.fittosize = fittosize
        self.margin = margin
        self.bboxenlarge = bboxenlarge
        self.bbox = bbox

    def pagetrafo(self, abbox):
        """ calculate a trafo which rotates and fits a canvas on the page

        The canvas extents are described by abbox, which, however, is only used
        when during page construction no bbox has been specified.
        """
        if self.bbox is not None:
            abbox = self.bbox
        if self.rotated or self.centered or self.fittosize:
            paperwidth, paperheight = self.paperformat.width, self.paperformat.height

            # center (optionally rotated) output on page
            if self.rotated:
                atrafo = trafo.rotate(90).translated(paperwidth, 0)
                if self.centered or self.fittosize:
                    atrafo = atrafo.translated(-0.5*(paperwidth - abbox.height()) + abbox.bottom(),
                                               0.5*(paperheight - abbox.width()) - abbox.left())
            else:
                if self.centered or self.fittosize:
                    atrafo = trafo.trafo()
                else:
                    return None # no page transformation needed
                if self.centered or self.fittosize:
                    atrafo = atrafo.translated(0.5*(paperwidth - abbox.width())  - abbox.left(),
                                               0.5*(paperheight - abbox.height()) - abbox.bottom())

            if self.fittosize:

                if 2*self.margin > paperwidth or 2*self.margin > paperheight:
                    raise ValueError("Margins too broad for selected paperformat. Aborting.")

                paperwidth -= 2 * self.margin
                paperheight -= 2 * self.margin

                # scale output to pagesize - margins
                if self.rotated:
                    sfactor = min(unit.topt(paperheight)/abbox.width_pt(), unit.topt(paperwidth)/abbox.height_pt())
                else:
                    sfactor = min(unit.topt(paperwidth)/abbox.width_pt(), unit.topt(paperheight)/abbox.height_pt())

                atrafo = atrafo.scaled(sfactor, sfactor, self.margin + 0.5*paperwidth, self.margin + 0.5*paperheight)

            return atrafo
        
        return None # no page transformation needed


class document:

    """holds a collection of page instances which are output as pages of a document"""

    def __init__(self, pages=[]):
        self.pages = pages

    def append(self, page):
        self.pages.append(page)

    def writePSfile(self, filename, *args, **kwargs):
        pswriter.pswriter(self, filename, *args, **kwargs)

    def writeEPSfile(self, filename, *args, **kwargs):
        pswriter.epswriter(self, filename, *args, **kwargs)

    def writePDFfile(self, filename, *args, **kwargs):
        pdfwriter.PDFwriter(self, filename, *args, **kwargs)

    def writetofile(self, filename, *args, **kwargs):
        if filename[-4:] == ".eps":
            self.writeEPSfile(filename, *args, **kwargs)
        elif filename[-4:] == ".pdf":
            self.writePDFfile(filename, *args, **kwargs)
        else:
            raise ValueError("unknown file extension")
