# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2002-2005 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2002-2005 André Wobst <wobsta@users.sourceforge.net>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

import cStringIO
import attr, canvas, style, pdfwriter, pswriter, unit, trafo

class pattern(canvas._canvas, attr.exclusiveattr, style.fillstyle):

    def __init__(self, painttype=1, tilingtype=1, xstep=None, ystep=None, bbox=None, trafo=None, **kwargs):
        canvas._canvas.__init__(self, **kwargs)
        attr.exclusiveattr.__init__(self, pattern)
        self.id = "pattern%d" % id(self)
        self.patterntype = 1
        if painttype not in (1,2):
            raise ValueError("painttype must be 1 or 2")
        self.painttype = painttype
        if tilingtype not in (1,2,3):
            raise ValueError("tilingtype must be 1, 2 or 3")
        self.tilingtype = tilingtype
        self.xstep = xstep
        self.ystep = ystep
        self.patternbbox = bbox
        self.patterntrafo = trafo

    def bbox(self):
        return None

    def outputPS(self, file):
        file.write("%s setpattern\n" % self.id)

    def outputPDF(self, file, writer, context):
        if context.colorspace != "Pattern":
            # we only set the fill color space
            file.write("/Pattern cs\n")
            context.colorspace = "Pattern"
        assert not context.strokeattr, "this should not happen"
        if context.fillattr:
            file.write("/%s scn\n"% self.id)

    def registerPS(self, registry):
        canvas._canvas.registerPS(self, registry)
        realpatternbbox = canvas._canvas.bbox(self)
        if self.xstep is None:
           xstep = unit.topt(realpatternbbox.width())
        else:
           xstep = unit.topt(self.xstep)
        if self.ystep is None:
            ystep = unit.topt(realpatternbbox.height())
        else:
           ystep = unit.topt(self.ystep)
        if not xstep:
            raise ValueError("xstep in pattern cannot be zero")
        if not ystep:
            raise ValueError("ystep in pattern cannot be zero")
        patternbbox = self.patternbbox or realpatternbbox.enlarged(5*unit.pt)

        patternprefix = "\n".join(("<<",
                                   "/PatternType %d" % self.patterntype,
                                   "/PaintType %d" % self.painttype,
                                   "/TilingType %d" % self.tilingtype,
                                   "/BBox[%s]" % str(patternbbox),
                                   "/XStep %g" % xstep,
                                   "/YStep %g" % ystep,
                                   "/PaintProc {\nbegin\n"))
        stringfile = cStringIO.StringIO()
        canvas._canvas.outputPS(self, stringfile)
        patternproc = stringfile.getvalue()
        stringfile.close()
        patterntrafostring = self.patterntrafo is None and "matrix" or str(self.patterntrafo)
        patternsuffix = "end\n} bind\n>>\n%s\nmakepattern" % patterntrafostring

        registry.add(pswriter.PSdefinition(self.id, "".join((patternprefix, patternproc, patternsuffix))))

    def registerPDF(self, registry):
        realpatternbbox = canvas._canvas.bbox(self)
        if self.xstep is None:
           xstep = unit.topt(realpatternbbox.width())
        else:
           xstep = unit.topt(self.xstep)
        if self.ystep is None:
            ystep = unit.topt(realpatternbbox.height())
        else:
           ystep = unit.topt(self.ystep)
        if not xstep:
            raise ValueError("xstep in pattern cannot be zero")
        if not ystep:
            raise ValueError("ystep in pattern cannot be zero")
        patternbbox = self.patternbbox or realpatternbbox.enlarged(5*unit.pt)
        patterntrafo = self.patterntrafo or trafo.trafo()

        registry.add(PDFpattern(self.id, self.patterntype, self.painttype, self.tilingtype,
                                patternbbox, xstep, ystep, patterntrafo,
                                lambda file, writer, context: canvas._canvas.outputPDF(self, file, writer, context),
                                lambda registry: canvas._canvas.registerPDF(self, registry),
                                registry))

pattern.clear = attr.clearclass(pattern)


class PDFpattern(pdfwriter.PDFobject):

    def __init__(self, name, patterntype, painttype, tilingtype, bbox, xstep, ystep, trafo,
                 canvasoutputPDF, canvasregisterPDF, registry):
        pdfwriter.PDFobject.__init__(self, "pattern", name)
        self.name = name
        self.patterntype = patterntype
        self.painttype = painttype
        self.tilingtype = tilingtype
        self.bbox = bbox
        self.xstep = xstep
        self.ystep = ystep
        self.trafo = trafo
        self.canvasoutputPDF = canvasoutputPDF

        self.contentlength = pdfwriter.PDFcontentlength((self.type, self.id))
        registry.add(self.contentlength)

        # we need to keep track of the resources used by the pattern, hence
        # we create our own registry, which we merge immediately in the main registry
        self.patternregistry = pdfwriter.PDFregistry()
        # XXX passing canvasregisterPDF is a Q&D way to get access to the registerPDF method
        # of the _canvas superclass of the pattern
        canvasregisterPDF(self.patternregistry)
        registry.mergeregistry(self.patternregistry)

    def outputPDF(self, file, writer, registry):
        file.write("<<\n"
                   "/Type /Pattern\n"
                   "/PatternType %d\n" % self.patterntype)
        file.write("/PaintType %d\n" % self.painttype)
        file.write("/TilingType %d\n" % self.tilingtype)
        file.write("/BBox [%s]\n" % str(self.bbox))
        file.write("/XStep %f\n" % self.xstep)
        file.write("/YStep %f\n" % self.ystep)
        file.write("/Matrix %s\n" % str(self.trafo))
        file.write("/Resources <<\n")
        if self.patternregistry.types.has_key("font"):
            file.write("/Font << %s >>\n" % " ".join(["/%s %i 0 R" % (font.name, registry.getrefno(font))
                                                    for font in self.patternregistry.types["font"].values()]))
        if self.patternregistry.types.has_key("pattern"):
            file.write("/Pattern << %s >>\n" % " ".join(["/%s %i 0 R" % (pattern.name, registry.getrefno(pattern))
                                                         for pattern in self.patternregistry.types["pattern"].values()]))
        file.write(">>\n")
        file.write("/Length %i 0 R\n" % registry.getrefno(self.contentlength))
        if writer.compress:
            file.write("/Filter /FlateDecode\n")
        file.write(">>\n")

        file.write("stream\n")
        beginstreampos = file.tell()

        if writer.compress:
            stream = pdfwriter.compressedstream(file, writer.compresslevel)
        else:
            stream = file

        acontext = pdfwriter.context()
        self.canvasoutputPDF(stream, writer, acontext)
        if writer.compress:
            stream.flush()

        self.contentlength.contentlength = file.tell() - beginstreampos
        file.write("endstream\n")
