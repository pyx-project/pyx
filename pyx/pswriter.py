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


class epswriter:

    def __init__(self, document):
        self.document = document

    def write(self, filename):
        if len(document.pages) != 1:
            raise ValueError("EPS file can be construced out of a single page document only")

        if filename[-4:]!=".eps":
            filename = filename + ".eps"
        self.filename = filename

        try:
            self.file = open(self.filename, "w")
        except IOError:
            raise IOError("cannot open output file")

        abbox = bbox is not None and bbox or self.bbox()
        abbox.enlarge(bboxenlarge)
        ctrafo = calctrafo(abbox, paperformat, margin, rotated, fittosize)

        # if there has been a global transformation, adjust the bounding box
        # accordingly
        if ctrafo: abbox.transform(ctrafo)

        file.write("%!PS-Adobe-3.0 EPSF-3.0\n")
        abbox.outputPS(file)
        file.write("%%%%Creator: PyX %s\n" % version.version)
        file.write("%%%%Title: %s\n" % filename)
        file.write("%%%%CreationDate: %s\n" %
                   time.asctime(time.localtime(time.time())))
        file.write("%%EndComments\n")

        file.write("%%BeginProlog\n")

        mergedprolog = []

        for pritem in self.prolog():
            for mpritem in mergedprolog:
                if mpritem.merge(pritem) is None: break
            else:
                mergedprolog.append(pritem)

        for pritem in mergedprolog:
            pritem.outputPS(file)

        file.write("%%EndProlog\n")

        # apply a possible global transformation
        if ctrafo: ctrafo.outputPS(file)

        file.write("%f setlinewidth\n" % unit.topt(style.linewidth.normal))

        # here comes the actual content
        self.outputPS(file)

        file.write("showpage\n")
        file.write("%%Trailer\n")
        file.write("%%EOF\n")

