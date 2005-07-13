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

from __future__ import nested_scopes

import cStringIO, math, warnings
import attr, canvas, helper, path, pdfwriter, pswriter, style, unit, trafo

# TODO: pattern should not derive from canvas but wrap a canvas

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

    def __call__(self, painttype=helper.nodefault, tilingtype=helper.nodefault, xstep=helper.nodefault, ystep=helper.nodefault, 
                 bbox=helper.nodefault, trafo=helper.nodefault):
        if painttype is helper.nodefault:
            painttype = self.painttype
        if tilingtype is helper.nodefault:
            tilingtype = self.tilingtype
        if xstep is helper.nodefault:
            xstep = self.xstep
        if ystep is helper.nodefault:
            ystep = self.ystep
        if bbox is helper.nodefault:
            bbox = self.bbox
        if trafo is helper.nodefault:
            trafo = self.trafo
        return pattern(painttype, tilingtype, xstep, ystep, bbox, trafo)

    def bbox(self):
        return None

    def outputPS(self, file, writer, context):
        file.write("%s setpattern\n" % self.id)

    def outputPDF(self, file, writer, context):
        if context.colorspace != "Pattern":
            # we only set the fill color space (see next comment)
            file.write("/Pattern cs\n")
            context.colorspace = "Pattern"
        if context.strokeattr:
            # using patterns as stroke colors doesn't seem to work, so
            # we just don't do this...
            pass
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
                                   "/BBox[%d %d %d %d]" % patternbbox.lowrestuple_pt(),
                                   "/XStep %g" % xstep,
                                   "/YStep %g" % ystep,
                                   "/PaintProc {\nbegin\n"))
        stringfile = cStringIO.StringIO()
        # XXX here, we have a problem since the writer is not definined at that point
        # for the moment, we just path None since we do not use it anyway
        canvas._canvas.outputPS(self, stringfile, None, pswriter.context())
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
                                lambda file, writer, context: canvas._canvas.outputPDF(self, file, writer, context()),
                                lambda registry: canvas._canvas.registerPDF(self, registry),
                                registry))

pattern.clear = attr.clearclass(pattern)


_base = 0.1 * unit.v_cm

class hatched(pattern):
    def __init__(self, dist, angle, strokestyles=[]):
        pattern.__init__(self, painttype=1, tilingtype=1, xstep=dist, ystep=1000*unit.t_pt, bbox=None, trafo=trafo.rotate(angle))
        self.strokestyles = attr.mergeattrs([style.linewidth.THIN] + strokestyles)
        attr.checkattrs(self.strokestyles, [style.strokestyle])
        self.dist = dist
        self.angle = angle
        self.stroke(path.line_pt(0, -500, 0, 500), self.strokestyles)

    def __call__(self, dist=None, angle=None, strokestyles=None):
        if dist is None:
            dist = self.dist
        if angle is None:
            angle = self.angle
        if strokestyles is None:
            strokestyles = self.strokestyles
        return hatched(dist, angle, strokestyles)

hatched0 = hatched(_base, 0)
hatched0.SMALL = hatched0(_base/math.sqrt(64))
hatched0.SMALL = hatched0(_base/math.sqrt(64))
hatched0.SMALl = hatched0(_base/math.sqrt(32))
hatched0.SMAll = hatched0(_base/math.sqrt(16))
hatched0.SMall = hatched0(_base/math.sqrt(8))
hatched0.Small = hatched0(_base/math.sqrt(4))
hatched0.small = hatched0(_base/math.sqrt(2))
hatched0.normal = hatched0(_base)
hatched0.large = hatched0(_base*math.sqrt(2))
hatched0.Large = hatched0(_base*math.sqrt(4))
hatched0.LArge = hatched0(_base*math.sqrt(8))
hatched0.LARge = hatched0(_base*math.sqrt(16))
hatched0.LARGe = hatched0(_base*math.sqrt(32))
hatched0.LARGE = hatched0(_base*math.sqrt(64))

hatched45 = hatched(_base, 45)
hatched45.SMALL = hatched45(_base/math.sqrt(64))
hatched45.SMALl = hatched45(_base/math.sqrt(32))
hatched45.SMAll = hatched45(_base/math.sqrt(16))
hatched45.SMall = hatched45(_base/math.sqrt(8))
hatched45.Small = hatched45(_base/math.sqrt(4))
hatched45.small = hatched45(_base/math.sqrt(2))
hatched45.normal = hatched45(_base)
hatched45.large = hatched45(_base*math.sqrt(2))
hatched45.Large = hatched45(_base*math.sqrt(4))
hatched45.LArge = hatched45(_base*math.sqrt(8))
hatched45.LARge = hatched45(_base*math.sqrt(16))
hatched45.LARGe = hatched45(_base*math.sqrt(32))
hatched45.LARGE = hatched45(_base*math.sqrt(64))

hatched90 = hatched(_base, 90)
hatched90.SMALL = hatched90(_base/math.sqrt(64))
hatched90.SMALl = hatched90(_base/math.sqrt(32))
hatched90.SMAll = hatched90(_base/math.sqrt(16))
hatched90.SMall = hatched90(_base/math.sqrt(8))
hatched90.Small = hatched90(_base/math.sqrt(4))
hatched90.small = hatched90(_base/math.sqrt(2))
hatched90.normal = hatched90(_base)
hatched90.large = hatched90(_base*math.sqrt(2))
hatched90.Large = hatched90(_base*math.sqrt(4))
hatched90.LArge = hatched90(_base*math.sqrt(8))
hatched90.LARge = hatched90(_base*math.sqrt(16))
hatched90.LARGe = hatched90(_base*math.sqrt(32))
hatched90.LARGE = hatched90(_base*math.sqrt(64))

hatched135 = hatched(_base, 135)
hatched135.SMALL = hatched135(_base/math.sqrt(64))
hatched135.SMALl = hatched135(_base/math.sqrt(32))
hatched135.SMAll = hatched135(_base/math.sqrt(16))
hatched135.SMall = hatched135(_base/math.sqrt(8))
hatched135.Small = hatched135(_base/math.sqrt(4))
hatched135.small = hatched135(_base/math.sqrt(2))
hatched135.normal = hatched135(_base)
hatched135.large = hatched135(_base*math.sqrt(2))
hatched135.Large = hatched135(_base*math.sqrt(4))
hatched135.LArge = hatched135(_base*math.sqrt(8))
hatched135.LARge = hatched135(_base*math.sqrt(16))
hatched135.LARGe = hatched135(_base*math.sqrt(32))
hatched135.LARGE = hatched135(_base*math.sqrt(64))


class crosshatched(pattern):
    def __init__(self, dist, angle, strokestyles=[]):
        pattern.__init__(self, painttype=1, tilingtype=1, xstep=dist, ystep=dist, bbox=None, trafo=trafo.rotate(angle))
        self.strokestyles = attr.mergeattrs([style.linewidth.THIN] + strokestyles)
        attr.checkattrs(self.strokestyles, [style.strokestyle])
        self.dist = dist
        self.angle = angle
        self.stroke(path.line_pt(0, 0, 0, unit.topt(dist)), self.strokestyles)
        self.stroke(path.line_pt(0, 0, unit.topt(dist), 0), self.strokestyles)

    def __call__(self, dist=None, angle=None, strokestyles=None):
        if dist is None:
            dist = self.dist
        if angle is None:
            angle = self.angle
        if strokestyles is None:
            strokestyles = self.strokestyles
        return crosshatched(dist, angle, strokestyles)

crosshatched0 = crosshatched(_base, 0)
crosshatched0.SMALL = crosshatched0(_base/math.sqrt(64))
crosshatched0.SMALl = crosshatched0(_base/math.sqrt(32))
crosshatched0.SMAll = crosshatched0(_base/math.sqrt(16))
crosshatched0.SMall = crosshatched0(_base/math.sqrt(8))
crosshatched0.Small = crosshatched0(_base/math.sqrt(4))
crosshatched0.small = crosshatched0(_base/math.sqrt(2))
crosshatched0.normal = crosshatched0
crosshatched0.large = crosshatched0(_base*math.sqrt(2))
crosshatched0.Large = crosshatched0(_base*math.sqrt(4))
crosshatched0.LArge = crosshatched0(_base*math.sqrt(8))
crosshatched0.LARge = crosshatched0(_base*math.sqrt(16))
crosshatched0.LARGe = crosshatched0(_base*math.sqrt(32))
crosshatched0.LARGE = crosshatched0(_base*math.sqrt(64))

crosshatched45 = crosshatched(_base, 45)
crosshatched45.SMALL = crosshatched45(_base/math.sqrt(64))
crosshatched45.SMALl = crosshatched45(_base/math.sqrt(32))
crosshatched45.SMAll = crosshatched45(_base/math.sqrt(16))
crosshatched45.SMall = crosshatched45(_base/math.sqrt(8))
crosshatched45.Small = crosshatched45(_base/math.sqrt(4))
crosshatched45.small = crosshatched45(_base/math.sqrt(2))
crosshatched45.normal = crosshatched45
crosshatched45.large = crosshatched45(_base*math.sqrt(2))
crosshatched45.Large = crosshatched45(_base*math.sqrt(4))
crosshatched45.LArge = crosshatched45(_base*math.sqrt(8))
crosshatched45.LARge = crosshatched45(_base*math.sqrt(16))
crosshatched45.LARGe = crosshatched45(_base*math.sqrt(32))
crosshatched45.LARGE = crosshatched45(_base*math.sqrt(64))


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
        file.write("/BBox [%d %d %d %d]\n" % self.bbox.lowrestuple_pt())
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
        file.write("\n"
                   "endstream\n")
