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

# XXX what are the correct base classes of clip and pattern

"""The canvas module provides a PostScript canvas class and related classes

A canvas holds a collection of all elements that should be displayed together
with their attributes.
"""

import sys, cStringIO, time
import attr, base,  bbox, deco, unit, prolog, style, trafo, version

# temporary for pdf fonts:
import zlib
from t1strip import fullfont
import pykpathsea

import pdfwriter

try:
    enumerate([])
except NameError:
    # fallback implementation for Python 2.2. and below
    def enumerate(list):
        return zip(xrange(len(list)), list)

# known paperformats as tuple (width, height)

_paperformats = { "A4"      : (210 * unit.t_mm,   297  * unit.t_mm),
                  "A3"      : (297 * unit.t_mm,   420  * unit.t_mm),
                  "A2"      : (420 * unit.t_mm,   594  * unit.t_mm),
                  "A1"      : (594 * unit.t_mm,   840  * unit.t_mm),
                  "A0"      : (840 * unit.t_mm,   1188 * unit.t_mm),
                  "A0b"     : (910 * unit.t_mm,   1370 * unit.t_mm),
                  "Letter"  : (8.5 * unit.t_inch, 11   * unit.t_inch),
                  "Legal"   : (8.5 * unit.t_inch, 14   * unit.t_inch)}

#
# clipping class
#

class clip(base.PSCmd):

    """class for use in canvas constructor which clips to a path"""

    def __init__(self, path):
        """construct a clip instance for a given path"""
        self.path = path

    def bbox(self):
        # as a PSCmd a clipping path has NO influence on the bbox...
        return None

    def clipbbox(self):
        # ... but for clipping, we nevertheless need the bbox
        return self.path.bbox()

    def outputPS(self, file):
        file.write("newpath\n")
        self.path.outputPS(file)
        file.write("clip\n")

    def outputPDF(self, file):
        self.path.outputPDF(file)
        file.write("W n\n")

#
# general canvas class
#

class _canvas(base.PSCmd):

    """a canvas is a collection of PSCmds together with PSAttrs"""

    def __init__(self, attrs=[], texrunner=None):

        """construct a canvas

        The canvas can be modfied by supplying args, which have
        to be instances of one of the following classes:
         - trafo.trafo (leading to a global transformation of the canvas)
         - canvas.clip (clips the canvas)
         - base.PathStyle (sets some global attributes of the canvas)

        Note that, while the first two properties are fixed for the
        whole canvas, the last one can be changed via canvas.set().

        The texrunner instance used for the text method can be specified
        using the texrunner argument. It defaults to text.defaulttexrunner

        """

        self.PSOps     = []
        self.trafo     = trafo.trafo()
        self.clipbbox  = None
        if texrunner is not None:
            self.texrunner = texrunner
        else:
            # prevent cyclic imports
            import text
            self.texrunner = text.defaulttexrunner

        for attr in attrs:
            if isinstance(attr, trafo.trafo_pt):
                self.trafo = self.trafo*attr
                self.PSOps.append(attr)
            elif isinstance(attr, clip):
                if self.clipbbox is None:
                    self.clipbbox = attr.clipbbox().transformed(self.trafo)
                else:
                    self.clippbox *= attr.clipbbox().transformed(self.trafo)
                self.PSOps.append(attr)
            else:
                self.set([attr])

    def bbox(self):
        """returns bounding box of canvas"""
        obbox = None
        for cmd in self.PSOps:
            if isinstance(cmd, base.PSCmd):
                abbox = cmd.bbox()
                if obbox is None:
                    obbox = abbox
                elif abbox is not None:
                    obbox += abbox

        # transform according to our global transformation and
        # intersect with clipping bounding box (which have already been
        # transformed in canvas.__init__())
        if obbox is not None and self.clipbbox is not None:
            return obbox.transformed(self.trafo)*self.clipbbox
        elif obbox is not None:
            return obbox.transformed(self.trafo)
        else:
            return self.clipbbox

    def prolog(self):
        result = []
        for cmd in self.PSOps:
            result.extend(cmd.prolog())
        return result

    def outputPS(self, file):
        if self.PSOps:
            file.write("gsave\n")
            for cmd in self.PSOps:
                cmd.outputPS(file)
            file.write("grestore\n")

    def outputPDF(self, file):
        if self.PSOps:
            file.write("q\n") # gsave
            for cmd in self.PSOps:
                cmd.outputPDF(file)
            file.write("Q\n") # grestore

    def insert(self, PSOp, attrs=[]):
        """insert PSOp in the canvas.

        If attrss are given, a canvas containing the PSOp is inserted applying attrs.

        returns the PSOp

        """

        # XXX check for PSOp

        if attrs:
            sc = _canvas(attrs)
            sc.insert(PSOp)
            self.PSOps.append(sc)
        else:
            self.PSOps.append(PSOp)

        return PSOp

    def set(self, attrs):
        """sets styles args globally for the rest of the canvas
        """

        attr.checkattrs(attrs, [style.strokestyle, style.fillstyle])
        for astyle in attrs:
            self.insert(astyle)

    def draw(self, path, attrs):
        """draw path on canvas using the style given by args

        The argument attrs consists of PathStyles, which modify
        the appearance of the path, PathDecos, which add some new
        visual elements to the path, or trafos, which are applied
        before drawing the path.

        """

        attrs = attr.mergeattrs(attrs)
        attr.checkattrs(attrs, [deco.deco, style.fillstyle, style.strokestyle, trafo.trafo_pt])

        for t in attr.getattrs(attrs, [trafo.trafo_pt]):
            path = path.transformed(t)

        dp = deco.decoratedpath(path)

        # set global styles
        dp.styles = attr.getattrs(attrs, [style.fillstyle, style.strokestyle])

        # add path decorations and modify path accordingly
        for adeco in attr.getattrs(attrs, [deco.deco]):
            dp = adeco.decorate(dp)

        self.insert(dp)

    def stroke(self, path, attrs=[]):
        """stroke path on canvas using the style given by args

        The argument attrs consists of PathStyles, which modify
        the appearance of the path, PathDecos, which add some new
        visual elements to the path, or trafos, which are applied
        before drawing the path.

        """

        self.draw(path, [deco.stroked]+list(attrs))

    def fill(self, path, attrs=[]):
        """fill path on canvas using the style given by args

        The argument attrs consists of PathStyles, which modify
        the appearance of the path, PathDecos, which add some new
        visual elements to the path, or trafos, which are applied
        before drawing the path.

        """

        self.draw(path, [deco.filled]+list(attrs))

    def settexrunner(self, texrunner):
        """sets the texrunner to be used to within the text and text_pt methods"""

        self.texrunner = texrunner

    def text(self, x, y, atext, *args, **kwargs):
        """insert a text into the canvas

        inserts a textbox created by self.texrunner.text into the canvas

        returns the inserted textbox"""

        return self.insert(self.texrunner.text(x, y, atext, *args, **kwargs))


    def text_pt(self, x, y, atext, *args):
        """insert a text into the canvas

        inserts a textbox created by self.texrunner.text_pt into the canvas

        returns the inserted textbox"""

        return self.insert(self.texrunner.text_pt(x, y, atext, *args))

#
# canvas for patterns
#

class pattern(_canvas, attr.exclusiveattr, style.fillstyle):

    def __init__(self, painttype=1, tilingtype=1, xstep=None, ystep=None, bbox=None, trafo=None):
        attr.exclusiveattr.__init__(self, pattern)
        _canvas.__init__(self)
        attr.exclusiveattr.__init__(self, pattern)
        self.id = "pattern%d" % id(self)
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

    def prolog(self):
        realpatternbbox = _canvas.bbox(self)
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
                                   "/PatternType 1",
                                   "/PaintType %d" % self.painttype,
                                   "/TilingType %d" % self.tilingtype,
                                   "/BBox[%s]" % str(patternbbox),
                                   "/XStep %g" % xstep,
                                   "/YStep %g" % ystep,
                                   "/PaintProc {\nbegin\n"))
        stringfile = cStringIO.StringIO()
        _canvas.outputPS(self, stringfile)
        patternproc = stringfile.getvalue()
        stringfile.close()
        patterntrafostring = self.patterntrafo is None and "matrix" or str(self.patterntrafo)
        patternsuffix = "end\n} bind\n>>\n%s\nmakepattern" % patterntrafostring

        pr = _canvas.prolog(self)
        pr.append(prolog.definition(self.id, "".join((patternprefix, patternproc, patternsuffix))))
        return pr

pattern.clear = attr.clearclass(pattern)

# helper function

def calctrafo(abbox, paperformat, margin, rotated, fittosize):
    """ calculate a trafo which rotates and fits a canvas with
    bounding box abbox on the given paperformat with a margin on all
    sides"""
    if not isinstance(margin, unit.length):
        margin = unit.length(margin)
    atrafo = None     # global transformation of canvas

    if rotated:
        atrafo = trafo.rotate(90, *abbox.center())

    if paperformat:
        # center (optionally rotated) output on page
        try:
            paperwidth, paperheight = _paperformats[paperformat.capitalize()]
        except KeyError:
            raise KeyError, "unknown paperformat '%s'" % paperformat

        paperwidth -= 2*margin
        paperheight -= 2*margin

        if not atrafo: atrafo = trafo.trafo()

        atrafo = atrafo.translated(margin + 0.5*(paperwidth  - abbox.width())  - abbox.left(),
                                   margin + 0.5*(paperheight - abbox.height()) - abbox.bottom())

        if fittosize:
            # scale output to pagesize - margins
            if 2*margin > min(paperwidth, paperheight):
                raise RuntimeError("Margins too broad for selected paperformat. Aborting.")

            if rotated:
                sfactor = min(unit.topt(paperheight)/unit.topt(abbox.width()),
                              unit.topt(paperwidth)/unit.topt(abbox.height()))
            else:
                sfactor = min(unit.topt(paperwidth)/unit.topt(abbox.width()),
                              unit.topt(paperheight)/unit.topt(abbox.height()))

            atrafo = atrafo.scaled(sfactor, sfactor, margin + 0.5*paperwidth, margin + 0.5*paperheight)
    elif fittosize:
        raise ValueError("must specify paper size for fittosize")

    return atrafo

#
# The main canvas class
#

class canvas(_canvas):

    """a canvas is a collection of PSCmds together with PSAttrs"""

    def writeEPSfile(self, filename, paperformat=None, rotated=0, fittosize=0, margin=1 * unit.t_cm,
                    bbox=None, bboxenlarge=1 * unit.t_pt):
        """write canvas to EPS file

        If paperformat is set to a known paperformat, the output will be centered on
        the page.

        If rotated is set, the output will first be rotated by 90 degrees.

        If fittosize is set, then the output is scaled to the size of the
        page (minus margin). In that case, the paperformat the specification
        of the paperformat is obligatory.

        The bbox parameter overrides the automatic bounding box determination.
        bboxenlarge may be used to enlarge the bbox of the canvas (or the
        manually specified bbox).
        """

        if filename[-4:]!=".eps":
            filename = filename + ".eps"

        try:
            file = open(filename, "w")
        except IOError:
            raise IOError("cannot open output file")

        abbox = bbox is not None and bbox or self.bbox()
        abbox.enlarge(bboxenlarge)
        ctrafo = calctrafo(abbox, paperformat, margin, rotated, fittosize)

        # if there has been a global transformation, adjust the bounding box
        # accordingly
        if ctrafo: abbox.transform(ctrafo)

        file.write("%!PS-Adobe-3.0 EPSF 3.0\n")
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

    def writePDFfile(self, filename, paperformat=None, rotated=0, fittosize=0, margin=1 * unit.t_cm,
                    bbox=None, bboxenlarge=1 * unit.t_pt):
        sys.stderr.write("*** PyX Warning: writePDFfile is experimental and supports only a subset of PyX's features\n")

        if filename[-4:]!=".pdf":
            filename = filename + ".pdf"

        try:
            file = open(filename, "wb")
        except IOError:
            raise IOError("cannot open output file")

        abbox = bbox is not None and bbox or self.bbox()
        abbox.enlarge(bboxenlarge)

        ctrafo = calctrafo(abbox, paperformat, margin, rotated, fittosize)

        # if there has been a global transformation, adjust the bounding box
        # accordingly
        if ctrafo: abbox.transform(ctrafo)

        mergedprolog = []

        for pritem in self.prolog():
            for mpritem in mergedprolog:
                if mpritem.merge(pritem) is None: break
            else:
                mergedprolog.append(pritem)

        file.write("%%PDF-1.4\n%%%s%s%s%s\n" % (chr(195), chr(182), chr(195), chr(169)))
        reflist = [file.tell()]
        file.write("1 0 obj\n"
                   "<<\n"
                   "/Type /Catalog\n"
                   "/Pages 2 0 R\n"
                   ">>\n"
                   "endobj\n")
        reflist.append(file.tell())
        file.write("2 0 obj\n"
                   "<<\n"
                   "/Type /Pages\n"
                   "/Kids [3 0 R]\n"
                   "/Count 1\n"
                   ">>\n"
                   "endobj\n")
        reflist.append(file.tell())
        file.write("3 0 obj\n"
                   "<<\n"
                   "/Type /Page\n"
                   "/Parent 2 0 R\n"
                   "/MediaBox ")
        abbox.outputPDF(file)
        file.write("/Contents 4 0 R\n"
                   "/Resources <<\n")
        fontstartref = 5

        fontnr = 0
        if len([pritem for pritem in mergedprolog if isinstance(pritem, prolog.fontdefinition)]):
            file.write("/Font\n"
                       "<<\n")
            for pritem in mergedprolog:
                if isinstance(pritem, prolog.fontdefinition):
                    fontnr += 1
                    file.write("/%s %d 0 R\n" % (pritem.font.getpsname(), fontnr+fontstartref))
                    fontnr += 3 # further objects due to a font
            file.write(">>\n")

        file.write(">>\n"
                   ">>\n"
                   "endobj\n")
        reflist.append(file.tell())
        file.write("4 0 obj\n"
                   "<< /Length 5 0 R >>\n"
                   "stream\n")
        streamstartpos = file.tell()

        # apply a possible global transformation
        if ctrafo: ctrafo.outputPDF(file)
        style.linewidth.normal.outputPDF(file)

        self.outputPDF(file)
        streamendpos = file.tell()
        file.write("endstream\n"
                   "endobj\n")
        reflist.append(file.tell())
        file.write("5 0 obj\n"
                   "%s\n"
                   "endobj\n" % (streamendpos - streamstartpos))

        fontnr = 0
        for pritem in mergedprolog:
            if isinstance(pritem, prolog.fontdefinition):
                fontnr += 1
                reflist.append(file.tell())
                file.write("%d 0 obj\n"
                           "<<\n"
                           "/Type /Font\n"
                           "/Subtype /Type1\n"
                           "/Name /%s\n"
                           "/BaseFont /%s\n"
                           "/FirstChar 0\n"
                           "/LastChar 255\n"
                           "/Widths %d 0 R\n"
                           "/FontDescriptor %d 0 R\n"
                           "/Encoding /StandardEncoding\n" # FIXME
                           ">>\n"
                           "endobj\n" % (fontnr+fontstartref, pritem.font.getpsname(), pritem.font.getbasepsname(),
                                         fontnr+fontstartref+1, fontnr+fontstartref+2))
                fontnr += 1
                reflist.append(file.tell())
                file.write("%d 0 obj\n"
                           "[\n" % (fontnr+fontstartref))
                for i in range(256):
                    try:
                        width = pritem.font.getwidth_pt(i)*1000/pritem.font.getsize_pt()
                    except:
                        width = 0
                    file.write("%f\n" % width)
                file.write("]\n"
                           "endobj\n")
                if pritem.filename:
                    fontnr += 1
                    reflist.append(file.tell())
                    file.write("%d 0 obj\n"
                               "<<\n"
                               "/Type /FontDescriptor\n"
                               "/FontName /%s\n"
                               "/Flags 4\n" # FIXME
                               "/FontBBox [-10 -10 1000 1000]\n" # FIXME
                               "/ItalicAngle 0\n" # FIXME
                               "/Ascent 20\n" # FIXME
                               "/Descent -5\n" # FIXME
                               "/CapHeight 15\n" # FIXME
                               "/StemV 3\n" # FIXME
                               "/FontFile %d 0 R\n" # FIXME
                               # "/CharSet \n" # fill in when stripping
                               ">>\n"
                               "endobj\n" % (fontnr+fontstartref, pritem.font.getbasepsname(),
                                             fontnr+fontstartref+1))

                    fontnr += 1
                    reflist.append(file.tell())

                    fontdata = open(pykpathsea.find_file(pritem.filename, pykpathsea.kpse_type1_format)).read()
                    if fontdata[0:2] != fullfont._PFB_ASCII:
                        raise RuntimeError("PFB_ASCII mark expected")
                    length1 = fullfont.pfblength(fontdata[2:6])
                    if fontdata[6+length1:8+length1] != fullfont._PFB_BIN:
                        raise RuntimeError("PFB_BIN mark expected")
                    length2 = fullfont.pfblength(fontdata[8+length1:12+length1])
                    if fontdata[12+length1+length2:14+length1+length2] != fullfont._PFB_ASCII:
                        raise RuntimeError("PFB_ASCII mark expected")
                    length3 = fullfont.pfblength(fontdata[14+length1+length2:18+length1+length2])
                    if fontdata[18+length1+length2+length3:20+length1+length2+length3] != fullfont._PFB_DONE:
                        raise RuntimeError("PFB_DONE mark expected")
                    if len(fontdata) != 20 + length1 + length2 + length3:
                        raise RuntimeError("end of pfb file expected")

                    # we might be allowed to skip the third part ...
                    if fontdata[18+length1+length2:18+length1+length2+length3].replace("\n", "").replace("\r", "").replace("\t", "").replace(" ", "") == "0"*512 + "cleartomark":
                        length3 = 0

                    uncompresseddata = fontdata[6:6+length1] + fontdata[12+length1:12+length1+length2] + fontdata[18+length1+length2:18+length1+length2+length3]
                    compresseddata = zlib.compress(uncompresseddata)

                    file.write("%d 0 obj\n"
                               "<<\n"
                               "/Length %d\n"
                               "/Length1 %d\n"
                               "/Length2 %d\n"
                               "/Length3 %d\n"
                               "/Filter /FlateDecode\n"
                               ">>\n"
                               "stream\n" % (fontnr+fontstartref, len(compresseddata),
                                                                  length1,
                                                                  length2,
                                                                  length3))
                    #file.write(fontdata[6:6+length1])
                    #file.write(fontdata[12+length1:12+length1+length2])
                    #file.write(fontdata[18+length1+length2:18+length1+length2+length3])
                    file.write(compresseddata)
                    file.write("endstream\n"
                               "endobj\n")
                else:
                    fontnr += 2

        xrefpos = file.tell()
        file.write("xref\n"
                   "0 %d\n" % (len(reflist)+1))
        file.write("0000000000 65535 f \n")
        for ref in reflist:
            file.write("%010i 00000 n \n" % ref)
        file.write("trailer\n"
                   "<<\n"
                   "/Size 8\n"
                   "/Root 1 0 R\n"
                   ">>\n"
                   "startxref\n"
                   "%i\n"
                   "%%%%EOF\n" % xrefpos)

    def writePDFfile_new(self, filename, paperformat=None, rotated=0, fittosize=0, margin=1 * unit.t_cm,
                    bbox=None, bboxenlarge=1 * unit.t_pt):
        sys.stderr.write("*** PyX Warning: writePDFfile is experimental and supports only a subset of PyX's features\n")

        if filename[-4:]!=".pdf":
            filename = filename + ".pdf"

        try:
            writer = pdfwriter.pdfwriter(filename)
        except IOError:
            raise IOError("cannot open output file")

        abbox = bbox is not None and bbox or self.bbox()
        abbox.enlarge(bboxenlarge)

        ctrafo = calctrafo(abbox, paperformat, margin, rotated, fittosize)

        # if there has been a global transformation, adjust the bounding box
        # accordingly
        if ctrafo: abbox.transform(ctrafo)

        mergedprolog = []

        for pritem in self.prolog():
            for mpritem in mergedprolog:
                if mpritem.merge(pritem) is None: break
            else:
                mergedprolog.append(pritem)
        writer.page(abbox, self, mergedprolog, ctrafo)
        writer.close()

    def writetofile(self, filename, *args, **kwargs):
        if filename[-4:] == ".eps":
            self.writeEPSfile(filename, *args, **kwargs)
        elif filename[-4:] == ".pdf":
            self.writePDFfile(filename, *args, **kwargs)
        else:
            sys.stderr.write("*** PyX Warning: deprecated usage of writetofile -- writetofile needs a filename extension or use an explicit call to writeEPSfile or the like\n")
            self.writeEPSfile(filename, *args, **kwargs)

class page(canvas):

    def __init__(self, attrs=[], texrunner=None, pagename=None, paperformat="a4", rotated=0, fittosize=0,
                 margin=1 * unit.t_cm, bboxenlarge=1 * unit.t_pt):
        canvas.__init__(self, attrs, texrunner)
        self.pagename = pagename
        self.paperformat = paperformat.capitalize()
        self.rotated = rotated
        self.fittosize = fittosize
        self.margin = margin
        self.bboxenlarge = bboxenlarge

    def bbox(self):
        # the bounding box of a page is fixed by its format and an optional rotation
        pbbox = bbox.bbox(0, 0, *_paperformats[self.paperformat])
        pbbox.enlarge(self.bboxenlarge)
        if self.rotated:
            pbbox.transform(trafo.rotate(90, *pbbox.center()))
        return pbbox

    def outputPS(self, file):
        file.write("%%%%PageMedia: %s\n" % self.paperformat)
        file.write("%%%%PageOrientation: %s\n" % (self.rotated and "Landscape" or "Portrait"))
        # file.write("%%%%PageBoundingBox: %d %d %d %d\n" % (math.floor(pbbox.llx_pt), math.floor(pbbox.lly_pt),
        #                                                    math.ceil(pbbox.urx_pt), math.ceil(pbbox.ury_pt)))

        # page setup section
        file.write("%%BeginPageSetup\n")
        file.write("/pgsave save def\n")
        # for scaling, we need the real bounding box of the page contents
        pbbox = canvas.bbox(self)
        pbbox.enlarge(self.bboxenlarge)
        ptrafo = calctrafo(pbbox, self.paperformat, self.margin, self.rotated, self.fittosize)
        if ptrafo:
            ptrafo.outputPS(file)
        file.write("%f setlinewidth\n" % unit.topt(style.linewidth.normal))
        file.write("%%EndPageSetup\n")

        # here comes the actual content
        canvas.outputPS(self, file)
        file.write("pgsave restore\n")
        file.write("showpage\n")
        # file.write("%%PageTrailer\n")


class document:

    """holds a collection of page instances which are output as pages of a document"""

    def __init__(self, pages=[]):
        self.pages = pages

    def append(self, page):
        self.pages.append(page)

    def writePSfile(self, filename):
        """write pages to PS file """

        if filename[-3:]!=".ps":
            filename = filename + ".ps"

        try:
            file = open(filename, "w")
        except IOError:
            raise IOError("cannot open output file")

        docbbox = None
        for apage in self.pages:
            pbbox = apage.bbox()
            if docbbox is None:
                docbbox = pbbox
            else:
                docbbox += pbbox

        # document header
        file.write("%!PS-Adobe-3.0\n")
        docbbox.outputPS(file)
        file.write("%%%%Creator: PyX %s\n" % version.version)
        file.write("%%%%Title: %s\n" % filename)
        file.write("%%%%CreationDate: %s\n" %
                   time.asctime(time.localtime(time.time())))
        # required paper formats
        paperformats = {}
        for apage in self.pages:
            if isinstance(apage, page):
                paperformats[apage.paperformat] = _paperformats[apage.paperformat]
        first = 1
        for paperformat, size in paperformats.items():
            if first:
                file.write("%%DocumentMedia: ")
                first = 0
            else:
                file.write("%%+ ")
            file.write("%s %d %d 75 white ()\n" % (paperformat, unit.topt(size[0]), unit.topt(size[1])))

        file.write("%%%%Pages: %d\n" % len(self.pages))
        file.write("%%PageOrder: Ascend\n")
        file.write("%%EndComments\n")

        # document default section
        #file.write("%%BeginDefaults\n")
        #if paperformat:
        #    file.write("%%%%PageMedia: %s\n" % paperformat)
        #file.write("%%%%PageOrientation: %s\n" % (rotated and "Landscape" or "Portrait"))
        #file.write("%%EndDefaults\n")

        # document prolog section
        file.write("%%BeginProlog\n")
        mergedprolog = []
        for apage in self.pages:
            for pritem in apage.prolog():
                for mpritem in mergedprolog:
                    if mpritem.merge(pritem) is None: break
                else:
                    mergedprolog.append(pritem)
        for pritem in mergedprolog:
            pritem.outputPS(file)
        file.write("%%EndProlog\n")

        # document setup section
        #file.write("%%BeginSetup\n")
        #file.write("%%EndSetup\n")

        # pages section
        for nr, apage in enumerate(self.pages):
            file.write("%%%%Page: %s %d\n" % (apage.pagename is None and str(nr) or apage.pagename , nr+1))
            apage.outputPS(file)

        file.write("%%Trailer\n")
        file.write("%%EOF\n")
