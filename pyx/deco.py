#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2002, 2003 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2003 Michael Schindler <m-schindler@users.sourceforge.net>
# Copyright (C) 2002, 2003 André Wobst <wobsta@users.sourceforge.net>
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

class deco(attr.attr):

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

class stroked(deco):

    """stroked is a decorator, which draws the outline of the path"""

    def __init__(self, *styles):
        self.styles = list(styles)

    def decorate(self, dp):
        dp.strokepath = dp.path
        dp.strokestyles = self.styles
        return dp

stroked.clear = attr.clearclass(stroked)


class filled(deco):

    """filled is a decorator, which fills the interior of the path"""

    def __init__(self, *styles):
        self.styles = list(styles)

    def decorate(self, dp):
        dp.fillpath = dp.path
        dp.fillstyles = self.styles
        return dp

filled.clear = attr.clearclass(filled)

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

class arrow(deco):

    """arrow is a decorator which adds an arrow to either side of the path"""

    def __init__(self, position=0, size=_base, attrs=[], angle=45, constriction=0.8):
        self.position = position
        self.size = unit.length(size, default_type="v")
        self.angle = angle
        self.constriction = constriction
        self.attrs = [stroked(), filled()] + helper.ensurelist(attrs)
        attr.mergeattrs(self.attrs)
        attr.checkattrs(self.attrs, [deco, style.fillstyle, style.strokestyle])

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
                          *self.attrs)

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


class barrow(arrow):

    """arrow at begin of path"""

    def __init__(self, *args, **kwargs):
        arrow.__init__(self, 0, *args, **kwargs)

class _barrow_SMALL(barrow):
    def __init__(self, *args, **kwargs):
        barrow.__init__(self, _base/math.sqrt(64), *args, **kwargs)
barrow.SMALL = _barrow_SMALL

class _barrow_SMALl(barrow):
    def __init__(self, *args, **kwargs):
        barrow.__init__(self, _base/math.sqrt(32), *args, **kwargs)
barrow.SMALl = _barrow_SMALl

class _barrow_SMAll(barrow):
    def __init__(self, *args, **kwargs):
        barrow.__init__(self, _base/math.sqrt(16), *args, **kwargs)
barrow.SMAll = _barrow_SMAll

class _barrow_SMall(barrow):
    def __init__(self, *args, **kwargs):
        barrow.__init__(self, _base/math.sqrt(8), *args, **kwargs)
barrow.SMall = _barrow_SMall

class _barrow_Small(barrow):
    def __init__(self, *args, **kwargs):
        barrow.__init__(self, _base/math.sqrt(4), *args, **kwargs)
barrow.Small = _barrow_Small

class _barrow_small(barrow):
    def __init__(self, *args, **kwargs):
        barrow.__init__(self, _base/math.sqrt(2), *args, **kwargs)
barrow.small = _barrow_small

class _barrow_normal(barrow):
    def __init__(self, *args, **kwargs):
        barrow.__init__(self, _base, *args, **kwargs)
barrow.normal = _barrow_normal

class _barrow_large(barrow):
    def __init__(self, *args, **kwargs):
        barrow.__init__(self, _base*math.sqrt(2), *args, **kwargs)
barrow.large = _barrow_large

class _barrow_Large(barrow):
    def __init__(self, *args, **kwargs):
        barrow.__init__(self, _base*math.sqrt(4), *args, **kwargs)
barrow.Large = _barrow_Large

class _barrow_LArge(barrow):
    def __init__(self, *args, **kwargs):
        barrow.__init__(self, _base*math.sqrt(8), *args, **kwargs)
barrow.LArge = _barrow_LArge

class _barrow_LARge(barrow):
    def __init__(self, *args, **kwargs):
        barrow.__init__(self, _base*math.sqrt(16), *args, **kwargs)
barrow.LARge = _barrow_LARge

class _barrow_LARGe(barrow):
    def __init__(self, *args, **kwargs):
        barrow.__init__(self, _base*math.sqrt(32), *args, **kwargs)
barrow.LARGe = _barrow_LARGe

class _barrow_LARGE(barrow):
    def __init__(self, *args, **kwargs):
        barrow.__init__(self, _base*math.sqrt(64), *args, **kwargs)
barrow.LARGE = _barrow_LARGE


class earrow(arrow):

    """arrow at end of path"""

    def __init__(self, *args, **kwargs):
        arrow.__init__(self, 1, *args, **kwargs)

class _earrow_SMALL(earrow):
    def __init__(self, *args, **kwargs):
        earrow.__init__(self, _base/math.sqrt(64), *args, **kwargs)
earrow.SMALL = _earrow_SMALL

class _earrow_SMALl(earrow):
    def __init__(self, *args, **kwargs):
        earrow.__init__(self, _base/math.sqrt(32), *args, **kwargs)
earrow.SMALl = _earrow_SMALl

class _earrow_SMAll(earrow):
    def __init__(self, *args, **kwargs):
        earrow.__init__(self, _base/math.sqrt(16), *args, **kwargs)
earrow.SMAll = _earrow_SMAll

class _earrow_SMall(earrow):
    def __init__(self, *args, **kwargs):
        earrow.__init__(self, _base/math.sqrt(8), *args, **kwargs)
earrow.SMall = _earrow_SMall

class _earrow_Small(earrow):
    def __init__(self, *args, **kwargs):
        earrow.__init__(self, _base/math.sqrt(4), *args, **kwargs)
earrow.Small = _earrow_Small

class _earrow_small(earrow):
    def __init__(self, *args, **kwargs):
        earrow.__init__(self, _base/math.sqrt(2), *args, **kwargs)
earrow.small = _earrow_small

class _earrow_normal(earrow):
    def __init__(self, *args, **kwargs):
        earrow.__init__(self, _base, *args, **kwargs)
earrow.normal = _earrow_normal

class _earrow_large(earrow):
    def __init__(self, *args, **kwargs):
        earrow.__init__(self, _base*math.sqrt(2), *args, **kwargs)
earrow.large = _earrow_large

class _earrow_Large(earrow):
    def __init__(self, *args, **kwargs):
        earrow.__init__(self, _base*math.sqrt(4), *args, **kwargs)
earrow.Large = _earrow_Large

class _earrow_LArge(earrow):
    def __init__(self, *args, **kwargs):
        earrow.__init__(self, _base*math.sqrt(8), *args, **kwargs)
earrow.LArge = _earrow_LArge

class _earrow_LARge(earrow):
    def __init__(self, *args, **kwargs):
        earrow.__init__(self, _base*math.sqrt(16), *args, **kwargs)
earrow.LARge = _earrow_LARge

class _earrow_LARGe(earrow):
    def __init__(self, *args, **kwargs):
        earrow.__init__(self, _base*math.sqrt(32), *args, **kwargs)
earrow.LARGe = _earrow_LARGe

class _earrow_LARGE(earrow):
    def __init__(self, *args, **kwargs):
        earrow.__init__(self, _base*math.sqrt(64), *args, **kwargs)
earrow.LARGE = _earrow_LARGE
