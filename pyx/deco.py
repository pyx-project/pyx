#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2002-2004 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2003-2004 Michael Schindler <m-schindler@users.sourceforge.net>
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

# TODO:
# - should we improve on the arc length -> arg parametrization routine or
#   should we at least factor it out?

import sys, math
import attr, base, canvas, color, path, style, trafo, unit

try:
    from math import radians
except ImportError:
    # fallback implementation for Python 2.1 and below
    def radians(x): return x*math.pi/180

#
# Decorated path
#

class decoratedpath(base.canvasitem):
    """Decorated path

    The main purpose of this class is during the drawing
    (stroking/filling) of a path. It collects attributes for the
    stroke and/or fill operations.
    """

    def __init__(self, path, strokepath=None, fillpath=None,
                 styles=None, strokestyles=None, fillstyles=None,
                 ornaments=None):

        self.path = path

        # global style for stroking and filling and subdps
        self.styles = styles

        # styles which apply only for stroking and filling
        self.strokestyles = strokestyles
        self.fillstyles = fillstyles

        # the decoratedpath can contain additional elements of the
        # path (ornaments), e.g., arrowheads.
        if ornaments is None:
            self.ornaments = canvas.canvas()
        else:
            self.ornaments = ornaments

        self.nostrokeranges = None

    def ensurenormpath(self):
        """convert self.path into a normpath"""
        assert self.nostrokeranges is None or isinstance(self.path, path.normpath), "you don't understand what you are doing"
        self.path = self.path.normpath()

    def excluderange(self, begin, end):
        assert isinstance(self.path, path.normpath), "you don't understand what this is about"
        if self.nostrokeranges is None:
            self.nostrokeranges = [(begin, end)]
        else:
            ibegin = 0
            while ibegin < len(self.nostrokeranges) and self.nostrokeranges[ibegin][1] < begin:
                ibegin += 1

            if ibegin == len(self.nostrokeranges):
                self.nostrokeranges.append((begin, end))
                return

            iend = len(self.nostrokeranges) - 1
            while 0 <= iend and end < self.nostrokeranges[iend][0]:
                iend -= 1

            if iend == -1:
                self.nostrokeranges.insert(0, (begin, end))
                return

            if self.nostrokeranges[ibegin][0] < begin:
                begin = self.nostrokeranges[ibegin][0]
            if end < self.nostrokeranges[iend][1]:
                end = self.nostrokeranges[iend][1]

            self.nostrokeranges[ibegin:iend+1] = [(begin, end)]

    def bbox(self):
        pathbbox = self.path.bbox()
        ornamentsbbox = self.ornaments.bbox()
        if ornamentsbbox is not None:
            return ornamentsbbox + pathbbox
        else:
            return pathbbox

    def prolog(self):
        result = []
        if self.styles:
            for style in self.styles: 
                result.extend(style.prolog())
        if self.fillstyles:
            for style in self.fillstyles: 
                result.extend(style.prolog())
        if self.strokestyles:
            for style in self.strokestyles: 
                result.extend(style.prolog())
        result.extend(self.ornaments.prolog())
        return result

    def strokepath(self):
        if self.nostrokeranges:
            splitlist = []
            for begin, end in self.nostrokeranges:
                splitlist.append(begin)
                splitlist.append(end)
            split = self.path.split(splitlist)
            # XXX properly handle closed paths?
            result = split[0]
            for i in range(2, len(split), 2):
                result += split[i]
            return result
        else:
            return self.path

    def outputPS(self, file):
        # draw (stroke and/or fill) the decoratedpath on the canvas
        # while trying to produce an efficient output, e.g., by
        # not writing one path two times

        # small helper
        def _writestyles(styles, file=file):
            for style in styles:
                style.outputPS(file)

        if self.strokestyles is None and self.fillstyles is None:
            raise RuntimeError("Path neither to be stroked nor filled")

        strokepath = self.strokepath()
        fillpath = self.path

        # apply global styles
        if self.styles:
            file.write("gsave\n")
            _writestyles(self.styles)

        if self.fillstyles is not None:
            file.write("newpath\n")
            fillpath.outputPS(file)

            if self.strokestyles is not None and strokepath is fillpath:
                # do efficient stroking + filling if respective paths are identical
                file.write("gsave\n")

                if self.fillstyles:
                    _writestyles(self.fillstyles)

                file.write("fill\n")
                file.write("grestore\n")

                if self.strokestyles:
                    file.write("gsave\n")
                    _writestyles(self.strokestyles)

                file.write("stroke\n")

                if self.strokestyles:
                    file.write("grestore\n")
            else:
                # only fill fillpath - for the moment
                if self.fillstyles:
                    file.write("gsave\n")
                    _writestyles(self.fillstyles)

                file.write("fill\n")

                if self.fillstyles:
                    file.write("grestore\n")

        if self.strokestyles is not None and (strokepath is not fillpath or self.fillstyles is None):
            # this is the only relevant case still left
            # Note that a possible stroking has already been done.

            if self.strokestyles:
                file.write("gsave\n")
                _writestyles(self.strokestyles)

            file.write("newpath\n")
            strokepath.outputPS(file)
            file.write("stroke\n")

            if self.strokestyles:
                file.write("grestore\n")

        # now, draw additional elements of decoratedpath
        self.ornaments.outputPS(file)

        # restore global styles
        if self.styles:
            file.write("grestore\n")

    def outputPDF(self, file):
        # draw (stroke and/or fill) the decoratedpath on the canvas

        def _writestyles(styles, file=file):
            for style in styles:
                style.outputPDF(file)

        def _writestrokestyles(strokestyles, file=file):
            for style in strokestyles:
                if isinstance(style, color.color):
                    style.outputPDF(file, fillattr=0)
                else:
                    style.outputPDF(file)

        def _writefillstyles(fillstyles, file=file):
            for style in fillstyles:
                if isinstance(style, color.color):
                    style.outputPDF(file, strokeattr=0)
                else:
                    style.outputPDF(file)

        if self.strokestyles is None and self.fillstyles is None:
            raise RuntimeError("Path neither to be stroked nor filled")

        strokepath = self.strokepath()
        fillpath = self.path

        # apply global styles
        if self.styles:
            file.write("q\n") # gsave
            _writestyles(self.styles)

        if self.fillstyles is not None:
            fillpath.outputPDF(file)

            if self.strokestyles is not None and strokepath is fillpath:
                # do efficient stroking + filling
                file.write("q\n") # gsave

                if self.fillstyles:
                    _writefillstyles(self.fillstyles)
                if self.strokestyles:
                    _writestrokestyles(self.strokestyles)

                file.write("B\n") # both stroke and fill
                file.write("Q\n") # grestore
            else:
                # only fill fillpath - for the moment
                if self.fillstyles:
                    file.write("q\n") # gsave
                    _writefillstyles(self.fillstyles)

                file.write("f\n") # fill

                if self.fillstyles:
                    file.write("Q\n") # grestore

        if self.strokestyles is not None and (strokepath is not fillpath or self.fillstyles is None):
            # this is the only relevant case still left
            # Note that a possible stroking has already been done.

            if self.strokestyles:
                file.write("q\n") # gsave
                _writestrokestyles(self.strokestyles)

            strokepath.outputPDF(file)
            file.write("S\n") # stroke

            if self.strokestyles:
                file.write("Q\n") # grestore

        # now, draw additional elements of decoratedpath
        self.ornaments.outputPDF(file)

        # restore global styles
        if self.styles:
            file.write("Q\n") # grestore

#
# Path decorators
#

class deco:

    """decorators

    In contrast to path styles, path decorators depend on the concrete
    path to which they are applied. In particular, they don't make
    sense without any path and can thus not be used in canvas.set!

    """

    def decorate(self, dp):
        """apply a style to a given decoratedpath object dp

        decorate accepts a decoratedpath object dp, applies PathStyle
        by modifying dp in place and returning the new dp.
        """

        pass

#
# stroked and filled: basic decos which stroked and fill,
# respectively the path
#

class _stroked(deco, attr.exclusiveattr):

    """stroked is a decorator, which draws the outline of the path"""

    def __init__(self, styles=[]):
        attr.exclusiveattr.__init__(self, _stroked)
        self.styles = attr.mergeattrs(styles)
        attr.checkattrs(self.styles, [style.strokestyle])

    def __call__(self, styles=[]):
        # XXX or should we also merge self.styles
        return _stroked(styles)

    def decorate(self, dp):
        if dp.strokestyles is not None:
            raise RuntimeError("Cannot stroke an already stroked path")
        dp.strokestyles = self.styles
        return dp

stroked = _stroked()
stroked.clear = attr.clearclass(_stroked)


class _filled(deco, attr.exclusiveattr):

    """filled is a decorator, which fills the interior of the path"""

    def __init__(self, styles=[]):
        attr.exclusiveattr.__init__(self, _filled)
        self.styles = attr.mergeattrs(styles)
        attr.checkattrs(self.styles, [style.fillstyle])

    def __call__(self, styles=[]):
        # XXX or should we also merge self.styles
        return _filled(styles)

    def decorate(self, dp):
        if dp.fillstyles is not None:
            raise RuntimeError("Cannot fill an already filled path")
        dp.fillstyles = self.styles
        return dp

filled = _filled()
filled.clear = attr.clearclass(_filled)

#
# Arrows
#

# helper function which constructs the arrowhead

def _arrowhead(anormsubpath, size, angle, constrictionlen, reversed):

    """helper routine, which returns an arrowhead from a given anormsubpath

    returns arrowhead at begin of anormpath with size,
    opening angle and constriction length constrictionlen
    """

    if reversed:
        anormsubpath = anormsubpath.reversed()
    alen = anormsubpath.arclentoparam(size)
    tx, ty = anormsubpath.begin()

    # now we construct the template for our arrow but cutting
    # the path a the corresponding length
    arrowtemplate = anormsubpath.split([alen])[0]

    # from this template, we construct the two outer curves
    # of the arrow
    arrowl = path.normpath([arrowtemplate.transformed(trafo.rotate(-angle/2.0, tx, ty))])
    arrowr = path.normpath([arrowtemplate.transformed(trafo.rotate( angle/2.0, tx, ty))])

    # now come the joining backward parts

    # constriction point (cx, cy) lies on path
    cx, cy = anormsubpath.at(anormsubpath.arclentoparam(constrictionlen))

    arrowcr= path.line(*(arrowr.end()+(cx,cy)))

    arrow = arrowl.reversed() << arrowr << arrowcr
    arrow[-1].close()

    return arrow


_base = 6 * unit.v_pt

class arrow(deco, attr.attr):

    """arrow is a decorator which adds an arrow to either side of the path"""

    def __init__(self, attrs=[], position=0, size=_base, angle=45, constriction=0.8):
        self.attrs = attr.mergeattrs([style.linestyle.solid, filled] + attrs)
        attr.checkattrs(self.attrs, [deco, style.fillstyle, style.strokestyle])
        self.position = position
        self.size = size
        self.angle = angle
        self.constriction = constriction

    def __call__(self, attrs=None, position=None, size=None, angle=None, constriction=None):
        if attrs is None:
            attrs = self.attrs
        if position is None:
            position = self.position
        if size is None:
            size = self.size
        if angle is None:
            angle = self.angle
        if constriction is None:
            constriction = self.constriction
        return arrow(attrs=attrs, position=position, size=size, angle=angle, constriction=constriction)

    def decorate(self, dp):
        dp.ensurenormpath()
        anormpath = dp.path

        # calculate absolute arc length of constricition
        # Note that we have to correct this length because the arrowtemplates are rotated
        # by self.angle/2 to the left and right. Hence, if we want no constriction, i.e., for
        # self.constriction = 1, we actually have a length which is approximately shorter
        # by the given geometrical factor.
        constrictionlen = self.size*self.constriction*math.cos(radians(self.angle/2.0))
        
        if self.position == 0:
            # Note that the template for the arrow head should only be constructed
            # from the first normsubpath
            firstnormsubpath = anormpath[0]
            arrowhead = _arrowhead(firstnormsubpath, self.size, self.angle, constrictionlen, reversed=0)
        else:
            lastnormsubpath = anormpath[-1]
            arrowhead = _arrowhead(lastnormsubpath, self.size, self.angle, constrictionlen, reversed=1)

        # add arrowhead to decoratedpath
        dp.ornaments.draw(arrowhead, self.attrs)

        if self.position == 0:
            # exclude first part of the first normsubpath from stroking
            ilen = firstnormsubpath.arclentoparam(min(self.size, constrictionlen))
            dp.excluderange((0, 0), (0,ilen))
        else:
            ilen = lastnormsubpath.arclentoparam(lastnormsubpath.arclen()-min(self.size, constrictionlen))
            # TODO. provide a better way to access the number of normsubpaths in a normpath
            lastnormsubpathindex = len(anormpath.normsubpaths)-1
            dp.excluderange((lastnormsubpathindex, ilen), (lastnormsubpathindex, lastnormsubpath.range()))

        return dp

arrow.clear = attr.clearclass(arrow)

# arrows at begin of path
barrow = arrow(position=0)
barrow.SMALL = barrow(size=_base/math.sqrt(64))
barrow.SMALl = barrow(size=_base/math.sqrt(32))
barrow.SMAll = barrow(size=_base/math.sqrt(16))
barrow.SMall = barrow(size=_base/math.sqrt(8))
barrow.Small = barrow(size=_base/math.sqrt(4))
barrow.small = barrow(size=_base/math.sqrt(2))
barrow.normal = barrow(size=_base)
barrow.large = barrow(size=_base*math.sqrt(2))
barrow.Large = barrow(size=_base*math.sqrt(4))
barrow.LArge = barrow(size=_base*math.sqrt(8))
barrow.LARge = barrow(size=_base*math.sqrt(16))
barrow.LARGe = barrow(size=_base*math.sqrt(32))
barrow.LARGE = barrow(size=_base*math.sqrt(64))

# arrows at end of path
earrow = arrow(position=1)
earrow.SMALL = earrow(size=_base/math.sqrt(64))
earrow.SMALl = earrow(size=_base/math.sqrt(32))
earrow.SMAll = earrow(size=_base/math.sqrt(16))
earrow.SMall = earrow(size=_base/math.sqrt(8))
earrow.Small = earrow(size=_base/math.sqrt(4))
earrow.small = earrow(size=_base/math.sqrt(2))
earrow.normal = earrow(size=_base)
earrow.large = earrow(size=_base*math.sqrt(2))
earrow.Large = earrow(size=_base*math.sqrt(4))
earrow.LArge = earrow(size=_base*math.sqrt(8))
earrow.LARge = earrow(size=_base*math.sqrt(16))
earrow.LARGe = earrow(size=_base*math.sqrt(32))
earrow.LARGE = earrow(size=_base*math.sqrt(64))

