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

# XXX remove string module
# XXX what is a pattern
# XXX what is a color


"""The canvas module provides a PostScript canvas class and related classes

A canvas holds a collection of all elements that should be displayed together
with their attributes.
"""

import string, cStringIO, time
import attr, base, bbox, deco, unit, prolog, style, trafo, version

# known paperformats as tuple(width, height)

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

# XXX help me find my identity

class clip(base.PSCmd):

    """class for use in canvas constructor which clips to a path"""

    def __init__(self, path):
        """construct a clip instance for a given path"""
        self.path = path

    def bbox(self):
        # as a PSCmd a clipping path has NO influence on the bbox...
        return bbox._bbox()

    def clipbbox(self):
        # ... but for clipping, we nevertheless need the bbox
        return self.path.bbox()

    def write(self, file):
        _newpath().write(file)
        self.path.write(file)
        _clip().write(file)

#
# some very primitive Postscript operators
#

class _newpath(base.PSOp):
    def write(self, file):
       file.write("newpath\n")


class _stroke(base.PSOp):
    def write(self, file):
       file.write("stroke\n")


class _fill(base.PSOp):
    def write(self, file):
        file.write("fill\n")


class _clip(base.PSOp):
    def write(self, file):
       file.write("clip\n")


class _gsave(base.PSOp):
    def write(self, file):
       file.write("gsave\n")


class _grestore(base.PSOp):
    def write(self, file):
       file.write("grestore\n")

#
#
#

class _canvas(base.PSCmd):

    """a canvas is a collection of PSCmds together with PSAttrs"""

    def __init__(self, *args):

        """construct a canvas

        The canvas can be modfied by supplying args, which have
        to be instances of one of the following classes:
         - trafo.trafo (leading to a global transformation of the canvas)
         - canvas.clip (clips the canvas)
         - base.PathStyle (sets some global attributes of the canvas)

        Note that, while the first two properties are fixed for the
        whole canvas, the last one can be changed via canvas.set()

        """

        self.PSOps     = []
        self.trafo     = trafo.trafo()
        self.clipbbox  = bbox._bbox()

        # prevent cyclic imports
        import text
        self.texrunner = text.defaulttexrunner

        for arg in args:
            if isinstance(arg, trafo.trafo_pt):
                self.trafo = self.trafo*arg
                self.PSOps.append(arg)
            elif isinstance(arg, clip):
                self.clipbbox=(self.clipbbox*
                               arg.clipbbox().transformed(self.trafo))
                self.PSOps.append(arg)
            else:
                self.set(arg)

    def bbox(self):
        """returns bounding box of canvas"""
        obbox = reduce(lambda x,y:
                       isinstance(y, base.PSCmd) and x+y.bbox() or x,
                       self.PSOps,
                       bbox._bbox())

        # transform according to our global transformation and
        # intersect with clipping bounding box (which have already been
        # transformed in canvas.__init__())
        return obbox.transformed(self.trafo)*self.clipbbox

    def prolog(self):
        result = []
        for cmd in self.PSOps:
            result.extend(cmd.prolog())
        return result

    def write(self, file):
        if self.PSOps:
            _gsave().write(file)
            for cmd in self.PSOps:
                cmd.write(file)
            _grestore().write(file)

    def insert(self, PSOp, args=[]):
        """insert PSOp in the canvas.

        If args are given, then insert a canvas containing PSOp applying args.

        returns the PSOp

        """

        # XXX check for PSOp

        if args:
            sc = _canvas(*args)
            sc.insert(PSOp)
            self.PSOps.append(sc)
        else:
            self.PSOps.append(PSOp)

        return PSOp

    def set(self, attrs):
        """sets styles args globally for the rest of the canvas

        returns canvas

        """

        attr.checkattrs(attrs, [style.strokestyle, style.fillstyle])
        for astyle in attrs:
            self.insert(astyle)
        return self

    def draw(self, path, attrs):
        """draw path on canvas using the style given by args

        The argument attrs consists of PathStyles, which modify
        the appearance of the path, PathDecos, which add some new
        visual elements to the path, or trafos, which are applied
        before drawing the path.

        returns the canvas

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

        return self

    def stroke(self, path, attrs=[]):
        """stroke path on canvas using the style given by args

        The argument attrs consists of PathStyles, which modify
        the appearance of the path, PathDecos, which add some new
        visual elements to the path, or trafos, which are applied
        before drawing the path.

        returns the canvas

        """

        return self.draw(path, [deco.stroked]+list(attrs))

    def fill(self, path, attrs=[]):
        """fill path on canvas using the style given by args

        The argument attrs consists of PathStyles, which modify
        the appearance of the path, PathDecos, which add some new
        visual elements to the path, or trafos, which are applied
        before drawing the path.

        returns the canvas

        """

        return self.draw(path, [deco.filled]+list(attrs))

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
        # XXX: some checks are in order
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
        return bbox._bbox()

    def write(self, file):
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

        patternprefix = string.join(("<<",
                                     "/PatternType 1",
                                     "/PaintType %d" % self.painttype,
                                     "/TilingType %d" % self.tilingtype,
                                     "/BBox[%s]" % str(patternbbox),
                                     "/XStep %g" % xstep,
                                     "/YStep %g" % ystep,
                                     "/PaintProc {\nbegin\n"),
                                    sep="\n")
        stringfile = cStringIO.StringIO()
        _canvas.write(self, stringfile)
        patternproc = stringfile.getvalue()
        stringfile.close()
        patterntrafostring = self.patterntrafo is None and "matrix" or str(self.patterntrafo)
        patternsuffix = "end\n} bind\n>>\n%s\nmakepattern" % patterntrafostring

        pr = _canvas.prolog(self)
        pr.append(prolog.definition(self.id, string.join((patternprefix, patternproc, patternsuffix), "")))
        return pr

pattern.clear = attr.clearclass(pattern)

#
# The main canvas class
#

class canvas(_canvas):

    """a canvas is a collection of PSCmds together with PSAttrs"""

    def writetofile(self, filename, paperformat=None, rotated=0, fittosize=0, margin="1 t cm",
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
        abbox = abbox.enlarged(bboxenlarge)
        ctrafo = None     # global transformation of canvas

        if rotated:
            ctrafo = trafo.rotate_pt(90,
                                     0.5*(abbox.llx+abbox.urx),
                                     0.5*(abbox.lly+abbox.ury))

        if paperformat:
            # center (optionally rotated) output on page
            try:
                width, height = _paperformats[paperformat.upper()]
            except KeyError:
                raise KeyError, "unknown paperformat '%s'" % paperformat
            width = unit.topt(width)
            height = unit.topt(height)

            if not ctrafo: ctrafo=trafo.trafo()

            ctrafo = ctrafo.translated_pt(0.5*(width -(abbox.urx-abbox.llx))-
                                       abbox.llx,
                                       0.5*(height-(abbox.ury-abbox.lly))-
                                       abbox.lly)

            if fittosize:
                # scale output to pagesize - margins
                margin = unit.topt(margin)
                if 2*margin > min(width, height):
                    raise RuntimeError("Margins too broad for selected paperformat. Aborting.")

                if rotated:
                    sfactor = min((height-2*margin)/(abbox.urx-abbox.llx),
                                  (width-2*margin)/(abbox.ury-abbox.lly))
                else:
                    sfactor = min((width-2*margin)/(abbox.urx-abbox.llx),
                                  (height-2*margin)/(abbox.ury-abbox.lly))

                ctrafo = ctrafo.scaled_pt(sfactor, sfactor, 0.5*width, 0.5*height)


        elif fittosize:
            raise ValueError("must specify paper size for fittosize")

        # if there has been a global transformation, adjust the bounding box
        # accordingly
        if ctrafo: abbox = abbox.transformed(ctrafo)

        file.write("%!PS-Adobe-3.0 EPSF 3.0\n")
        abbox.write(file)
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
            pritem.write(file)

        file.write("%%EndProlog\n")

        # again, if there has occured global transformation, apply it now
        if ctrafo: ctrafo.write(file)

        file.write("%f setlinewidth\n" % unit.topt(style.linewidth.normal))

        # here comes the actual content
        self.write(file)

        file.write("showpage\n")
        file.write("%%Trailer\n")
        file.write("%%EOF\n")
