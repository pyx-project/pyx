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

import math
import attr, base, canvas, helper, path, style, trafo, unit

#
# Decorated path
#

class decoratedpath(base.PSCmd):
    """Decorated path

    The main purpose of this class is during the drawing
    (stroking/filling) of a path. It collects attributes for the
    stroke and/or fill operations.
    """

    def __init__(self, path, strokepath=None, fillpath=None,
                 styles=None, strokestyles=None, fillstyles=None, 
                 subcanvas=None):

        self.path = path

        # path to be stroked or filled (or None)
        self.strokepath = strokepath
        self.fillpath = fillpath

        # global style for stroking and filling and subdps
        self.styles = helper.ensurelist(styles)

        # styles which apply only for stroking and filling
        self.strokestyles = helper.ensurelist(strokestyles)
        self.fillstyles = helper.ensurelist(fillstyles)

        # the canvas can contain additional elements of the path, e.g.,
        # arrowheads,
        if subcanvas is None:
            self.subcanvas = canvas.canvas()
        else:
            self.subcanvas = subcanvas


    def bbox(self):
        return self.subcanvas.bbox() + self.path.bbox()

    def prolog(self):
        result = []
        for style in list(self.styles) + list(self.fillstyles) + list(self.strokestyles):
            result.extend(style.prolog())
        result.extend(self.subcanvas.prolog())
        return result

    def write(self, file):
        # draw (stroke and/or fill) the decoratedpath on the canvas
        # while trying to produce an efficient output, e.g., by
        # not writing one path two times

        # small helper
        def _writestyles(styles, file=file):
            for style in styles:
                style.write(file)

        # apply global styles
        if self.styles:
            canvas._gsave().write(file)
            _writestyles(self.styles)

        if self.fillpath is not None:
            canvas._newpath().write(file)
            self.fillpath.write(file)

            if self.strokepath==self.fillpath:
                # do efficient stroking + filling
                canvas._gsave().write(file)

                if self.fillstyles:
                    _writestyles(self.fillstyles)

                canvas._fill().write(file)
                canvas._grestore().write(file)

                if self.strokestyles:
                    canvas._gsave().write(file)
                    _writestyles(self.strokestyles)

                canvas._stroke().write(file)

                if self.strokestyles:
                    canvas._grestore().write(file)
            else:
                # only fill fillpath - for the moment
                if self.fillstyles:
                    canvas._gsave().write(file)
                    _writestyles(self.fillstyles)

                canvas._fill().write(file)

                if self.fillstyles:
                    canvas._grestore().write(file)

        if self.strokepath is not None and self.strokepath!=self.fillpath:
            # this is the only relevant case still left
            # Note that a possible stroking has already been done.

            if self.strokestyles:
                canvas._gsave().write(file)
                _writestyles(self.strokestyles)

            canvas._newpath().write(file)
            self.strokepath.write(file)
            canvas._stroke().write(file)

            if self.strokestyles:
                canvas._grestore().write(file)

        if not self.strokepath is not None and not self.fillpath:
            raise RuntimeError("Path neither to be stroked nor filled")

        # now, draw additional elements of decoratedpath
        self.subcanvas.write(file)

        # restore global styles
        if self.styles:
            canvas._grestore().write(file)

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
        dp.strokepath = dp.path
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
        dp.fillpath = dp.path
        dp.fillstyles = self.styles
        return dp

filled = _filled()
filled.clear = attr.clearclass(_filled)

# 
# Arrows
#

# two helper functions which construct the arrowhead and return its size, respectively

def _arrowheadtemplatelength(anormpath, size):
    "calculate length of arrowhead template (in parametrisation of anormpath)"
    # get tip (tx, ty)
    tx, ty = anormpath.begin()

    # obtain arrow template by using path up to first intersection
    # with circle around tip (as suggested by Michael Schindler)
    ipar = anormpath.intersect(path.circle(tx, ty, size))
    if ipar[0]:
        alen = ipar[0][0]
    else:
        # if this doesn't work, use first order conversion from pts to
        # the bezier curve's parametrization
        tlen = unit.topt(anormpath.tangent(0).arclength())
        try:
            alen = unit.topt(size)/tlen
        except ArithmeticError:
            # take maximum, we can get
            alen = anormpath.range()
        if alen > anormpath.range(): alen = anormpath.range()

    return alen


def _arrowhead(anormpath, size, angle, constriction):

    """helper routine, which returns an arrowhead for a normpath

    returns arrowhead at begin of anormpath with size,
    opening angle and relative constriction
    """

    alen = _arrowheadtemplatelength(anormpath, size)
    tx, ty = anormpath.begin()

    # now we construct the template for our arrow but cutting
    # the path a the corresponding length
    arrowtemplate = anormpath.split([alen])[0]

    # from this template, we construct the two outer curves
    # of the arrow
    arrowl = arrowtemplate.transformed(trafo.rotate(-angle/2.0, tx, ty))
    arrowr = arrowtemplate.transformed(trafo.rotate( angle/2.0, tx, ty))

    # now come the joining backward parts
    if constriction:
        # arrow with constriction

        # constriction point (cx, cy) lies on path
        cx, cy = anormpath.at(constriction*alen)

        arrowcr= path.line(*(arrowr.end()+(cx,cy)))

        arrow = arrowl.reversed() << arrowr << arrowcr
        arrow.append(path.closepath())
    else:
        # arrow without constriction
        arrow = arrowl.reversed() << arrowr
        arrow.append(path.closepath())

    return arrow


_base = unit.v_pt(4)

class arrow(deco, attr.attr):

    """arrow is a decorator which adds an arrow to either side of the path"""

    def __init__(self, attrs=[], position=0, size=_base, angle=45, constriction=0.8):
        self.attrs = attr.mergeattrs(attrs, defaults=[style.linestyle.solid, stroked, filled])
        attr.checkattrs(self.attrs, [deco, style.fillstyle, style.strokestyle])
        self.position = position
        self.size = unit.length(size, default_type="v")
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
        # XXX raise exception error, when strokepath is not defined

        # convert to normpath if necessary
        if isinstance(dp.strokepath, path.normpath):
            anormpath = dp.strokepath
        else:
            anormpath = path.normpath(dp.path)
        if self.position:
            anormpath = anormpath.reversed()

        # add arrowhead to decoratedpath
        dp.subcanvas.draw(_arrowhead(anormpath, self.size, self.angle, self.constriction),
                          self.attrs)

        # calculate new strokepath
        alen = _arrowheadtemplatelength(anormpath, self.size)
        if self.constriction:
            ilen = alen*self.constriction
        else:
            ilen = alen

        # correct somewhat for rotation of arrow segments
        ilen = ilen*math.cos(math.pi*self.angle/360.0)

        # this is the rest of the path, we have to draw
        anormpath = anormpath.split([ilen])[1]

        # go back to original orientation, if necessary
        if self.position:
            anormpath=anormpath.reversed()

        # set the new (shortened) strokepath
        dp.strokepath=anormpath

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
