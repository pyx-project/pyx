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
import attr, base, canvas, color, helper, path, style, trafo, unit

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
            file.write("gsave\n")
            _writestyles(self.styles)

        if self.fillpath is not None:
            file.write("newpath\n")
            self.fillpath.outputPS(file)

            if self.strokepath==self.fillpath:
                # do efficient stroking + filling
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

        if self.strokepath is not None and self.strokepath!=self.fillpath:
            # this is the only relevant case still left
            # Note that a possible stroking has already been done.

            if self.strokestyles:
                file.write("gsave\n")
                _writestyles(self.strokestyles)

            file.write("newpath\n")
            self.strokepath.outputPS(file)
            file.write("stroke\n")

            if self.strokestyles:
                file.write("grestore\n")

        if self.strokepath is None and self.fillpath is None:
            raise RuntimeError("Path neither to be stroked nor filled")

        # now, draw additional elements of decoratedpath
        self.subcanvas.outputPS(file)

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

        # apply global styles
        if self.styles:
            file.write("q\n") # gsave
            _writestyles(self.styles)

        if self.fillpath is not None:
            self.fillpath.outputPDF(file)

            if self.strokepath==self.fillpath:
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

        if self.strokepath is not None and self.strokepath!=self.fillpath:
            # this is the only relevant case still left
            # Note that a possible stroking has already been done.

            if self.strokestyles:
                file.write("q\n") # gsave
                _writestrokestyles(self.strokestyles)

            self.strokepath.outputPDF(file)
            file.write("S\n") # stroke

            if self.strokestyles:
                file.write("Q\n") # grestore

        if self.strokepath is None and self.fillpath is None:
            raise RuntimeError("Path neither to be stroked nor filled")

        # now, draw additional elements of decoratedpath
        self.subcanvas.outputPDF(file)

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
        tvec = anormpath.tangent(0)
        tlen = tvec.arclen_pt()
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


_base = unit.v_pt(6)

class arrow(deco, attr.attr):

    """arrow is a decorator which adds an arrow to either side of the path"""

    def __init__(self, attrs=[], position=0, size=_base, angle=45, constriction=0.8):
        self.attrs = attr.mergeattrs([style.linestyle.solid, filled] + attrs)
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
        startpar, endpar = basepath.arclentoparam(map(unit.t_pt, [skipleft, basepath.arclen_pt() - skipright]))
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
        startpos = basepath.split([startcircpar])[0].arclen_pt()
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
        endpos = basepath.split([endcircpar])[0].arclen_pt()
        endangle = math.atan2(y-y2, x-x2)

        if endangle < startangle:
            endangle += 2*math.pi

        # calculate basepath points
        sections = self.loops * self.curvesperloop
        posrange = endpos - startpos
        poslist = [startpos + i*posrange/sections for i in range(sections+1)]
        parlist = basepath.arclentoparam(map(unit.t_pt, poslist))
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


class smoothed(deco, attr.attr):

    """Bends corners in a path.

    This decorator replaces corners in a path with bezier curves. There are two cases:
    - If the corner lies between two lines, _two_ bezier curves will be used
      that are highly optimized to look good (their curvature is to be zero at the ends
      and has to have zero derivative in the middle).
      Additionally, it can controlled by the softness-parameter.
    - If the corner lies between curves then _one_ bezier is used that is (except in some
      special cases) uniquely determined by the tangents and curvatures at its end-points.
      In some cases it is necessary to use only the absolute value of the curvature to avoid a
      cusp-shaped connection of the new bezier to the old path. In this case the use of
      "strict=0" allows the sign of the curvature to switch.
    - The radius argument gives the arclength-distance of the corner to the points where the
      old path is cut and the beziers are inserted.
    - Path elements that are too short (shorter than the radius) are skipped
    """

    def __init__(self, radius=None, softness=1, strict=0):
        self.radius = unit.length(radius, default_type="v")
        self.softness = softness
        self.strict = strict

    def _twobeziersbetweentolines(self, B, tangent1, tangent2, r1, r2, softness=1):
        # Takes the corner B
        # and two tangent vectors heading to and from B
        # and two radii r1 and r2:
        # All arguments must be in Points
        # Returns the seven control points of the two bezier curves:
        #  - start d1
        #  - control points g1 and f1
        #  - midpoint e
        #  - control points f2 and g2
        #  - endpoint d2

        # make direction vectors d1: from B to A
        #                        d2: from B to C
        d1 = -tangent1[0] / math.hypot(*tangent1), -tangent1[1] / math.hypot(*tangent1)
        d2 =  tangent2[0] / math.hypot(*tangent2),  tangent2[1] / math.hypot(*tangent2)

        # 0.3192 has turned out to be the maximum softness available
        # for straight lines ;-)
        f = 0.3192 * softness
        g = (15.0 * f + math.sqrt(-15.0*f*f + 24.0*f))/12.0

        # make the control points
        f1 = B[0] + f * r1 * d1[0], B[1] + f * r1 * d1[1]
        f2 = B[0] + f * r2 * d2[0], B[1] + f * r2 * d2[1]
        g1 = B[0] + g * r1 * d1[0], B[1] + g * r1 * d1[1]
        g2 = B[0] + g * r2 * d2[0], B[1] + g * r2 * d2[1]
        d1 = B[0] +     r1 * d1[0], B[1] +     r1 * d1[1]
        d2 = B[0] +     r2 * d2[0], B[1] +     r2 * d2[1]
        e  = 0.5 * (f1[0] + f2[0]), 0.5 * (f1[1] + f2[1])

        return [d1, g1, f1, e, f2, g2, d2]

    def _onebezierbetweentwopathels(self, A, B, tangentA, tangentB, curvA, curvB, strict=0):
        # connects points A and B with a bezier curve that has
        # prescribed tangents dirA, dirB and curvatures curA, curB.
        # If strict, the sign of the curvature will be forced which may invert
        # the sign of the tangents. If not strict, the sign of the curvature may
        # be switched but the tangent may not.

        def sign(x):
            try: return abs(a) / a
            except ZeroDivisionError: return 0

        # normalise the tangent vectors
        dirA = (tangentA[0] / math.hypot(*tangentA), tangentA[1] / math.hypot(*tangentA))
        dirB = (tangentB[0] / math.hypot(*tangentB), tangentB[1] / math.hypot(*tangentB))
        # some shortcuts
        T = dirA[0] * dirB[1] - dirA[1] * dirB[0]
        D = 3 * (dirA[0] * (B[1]-A[1]) - dirA[1] * (B[0]-A[0]))
        E = 3 * (dirB[0] * (B[1]-A[1]) - dirB[1] * (B[0]-A[0]))
        # the variables: \dot X(0) = a * dirA
        #                \dot X(1) = b * dirB
        a, b = None, None

        # ask for some special cases:
        # Newton iteration is likely to fail if T==0 or curvA,curvB==0
        if abs(T) < 1e-10:
            try:
                a = 2.0 * D / curvA
                a = math.sqrt(abs(a)) * sign(a)
                b = -2.0 * E / curvB
                b = math.sqrt(abs(b)) * sign(b)
            except ZeroDivisionError:
                sys.stderr.write("*** PyX Warning: The connecting bezier is not uniquely determined."
                    "The simple heuristic solution may not be optimal.")
                a = b = 1.5 * hypot(A[0] - B[0], A[1] - B[1])
        else:
            if abs(curvA) < 1.0e-4:
                b = D / T
                a = - (E + b*abs(b)*curvB*0.5) / T
            elif abs(curvB) < 1.0e-4:
                a = -E / T
                b = (D - a*abs(a)*curvA*0.5) / T
            else:
                a, b = None, None

        # do the general case: Newton iteration
        if a is None:
            # solve the coupled system
            #     0 = Ga(a,b) = 0.5 a |a| curvA + b * T - D
            #     0 = Gb(a,b) = 0.5 b |b| curvB + a * T + E
            # this system is equivalent to the geometric contraints:
            #     the curvature and the normal tangent vectors
            #     at parameters 0 and 1 are to be continuous
            # the system is solved by 2-dim Newton-Iteration
            # (a,b)^{i+1} = (a,b)^i - (DG)^{-1} (Ga(a^i,b^i), Gb(a^i,b^i))
            a = b = 0
            Ga = Gb = 1
            while max(abs(Ga),abs(Gb)) > 1.0e-5:
                detDG = abs(a*b) * curvA*curvB - T*T
                invDG = [[curvB*abs(b)/detDG, -T/detDG], [-T/detDG, curvA*abs(a)/detDG]]

                Ga = a*abs(a)*curvA*0.5 + b*T - D
                Gb = b*abs(b)*curvB*0.5 + a*T + E

                a, b = a - invDG[0][0]*Ga - invDG[0][1]*Gb, b - invDG[1][0]*Ga - invDG[1][1]*Gb

        # the curvature may change its sign if we would get a cusp
        # in the optimal case we have a>0 and b>0
        if not strict:
            a, b = abs(a), abs(b)

        return [A, (A[0] + a * dirA[0] / 3.0, A[1] + a * dirA[1] / 3.0),
                   (B[0] - b * dirB[0] / 3.0, B[1] - b * dirB[1] / 3.0), B]


    def decorate(self, dp):
        radius = unit.topt(self.radius)
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
        for normsubpath in basepath.subpaths:
            npels = normsubpath.normpathels
            arclens = [npel.arclen_pt() for npel in npels]

            # 1. Build up a list of all relevant normpathels
            #    and the lengths where they will be cut (length with respect to the normsubpath)
            npelnumbers = []
            cumalen = 0
            for no in range(len(arclens)):
                alen = arclens[no]
                # a first selection criterion for skipping too short normpathels
                # the rest will queeze the radius
                if alen > radius:
                    npelnumbers.append(no)
                else:
                    sys.stderr.write("*** PyX Warning: smoothed is skipping a normpathel that is too short\n")
                cumalen += alen
            # XXX: what happens, if 0 or -1 is skipped and path not closed?

            # 2. Find the parameters, points,
            #    and calculate tangents and curvatures
            params, tangents, curvatures, points = [], [], [], []
            for no in npelnumbers:
                npel = npels[no]
                alen = arclens[no]

                # find the parameter(s): either one or two
                if no is npelnumbers[0] and not normsubpath.closed:
                    pars = npel._arclentoparam_pt([max(0, alen - radius)])[0]
                elif alen > 2 * radius:
                    pars = npel._arclentoparam_pt([radius, alen - radius])[0]
                else:
                    pars = npel._arclentoparam_pt([0.5 * alen])[0]

                # find points, tangents and curvatures
                ts,cs,ps = [],[],[]
                for par in pars:
                    # XXX: there is no trafo method for normpathels?
                    thetrafo = normsubpath.trafo(par + no)
                    p = thetrafo._apply(0,0)
                    t = thetrafo._apply(1,0)
                    ps.append(p)
                    ts.append((t[0]-p[0], t[1]-p[1]))
                    c = npel.curvradius_pt(par)
                    if c is None: cs.append(0)
                    else: cs.append(1.0/c)
                    #dp.subcanvas.stroke(path.circle_pt(p[0], p[1], 3), [color.grey.black, style.linewidth.THin])
                    #dp.subcanvas.stroke(path.line_pt(p[0], p[1], p[0] + 10*(t[0]-p[0]), p[1] + 10*(t[1]-p[1])), [color.grey.black, earrow.small, style.linewidth.THin])

                params.append(pars)
                points.append(ps)
                tangents.append(ts)
                curvatures.append(cs)

            do_moveto = 1 # we do not know yet where to moveto
            # 3. First part of extra handling of closed paths
            if not normsubpath.closed:
                bpart = npels[npelnumbers[0]].split(params[0])[0]
                if do_moveto:
                    newpath.append(path.moveto_pt(*bpart.begin_pt()))
                    do_moveto = 0
                if isinstance(bpart, path.normline):
                    newpath.append(path.lineto_pt(*bpart.end_pt()))
                elif isinstance(bpart, path.normcurve):
                    newpath.append(path.curveto_pt(bpart.x1, bpart.y1, bpart.x2, bpart.y2, bpart.x3, bpart.y3))
                do_moveto = 0

            # 4. Do the splitting for the first to the last element,
            #    a closed path must be closed later
            for i in range(len(npelnumbers)-1+(normsubpath.closed==1)):
                this = npelnumbers[i]
                next = npelnumbers[(i+1) % len(npelnumbers)]
                thisnpel, nextnpel = npels[this], npels[next]

                # split thisnpel apart and take the middle peace
                if len(points[this]) == 2:
                    mpart = thisnpel.split(params[this])[1]
                    if do_moveto:
                        newpath.append(path.moveto_pt(*mpart.begin_pt()))
                        do_moveto = 0
                    if isinstance(mpart, path.normline):
                        newpath.append(path.lineto_pt(*mpart.end_pt()))
                    elif isinstance(mpart, path.normcurve):
                        newpath.append(path.curveto_pt(mpart.x1, mpart.y1, mpart.x2, mpart.y2, mpart.x3, mpart.y3))

                # add the curve(s) replacing the corner
                if isinstance(thisnpel, path.normline) and isinstance(nextnpel, path.normline) \
                   and (next-this == 1 or (this==0 and next==len(npels)-1)):
                    d1,g1,f1,e,f2,g2,d2 = self._twobeziersbetweentolines(
                        thisnpel.end_pt(), tangents[this][-1], tangents[next][0],
                        math.hypot(points[this][-1][0] - thisnpel.end_pt()[0], points[this][-1][1] - thisnpel.end_pt()[1]),
                        math.hypot(points[next][0][0] - nextnpel.begin_pt()[0], points[next][0][1] - nextnpel.begin_pt()[1]),
                        softness=self.softness)
                    if do_moveto:
                        newpath.append(path.moveto_pt(*d1))
                        do_moveto = 0
                    newpath.append(path.curveto_pt(*(g1 + f1 + e)))
                    newpath.append(path.curveto_pt(*(f2 + g2 + d2)))
                else:
                    #dp.subcanvas.fill(path.circle_pt(points[next][0][0], points[next][0][1], 2))
                    if not self.strict:
                        # the curvature may have the wrong sign -- produce a heuristic for the sign:
                        vx, vy = thisnpel.end_pt()[0] - points[this][-1][0], thisnpel.end_pt()[1] - points[this][-1][1]
                        wx, wy = points[next][0][0] - thisnpel.end_pt()[0], points[next][0][1] - thisnpel.end_pt()[1]
                        sign = vx * wy - vy * wx
                        sign = sign / abs(sign)
                        curvatures[this][-1] = sign * abs(curvatures[this][-1])
                        curvatures[next][0] = sign * abs(curvatures[next][0])
                    A,B,C,D = self._onebezierbetweentwopathels(
                        points[this][-1], points[next][0], tangents[this][-1], tangents[next][0],
                        curvatures[this][-1], curvatures[next][0], strict=self.strict)
                    if do_moveto:
                        newpath.append(path.moveto_pt(*A))
                        do_moveto = 0
                    newpath.append(path.curveto_pt(*(B + C + D)))

            # 5. Second part of extra handling of closed paths
            if normsubpath.closed:
                if do_moveto:
                    newpath.append(path.moveto_pt(*dp.strokepath.begin()))
                    sys.stderr.write("*** PyXWarning: The whole path has been smoothed away -- sorry\n")
                newpath.append(path.closepath())
            else:
                epart = npels[npelnumbers[-1]].split([params[-1][0]])[-1]
                if do_moveto:
                    newpath.append(path.moveto_pt(*epart.begin_pt()))
                    do_moveto = 0
                if isinstance(epart, path.normline):
                    newpath.append(path.lineto_pt(*epart.end_pt()))
                elif isinstance(epart, path.normcurve):
                    newpath.append(path.curveto_pt(epart.x1, epart.y1, epart.x2, epart.y2, epart.x3, epart.y3))

        dp.strokepath = newpath
        return dp

smoothed.clear = attr.clearclass(smoothed)

_base = 1
smoothed.SHARP = smoothed(radius="%f cm" % (_base/math.sqrt(64)))
smoothed.SHARp = smoothed(radius="%f cm" % (_base/math.sqrt(32)))
smoothed.SHArp = smoothed(radius="%f cm" % (_base/math.sqrt(16)))
smoothed.SHarp = smoothed(radius="%f cm" % (_base/math.sqrt(8)))
smoothed.Sharp = smoothed(radius="%f cm" % (_base/math.sqrt(4)))
smoothed.sharp = smoothed(radius="%f cm" % (_base/math.sqrt(2)))
smoothed.normal = smoothed(radius="%f cm" % (_base))
smoothed.round = smoothed(radius="%f cm" % (_base*math.sqrt(2)))
smoothed.Round = smoothed(radius="%f cm" % (_base*math.sqrt(4)))
smoothed.ROund = smoothed(radius="%f cm" % (_base*math.sqrt(8)))
smoothed.ROUnd = smoothed(radius="%f cm" % (_base*math.sqrt(16)))
smoothed.ROUNd = smoothed(radius="%f cm" % (_base*math.sqrt(32)))
smoothed.ROUND = smoothed(radius="%f cm" % (_base*math.sqrt(64)))

