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

import pswriter, pdfwriter


class paperformat:

    def __init__(self, height, width, name=None):
        self.height = height
        self.width = width
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
    return getattr(paperformat, paperformat.capitalize())


class page:

    def __init__(self, canvas, pagename=None, paperformat=paperformat.A4, rotated=0, fittosize=0,
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
            sys.stderr("*** PyX Warning: specification of paperformat by string is depricated, use document.paperformat.%s instead\n" % paperformat.capitalize())
        self.rotated = rotated
        self.fittosize = fittosize
        self.margin = margin
        self.bboxenlarge = bboxenlarge
        self.bbox = bbox

#     def outputPS(self, file):
#         file.write("%%%%PageMedia: %s\n" % self.paperformat)
#         file.write("%%%%PageOrientation: %s\n" % (self.rotated and "Landscape" or "Portrait"))
#         # file.write("%%%%PageBoundingBox: %d %d %d %d\n" % (math.floor(pbbox.llx_pt), math.floor(pbbox.lly_pt),
#         #                                                    math.ceil(pbbox.urx_pt), math.ceil(pbbox.ury_pt)))
# 
#         # page setup section
#         file.write("%%BeginPageSetup\n")
#         file.write("/pgsave save def\n")
#         # for scaling, we need the real bounding box of the page contents
#         pbbox = canvas.bbox(self)
#         pbbox.enlarge(self.bboxenlarge)
#         ptrafo = calctrafo(pbbox, self.paperformat, self.margin, self.rotated, self.fittosize)
#         if ptrafo:
#             ptrafo.outputPS(file)
#         file.write("%f setlinewidth\n" % unit.topt(style.linewidth.normal))
#         file.write("%%EndPageSetup\n")
# 
#         # here comes the actual content
#         canvas.outputPS(self, file)
#         file.write("pgsave restore\n")
#         file.write("showpage\n")
#         # file.write("%%PageTrailer\n")


class document:

    """holds a collection of page instances which are output as pages of a document"""

    def __init__(self, pages=[]):
        self.pages = pages

    def append(self, page):
        self.pages.append(page)

    def writePSfile(self, filename, *args, **kwargs):
        writer = pswriter.pswriter(self)
        writer.write(filename, *args, **kwargs)

    def writeEPSfile(self, filename, *args, **kwargs):
        writer = pswriter.epswriter(self)
        writer.write(filename, *args, **kwargs)

    def writePDFfile(self, filename, *args, **kwargs):
        writer = pdfwriter.pdfwriter(self)
        writer.write(filename, *args, **kwargs)

    def writetofile(self, filename, *args, **kwargs):
        if filename[-4:] == ".eps":
            self.writeEPSfile(filename, *args, **kwargs)
        elif filename[-4:] == ".pdf":
            self.writePDFfile(filename, *args, **kwargs)
        else:
            raise ValueError("unknown file extension")


#     def writePSfile(self, filename):
#         """write pages to PS file """
# 
#         if filename[-3:]!=".ps":
#             filename = filename + ".ps"
# 
#         try:
#             file = open(filename, "w")
#         except IOError:
#             raise IOError("cannot open output file")
# 
#         docbbox = None
#         for apage in self.pages:
#             pbbox = apage.bbox()
#             if docbbox is None:
#                 docbbox = pbbox
#             else:
#                 docbbox += pbbox
# 
#         # document header
#         file.write("%!PS-Adobe-3.0\n")
#         docbbox.outputPS(file)
#         file.write("%%%%Creator: PyX %s\n" % version.version)
#         file.write("%%%%Title: %s\n" % filename)
#         file.write("%%%%CreationDate: %s\n" %
#                    time.asctime(time.localtime(time.time())))
#         # required paper formats
#         paperformats = {}
#         for apage in self.pages:
#             if isinstance(apage, page):
#                 paperformats[apage.paperformat] = _paperformats[apage.paperformat]
#         first = 1
#         for paperformat, size in paperformats.items():
#             if first:
#                 file.write("%%DocumentMedia: ")
#                 first = 0
#             else:
#                 file.write("%%+ ")
#             file.write("%s %d %d 75 white ()\n" % (paperformat, unit.topt(size[0]), unit.topt(size[1])))
# 
#         file.write("%%%%Pages: %d\n" % len(self.pages))
#         file.write("%%PageOrder: Ascend\n")
#         file.write("%%EndComments\n")
# 
#         # document default section
#         #file.write("%%BeginDefaults\n")
#         #if paperformat:
#         #    file.write("%%%%PageMedia: %s\n" % paperformat)
#         #file.write("%%%%PageOrientation: %s\n" % (rotated and "Landscape" or "Portrait"))
#         #file.write("%%EndDefaults\n")
# 
#         # document prolog section
#         file.write("%%BeginProlog\n")
#         mergedprolog = []
#         for apage in self.pages:
#             for pritem in apage.prolog():
#                 for mpritem in mergedprolog:
#                     if mpritem.merge(pritem) is None: break
#                 else:
#                     mergedprolog.append(pritem)
#         for pritem in mergedprolog:
#             pritem.outputPS(file)
#         file.write("%%EndProlog\n")
# 
#         # document setup section
#         #file.write("%%BeginSetup\n")
#         #file.write("%%EndSetup\n")
# 
#         # pages section
#         for nr, apage in enumerate(self.pages):
#             file.write("%%%%Page: %s %d\n" % (apage.pagename is None and str(nr) or apage.pagename , nr+1))
#             apage.outputPS(file)
# 
#         file.write("%%Trailer\n")
#         file.write("%%EOF\n")
