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

import time
import style, version


class epswriter:

    def __init__(self, document, filename):
        if len(document.pages) != 1:
            raise ValueError("EPS file can be construced out of a single page document only")
        page = document.pages[0]
        canvas = page.canvas

        if filename[-4:] != ".eps":
            filename = filename + ".eps"
        try:
            file = open(filename, "w")
        except IOError:
            raise IOError("cannot open output file")

        bbox = canvas.bbox()
        pagetrafo = page.pagetrafo(bbox)

        # if a page transformation is necessary, we have to adjust the bounding box
        # accordingly
        if pagetrafo is not None:
            bbox.transform(pagetrafo)

        file.write("%!PS-Adobe-3.0 EPSF-3.0\n")
        bbox.outputPS(file)
        file.write("%%%%Creator: PyX %s\n" % version.version)
        file.write("%%%%Title: %s\n" % filename)
        file.write("%%%%CreationDate: %s\n" %
                   time.asctime(time.localtime(time.time())))
        file.write("%%EndComments\n")

        file.write("%%BeginProlog\n")

        mergedprolog = []

        for pritem in canvas.prolog():
            for mpritem in mergedprolog:
                if mpritem.merge(pritem) is None: break
            else:
                mergedprolog.append(pritem)

        for pritem in mergedprolog:
            pritem.outputPS(file)

        file.write("%%EndProlog\n")

        # apply a possible page transformation
        if pagetrafo is not None:
            pagetrafo.outputPS(file)

        style.linewidth.normal.outputPS(file)

        # here comes the canvas content
        canvas.outputPS(file)

        file.write("showpage\n")
        file.write("%%Trailer\n")
        file.write("%%EOF\n")


class pswriter:
    pass

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
