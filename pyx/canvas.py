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

import sys, cStringIO, math, time
import attr, base,  deco, unit, prolog, style, trafo, version

# known paperformats as tuple (width, height)

_paperformats = { "A4"      : ("210 t mm",  "297 t mm"),
                  "A3"      : ("297 t mm",  "420 t mm"),
                  "A2"      : ("420 t mm",  "594 t mm"),
                  "A1"      : ("594 t mm",  "840 t mm"),
                  "A0"      : ("840 t mm", "1188 t mm"),
                  "A0B"     : ("910 t mm", "1370 t mm"),
                  "LETTER"  : ("8.5 t inch", "11 t inch"),
                  "LEGAL"   : ("8.5 t inch", "14 t inch")}

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

        If args are given, then insert a canvas containing PSOp applying args.

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
           xstep = unit.topt(unit.length(self.xstep))
        if self.ystep is None:
            ystep = unit.topt(realpatternbbox.height())
        else:
           ystep = unit.topt(unit.length(self.ystep))
        if not xstep:
            raise ValueError("xstep in pattern cannot be zero")
        if not ystep:
            raise ValueError("ystep in pattern cannot be zero")
        patternbbox = self.patternbbox or realpatternbbox.enlarged("5 pt")

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

#
# The main canvas class
#

class canvas(_canvas):

    """a canvas is a collection of PSCmds together with PSAttrs"""

    def writeEPSfile(self, filename, paperformat=None, rotated=0, fittosize=0, margin="1 t cm",
                    bbox=None, bboxenlarge="1 t pt"):
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
        ctrafo = None     # global transformation of canvas

        if rotated:
            ctrafo = trafo.rotate_pt(90,
                                     0.5*(abbox.llx_pt+abbox.urx_pt),
                                     0.5*(abbox.lly_pt+abbox.ury_pt))

        if paperformat:
            # center (optionally rotated) output on page
            try:
                width, height = _paperformats[paperformat.upper()]
            except KeyError:
                raise KeyError, "unknown paperformat '%s'" % paperformat
            width = unit.topt(width)
            height = unit.topt(height)

            if not ctrafo: ctrafo=trafo.trafo()

            ctrafo = ctrafo.translated_pt(0.5*(width -(abbox.urx_pt-abbox.llx_pt))-
                                       abbox.llx_pt,
                                       0.5*(height-(abbox.ury_pt-abbox.lly_pt))-
                                       abbox.lly_pt)

            if fittosize:
                # scale output to pagesize - margins
                margin = unit.topt(margin)
                if 2*margin > min(width, height):
                    raise RuntimeError("Margins too broad for selected paperformat. Aborting.")

                if rotated:
                    sfactor = min((height-2*margin)/(abbox.urx_pt-abbox.llx_pt),
                                  (width-2*margin)/(abbox.ury_pt-abbox.lly_pt))
                else:
                    sfactor = min((width-2*margin)/(abbox.urx_pt-abbox.llx_pt),
                                  (height-2*margin)/(abbox.ury_pt-abbox.lly_pt))

                ctrafo = ctrafo.scaled_pt(sfactor, sfactor, 0.5*width, 0.5*height)


        elif fittosize:
            raise ValueError("must specify paper size for fittosize")

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

        # again, if there has occured global transformation, apply it now
        if ctrafo: ctrafo.outputPS(file)

        file.write("%f setlinewidth\n" % unit.topt(style.linewidth.normal))

        # here comes the actual content
        self.outputPS(file)

        file.write("showpage\n")
        file.write("%%Trailer\n")
        file.write("%%EOF\n")

    def writePDFfile(self, filename, bbox=None, bboxenlarge="1 t pt"):
        sys.stderr.write("*** PyX Warning: writePDFfile is experimental and supports only a subset of PyX's features\n")

        if filename[-4:]!=".pdf":
            filename = filename + ".pdf"

        try:
            file = open(filename, "wb")
        except IOError:
            raise IOError("cannot open output file")

        abbox = bbox is not None and bbox or self.bbox()
        abbox.enlarge(bboxenlarge)

        file.write("%%PDF-1.4\n%%%s%s%s%s\n" % (chr(195), chr(182), chr(195), chr(169)))
        reflist = [file.tell()]
        file.write("1 0 obj\n"
                   "<<\n"
                   "/Type /Catalog\n"
                   "/Outlines 2 0 R\n"
                   "/Pages 3 0 R\n"
                   ">>\n"
                   "endobj\n")
        reflist.append(file.tell())
        file.write("2 0 obj\n"
                   "<<\n"
                   "/Type Outlines\n"
                   "/Count 0\n"
                   ">>\n"
                   "endobj\n")
        reflist.append(file.tell())
        file.write("3 0 obj\n"
                   "<<\n"
                   "/Type /Pages\n"
                   "/Kids [4 0 R]\n"
                   "/Count 1\n"
                   ">>\n"
                   "endobj\n")
        reflist.append(file.tell())
        file.write("4 0 obj\n"
                   "<<\n"
                   "/Type /Page\n"
                   "/Parent 3 0 R\n")
        abbox.outputPDF(file)
        file.write("/Contents 5 0 R\n"
                   "/Resources << /ProcSet 7 0 R >>\n"
                   ">>\n"
                   "endobj\n")
        reflist.append(file.tell())
        file.write("5 0 obj\n"
                   "<< /Length 6 0 R >>\n"
                   "stream\n")
        streamstartpos = file.tell()
        style.linewidth.normal.outputPDF(file)
        self.outputPDF(file)
        streamendpos = file.tell()
        file.write("endstream\n"
                   "endobj\n")
        reflist.append(file.tell())
        file.write("6 0 obj\n"
                   "%s\n"
                   "endobj\n" % (streamendpos - streamstartpos))
        reflist.append(file.tell())
        file.write("7 0 obj\n"
                   "[/PDF]\n"
                   "endobj\n")
        xrefpos = file.tell()
        file.write("xref\n"
                   "0 8\n")
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

    def writetofile(self, filename, *args, **kwargs):
        if filename[-4:] == ".eps":
            self.writeEPSfile(filename, *args, **kwargs)
        elif filename[-4:] == ".pdf":
            self.writePDFfile(filename, *args, **kwargs)
        else:
            sys.stderr.write("*** PyX Warning: deprecated usage of writetofile -- writetofile needs a filename extension or use an explicit call to writeEPSfile or the like\n")
            self.writeEPSfile(filename, *args, **kwargs)
