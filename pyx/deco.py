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
        scbbox = self.subcanvas.bbox()
        pbbox = self.path.bbox()
        if scbbox is not None:
            return scbbox+pbbox
        else:
            return pbbox

    def prolog(self):
        result = []
        for style in list(self.styles) + list(self.fillstyles) + list(self.strokestyles):
            result.extend(style.prolog())
        result.extend(self.subcanvas.prolog())
        return result

    def outputPS(self, file):
        # draw (stroke and/or fill) the decoratedpath on the canvas
        # while trying to produce an efficient output, e.g., by
        # not writing one path two times

        # small helper
        def _writestyles(styles, file=file):
            for style in styles:
                style.outputPS(file)

        # apply global styles
        if self.styles:
            canvas._gsave().outputPS(file)
            _writestyles(self.styles)

        if self.fillpath is not None:
            canvas._newpath().outputPS(file)
            self.fillpath.outputPS(file)

            if self.strokepath==self.fillpath:
                # do efficient stroking + filling
                canvas._gsave().outputPS(file)

                if self.fillstyles:
                    _writestyles(self.fillstyles)

                canvas._fill().outputPS(file)
                canvas._grestore().outputPS(file)

                if self.strokestyles:
                    canvas._gsave().outputPS(file)
                    _writestyles(self.strokestyles)

                canvas._stroke().outputPS(file)

                if self.strokestyles:
                    canvas._grestore().outputPS(file)
            else:
                # only fill fillpath - for the moment
                if self.fillstyles:
                    canvas._gsave().outputPS(file)
                    _writestyles(self.fillstyles)

                canvas._fill().outputPS(file)

                if self.fillstyles:
                    canvas._grestore().outputPS(file)

        if self.strokepath is not None and self.strokepath!=self.fillpath:
            # this is the only relevant case still left
            # Note that a possible stroking has already been done.

            if self.strokestyles:
                canvas._gsave().outputPS(file)
                _writestyles(self.strokestyles)

            canvas._newpath().outputPS(file)
            self.strokepath.outputPS(file)
            canvas._stroke().outputPS(file)

            if self.strokestyles:
                canvas._grestore().outputPS(file)

        if self.strokepath is None and self.fillpath is None:
            raise RuntimeError("Path neither to be stroked nor filled")

        # now, draw additional elements of decoratedpath
        self.subcanvas.outputPS(file)

        # restore global styles
        if self.styles:
            canvas._grestore().outputPS(file)

    def outputPDF(self, file):
        # draw (stroke and/or fill) the decoratedpath on the canvas
        # while trying to produce an efficient output, e.g., by
        # not writing one path two times

        def _writestyles(styles, file=file):
            for style in styles:
                style.outputPDF(file)

        # apply global styles
        if self.styles:
            canvas._gsave().outputPDF(file)
            _writestyles(self.styles)

        if self.fillpath is not None:
            canvas._newpath().outputPDF(file)
            self.fillpath.outputPDF(file)

            if self.strokepath==self.fillpath:
                # do efficient stroking + filling
                canvas._gsave().outputPDF(file)

                if self.fillstyles:
                    _writestyles(self.fillstyles)

                canvas._fill().outputPDF(file)
                canvas._grestore().outputPDF(file)

                if self.strokestyles:
                    canvas._gsave().outputPDF(file)
                    _writestyles(self.strokestyles)

                canvas._stroke().outputPDF(file)

                if self.strokestyles:
                    canvas._grestore().outputPDF(file)
            else:
                # only fill fillpath - for the moment
                if self.fillstyles:
                    canvas._gsave().outputPDF(file)
                    _writestyles(self.fillstyles)

                canvas._fill().outputPDF(file)

                if self.fillstyles:
                    canvas._grestore().outputPDF(file)

        if self.strokepath is not None and self.strokepath!=self.fillpath:
            # this is the only relevant case still left
            # Note that a possible stroking has already been done.

            if self.strokestyles:
                canvas._gsave().outputPDF(file)
                _writestyles(self.strokestyles)

            canvas._newpath().outputPDF(file)
            self.strokepath.outputPDF(file)
            canvas._stroke().outputPDF(file)

            if self.strokestyles:
                canvas._grestore().outputPDF(file)

        if self.strokepath is None and self.fillpath is None:
            raise RuntimeError("Path neither to be stroked nor filled")

        # now, draw additional elements of decoratedpath
        self.subcanvas.outputPDF(file)

        # restore global styles
        if self.styles:
            canvas._grestore().outputPDF(file)

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
        tlen = anormpath.tangent(0).arclength_pt()
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
        self.attrs = attr.mergeattrs([style.linestyle.solid, stroked, filled] + attrs)
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
            anormpath.reverse()

        # set the new (shortened) strokepath
        dp.strokepath = anormpath

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


class wriggle(deco, attr.attr):

    def __init__(self, skipleft=1, skipright=1, radius=0.5, loops=8, curvesperloop=10):
        self.skipleft_str = skipleft
        self.skipright_str = skipright
        self.radius_str = radius
        self.loops = loops
        self.curvesperloop = curvesperloop

    def decorate(self, dp):
        # XXX: is this the correct way to select the basepath???!!!
        if isinstance(dp.strokepath, path.normpath):
            basepath = dp.strokepath
        elif dp.strokepath is not None:
            basepath = path.normpath(dp.strokepath)
        elif isinstance(dp.path, path.normpath):
            basepath = dp.path
        else:
            basepath = path.normpath(dp.path)

        skipleft = unit.topt(unit.length(self.skipleft_str, default_type="v"))
        skipright = unit.topt(unit.length(self.skipright_str, default_type="v"))
        startpar, endpar = basepath.lentopar(map(unit.t_pt, [skipleft, basepath.arclength_pt() - skipright]))
        radius = unit.topt(unit.length(self.radius_str))

        # search for the first intersection of a circle around start point x, y bigger than startpar
        x, y = basepath.at_pt(startpar)
        startcircpar = None
        for intersectpar in basepath.intersect(path.circle_pt(x, y, radius))[0]:
            if startpar < intersectpar and (startcircpar is None or startcircpar > intersectpar):
                startcircpar = intersectpar
        if startcircpar is None:
            raise RuntimeError("couldn't find wriggle start point")
        # calculate start position and angle
        xcenter, ycenter = basepath.at_pt(startcircpar)
        startpos = basepath.split([startcircpar])[0].arclength_pt()
        startangle = math.atan2(y-ycenter, x-xcenter)

        # find the last intersection of a circle around x, y smaller than endpar
        x, y = basepath.at_pt(endpar)
        endcircpar = None
        for intersectpar in basepath.intersect(path.circle_pt(x, y, radius))[0]:
            if endpar > intersectpar and (endcircpar is None or endcircpar < intersectpar):
                endcircpar = intersectpar
        if endcircpar is None:
            raise RuntimeError("couldn't find wriggle end point")
        # calculate end position and angle
        x2, y2 = basepath.at_pt(endcircpar)
        endpos = basepath.split([endcircpar])[0].arclength_pt()
        endangle = math.atan2(y-y2, x-x2)

        if endangle < startangle:
            endangle += 2*math.pi

        # calculate basepath points
        sections = self.loops * self.curvesperloop
        posrange = endpos - startpos
        poslist = [startpos + i*posrange/sections for i in range(sections+1)]
        parlist = basepath.lentopar(map(unit.t_pt, poslist))
        atlist = [basepath.at_pt(x) for x in parlist]

        # from pyx import color
        # for at in atlist:
        #     dp.subcanvas.stroke(path.circle_pt(at[0], at[1], 1), [color.rgb.blue])

        # calculate wriggle points and tangents
        anglerange = 2*math.pi*self.loops + endangle - startangle
        deltaangle = anglerange / sections
        tangentlength = radius * 4 * (1 - math.cos(deltaangle/2)) / (3 * math.sin(deltaangle/2))
        wriggleat = [None]*(sections+1)
        wriggletangentstart = [None]*(sections+1)
        wriggletangentend = [None]*(sections+1)
        for i in range(sections+1):
            x, y = atlist[i]
            angle = startangle + i*anglerange/sections
            dx, dy = math.cos(angle), math.sin(angle)
            wriggleat[i] = x + radius*dx, y + radius*dy
            # dp.subcanvas.stroke(path.line_pt(x, y, x + radius*dx, y + radius*dy), [color.rgb.blue])
            wriggletangentstart[i] = x + radius*dx + tangentlength*dy, y + radius*dy - tangentlength*dx
            wriggletangentend[i] = x + radius*dx - tangentlength*dy, y + radius*dy + tangentlength*dx

        # build wriggle path
        wrigglepath = basepath.split([startpar])[0]
        wrigglepath.append(path.multicurveto_pt([wriggletangentend[i-1] +
                                                 wriggletangentstart[i] +
                                                 wriggleat[i]
                                                 for i in range(1, sections+1)]))
        wrigglepath = wrigglepath.glue(basepath.split([endpar])[1]) # glue and glued?!?

        # store wriggle path
        dp.path = wrigglepath # otherwise the bbox is wrong!
        dp.strokepath = wrigglepath
        return dp


class curvecorners(deco, attr.attr):

    """bends corners in a path

    curvecorners replaces corners between two lines in a path by an optimized
    curve that has zero curvature at the connections to the lines.
    Corners between curves and lines are left as they are."""

    def __init__(self, radius=None, softness=1):
        self.radius = unit.topt(radius)
        self.softness = softness

    def controlpoints_pt(self, A, B, C, r1, r2, softness):
        # Takes three endpoints of two straight lines:
        # start A, connecting midpoint B, endpoint C
        # and two radii r1 and r2:
        # Returns the seven control points of the two bezier curves:
        #  - start d1
        #  - control points g1 and f1
        #  - midpoint e
        #  - control points f2 and g2
        #  - endpoint d2

        def normed(v):
            n = math.sqrt(v[0] * v[0] + v[1] * v[1])
            return v[0] / n, v[1] / n
        # make direction vectors d1: from B to A
        #                        d2: from B to C
        d1 = normed([A[i] - B[i] for i in [0,1]])
        d2 = normed([C[i] - B[i] for i in [0,1]])

        # 0.3192 has turned out to be the maximum softness available
        # for straight lines ;-)
        f = 0.3192 * softness
        g = (15.0 * f + math.sqrt(-15.0*f*f + 24.0*f))/12.0

        # make the control points
        f1 = [B[i] + f * r1 * d1[i] for i in [0,1]]
        f2 = [B[i] + f * r2 * d2[i] for i in [0,1]]
        g1 = [B[i] + g * r1 * d1[i] for i in [0,1]]
        g2 = [B[i] + g * r2 * d2[i] for i in [0,1]]
        d1 = [B[i] +     r1 * d1[i] for i in [0,1]]
        d2 = [B[i] +     r2 * d2[i] for i in [0,1]]
        e  = [0.5 * (f1[i] + f2[i]) for i in [0,1]]

        return [d1, g1, f1, e, f2, g2, d2]

    def decorate(self, dp):
        # XXX: is this the correct way to select the basepath???!!!
        # compare to wriggle()
        if isinstance(dp.strokepath, path.normpath):
            basepath = dp.strokepath
        elif dp.strokepath is not None:
            basepath = path.normpath(dp.strokepath)
        elif isinstance(dp.path, path.normpath):
            basepath = dp.path
        else:
            basepath = path.normpath(dp.path)

        newpath = path.path()
        for subpath in basepath.subpaths:
            newpels = []
            # it is not clear yet, where to moveto (e.g. with a closed subpath we
            # will get the starting point when inserting the bended corner)
            domoveto = subpath.begin_pt()
            dolineto = None

            # for a closed subpath we eventually have to bend the initial corner
            if subpath.closed:
                A = subpath.normpathels[-1].begin_pt()
                previsline = isinstance(subpath.normpathels[-1], path.normline)
            else:
                A = subpath.begin_pt()
                previsline = 0

            # go through the list of normpathels in this subpath
            for i in range(len(subpath.normpathels)):
                # XXX: at the moment, we have to build up a path, not a normpath
                # this should be changed later
                thispel = subpath.normpathels[i]
                prevpel = subpath.normpathels[i-1]
                # from this pel: B,C, thisstraight
                # from previus pel: A, prevstraight
                B, C = thispel.begin_pt(), thispel.end_pt()
                thisisline = isinstance(thispel, path.normline)
                if thisisline and previsline:
                    d1,g1,f1,e,f2,g2,d2 = self.controlpoints_pt(A,B,C, self.radius, self.radius, self.softness)
                    if domoveto is not None:
                        newpath.append(path.moveto_pt(d1[0],d1[1]))
                    if dolineto is not None:
                        newpath.append(path.lineto_pt(d1[0],d1[1]))
                    newpath.append(path.curveto_pt(*(g1 + f1 + e)))
                    newpath.append(path.curveto_pt(*(f2 + g2 + d2)))
                    dolineto = C
                else:
                    if domoveto is not None:
                        newpath.append(path.moveto_pt(*domoveto))
                    if dolineto is not None:
                        newpath.append(path.lineto_pt(*dolineto))
                    if isinstance(thispel, path.normcurve):
                        # convert the normcurve to a curveto
                        newpath.append(path.curveto_pt(thispel.x1,thispel.y1,thispel.x2,thispel.y2,thispel.x3,thispel.y3))
                        dolineto = None
                    elif isinstance (thispel, path.normline):
                        dolineto = C # just store something here which is not None

                domoveto = None
                previsline = thisisline
                A = B

            if dolineto is not None:
                newpath.append(path.lineto_pt(*dolineto))
            if subpath.closed:
                newpath.append(path.closepath())

        dp.path = newpath
        dp.strokepath = newpath
        return dp


