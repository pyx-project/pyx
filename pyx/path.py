#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2002-2005 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2003-2004 Michael Schindler <m-schindler@users.sourceforge.net>
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

#       - exceptions: nocurrentpoint, paramrange
#       - correct bbox for curveto and normcurve
#         (maybe we still need the current bbox implementation (then maybe called
#          cbox = control box) for normcurve for the use during the
#          intersection of bpaths)

from __future__ import nested_scopes

import math, bisect
from math import cos, sin, pi
try:
    from math import radians, degrees
except ImportError:
    # fallback implementation for Python 2.1
    def radians(x): return x*pi/180
    def degrees(x): return x*180/pi
import base, bbox, trafo, unit, helper

try:
    sum([])
except NameError:
    # fallback implementation for Python 2.2 and below
    def sum(list):
        return reduce(lambda x, y: x+y, list, 0)

try:
    enumerate([])
except NameError:
    # fallback implementation for Python 2.2 and below
    def enumerate(list):
        return zip(xrange(len(list)), list)

# use new style classes when possible
__metaclass__ = type

################################################################################

# global epsilon (default precision of normsubpaths)
_epsilon = 1e-5

def set(epsilon=None):
    global _epsilon
    if epsilon is not None:
        _epsilon = epsilon

################################################################################
# Bezier helper functions
################################################################################

def _arctobcurve(x_pt, y_pt, r_pt, phi1, phi2):
    """generate the best bezier curve corresponding to an arc segment"""

    dphi = phi2-phi1

    if dphi==0: return None

    # the two endpoints should be clear 
    x0_pt, y0_pt = x_pt+r_pt*cos(phi1), y_pt+r_pt*sin(phi1)
    x3_pt, y3_pt = x_pt+r_pt*cos(phi2), y_pt+r_pt*sin(phi2)

    # optimal relative distance along tangent for second and third
    # control point
    l = r_pt*4*(1-cos(dphi/2))/(3*sin(dphi/2))

    x1_pt, y1_pt = x0_pt-l*sin(phi1), y0_pt+l*cos(phi1)
    x2_pt, y2_pt = x3_pt+l*sin(phi2), y3_pt-l*cos(phi2)

    return normcurve_pt(x0_pt, y0_pt, x1_pt, y1_pt, x2_pt, y2_pt, x3_pt, y3_pt)


def _arctobezierpath(x_pt, y_pt, r_pt, phi1, phi2, dphimax=45):
    apath = []

    phi1 = radians(phi1)
    phi2 = radians(phi2)
    dphimax = radians(dphimax)

    if phi2<phi1:
        # guarantee that phi2>phi1 ...
        phi2 = phi2 + (math.floor((phi1-phi2)/(2*pi))+1)*2*pi
    elif phi2>phi1+2*pi:
        # ... or remove unnecessary multiples of 2*pi
        phi2 = phi2 - (math.floor((phi2-phi1)/(2*pi))-1)*2*pi

    if r_pt == 0 or phi1-phi2 == 0: return []

    subdivisions = abs(int((1.0*(phi1-phi2))/dphimax))+1

    dphi = (1.0*(phi2-phi1))/subdivisions

    for i in range(subdivisions):
        apath.append(_arctobcurve(x_pt, y_pt, r_pt, phi1+i*dphi, phi1+(i+1)*dphi))

    return apath

#
# we define one exception
#

class PathException(Exception): pass

################################################################################
# _pathcontext: context during walk along path
################################################################################

class _invalidcontextclass:

    def invalid1(self):
        raise PathException("invalid path context (path must start with moveto or the like)")
    __str__ = __repr__ = __neg__ = invalid1

    def invalid2(self, other):
        self.invalid1()
    __cmp__ = __add__ = __iadd__ = __sub__ = __isub__ = __mul__ = __imul__ = __div__ = __idiv__ = invalid2

_invalidcontext = _invalidcontextclass()


class _pathcontext:

    """context during walk along path"""

    __slots__ = "x_pt", "y_pt"


    def __init__(self, x_pt=_invalidcontext, y_pt=_invalidcontext):
        """initialize context

        By default the context is marked invalid.
        """
        self.x_pt = x_pt
        self.y_pt = y_pt

    def invalidate(self):
        """mark context invalid"""
        self.x_pt = _invalidcontext

    def valid(self):
        """checks whether the context is invalid"""
        return self.x_pt is not _invalidcontext


################################################################################ 
# pathitem: element of a PS style path 
################################################################################

class pathitem(base.canvasitem):

    """element of a PS style path"""

    def _updatecontext(self, context):
        """update context of during walk along pathitem

        changes context in place
        """
        raise NotImplementedError()


    def _bbox(self, context):
        """calculate bounding box of pathitem

        context: context of pathitem

        returns bounding box of pathitem (in given context)

        Important note: all coordinates in bbox, currentpoint, and
        currrentsubpath are measured in pts
        """
        raise NotImplementedError()

    def _normalized(self, context):
        """returns list of normalized version of pathitem

        context: context of pathitem

        Returns the path converted into a list of normline or normcurve
        instances. Additionally instances of moveto_pt and closepath are
        contained, which act as markers.
        """
        raise NotImplementedError()

    def outputPS(self, file):
        """write PS code corresponding to pathitem to file"""
        raise NotImplementedError()

    def outputPDF(self, file):
        """write PDF code corresponding to pathitem to file

        Since PDF is limited to lines and curves, _normalized is used to
        generate PDF outout. Thus only moveto_pt and closepath need to
        implement the outputPDF method."""
        raise NotImplementedError()


# various pathitems
#
# Each one comes in two variants:
#  - one with suffix _pt. This one requires the coordinates
#    to be already in pts (mainly used for internal purposes)
#  - another which accepts arbitrary units


class closepath(pathitem): 

    """Connect subpath back to its starting point"""

    __slots__ = ()

    def __str__(self):
        return "closepath"

    def _updatecontext(self, context):
        if not context.valid():
            raise PathException("closepath on an empty path")
        context.invalidate()

    def _bbox(self, context):
        # we do not want to keep the currentsubpath ... and this should work well
        return None

        # x0_pt, y0_pt = context.currentpoint
        # x1_pt, y1_pt = context.currentsubpath

        # return bbox.bbox_pt(min(x0_pt, x1_pt), min(y0_pt, y1_pt), 
        #                     max(x0_pt, x1_pt), max(y0_pt, y1_pt))

    def _normalized(self, context):
        return [self]

    def outputPS(self, file):
        file.write("closepath\n")

    def outputPDF(self, file):
        file.write("h\n")


class moveto_pt(pathitem):

    """Set current point to (x_pt, y_pt) (coordinates in pts)"""

    __slots__ = "x_pt", "y_pt"

    def __init__(self, x_pt, y_pt):
        self.x_pt = x_pt
        self.y_pt = y_pt

    def __str__(self):
        return "%g %g moveto" % (self.x_pt, self.y_pt)

    def _updatecontext(self, context):
        context.x_pt = self.x_pt
        context.y_pt = self.y_pt

    def _bbox(self, context):
        return None

    def _normalized(self, context):
        return [moveto_pt(self.x_pt, self.y_pt)]

    def outputPS(self, file):
        file.write("%g %g moveto\n" % (self.x_pt, self.y_pt) )

    def outputPDF(self, file):
        file.write("%f %f m\n" % (self.x_pt, self.y_pt) )


class lineto_pt(pathitem):

    """Append straight line to (x_pt, y_pt) (coordinates in pts)"""

    __slots__ = "x_pt", "y_pt"

    def __init__(self, x_pt, y_pt):
        self.x_pt = x_pt
        self.y_pt = y_pt

    def __str__(self):
        return "%g %g lineto" % (self.x_pt, self.y_pt)

    def _updatecontext(self, context):
        context.x_pt = self.x_pt
        context.y_pt = self.y_pt

    def _bbox(self, context):
        return bbox.bbox_pt(min(context.x_pt, self.x_pt),
                            min(context.y_pt, self.y_pt), 
                            max(context.x_pt, self.x_pt),
                            max(context.y_pt, self.y_pt))

    def _normalized(self, context):
        return [normline_pt(context.x_pt, context.y_pt, self.x_pt, self.y_pt)]

    def outputPS(self, file):
        file.write("%g %g lineto\n" % (self.x_pt, self.y_pt) )


class curveto_pt(pathitem):

    """Append curveto (coordinates in pts)"""

    __slots__ = "x1_pt", "y1_pt", "x2_pt", "y2_pt", "x3_pt", "y3_pt"

    def __init__(self, x1_pt, y1_pt, x2_pt, y2_pt, x3_pt, y3_pt):
        self.x1_pt = x1_pt
        self.y1_pt = y1_pt
        self.x2_pt = x2_pt
        self.y2_pt = y2_pt
        self.x3_pt = x3_pt
        self.y3_pt = y3_pt

    def __str__(self):
        return "%g %g %g %g %g %g curveto" % (self.x1_pt, self.y1_pt,
                                              self.x2_pt, self.y2_pt,
                                              self.x3_pt, self.y3_pt)

    def _updatecontext(self, context):
        context.x_pt = self.x3_pt
        context.y_pt = self.y3_pt

    def _bbox(self, context):
        return bbox.bbox_pt(min(context.x_pt, self.x1_pt, self.x2_pt, self.x3_pt),
                            min(context.y_pt, self.y1_pt, self.y2_pt, self.y3_pt),
                            max(context.x_pt, self.x1_pt, self.x2_pt, self.x3_pt),
                            max(context.y_pt, self.y1_pt, self.y2_pt, self.y3_pt))

    def _normalized(self, context):
        return [normcurve_pt(context.x_pt, context.y_pt,
                             self.x1_pt, self.y1_pt,
                             self.x2_pt, self.y2_pt,
                             self.x3_pt, self.y3_pt)]

    def outputPS(self, file):
        file.write("%g %g %g %g %g %g curveto\n" % ( self.x1_pt, self.y1_pt,
                                                     self.x2_pt, self.y2_pt,
                                                     self.x3_pt, self.y3_pt ) )


class rmoveto_pt(pathitem):

    """Perform relative moveto (coordinates in pts)"""

    __slots__ = "dx_pt", "dy_pt"

    def __init__(self, dx_pt, dy_pt):
         self.dx_pt = dx_pt
         self.dy_pt = dy_pt

    def _updatecontext(self, context):
        context.x_pt += self.dx_pt
        context.y_pt += self.dy_pt

    def _bbox(self, context):
        return None

    def _normalized(self, context):
        return [moveto_pt(context.x_pt + self.dx_pt, context.y_pt + self.dy_pt)]

    def outputPS(self, file):
        file.write("%g %g rmoveto\n" % (self.dx_pt, self.dy_pt) )


class rlineto_pt(pathitem):

    """Perform relative lineto (coordinates in pts)"""

    __slots__ = "dx_pt", "dy_pt"

    def __init__(self, dx_pt, dy_pt):
        self.dx_pt = dx_pt
        self.dy_pt = dy_pt

    def _updatecontext(self, context):
        context.x_pt += self.dx_pt
        context.y_pt += self.dy_pt

    def _bbox(self, context):
        x_pt = context.x_pt + self.dx_pt
        y_pt = context.y_pt + self.dy_pt
        return bbox.bbox_pt(min(context.x_pt, x_pt),
                            min(context.y_pt, y_pt),
                            max(context.x_pt, x_pt),
                            max(context.y_pt, y_pt))

    def _normalized(self, context):
        return [normline_pt(context.x_pt, context.y_pt,
                            context.x_pt + self.dx_pt, context.y_pt + self.dy_pt)]

    def outputPS(self, file):
        file.write("%g %g rlineto\n" % (self.dx_pt, self.dy_pt) )


class rcurveto_pt(pathitem):

    """Append rcurveto (coordinates in pts)"""

    __slots__ = "dx1_pt", "dy1_pt", "dx2_pt", "dy2_pt", "dx3_pt", "dy3_pt"

    def __init__(self, dx1_pt, dy1_pt, dx2_pt, dy2_pt, dx3_pt, dy3_pt):
        self.dx1_pt = dx1_pt
        self.dy1_pt = dy1_pt
        self.dx2_pt = dx2_pt
        self.dy2_pt = dy2_pt
        self.dx3_pt = dx3_pt
        self.dy3_pt = dy3_pt

    def outputPS(self, file):
        file.write("%g %g %g %g %g %g rcurveto\n" % ( self.dx1_pt, self.dy1_pt,
                                                      self.dx2_pt, self.dy2_pt,
                                                      self.dx3_pt, self.dy3_pt ) )

    def _updatecontext(self, context):
        context.x_pt += self.dx3_pt
        context.y_pt += self.dy3_pt

    def _bbox(self, context):
        x1_pt = context.x_pt + self.dx1_pt
        y1_pt = context.y_pt + self.dy1_pt
        x2_pt = context.x_pt + self.dx2_pt
        y2_pt = context.y_pt + self.dy2_pt
        x3_pt = context.x_pt + self.dx3_pt
        y3_pt = context.y_pt + self.dy3_pt
        return bbox.bbox_pt(min(context.x_pt, x1_pt, x2_pt, x3_pt),
                            min(context.y_pt, y1_pt, y2_pt, y3_pt),
                            max(context.x_pt, x1_pt, x2_pt, x3_pt),
                            max(context.y_pt, y1_pt, y2_pt, y3_pt))

    def _normalized(self, context):
        return [normcurve_pt(context.x_pt, context.y_pt,
                             context.x_pt + self.dx1_pt, context.y_pt + self.dy1_pt,
                             context.x_pt + self.dx2_pt, context.y_pt + self.dy2_pt,
                             context.x_pt + self.dx3_pt, context.y_pt + self.dy3_pt)]


class arc_pt(pathitem):

    """Append counterclockwise arc (coordinates in pts)"""

    __slots__ = "x_pt", "y_pt", "r_pt", "angle1", "angle2"

    def __init__(self, x_pt, y_pt, r_pt, angle1, angle2):
        self.x_pt = x_pt
        self.y_pt = y_pt
        self.r_pt = r_pt
        self.angle1 = angle1
        self.angle2 = angle2

    def _sarc(self):
        """Return starting point of arc segment"""
        return (self.x_pt+self.r_pt*cos(radians(self.angle1)),
                self.y_pt+self.r_pt*sin(radians(self.angle1)))

    def _earc(self):
        """Return end point of arc segment"""
        return (self.x_pt+self.r_pt*cos(radians(self.angle2)),
                self.y_pt+self.r_pt*sin(radians(self.angle2)))

    def _updatecontext(self, context):
        context.x_pt, context.y_pt = self._earc()

    def _bbox(self, context):
        phi1 = radians(self.angle1)
        phi2 = radians(self.angle2)

        # starting end end point of arc segment
        sarcx_pt, sarcy_pt = self._sarc()
        earcx_pt, earcy_pt = self._earc()

        # Now, we have to determine the corners of the bbox for the
        # arc segment, i.e. global maxima/mimima of cos(phi) and sin(phi)
        # in the interval [phi1, phi2]. These can either be located
        # on the borders of this interval or in the interior.

        if phi2 < phi1:
            # guarantee that phi2>phi1
            phi2 = phi2 + (math.floor((phi1-phi2)/(2*pi))+1)*2*pi

        # next minimum of cos(phi) looking from phi1 in counterclockwise
        # direction: 2*pi*floor((phi1-pi)/(2*pi)) + 3*pi

        if phi2 < (2*math.floor((phi1-pi)/(2*pi))+3)*pi:
            minarcx_pt = min(sarcx_pt, earcx_pt)
        else:
            minarcx_pt = self.x_pt-self.r_pt

        # next minimum of sin(phi) looking from phi1 in counterclockwise
        # direction: 2*pi*floor((phi1-3*pi/2)/(2*pi)) + 7/2*pi

        if phi2 < (2*math.floor((phi1-3.0*pi/2)/(2*pi))+7.0/2)*pi:
            minarcy_pt = min(sarcy_pt, earcy_pt)
        else:
            minarcy_pt = self.y_pt-self.r_pt

        # next maximum of cos(phi) looking from phi1 in counterclockwise 
        # direction: 2*pi*floor((phi1)/(2*pi))+2*pi

        if phi2 < (2*math.floor((phi1)/(2*pi))+2)*pi:
            maxarcx_pt = max(sarcx_pt, earcx_pt)
        else:
            maxarcx_pt = self.x_pt+self.r_pt

        # next maximum of sin(phi) looking from phi1 in counterclockwise 
        # direction: 2*pi*floor((phi1-pi/2)/(2*pi)) + 1/2*pi

        if phi2 < (2*math.floor((phi1-pi/2)/(2*pi))+5.0/2)*pi:
            maxarcy_pt = max(sarcy_pt, earcy_pt)
        else:
            maxarcy_pt = self.y_pt+self.r_pt

        # Finally, we are able to construct the bbox for the arc segment.
        # Note that if we are in a valid context, we also
        # have to include the straight line from this point
        # to the first point of the arc segment.

        if context.valid():
            return (bbox.bbox_pt(min(context.x_pt, sarcx_pt),
                                 min(context.y_pt, sarcy_pt),
                                 max(context.x_pt, sarcx_pt),
                                 max(context.y_pt, sarcy_pt)) +
                    bbox.bbox_pt(minarcx_pt, minarcy_pt, maxarcx_pt, maxarcy_pt) )
        else:
            return  bbox.bbox_pt(minarcx_pt, minarcy_pt, maxarcx_pt, maxarcy_pt)

    def _normalized(self, context):
        # get starting and end point of arc segment and bpath corresponding to arc
        sarcx_pt, sarcy_pt = self._sarc()
        earcx_pt, earcy_pt = self._earc()
        barc = _arctobezierpath(self.x_pt, self.y_pt, self.r_pt, self.angle1, self.angle2)

        # convert to list of curvetos omitting movetos
        nbarc = []

        for bpathitem in barc:
            nbarc.append(normcurve_pt(bpathitem.x0_pt, bpathitem.y0_pt,
                                      bpathitem.x1_pt, bpathitem.y1_pt,
                                      bpathitem.x2_pt, bpathitem.y2_pt,
                                      bpathitem.x3_pt, bpathitem.y3_pt))

        # Note that if we are in a valid context, we also
        # have to include the straight line from this point
        # to the first point of the arc segment.
        # Otherwise, we have to add a moveto at the beginning.

        if context.valid():
            return [normline_pt(context.x_pt, context.y_pt, sarcx_pt, sarcy_pt)] + nbarc
        else:
            return [moveto_pt(sarcx_pt, sarcy_pt)] + nbarc

    def outputPS(self, file):
        file.write("%g %g %g %g %g arc\n" % ( self.x_pt, self.y_pt,
                                              self.r_pt,
                                              self.angle1,
                                              self.angle2 ) )


class arcn_pt(pathitem):

    """Append clockwise arc (coordinates in pts)"""

    __slots__ = "x_pt", "y_pt", "r_pt", "angle1", "angle2"

    def __init__(self, x_pt, y_pt, r_pt, angle1, angle2):
        self.x_pt = x_pt
        self.y_pt = y_pt
        self.r_pt = r_pt
        self.angle1 = angle1
        self.angle2 = angle2

    def _sarc(self):
        """Return starting point of arc segment"""
        return (self.x_pt+self.r_pt*cos(radians(self.angle1)),
                self.y_pt+self.r_pt*sin(radians(self.angle1)))

    def _earc(self):
        """Return end point of arc segment"""
        return (self.x_pt+self.r_pt*cos(radians(self.angle2)),
                self.y_pt+self.r_pt*sin(radians(self.angle2)))

    def _updatecontext(self, context):
        context.x_pt, context.y_pt = self._earc()

    def _bbox(self, context):
        # in principle, we obtain bbox of an arcn element from 
        # the bounding box of the corrsponding arc element with
        # angle1 and angle2 interchanged. Though, we have to be carefull
        # with the straight line segment, which is added if we are in a
        # valid context.

        # Hence, we first compute the bbox of the arc without this line:

        a = arc_pt(self.x_pt, self.y_pt, self.r_pt, 
                   self.angle2, 
                   self.angle1)

        sarcx_pt, sarcy_pt = self._sarc()
        arcbb = a._bbox(_pathcontext())

        # Then, we repeat the logic from arc.bbox, but with interchanged
        # start and end points of the arc
        # XXX: I found the code to be equal! (AW, 31.1.2005)

        if context.valid():
            return  bbox.bbox_pt(min(context.x_pt, sarcx_pt),
                                 min(context.y_pt, sarcy_pt),
                                 max(context.x_pt, sarcx_pt),
                                 max(context.y_pt, sarcy_pt)) + arcbb
        else:
            return arcbb

    def _normalized(self, context):
        # get starting and end point of arc segment and bpath corresponding to arc
        sarcx_pt, sarcy_pt = self._sarc()
        earcx_pt, earcy_pt = self._earc()
        barc = _arctobezierpath(self.x_pt, self.y_pt, self.r_pt, self.angle2, self.angle1)
        barc.reverse()

        # convert to list of curvetos omitting movetos
        nbarc = []

        for bpathitem in barc:
            nbarc.append(normcurve_pt(bpathitem.x3_pt, bpathitem.y3_pt,
                                      bpathitem.x2_pt, bpathitem.y2_pt,
                                      bpathitem.x1_pt, bpathitem.y1_pt,
                                      bpathitem.x0_pt, bpathitem.y0_pt))

        # Note that if we are in a valid context, we also
        # have to include the straight line from this point
        # to the first point of the arc segment.
        # Otherwise, we have to add a moveto at the beginning.

        if context.valid():
            return [normline_pt(context.x_pt, context.y_pt, sarcx_pt, sarcy_pt)] + nbarc
        else:
            return [moveto_pt(sarcx_pt, sarcy_pt)] + nbarc


    def outputPS(self, file):
        file.write("%g %g %g %g %g arcn\n" % ( self.x_pt, self.y_pt,
                                               self.r_pt,
                                               self.angle1,
                                               self.angle2 ) )


class arct_pt(pathitem):

    """Append tangent arc (coordinates in pts)"""

    __slots__ = "x1_pt", "y1_pt", "x2_pt", "y2_pt", "r_pt"

    def __init__(self, x1_pt, y1_pt, x2_pt, y2_pt, r_pt):
        self.x1_pt = x1_pt
        self.y1_pt = y1_pt
        self.x2_pt = x2_pt
        self.y2_pt = y2_pt
        self.r_pt = r_pt

    def _path(self, context):
        """returns the path consisting of arc and/or line which corresponds
        to arct

        this is a helper routine for _bbox and _normalized, which both need
        this path. Note: we don't want to calculate the bbox from a bpath
        """

        # direction and length of tangent 1
        dx1_pt = context.x_pt-self.x1_pt
        dy1_pt = context.y_pt-self.y1_pt
        l1 = math.hypot(dx1_pt, dy1_pt)

        # direction and length of tangent 2
        dx2_pt = self.x2_pt-self.x1_pt
        dy2_pt = self.y2_pt-self.y1_pt
        l2 = math.hypot(dx2_pt, dy2_pt)

        # intersection angle between two tangents
        alpha = math.acos((dx1_pt*dx2_pt+dy1_pt*dy2_pt)/(l1*l2))

        if math.fabs(sin(alpha)) >= 1e-15 and 1.0+self.r_pt != 1.0:
            cotalpha2 = 1.0/math.tan(alpha/2)

            # two tangent points
            xt1_pt = self.x1_pt + dx1_pt*self.r_pt*cotalpha2/l1
            yt1_pt = self.y1_pt + dy1_pt*self.r_pt*cotalpha2/l1
            xt2_pt = self.x1_pt + dx2_pt*self.r_pt*cotalpha2/l2
            yt2_pt = self.y1_pt + dy2_pt*self.r_pt*cotalpha2/l2

            # direction of center of arc 
            rx_pt = self.x1_pt - 0.5*(xt1_pt+xt2_pt)
            ry_pt = self.y1_pt - 0.5*(yt1_pt+yt2_pt)
            lr = math.hypot(rx_pt, ry_pt)

            # angle around which arc is centered
            if rx_pt >= 0:
                phi = degrees(math.atan2(ry_pt, rx_pt))
            else:
                # XXX why is rx_pt/ry_pt and not ry_pt/rx_pt used??? 
                phi = degrees(math.atan(rx_pt/ry_pt))+180

            # half angular width of arc 
            deltaphi = 90*(1-alpha/pi)

            # center position of arc
            mx_pt = self.x1_pt - rx_pt*self.r_pt/(lr*sin(alpha/2))
            my_pt = self.y1_pt - ry_pt*self.r_pt/(lr*sin(alpha/2))

            # now we are in the position to construct the path
            p = path(moveto_pt(context.x_pt, context.y_pt))

            if phi<0:
                p.append(arc_pt(mx_pt, my_pt, self.r_pt, phi-deltaphi, phi+deltaphi))
            else:
                p.append(arcn_pt(mx_pt, my_pt, self.r_pt, phi+deltaphi, phi-deltaphi))

            return p

        else:
            # we need no arc, so just return a straight line from context to x1_pt, y1_pt
            return line_pt(context.x_pt, context.y_pt, self.x1_pt, self.y1_pt)

    def _updatecontext(self, context):
        self._path(context)[-1]._updatecontext(context)

    def _bbox(self, context):
        return self._path(context).bbox()

    def _normalized(self, context):
        # XXX TODO NOTE
        return self._path(context).normpath().normsubpaths[0].normsubpathitems

    def outputPS(self, file):
        file.write("%g %g %g %g %g arct\n" % ( self.x1_pt, self.y1_pt,
                                               self.x2_pt, self.y2_pt,
                                               self.r_pt ) )

#
# now the pathitems that convert from user coordinates to pts
#

class moveto(moveto_pt):

    """Set current point to (x, y)"""

    __slots__ = "x_pt", "y_pt"

    def __init__(self, x, y):
        moveto_pt.__init__(self, unit.topt(x), unit.topt(y))


class lineto(lineto_pt):

    """Append straight line to (x, y)"""

    __slots__ = "x_pt", "y_pt"

    def __init__(self, x, y):
        lineto_pt.__init__(self, unit.topt(x), unit.topt(y))

        
class curveto(curveto_pt):

    """Append curveto"""

    __slots__ = "x1_pt", "y1_pt", "x2_pt", "y2_pt", "x3_pt", "y3_pt"

    def __init__(self, x1, y1, x2, y2, x3, y3):
        curveto_pt.__init__(self,
                            unit.topt(x1), unit.topt(y1),
                            unit.topt(x2), unit.topt(y2),
                            unit.topt(x3), unit.topt(y3))

class rmoveto(rmoveto_pt):

    """Perform relative moveto"""

    __slots__ = "dx_pt", "dy_pt"

    def __init__(self, dx, dy):
        rmoveto_pt.__init__(self, unit.topt(dx), unit.topt(dy))


class rlineto(rlineto_pt):

    """Perform relative lineto"""

    __slots__ = "dx_pt", "dy_pt"

    def __init__(self, dx, dy):
        rlineto_pt.__init__(self, unit.topt(dx), unit.topt(dy))


class rcurveto(rcurveto_pt):

    """Append rcurveto"""

    __slots__ = "dx1_pt", "dy1_pt", "dx2_pt", "dy2_pt", "dx3_pt", "dy3_pt"

    def __init__(self, dx1, dy1, dx2, dy2, dx3, dy3):
        rcurveto_pt.__init__(self,
                             unit.topt(dx1), unit.topt(dy1),
                             unit.topt(dx2), unit.topt(dy2),
                             unit.topt(dx3), unit.topt(dy3))


class arcn(arcn_pt):

    """Append clockwise arc"""

    __slots__ = "x_pt", "y_pt", "r_pt", "angle1", "angle2"

    def __init__(self, x, y, r, angle1, angle2):
        arcn_pt.__init__(self, unit.topt(x), unit.topt(y), unit.topt(r), angle1, angle2)


class arc(arc_pt):

    """Append counterclockwise arc"""

    __slots__ = "x_pt", "y_pt", "r_pt", "angle1", "angle2"

    def __init__(self, x, y, r, angle1, angle2):
        arc_pt.__init__(self, unit.topt(x), unit.topt(y), unit.topt(r), angle1, angle2)


class arct(arct_pt):

    """Append tangent arc"""

    __slots__ = "x1_pt", "y1_pt", "x2_pt", "y2_pt", "r"

    def __init__(self, x1, y1, x2, y2, r):
        arct_pt.__init__(self, unit.topt(x1), unit.topt(y1),
                         unit.topt(x2), unit.topt(y2), unit.topt(r))

#
# "combined" pathitems provided for performance reasons
#

class multilineto_pt(pathitem):

    """Perform multiple linetos (coordinates in pts)"""

    __slots__ = "points_pt"

    def __init__(self, points_pt):
        self.points_pt = points_pt

    def _updatecontext(self, context):
        context.x_pt, context.y_pt = self.points_pt[-1]

    def _bbox(self, context):
        xs_pt = [point[0] for point in self.points_pt]
        ys_pt = [point[1] for point in self.points_pt]
        return bbox.bbox_pt(min(context.x_pt, *xs_pt),
                            min(context.y_pt, *ys_pt),
                            max(context.x_pt, *xs_pt),
                            max(context.y_pt, *ys_pt))

    def _normalized(self, context):
        result = []
        x0_pt, y0_pt = context.currentpoint
        for x1_pt, y1_pt in self.points_pt:
            result.append(normline_pt(x0_pt, y0_pt, x1_pt, y1_pt))
            x0_pt, y0_pt = x1_pt, y1_pt
        return result

    def outputPS(self, file):
        for point_pt in self.points_pt:
            file.write("%g %g lineto\n" % point_pt )


class multicurveto_pt(pathitem):

    """Perform multiple curvetos (coordinates in pts)"""

    __slots__ = "points_pt"

    def __init__(self, points_pt):
        self.points_pt = points_pt

    def _updatecontext(self, context):
        context.x_pt, context.y_pt = self.points_pt[-1]

    def _bbox(self, context):
        xs = ( [point[0] for point in self.points_pt] +
               [point[2] for point in self.points_pt] +
               [point[4] for point in self.points_pt] )
        ys = ( [point[1] for point in self.points_pt] +
               [point[3] for point in self.points_pt] +
               [point[5] for point in self.points_pt] )
        return bbox.bbox_pt(min(context.x_pt, *xs_pt),
                            min(context.y_pt, *ys_pt),
                            max(context.x_pt, *xs_pt),
                            max(context.y_pt, *ys_pt))

    def _normalized(self, context):
        result = []
        x_pt, y_pt = context.currentpoint
        for point_pt in self.points_pt:
            result.append(normcurve_pt(x_pt, y_pt, *point_pt))
            x_pt, y_pt = point_pt[4:]
        return result

    def outputPS(self, file):
        for point_pt in self.points_pt:
            file.write("%g %g %g %g %g %g curveto\n" % point_pt)


################################################################################
# path: PS style path
################################################################################

class path(base.canvasitem):

    """PS style path"""

    __slots__ = "path", "_normpath"

    def __init__(self, *args):
        """construct a path from pathitems *args"""
        # if not (isinstance(args[0], moveto_pt) or
        #         isinstance(args[0], arc_pt) or
        #         isinstance(args[0], arcn_pt)):
        #     raise PathException("first path element must be either moveto, arc, or arcn")
        self.path = list(args)
        # normpath cache
        self._normpath = None

    def __add__(self, other):
        """create new path with path items of self and other"""
        return path(*(self.path+other.path))

    def __iadd__(self, other):
        """add other path inplace"""
        self.path += other.path
        self._normpath = None
        return self

    def __getitem__(self, i):
        """return path item i"""
        return self.path[i]

    def __len__(self):
        """returns the number of path items"""
        return len(self.path)

    def append(self, pathitem):
        """appends a path item"""
        self.path.append(pathitem)
        self._normpath = None

    def arclen_pt(self):
        """returns total arc length of path in pts"""
        return self.normpath().arclen_pt()

    def arclen(self):
        """returns total arc length of path"""
        return self.normpath().arclen()

    def arclentoparam(self, lengths):
        """returns the parameter value(s) matching the given length(s)"""
        return self.normpath().arclentoparam(lengths)

    def at_pt(self, params):
        """return coordinates of path in pts at param(s)."""
        return self.normpath().at_pt(params)

    def at(self, params):
        """return coordinates of path at param(s)."""
        return self.normpath().at(params)

    def atbegin_pt(self):
        """return coordinates of first point of first subpath in path in pts"""
        return self.normpath().atbegin_pt()

    def atbegin(self):
        """return coordinates of first point of first subpath in path"""
        return self.normpath().atbegin()

    def atend_pt(self):
        """return coordinates of last point of last subpath in path in pts"""
        return self.normpath().atend_pt()

    def atend(self):
        """return coordinates of last point of last subpath in path"""
        return self.normpath().atend()

    def bbox(self):
        """return bbox of path"""
        context = _pathcontext()
        abbox = None

        for pitem in self.path:
            nbbox =  pitem._bbox(context)
            pitem._updatecontext(context)
            if abbox is None:
                abbox = nbbox
            elif nbbox: 
                abbox += nbbox

        return abbox

    def curveradius_pt(self, params):
        """Returns the curvature radius in pts (or None if infinite)
        at param(s). This is the inverse of the curvature.

        Note that this radius can be negative or positive,
        depending on the sign of the curvature."""
        return self.normpath().curveradius_pt(params)

    def curveradius(self, params):
        """Returns the curvature radius (or None if infinite)
        at param(s).  This is the inverse of the curvature.

        Note that this radius can be negative or positive,
        depending on the sign of the curvature."""
        return self.normpath().curveradius(params)

    def extend(self, pathitems):
        """extent path by pathitems"""
        self.path.extend(pathitems)
        self._normpath = None

    def joined(self, other):
        """return path consisting of self and other joined together"""
        # TODO the other is a path as well, we might not switch to a normpath
        return self.normpath().joined(other)

    # << operator also designates joining
    __lshift__ = joined

    def intersect(self, other):
        """intersect normpath corresponding to self with other path"""
        return self.normpath().intersect(other)

    def normpath(self, epsilon=None):
        """converts the path into a normpath"""
        # use cached value if existent
        if self._normpath is not None:
            return self._normpath
        # split path in sub paths
        subpaths = []
        currentsubpathitems = []
        context = _pathcontext()
        for pitem in self.path:
            for npitem in pitem._normalized(context):
                if isinstance(npitem, moveto_pt):
                    if currentsubpathitems:
                        # append open sub path
                        subpaths.append(normsubpath(currentsubpathitems, closed=0, epsilon=epsilon))
                    # start new sub path
                    currentsubpathitems = []
                elif isinstance(npitem, closepath):
                    if currentsubpathitems:
                        # append closed sub path
                        currentsubpathitems.append(normline_pt(context.x_pt, context.y_pt,
                                                               *currentsubpathitems[0].atbegin_pt()))
                    subpaths.append(normsubpath(currentsubpathitems, closed=1, epsilon=epsilon))
                    currentsubpathitems = []
                else:
                    currentsubpathitems.append(npitem)
            pitem._updatecontext(context)

        if currentsubpathitems:
            # append open sub path
            subpaths.append(normsubpath(currentsubpathitems, 0, epsilon))
        self._normpath = normpath(subpaths)
        return self._normpath

    def reversed(self):
        """return reversed path"""
        # TODO: couldn't we try to return a path instead of a normpath
        #       (might not be worth the trouble)
        return self.normpath().reversed()

    def split(self, params):
        """return corresponding normpaths split at param(s)"""
        return self.normpath().split(params)

    def tangent(self, params, length=None):
        """return tangent vector of path at param(s)

        If length is not None, the tangent vector will be scaled to
        the desired length.
        """
        return self.normpath().tangent(params, length)

    def trafo(self, params):
        """return transformation at param(s)"""
        return self.normpath().trafo(params)

    def transformed(self, trafo):
        """return transformed path"""
        return self.normpath().transformed(trafo)

    def outputPS(self, file):
        """write PS code to file"""
        for pitem in self.path:
            pitem.outputPS(file)

    def outputPDF(self, file):
        """write PDF code to file"""
        # PDF only supports normsubpathitems
        context = _pathcontext()
        for pitem in self.path:
            for npitem in pitem._normalized(context):
                npitem.outputPDF(file)
            pitem._updatecontext(context)


################################################################################
# some special kinds of path, again in two variants
################################################################################

class line_pt(path):

   """straight line from (x1_pt, y1_pt) to (x2_pt, y2_pt) in pts"""

   def __init__(self, x1_pt, y1_pt, x2_pt, y2_pt):
       path.__init__(self, moveto_pt(x1_pt, y1_pt), lineto_pt(x2_pt, y2_pt))


class curve_pt(path):

   """bezier curve with control points (x0_pt, y1_pt),..., (x3_pt, y3_pt) in pts"""

   def __init__(self, x0_pt, y0_pt, x1_pt, y1_pt, x2_pt, y2_pt, x3_pt, y3_pt):
       path.__init__(self,
                     moveto_pt(x0_pt, y0_pt),
                     curveto_pt(x1_pt, y1_pt, x2_pt, y2_pt, x3_pt, y3_pt))


class rect_pt(path):

   """rectangle at position (x, y) with width and height in pts"""

   def __init__(self, x, y, width, height):
       path.__init__(self, moveto_pt(x, y),
                           lineto_pt(x+width, y),
                           lineto_pt(x+width, y+height),
                           lineto_pt(x, y+height),
                           closepath())


class circle_pt(path):

   """circle with center (x, y) and radius in pts"""

   def __init__(self, x, y, radius):
       path.__init__(self, arc_pt(x, y, radius, 0, 360), closepath())


class line(line_pt):

   """straight line from (x1, y1) to (x2, y2)"""

   def __init__(self, x1, y1, x2, y2):
       line_pt.__init__(self, unit.topt(x1), unit.topt(y1),
                              unit.topt(x2), unit.topt(y2))


class curve(curve_pt):

   """bezier curve with control points (x0, y1),..., (x3, y3)"""

   def __init__(self, x0, y0, x1, y1, x2, y2, x3, y3):
       curve_pt.__init__(self, unit.topt(x0), unit.topt(y0),
                               unit.topt(x1), unit.topt(y1),
                               unit.topt(x2), unit.topt(y2),
                               unit.topt(x3), unit.topt(y3))


class rect(rect_pt):

   """rectangle at position (x,y) with width and height"""

   def __init__(self, x, y, width, height):
       rect_pt.__init__(self, unit.topt(x), unit.topt(y),
                              unit.topt(width), unit.topt(height))


class circle(circle_pt):

   """circle with center (x,y) and radius"""

   def __init__(self, x, y, radius):
       circle_pt.__init__(self, unit.topt(x), unit.topt(y), unit.topt(radius))


################################################################################
# normpath and corresponding classes
################################################################################

# two helper functions for the intersection of normsubpathitems

def _intersectnormcurves(a, a_t0, a_t1, b, b_t0, b_t1, epsilon):
    """intersect two bpathitems

    a and b are bpathitems with parameter ranges [a_t0, a_t1],
    respectively [b_t0, b_t1].
    epsilon determines when the bpathitems are assumed to be straight
    """

    # intersection of bboxes is a necessary criterium for intersection
    if not a.bbox().intersects(b.bbox()): return []

    if not a.isstraight(epsilon):
        (aa, ab) = a.midpointsplit()
        a_tm = 0.5*(a_t0+a_t1)

        if not b.isstraight(epsilon):
            (ba, bb) = b.midpointsplit()
            b_tm = 0.5*(b_t0+b_t1)

            return ( _intersectnormcurves(aa, a_t0, a_tm,
                                          ba, b_t0, b_tm, epsilon) + 
                     _intersectnormcurves(ab, a_tm, a_t1,
                                          ba, b_t0, b_tm, epsilon) + 
                     _intersectnormcurves(aa, a_t0, a_tm,
                                          bb, b_tm, b_t1, epsilon) +
                     _intersectnormcurves(ab, a_tm, a_t1,
                                          bb, b_tm, b_t1, epsilon) )
        else:
            return ( _intersectnormcurves(aa, a_t0, a_tm,
                                          b, b_t0, b_t1, epsilon) +
                     _intersectnormcurves(ab, a_tm, a_t1,
                                          b, b_t0, b_t1, epsilon) )
    else:
        if not b.isstraight(epsilon):
            (ba, bb) = b.midpointsplit()
            b_tm = 0.5*(b_t0+b_t1)

            return  ( _intersectnormcurves(a, a_t0, a_t1,
                                           ba, b_t0, b_tm, epsilon) +
                      _intersectnormcurves(a, a_t0, a_t1,
                                           bb, b_tm, b_t1, epsilon) )
        else:
            # no more subdivisions of either a or b
            # => try to intersect a and b as straight line segments

            a_deltax = a.x3_pt - a.x0_pt
            a_deltay = a.y3_pt - a.y0_pt
            b_deltax = b.x3_pt - b.x0_pt
            b_deltay = b.y3_pt - b.y0_pt

            det = b_deltax*a_deltay - b_deltay*a_deltax

            ba_deltax0_pt = b.x0_pt - a.x0_pt
            ba_deltay0_pt = b.y0_pt - a.y0_pt

            try:
                a_t = ( b_deltax*ba_deltay0_pt - b_deltay*ba_deltax0_pt)/det
                b_t = ( a_deltax*ba_deltay0_pt - a_deltay*ba_deltax0_pt)/det
            except ArithmeticError:
                return []

            # check for intersections out of bound
            if not (0<=a_t<=1 and 0<=b_t<=1): return []

            # return rescaled parameters of the intersection
            return [ ( a_t0 + a_t * (a_t1 - a_t0),
                       b_t0 + b_t * (b_t1 - b_t0) ) ]


def _intersectnormlines(a, b):
    """return one-element list constisting either of tuple of
    parameters of the intersection point of the two normlines a and b
    or empty list if both normlines do not intersect each other"""

    a_deltax_pt = a.x1_pt - a.x0_pt
    a_deltay_pt = a.y1_pt - a.y0_pt
    b_deltax_pt = b.x1_pt - b.x0_pt
    b_deltay_pt = b.y1_pt - b.y0_pt

    det = 1.0*(b_deltax_pt * a_deltay_pt - b_deltay_pt * a_deltax_pt)

    ba_deltax0_pt = b.x0_pt - a.x0_pt
    ba_deltay0_pt = b.y0_pt - a.y0_pt

    try:
        a_t = ( b_deltax_pt * ba_deltay0_pt - b_deltay_pt * ba_deltax0_pt)/det
        b_t = ( a_deltax_pt * ba_deltay0_pt - a_deltay_pt * ba_deltax0_pt)/det
    except ArithmeticError:
        return []

    # check for intersections out of bound
    if not (0<=a_t<=1 and 0<=b_t<=1): return []

    # return parameters of the intersection
    return [( a_t, b_t)]


################################################################################
# normsubpathitem class
################################################################################

class normsubpathitem:

    """element of a normalized sub path"""

    def _arclentoparam_pt(self, lengths, epsilon):
        """returns tuple (t,l) with
          t the parameter where the arclen of normsubpathitem is length and
          l the total arclen

        length:  length (in pts) to find the parameter for
        epsilon: epsilon controls the accuracy for calculation of the
                 length of the Bezier elements
        """
        # Note: _arclentoparam returns both, parameters and total lengths
        # while  arclentoparam returns only parameters
        pass

    def arclen_pt(self, epsilon):
        """returns arc length of normsubpathitem in pts with given accuracy epsilon"""
        pass

    def at_pt(self, t):
        """returns coordinates of point in pts at parameter t (0<=t<=1) """
        pass

    def atbegin_pt(self):
        """returns coordinates in pts of begin of normsubpathitem """
        pass

    def atend_pt(self):
        """returns coordinates in pts of end of normsubpathitem """
        pass

    def bbox(self):
        """return bounding box of normsubpathitem"""
        pass

    def curveradius_pt(self, params):
        """Returns the curvature radiuses in pts at params.
        This is the inverse of the curvature at these parameters

        Please note that this radius can be negative or positive,
        depending on the sign of the curvature"""
        pass

    def intersect(self, other, epsilon):
        """intersect self with other normsubpathitem"""
        pass

    def modified(self, xs_pt=None, ys_pt=None, xe_pt=None, ye_pt=None):
        """returns a (new) modified normpath with different start and
        end points as provided"""
        pass

    def paramtoarclen_pt(self, param, epsilon):
        """ return arc length in pts corresponding to param """
        pass

    def reversed(self):
        """return reversed normsubpathitem"""
        pass

    def split(self, parameters):
        """splits normsubpathitem

        parameters: list of parameter values (0<=t<=1) at which to split

        returns None or list of tuple of normsubpathitems corresponding to 
        the orginal normsubpathitem.

        """
        pass

    def tangentvector_pt(self, t):
        """returns tangent vector of normsubpathitem in pts at parameter t (0<=t<=1)"""
        pass

    def transformed(self, trafo):
        """return transformed normsubpathitem according to trafo"""
        pass

    def outputPS(self, file):
        """write PS code corresponding to normsubpathitem to file"""
        pass

    def outputPS(self, file):
        """write PDF code corresponding to normsubpathitem to file"""
        pass

################################################################################
# there are only two normsubpathitems: normline and normcurve
################################################################################

def _valueorlistmethod(method):
    def wrappedmethod(self, valueorlist, *args, **kwargs):
        try:
            for item in valueorlist:
                break
        except:
            return method(self, [valueorlist], *args, **kwargs)[0]
        return method(self, valueorlist, *args, **kwargs)
    return wrappedmethod

class normline_pt(normsubpathitem):

    """Straight line from (x0_pt, y0_pt) to (x1_pt, y1_pt) (coordinates in pts)"""

    __slots__ = "x0_pt", "y0_pt", "x1_pt", "y1_pt"

    def __init__(self, x0_pt, y0_pt, x1_pt, y1_pt):
         self.x0_pt = x0_pt
         self.y0_pt = y0_pt
         self.x1_pt = x1_pt
         self.y1_pt = y1_pt

    def __str__(self):
        return "normline_pt(%g, %g, %g, %g)" % (self.x0_pt, self.y0_pt, self.x1_pt, self.y1_pt)

    def _arclentoparam_pt(self, lengths, epsilon):
        l = math.hypot(self.x0_pt-self.x1_pt, self.y0_pt-self.y1_pt)
        return [length/l for length in lengths], l

    def _normcurve(self):
        """ return self as equivalent normcurve """
        xa_pt = self.x0_pt+(self.x1_pt-self.x0_pt)/3.0
        ya_pt = self.y0_pt+(self.y1_pt-self.y0_pt)/3.0
        xb_pt = self.x0_pt+2.0*(self.x1_pt-self.x0_pt)/3.0
        yb_pt = self.y0_pt+2.0*(self.y1_pt-self.y0_pt)/3.0
        return normcurve_pt(self.x0_pt, self.y0_pt, xa_pt, ya_pt, xb_pt, yb_pt, self.x1_pt, self.y1_pt)

    def arclen_pt(self,  epsilon):
        return math.hypot(self.x0_pt-self.x1_pt, self.y0_pt-self.y1_pt)

    def at_pt(self, params):
        return [(self.x0_pt+(self.x1_pt-self.x0_pt)*t, self.y0_pt+(self.y1_pt-self.y0_pt)*t)
                for t in params]

    def atbegin_pt(self):
        return self.x0_pt, self.y0_pt

    def atend_pt(self):
        return self.x1_pt, self.y1_pt

    def bbox(self):
        return bbox.bbox_pt(min(self.x0_pt, self.x1_pt), min(self.y0_pt, self.y1_pt), 
                          max(self.x0_pt, self.x1_pt), max(self.y0_pt, self.y1_pt))

    def curveradius_pt(self, params):
        return [None] * len(params)

    def intersect(self, other, epsilon):
        if isinstance(other, normline_pt):
            return _intersectnormlines(self, other)
        else:
            return  _intersectnormcurves(self._normcurve(), 0, 1, other, 0, 1, epsilon)

    def isstraight(self, epsilon):
        return 1

    def modified(self, xs_pt=None, ys_pt=None, xe_pt=None, ye_pt=None):
        if xs_pt is None:
            xs_pt = self.x0_pt
        if ys_pt is None:
            ys_pt = self.y0_pt
        if xe_pt is None:
            xe_pt = self.x1_pt
        if ye_pt is None:
            ye_pt = self.y1_pt
        return normline_pt(xs_pt, ys_pt, xe_pt, ye_pt)

    def _paramtoarclen_pt(self, params, epsilon):
        totalarclen_pt = self.arclen_pt(epsilon)
        arclens_pt = [totalarclen_pt * param for param in params + [1]]
        return arclens_pt[:-1], arclens_pt[-1]

    def reverse(self):
        self.x0_pt, self.y0_pt, self.x1_pt, self.y1_pt = self.x1_pt, self.y1_pt, self.x0_pt, self.y0_pt

    def reversed(self):
        return normline_pt(self.x1_pt, self.y1_pt, self.x0_pt, self.y0_pt)

    def split(self, params):
        # just for performance reasons
        x0_pt, y0_pt = self.x0_pt, self.y0_pt
        x1_pt, y1_pt = self.x1_pt, self.y1_pt

        result = []

        xl_pt, yl_pt = x0_pt, y0_pt
        for t in params + [1]:
            xr_pt, yr_pt = x0_pt + (x1_pt-x0_pt)*t, y0_pt + (y1_pt-y0_pt)*t
            result.append(normline_pt(xl_pt, yl_pt, xr_pt, yr_pt))
            xl_pt, yl_pt = xr_pt, yr_pt

        return result

    def trafo(self, params):
        rotate = trafo.rotate(degrees(math.atan2(self.y1_pt-self.y0_pt, self.x1_pt-self.x0_pt)))
        return [trafo.translate_pt(*at_pt) * rotate
                for param, at_pt in zip(params, self.at_pt(params))]

    def transformed(self, trafo):
        return normline_pt(*(trafo._apply(self.x0_pt, self.y0_pt) + trafo._apply(self.x1_pt, self.y1_pt)))

    def outputPS(self, file):
        file.write("%g %g lineto\n" % (self.x1_pt, self.y1_pt))

    def outputPDF(self, file):
        file.write("%f %f l\n" % (self.x1_pt, self.y1_pt))


class normcurve_pt(normsubpathitem):

    """Bezier curve with control points x0_pt, y0_pt, x1_pt, y1_pt, x2_pt, y2_pt, x3_pt, y3_pt (coordinates in pts)"""

    __slots__ = "x0_pt", "y0_pt", "x1_pt", "y1_pt", "x2_pt", "y2_pt", "x3_pt", "y3_pt"

    def __init__(self, x0_pt, y0_pt, x1_pt, y1_pt, x2_pt, y2_pt, x3_pt, y3_pt):
        self.x0_pt = x0_pt
        self.y0_pt = y0_pt
        self.x1_pt = x1_pt
        self.y1_pt = y1_pt
        self.x2_pt = x2_pt
        self.y2_pt = y2_pt
        self.x3_pt = x3_pt
        self.y3_pt = y3_pt

    def __str__(self):
        return "normcurve_pt(%g, %g, %g, %g, %g, %g, %g, %g)" % (self.x0_pt, self.y0_pt, self.x1_pt, self.y1_pt,
                                                                 self.x2_pt, self.y2_pt, self.x3_pt, self.y3_pt)

    def _arclentoparam_pt(self, lengths, epsilon):
        """computes the parameters [t] of bpathitem where the given lengths (in pts) are assumed
        returns ( [parameters], total arclen)
        A negative length gives a parameter 0"""

        # create the list of accumulated lengths
        # and the length of the parameters
        seg = self.seglengths(1, epsilon)
        arclens = [seg[i][0] for i in range(len(seg))]
        Dparams = [seg[i][1] for i in range(len(seg))]
        l = len(arclens)
        for i in range(1,l):
            arclens[i] += arclens[i-1]

        # create the list of parameters to be returned
        params = []
        for length in lengths:
            # find the last index that is smaller than length
            try:
                lindex = bisect.bisect_left(arclens, length)
            except: # workaround for python 2.0
                lindex = bisect.bisect(arclens, length)
                while lindex and (lindex >= len(arclens) or
                                  arclens[lindex] >= length):
                    lindex -= 1
            if lindex == 0:
                param = Dparams[0] * length * 1.0 / arclens[0]
            elif lindex < l-1:
                param = Dparams[lindex+1] * (length - arclens[lindex]) * 1.0 / (arclens[lindex+1] - arclens[lindex])
                for i in range(lindex+1):
                    param += Dparams[i]
            else:
                param = 1 + Dparams[-1] * (length - arclens[-1]) * 1.0 / (arclens[-1] - arclens[-2])

            # param = max(min(param,1),0)
            params.append(param)
        return (params, arclens[-1])

    def arclen_pt(self, epsilon):
        """computes arclen of bpathitem in pts using successive midpoint split"""
        if self.isstraight(epsilon):
            return math.hypot(self.x3_pt-self.x0_pt, self.y3_pt-self.y0_pt)
        else:
            a, b = self.midpointsplit()
            return a.arclen_pt(epsilon) + b.arclen_pt(epsilon)

    def at_pt(self, params):
        return [( (-self.x0_pt+3*self.x1_pt-3*self.x2_pt+self.x3_pt)*t*t*t +
                  (3*self.x0_pt-6*self.x1_pt+3*self.x2_pt          )*t*t +
                  (-3*self.x0_pt+3*self.x1_pt                      )*t +
                  self.x0_pt,
                  (-self.y0_pt+3*self.y1_pt-3*self.y2_pt+self.y3_pt)*t*t*t +
                  (3*self.y0_pt-6*self.y1_pt+3*self.y2_pt          )*t*t +
                  (-3*self.y0_pt+3*self.y1_pt                      )*t +
                  self.y0_pt )
                for t in params]

    def atbegin_pt(self):
        return self.x0_pt, self.y0_pt

    def atend_pt(self):
        return self.x3_pt, self.y3_pt

    def bbox(self):
        return bbox.bbox_pt(min(self.x0_pt, self.x1_pt, self.x2_pt, self.x3_pt),
                          min(self.y0_pt, self.y1_pt, self.y2_pt, self.y3_pt),
                          max(self.x0_pt, self.x1_pt, self.x2_pt, self.x3_pt),
                          max(self.y0_pt, self.y1_pt, self.y2_pt, self.y3_pt))

    def curveradius_pt(self, params):
        result = []
        for param in params:
            xdot = ( 3 * (1-param)*(1-param) * (-self.x0_pt + self.x1_pt) +
                     6 * (1-param)*param * (-self.x1_pt + self.x2_pt) +
                     3 * param*param * (-self.x2_pt + self.x3_pt) )
            ydot = ( 3 * (1-param)*(1-param) * (-self.y0_pt + self.y1_pt) +
                     6 * (1-param)*param * (-self.y1_pt + self.y2_pt) +
                     3 * param*param * (-self.y2_pt + self.y3_pt) )
            xddot = ( 6 * (1-param) * (self.x0_pt - 2*self.x1_pt + self.x2_pt) +
                      6 * param * (self.x1_pt - 2*self.x2_pt + self.x3_pt) )
            yddot = ( 6 * (1-param) * (self.y0_pt - 2*self.y1_pt + self.y2_pt) +
                      6 * param * (self.y1_pt - 2*self.y2_pt + self.y3_pt) )
            result.append((xdot**2 + ydot**2)**1.5 / (xdot*yddot - ydot*xddot))
        return result

    def intersect(self, other, epsilon):
        if isinstance(other, normline_pt):
            return  _intersectnormcurves(self, 0, 1, other._normcurve(), 0, 1, epsilon)
        else:
            return  _intersectnormcurves(self, 0, 1, other, 0, 1, epsilon)

    def isstraight(self, epsilon):
        """check wheter the normcurve is approximately straight"""

        # just check, whether the modulus of the difference between
        # the length of the control polygon
        # (i.e. |P1-P0|+|P2-P1|+|P3-P2|) and the length of the
        # straight line between starting and ending point of the
        # normcurve (i.e. |P3-P1|) is smaller the epsilon
        return abs(math.hypot(self.x1_pt-self.x0_pt, self.y1_pt-self.y0_pt)+
                   math.hypot(self.x2_pt-self.x1_pt, self.y2_pt-self.y1_pt)+
                   math.hypot(self.x3_pt-self.x2_pt, self.y3_pt-self.y2_pt)-
                   math.hypot(self.x3_pt-self.x0_pt, self.y3_pt-self.y0_pt))<epsilon

    def midpointsplit(self):
        """splits bpathitem at midpoint returning bpath with two bpathitems"""

        # for efficiency reason, we do not use self.split(0.5)!

        # first, we have to calculate the  midpoints between adjacent
        # control points
        x01_pt = 0.5*(self.x0_pt + self.x1_pt)
        y01_pt = 0.5*(self.y0_pt + self.y1_pt)
        x12_pt = 0.5*(self.x1_pt + self.x2_pt)
        y12_pt = 0.5*(self.y1_pt + self.y2_pt)
        x23_pt = 0.5*(self.x2_pt + self.x3_pt)
        y23_pt = 0.5*(self.y2_pt + self.y3_pt)

        # In the next iterative step, we need the midpoints between 01 and 12
        # and between 12 and 23 
        x01_12_pt = 0.5*(x01_pt + x12_pt)
        y01_12_pt = 0.5*(y01_pt + y12_pt)
        x12_23_pt = 0.5*(x12_pt + x23_pt)
        y12_23_pt = 0.5*(y12_pt + y23_pt)

        # Finally the midpoint is given by
        xmidpoint_pt = 0.5*(x01_12_pt + x12_23_pt)
        ymidpoint_pt = 0.5*(y01_12_pt + y12_23_pt)

        return (normcurve_pt(self.x0_pt, self.y0_pt,
                          x01_pt, y01_pt,
                          x01_12_pt, y01_12_pt,
                          xmidpoint_pt, ymidpoint_pt),
                normcurve_pt(xmidpoint_pt, ymidpoint_pt,
                          x12_23_pt, y12_23_pt,
                          x23_pt, y23_pt,
                          self.x3_pt, self.y3_pt))

    def modified(self, xs_pt=None, ys_pt=None, xe_pt=None, ye_pt=None):
        if xs_pt is None:
            xs_pt = self.x0_pt
        if ys_pt is None:
            ys_pt = self.y0_pt
        if xe_pt is None:
            xe_pt = self.x3_pt
        if ye_pt is None:
            ye_pt = self.y3_pt
        return normcurve_pt(xs_pt, ys_pt,
                         self.x1_pt, self.y1_pt,
                         self.x2_pt, self.y2_pt,
                         xe_pt, ye_pt)

    def _paramtoarclen_pt(self, params, epsilon):
        arclens_pt = [splitpath.arclen_pt(epsilon) for splitpath in self.split(params)]
        for i in range(1, len(arclens_pt)):
            arclens_pt[i] += arclens_pt[i-1]
        return arclens_pt[:-1], arclens_pt[-1]

    def reverse(self):
        self.x0_pt, self.y0_pt, self.x1_pt, self.y1_pt, self.x2_pt, self.y2_pt, self.x3_pt, self.y3_pt = \
        self.x3_pt, self.y3_pt, self.x2_pt, self.y2_pt, self.x1_pt, self.y1_pt, self.x0_pt, self.y0_pt

    def reversed(self):
        return normcurve_pt(self.x3_pt, self.y3_pt, self.x2_pt, self.y2_pt, self.x1_pt, self.y1_pt, self.x0_pt, self.y0_pt)

    def seglengths(self, paraminterval, epsilon):
        """returns the list of segment line lengths (in pts) of the normcurve
           together with the length of the parameterinterval"""

        # lower and upper bounds for the arclen
        lowerlen = math.hypot(self.x3_pt-self.x0_pt, self.y3_pt-self.y0_pt)
        upperlen = ( math.hypot(self.x1_pt-self.x0_pt, self.y1_pt-self.y0_pt) +
                     math.hypot(self.x2_pt-self.x1_pt, self.y2_pt-self.y1_pt) +
                     math.hypot(self.x3_pt-self.x2_pt, self.y3_pt-self.y2_pt) )

        # instead of isstraight method:
        if abs(upperlen-lowerlen)<epsilon:
            return [( 0.5*(upperlen+lowerlen), paraminterval )]
        else:
            a, b = self.midpointsplit()
            return a.seglengths(0.5*paraminterval, epsilon) + b.seglengths(0.5*paraminterval, epsilon)

    def split(self, params):
        """return list of normcurves corresponding to split at parameters"""

        # first, we calculate the coefficients corresponding to our
        # original bezier curve. These represent a useful starting
        # point for the following change of the polynomial parameter
        a0x_pt = self.x0_pt
        a0y_pt = self.y0_pt
        a1x_pt = 3*(-self.x0_pt+self.x1_pt)
        a1y_pt = 3*(-self.y0_pt+self.y1_pt)
        a2x_pt = 3*(self.x0_pt-2*self.x1_pt+self.x2_pt)
        a2y_pt = 3*(self.y0_pt-2*self.y1_pt+self.y2_pt)
        a3x_pt = -self.x0_pt+3*(self.x1_pt-self.x2_pt)+self.x3_pt
        a3y_pt = -self.y0_pt+3*(self.y1_pt-self.y2_pt)+self.y3_pt

        params = [0] + params + [1]
        result = []

        for i in range(len(params)-1):
            t1 = params[i]
            dt = params[i+1]-t1

            # [t1,t2] part
            #
            # the new coefficients of the [t1,t1+dt] part of the bezier curve
            # are then given by expanding
            #  a0 + a1*(t1+dt*u) + a2*(t1+dt*u)**2 +
            #  a3*(t1+dt*u)**3 in u, yielding
            #
            #   a0 + a1*t1 + a2*t1**2 + a3*t1**3        +
            #   ( a1 + 2*a2 + 3*a3*t1**2 )*dt    * u    + 
            #   ( a2 + 3*a3*t1 )*dt**2           * u**2 +
            #   a3*dt**3                         * u**3
            #
            # from this values we obtain the new control points by inversion
            #
            # XXX: we could do this more efficiently by reusing for
            # (x0_pt, y0_pt) the control point (x3_pt, y3_pt) from the previous
            # Bezier curve

            x0_pt = a0x_pt + a1x_pt*t1 + a2x_pt*t1*t1 + a3x_pt*t1*t1*t1 
            y0_pt = a0y_pt + a1y_pt*t1 + a2y_pt*t1*t1 + a3y_pt*t1*t1*t1 
            x1_pt = (a1x_pt+2*a2x_pt*t1+3*a3x_pt*t1*t1)*dt/3.0 + x0_pt
            y1_pt = (a1y_pt+2*a2y_pt*t1+3*a3y_pt*t1*t1)*dt/3.0 + y0_pt
            x2_pt = (a2x_pt+3*a3x_pt*t1)*dt*dt/3.0 - x0_pt + 2*x1_pt
            y2_pt = (a2y_pt+3*a3y_pt*t1)*dt*dt/3.0 - y0_pt + 2*y1_pt
            x3_pt = a3x_pt*dt*dt*dt + x0_pt - 3*x1_pt + 3*x2_pt
            y3_pt = a3y_pt*dt*dt*dt + y0_pt - 3*y1_pt + 3*y2_pt

            result.append(normcurve_pt(x0_pt, y0_pt, x1_pt, y1_pt, x2_pt, y2_pt, x3_pt, y3_pt))

        return result

    def trafo(self, params):
        result = []
        for param, at_pt in zip(params, self.at_pt(params)):
            tdx_pt = (3*(  -self.x0_pt+3*self.x1_pt-3*self.x2_pt+self.x3_pt)*param*param +
                      2*( 3*self.x0_pt-6*self.x1_pt+3*self.x2_pt           )*param +
                        (-3*self.x0_pt+3*self.x1_pt                        ))
            tdy_pt = (3*(  -self.y0_pt+3*self.y1_pt-3*self.y2_pt+self.y3_pt)*param*param +
                      2*( 3*self.y0_pt-6*self.y1_pt+3*self.y2_pt           )*param +
                        (-3*self.y0_pt+3*self.y1_pt                        ))
            result.append(trafo.translate_pt(*at_pt) * trafo.rotate(degrees(math.atan2(tdy_pt, tdx_pt))))
        return result

    def transform(self, trafo):
        self.x0_pt, self.y0_pt = trafo._apply(self.x0_pt, self.y0_pt)
        self.x1_pt, self.y1_pt = trafo._apply(self.x1_pt, self.y1_pt)
        self.x2_pt, self.y2_pt = trafo._apply(self.x2_pt, self.y2_pt)
        self.x3_pt, self.y3_pt = trafo._apply(self.x3_pt, self.y3_pt)

    def transformed(self, trafo):
        return normcurve_pt(*(trafo._apply(self.x0_pt, self.y0_pt)+
                           trafo._apply(self.x1_pt, self.y1_pt)+
                           trafo._apply(self.x2_pt, self.y2_pt)+
                           trafo._apply(self.x3_pt, self.y3_pt)))

    def outputPS(self, file):
        file.write("%g %g %g %g %g %g curveto\n" % (self.x1_pt, self.y1_pt, self.x2_pt, self.y2_pt, self.x3_pt, self.y3_pt))

    def outputPDF(self, file):
        file.write("%f %f %f %f %f %f c\n" % (self.x1_pt, self.y1_pt, self.x2_pt, self.y2_pt, self.x3_pt, self.y3_pt))

################################################################################
# normsubpath class 
################################################################################

class normsubpath:

    """sub path of a normalized path

    A subpath consists of a list of normsubpathitems, i.e., lines and bcurves
    and can either be closed or not.

    Some invariants, which have to be obeyed:
    - All normsubpathitems have to be longer than epsilon pts.
    - At the end there may be a normline (stored in self.skippedline) whose
      length is shorter than epsilon
    - The last point of a normsubpathitem and the first point of the next
    element have to be equal.
    - When the path is closed, the last point of last normsubpathitem has
      to be equal to the first point of the first normsubpathitem.
    """

    __slots__ = "normsubpathitems", "closed", "epsilon", "skippedline"

    def __init__(self, normsubpathitems=[], closed=0, epsilon=None):
        if epsilon is None:
            epsilon = _epsilon
        self.epsilon = epsilon
        # If one or more items appended to the normsubpath have been
        # skipped (because their total length was shorter than
        # epsilon), we remember this fact by a line because we have to
        # take it properly into account when appending further subnormpathitems
        self.skippedline = None

        self.normsubpathitems = []
        self.closed = 0

        # a test (might be temporary)
        for anormsubpathitem in normsubpathitems:
            assert isinstance(anormsubpathitem, normsubpathitem), "only list of normsubpathitem instances allowed"

        self.extend(normsubpathitems)

        if closed:
            self.close()

    def __add__(self, other):
        # we take self.epsilon as accuracy for the resulting subnormpath
        result = subnormpath(self.normpathitems, self.closed, self.epsilon)
        result += other
        return result

    def __getitem__(self, i):
        return self.normsubpathitems[i]

    def __iadd__(self, other):
        if other.closed:
            raise PathException("Cannot extend normsubpath by closed normsubpath")
        self.extend(other.normsubpathitems)
        return self

    def __len__(self):
        return len(self.normsubpathitems)

    def __str__(self):
        return "subpath(%s, [%s])" % (self.closed and "closed" or "open",
                                    ", ".join(map(str, self.normsubpathitems)))

    def _distributeparamsold(self, params):
        """Creates a list tuples (normsubpathitem, itemparams),
        where itemparams are the parameter values corresponding
        to params in normsubpathitem. For the first normsubpathitem
        itemparams fulfil param < 1, for the last normsubpathitem
        itemparams fulfil 0 <= param, and for all other
        normsubpathitems itemparams fulfil 0 <= param < 1.
        Note that params have to be sorted.
        """
        if self.isshort():
            if params:
                raise PathException("Cannot select parameters for a short normsubpath")
            return []
        result = []
        paramindex = 0
        for index, normsubpathitem in enumerate(self.normsubpathitems[:-1]):
            oldparamindex = paramindex
            while paramindex < len(params) and params[paramindex] < index + 1:
                paramindex += 1
            result.append((normsubpathitem, [param - index for param in params[oldparamindex: paramindex]]))
        result.append((self.normsubpathitems[-1],
                       [param - len(self.normsubpathitems) + 1 for param in params[paramindex:]]))
        return result

    def _distributeparams(self, params):
        """Returns a dictionary mapping normsubpathitemindices to a tuple of a
        paramindices and normsubpathitemparams.

        normsubpathitemindex specifies a normsubpathitem containing
        one or several positions.  paramindex specify the index of the
        param in the original list and normsubpathitemparam is the
        parameter value in the normsubpathitem.
        """

        result = {}
        for i, param in enumerate(params):
            if param > 0:
                index = int(param)
                if index > len(self.normsubpathitems) - 1:
                    index = len(self.normsubpathitems) - 1
            else:
                index = 0
            result.setdefault(index, ([], []))
            result[index][0].append(i)
            result[index][1].append(param - index)
        return result

    def append(self, anormsubpathitem):
        assert isinstance(anormsubpathitem, normsubpathitem), "only normsubpathitem instances allowed"

        if self.closed:
            raise PathException("Cannot append to closed normsubpath")

        if self.skippedline:
            xs_pt, ys_pt = self.skippedline.atbegin_pt()
        else:
            xs_pt, ys_pt = anormsubpathitem.atbegin_pt()
        xe_pt, ye_pt = anormsubpathitem.atend_pt()

        if (math.hypot(xe_pt-xs_pt, ye_pt-ys_pt) >= self.epsilon or
            anormsubpathitem.arclen_pt(self.epsilon) >= self.epsilon):
            if self.skippedline:
                anormsubpathitem = anormsubpathitem.modified(xs_pt=xs_pt, ys_pt=ys_pt)
            self.normsubpathitems.append(anormsubpathitem)
            self.skippedline = None
        else:
            self.skippedline = normline_pt(xs_pt, ys_pt, xe_pt, ye_pt)

    def arclen_pt(self):
        """returns total arc length of normsubpath in pts with accuracy epsilon"""
        return sum([npitem.arclen_pt(self.epsilon) for npitem in self.normsubpathitems])

    def _arclentoparam_pt(self, lengths_pt):
        """ returns (t, l) where t are parameter values matching given lengths
        and l is the total length of the normsubpath """
        # work on a copy which is counted down to negative values
        lengths_pt = lengths_pt[:]
        results = [None] * len(lengths_pt)

        totalarclen = 0
        for normsubpathindex, normsubpathitem in enumerate(self.normsubpathitems):
            params, arclen = normsubpathitem._arclentoparam_pt(lengths_pt, self.epsilon)
            for i in range(len(results)):
                if results[i] is None:
                    lengths_pt[i] -= arclen
                    if lengths_pt[i] < 0 or normsubpathindex == len(self.normsubpathitems) - 1:
                        # overwrite the results until the length has become negative
                        results[i] = normsubpathindex + params[i]
            totalarclen += arclen

        return results, totalarclen

    def at_pt(self, params):
        """return coordinates in pts of sub path at parameter value params

        The parameter param must be smaller or equal to the number of
        segments in the normpath, otherwise None is returned.
        """
        result = [None] * len(params)
        for normsubpathitemindex, (indices, params) in self._distributeparams(params).items():
            for index, point_pt in zip(indices, self.normsubpathitems[normsubpathitemindex].at_pt(params)):
                result[index] = point_pt
        return result

    def atbegin_pt(self):
        if not self.normsubpathitems and self.skippedline:
            return self.skippedline.atbegin_pt()
        return self.normsubpathitems[0].atbegin_pt()

    def atend_pt(self):
        if self.skippedline:
            return self.skippedline.atend_pt()
        return self.normsubpathitems[-1].atend_pt()

    def bbox(self):
        if self.normsubpathitems:
            abbox = self.normsubpathitems[0].bbox()
            for anormpathitem in self.normsubpathitems[1:]:
                abbox += anormpathitem.bbox()
            return abbox
        else:
            return None

    def close(self):
        if self.closed:
            raise PathException("Cannot close already closed normsubpath")
        if not self.normsubpathitems:
            if self.skippedline is None:
                raise PathException("Cannot close empty normsubpath")
            else:
                raise PathException("Normsubpath too short, cannot be closed")

        xs_pt, ys_pt = self.normsubpathitems[-1].atend_pt()
        xe_pt, ye_pt = self.normsubpathitems[0].atbegin_pt()
        self.append(normline_pt(xs_pt, ys_pt, xe_pt, ye_pt))

        # the append might have left a skippedline, which we have to remove
        # from the end of the closed path
        if self.skippedline:
            self.normsubpathitems[-1] = self.normsubpathitems[-1].modified(xe_pt=self.skippedline.x1_pt,
                                                                           ye_pt=self.skippedline.y1_pt)
            self.skippedline = None

        self.closed = 1

    def curveradius_pt(self, params):
        result = [None] * len(params)
        for normsubpathitemindex, (indices, params) in self._distributeparams(params).items():
            for index, radius_pt in zip(indices, self.normsubpathitems[normsubpathitemindex].curveradius_pt(params)):
                result[index] = radius_pt
        return result

    def extend(self, normsubpathitems):
        for normsubpathitem in normsubpathitems:
            self.append(normsubpathitem)

    def intersect(self, other):
        """intersect self with other normsubpath

        returns a tuple of lists consisting of the parameter values
        of the intersection points of the corresponding normsubpath

        """
        intersections_a = []
        intersections_b = []
        epsilon = min(self.epsilon, other.epsilon)
        # Intersect all subpaths of self with the subpaths of other, possibly including
        # one intersection point several times
        for t_a, pitem_a  in enumerate(self.normsubpathitems):
            for t_b, pitem_b in enumerate(other.normsubpathitems):
                for intersection_a, intersection_b in pitem_a.intersect(pitem_b, epsilon):
                    intersections_a.append(intersection_a + t_a)
                    intersections_b.append(intersection_b + t_b)

        # although intersectipns_a are sorted for the different normsubpathitems,
        # within a normsubpathitem, the ordering has to be ensured separately:
        intersections = zip(intersections_a, intersections_b)
        intersections.sort()
        intersections_a = [a for a, b in intersections]
        intersections_b = [b for a, b in intersections]

        # for symmetry reasons we enumerate intersections_a as well, although
        # they are already sorted (note we do not need to sort intersections_a)
        intersections_a = zip(intersections_a, range(len(intersections_a)))
        intersections_b = zip(intersections_b, range(len(intersections_b)))
        intersections_b.sort()

        # now we search for intersections points which are closer together than epsilon
        # This task is handled by the following function
        def closepoints(normsubpath, intersections):
            split = normsubpath.split([intersection for intersection, index in intersections])
            result = []
            if normsubpath.closed:
                # note that the number of segments of a closed path is off by one
                # compared to an open path
                i = 0
                while i < len(split):
                    splitnormsubpath = split[i]
                    j = i
                    while splitnormsubpath.isshort():
                        ip1, ip2 = intersections[i-1][1], intersections[j][1]
                        if ip1<ip2:
                            result.append((ip1, ip2))
                        else:
                            result.append((ip2, ip1))
                        j += 1
                        if j == len(split):
                            j = 0
                        if j < len(split):
                            splitnormsubpath = splitnormsubpath.joined(split[j])
                        else:
                            break
                    i += 1
            else:
                i = 1
                while i < len(split)-1:
                    splitnormsubpath = split[i]
                    j = i
                    while splitnormsubpath.isshort():
                        ip1, ip2 = intersections[i-1][1], intersections[j][1]
                        if ip1<ip2:
                            result.append((ip1, ip2))
                        else:
                            result.append((ip2, ip1))
                        j += 1
                        if j < len(split)-1:
                            splitnormsubpath.join(split[j])
                        else:
                            break
                    i += 1
            return result

        closepoints_a = closepoints(self, intersections_a)
        closepoints_b = closepoints(other, intersections_b)

        # map intersection point to lowest point which is equivalent to the
        # point
        equivalentpoints = list(range(len(intersections_a)))

        for closepoint_a in closepoints_a:
            for closepoint_b in closepoints_b:
                if closepoint_a == closepoint_b:
                    for i in range(closepoint_a[1], len(equivalentpoints)):
                        if equivalentpoints[i] == closepoint_a[1]:
                            equivalentpoints[i] = closepoint_a[0]

        # determine the remaining intersection points
        intersectionpoints = {}
        for point in equivalentpoints:
            intersectionpoints[point] = 1

        # build result
        result = []
        intersectionpointskeys = intersectionpoints.keys()
        intersectionpointskeys.sort()
        for point in intersectionpointskeys:
            for intersection_a, index_a in intersections_a:
                if index_a == point:
                    result_a = intersection_a
            for intersection_b, index_b in intersections_b:
                if index_b == point:
                    result_b = intersection_b
            result.append((result_a, result_b))
        # note that the result is sorted in a, since we sorted
        # intersections_a in the very beginning

        return [x for x, y in result], [y for x, y in result]

    def isshort(self):
        """return whether the subnormpath is shorter than epsilon"""
        return not self.normsubpathitems

    def join(self, other):
        for othernormpathitem in other.normsubpathitems:
            self.append(othernormpathitem)
        if other.skippedline is not None:
            self.append(other.skippedline)

    def joined(self, other):
        result = normsubpath(self.normsubpathitems, self.closed, self.epsilon)
        result.skippedline = self.skippedline
        result.join(other)
        return result

    def _paramtoarclen_pt(self, params):
        """returns a tuple of arc lengths and the total arc length."""
        result = [None] * len(params)
        totalarclen_pt = 0
        distributeparams = self._distributeparams(params)
        for normsubpathitemindex in range(len(self.normsubpathitems)):
            if distributeparams.has_key(normsubpathitemindex):
                indices, params = distributeparams[normsubpathitemindex]
                arclens_pt, normsubpathitemarclen_pt = self.normsubpathitems[normsubpathitemindex]._paramtoarclen_pt(params, self.epsilon)
                for index, arclen_pt in zip(indices, arclens_pt):
                    result[index] = totalarclen_pt + arclen_pt
                totalarclen_pt += normsubpathitemarclen_pt
            else:
                totalarclen_pt += self.normsubpathitems[normsubpathitemindex].arclen_pt(self.epsilon)
        return result, totalarclen_pt

    def reverse(self):
        self.normsubpathitems.reverse()
        for npitem in self.normsubpathitems:
            npitem.reverse()

    def reversed(self):
        nnormpathitems = []
        for i in range(len(self.normsubpathitems)):
            nnormpathitems.append(self.normsubpathitems[-(i+1)].reversed())
        return normsubpath(nnormpathitems, self.closed)

    def split(self, params):
        """split normsubpath at list of parameter values params and return list
        of normsubpaths

        The parameter list params has to be sorted. Note that each element of
        the resulting list is an open normsubpath.
        """

        result = [normsubpath(epsilon=self.epsilon)]

        for normsubpathitem, itemparams in self._distributeparamsold(params):
            splititems = normsubpathitem.split(itemparams)
            result[-1].append(splititems[0])
            result.extend([normsubpath([splititem], epsilon=self.epsilon) for splititem in splititems[1:]])

        if self.closed:
            if params:
                # join last and first segment together if the normsubpath was originally closed and it has been split
                result[-1].normsubpathitems.extend(result[0].normsubpathitems)
                result = result[-1:] + result[1:-1]
            else:
                # otherwise just close the copied path again
                result[0].close()
        return result

    def trafo(self, params):
        result = [None] * len(params)
        for normsubpathitemindex, (indices, params) in self._distributeparams(params).items():
            for index, trafo in zip(indices, self.normsubpathitems[normsubpathitemindex].trafo(params)):
                result[index] = trafo
        return result

    def transform(self, trafo):
        """transform sub path according to trafo"""
        # note that we have to rebuild the path again since normsubpathitems
        # may become shorter than epsilon and/or skippedline may become
        # longer than epsilon
        normsubpathitems = self.normsubpathitems
        closed = self.closed
        skippedline = self.skippedline
        self.normsubpathitems = []
        self.closed = 0
        self.skippedline = None
        for pitem in normsubpathitems:
            self.append(pitem.transformed(trafo))
        if closed:
            self.close()
        elif skippedline is not None:
            self.append(skippedline.transformed(trafo))

    def transformed(self, trafo):
        """return sub path transformed according to trafo"""
        nnormsubpath = normsubpath(epsilon=self.epsilon)
        for pitem in self.normsubpathitems:
            nnormsubpath.append(pitem.transformed(trafo))
        if self.closed:
            nnormsubpath.close()
        elif self.skippedline is not None:
            nnormsubpath.append(skippedline.transformed(trafo))
        return nnormsubpath

    def outputPS(self, file):
        # if the normsubpath is closed, we must not output a normline at
        # the end
        if not self.normsubpathitems:
            return
        if self.closed and isinstance(self.normsubpathitems[-1], normline_pt):
            normsubpathitems = self.normsubpathitems[:-1]
        else:
            normsubpathitems = self.normsubpathitems
        if normsubpathitems:
            file.write("%g %g moveto\n" % self.atbegin_pt())
            for anormpathitem in normsubpathitems:
                anormpathitem.outputPS(file)
        if self.closed:
            file.write("closepath\n")

    def outputPDF(self, file):
        # if the normsubpath is closed, we must not output a normline at
        # the end
        if not self.normsubpathitems:
            return
        if self.closed and isinstance(self.normsubpathitems[-1], normline_pt):
            normsubpathitems = self.normsubpathitems[:-1]
        else:
            normsubpathitems = self.normsubpathitems
        if normsubpathitems:
            file.write("%f %f m\n" % self.atbegin_pt())
            for anormpathitem in normsubpathitems:
                anormpathitem.outputPDF(file)
        if self.closed:
            file.write("h\n")


################################################################################
# normpathparam class
################################################################################

class normpathparam:

    """ parameter of a certain point along a normpath """
    
    def __init__(self, normpath, normsubpathindex, normsubpathparam):
        self.normpath = normpath
        self.normsubpathindex = normsubpathindex
        self.normsubpathparam = normsubpathparam
        float(normsubpathparam)

    def __add__(self, other):
        if isinstance(other, normpathparam):
            assert self.normpath is other.normpath, "normpathparams have to belong to the same normpath"
            return self.normpath.arclentoparam_pt(self.normpath.paramtoarclen_pt(self) +
                                                  other.normpath.paramtoarclen_pt(other))
        else:
            return self.normpath.arclentoparam_pt(self.normpath.paramtoarclen_pt(self) + unit.topt(other))

    __radd__ = __add__

    def __sub__(self, other):
        if isinstance(other, normpathparam):
            assert self.normpath is other.normpath, "normpathparams have to belong to the same normpath"
            return self.normpath.arclentoparam_pt(self.normpath.paramtoarclen_pt(self) -
                                                  other.normpath.paramtoarclen_pt(other))
        else:
            return self.normpath.arclentoparam_pt(self.normpath.paramtoarclen_pt(self) - unit.topt(other))

    def __rsub__(self, other):
        # other has to be a length in this case
        return self.normpath.arclentoparam_pt(-self.normpath.paramtoarclen_pt(self) + unit.topt(other))
    
    def __mul__(self, factor):
        return self.normpath.arclentoparam_pt(self.normpath.paramtoarclen_pt(self) * factor)
    
    __rmul__ = __mul__

    def __div__(self, divisor):
        return self.normpath.arclentoparam_pt(self.normpath.paramtoarclen_pt(self) / divisor)

    def __neg__(self):
        return self.normpath.arclentoparam_pt(-self.normpath.paramtoarclen_pt(self))

    def __cmp__(self, other):
        if isinstance(other, normpathparam):
            assert self.normpath is other.normpath, "normpathparams have to belong to the same normpath"
            return cmp((self.normsubpathindex, self.normsubpathparam), (other.normsubpathindex, other.normsubpathparam))
        else:
            return cmp(self.normpath.paramtoarclen_pt(self), unit.topt(other))

    def arclen_pt(self):
        """ return arc length in pts corresponding to the normpathparam """
        return self.normpath.paramtoarclen_pt(self)

    def arclen(self):
        """ return arc length corresponding to the normpathparam """
        return self.normpath.paramtoarclen(self)


    
################################################################################
# normpath class
################################################################################

class normpath(base.canvasitem):

    """normalized path

    A normalized path consists of a list of normalized sub paths.

    """

    def __init__(self, normsubpaths=None):
        """ construct a normpath from another normpath passed as arg,
        a path or a list of normsubpaths. An accuracy of epsilon pts
        is used for numerical calculations.
        """
        if normsubpaths is None:
            self.normsubpaths = []
        else:
            self.normsubpaths = normsubpaths
            for subpath in normsubpaths:
                assert isinstance(subpath, normsubpath), "only list of normsubpath instances allowed"

    def __add__(self, other):
        result = normpath()
        result.normsubpaths = self.normsubpaths + other.normpath().normsubpaths
        return result

    def __getitem__(self, i):
        return self.normsubpaths[i]

    def __iadd__(self, other):
        self.normsubpaths += other.normpath().normsubpaths
        return self

    def __len__(self):
        return len(self.normsubpaths)

    def __str__(self):
        return "normpath(%s)" % ", ".join(map(str, self.normsubpaths))

    def _convertparams(self, params, convertmethod):
        """ Returns params with all non-normpathparam arguments converted
        by convertmethod """
        converttoparams = []
        convertparamindices = []
        for i, param in enumerate(params):
            if not isinstance(param, normpathparam):
                converttoparams.append(param)
                convertparamindices.append(i)
        if converttoparams:
            params = params[:]
            for i, param in zip(convertparamindices, convertmethod(converttoparams)):
                params[i] = param
        return params

    def _distributeparams(self, normpathparams):
        """Returns a dictionary mapping subpathindices to a tuple of a
        paramindices and subpathparams.

        subpathindex specifies a subpath containing one or several positions.
        paramindex specify the index of the normpathparam in the original list and
        subpathparam is the parameter value in the subpath.
        """

        result = {}
        for i, param in enumerate(normpathparams):
            assert param.normpath is self, "normpathparam has to belong to this path"
            result.setdefault(param.normsubpathindex, ([], []))
            result[param.normsubpathindex][0].append(i)
            result[param.normsubpathindex][1].append(param.normsubpathparam)
        return result

    def append(self, anormsubpath):
        if isinstance(anormsubpath, normsubpath):
            # the normsubpaths list can be appended by a normsubpath only
            self.normsubpaths.append(anormsubpath)
        else:
            # ... but we are kind and allow for regular path items as well
            # in order to make a normpath to behave more like a regular path

            for pathitem in anormsubpath._normalized(_pathcontext(self.normsubpaths[-1].atbegin_pt(),
                                                                  self.normsubpaths[-1].atend_pt())):
                if isinstance(pathitem, closepath):
                    self.normsubpaths[-1].close()
                elif isinstance(pathitem, moveto_pt):
                    self.normsubpaths.append(normsubpath([normline_pt(pathitem.x_pt, pathitem.y_pt,
                                                                   pathitem.x_pt, pathitem.y_pt)]))
                else:
                    self.normsubpaths[-1].append(pathitem)

    def arclen_pt(self):
        """returns total arc length of normpath in pts"""
        return sum([normsubpath.arclen_pt() for normsubpath in self.normsubpaths])

    def arclen(self):
        """returns total arc length of normpath"""
        return self.arclen_pt() * unit.t_pt

    def arclentoparam_pt(self, lengths_pt):
        """ returns the parameter values matching the given lengths """
        # work on a copy which is counted down to negative values
        lengths_pt = lengths_pt[:]
        results = [None] * len(lengths_pt)

        for normsubpathindex, normsubpath in enumerate(self.normsubpaths):
            params, arclen = normsubpath._arclentoparam_pt(lengths_pt)
            done = 1
            for i, result in enumerate(results):
                if results[i] is None:
                    lengths_pt[i] -= arclen
                    if lengths_pt[i] < 0 or normsubpathindex == len(self.normsubpaths) - 1:
                        # overwrite the results until the length has become negative
                        results[i] = normpathparam(self, normsubpathindex, params[i])
                    done = 0
            if done:
                break

        return results
    arclentoparam_pt = _valueorlistmethod(arclentoparam_pt)

    def arclentoparam(self, lengths):
        """ returns the parameter values matching the given lengths """
        return self.arclentoparam_pt([unit.topt(l) for l in lengths])
    arclentoparam = _valueorlistmethod(arclentoparam)

    def _at_pt(self, params):
        """return coordinates in pts of path at either parameter value param
        or arc length arclen.
        """

        result = [None] * len(params)
        for normsubpathindex, (indices, params) in self._distributeparams(params).items():
            for index, point_pt in zip(indices, self.normsubpaths[normsubpathindex].at_pt(params)):
                result[index] = point_pt
        return result

    def at_pt(self, params):
        """return coordinates of path (in pts) at either parameter value param
        or arc length arclen (in pts).
        """

        return self._at_pt(self._convertparams(params, self.arclentoparam_pt))
    at_pt = _valueorlistmethod(at_pt)

    def at(self, params):
        """return coordinates of path at either parameter value param
        or arc length arclen.
        """

        return [(x_pt * unit.t_pt, y_pt * unit.t_pt)
                for x_pt, y_pt in self._at_pt(self._convertparams(params, self.arclentoparam))]
    at = _valueorlistmethod(at)

    def atbegin_pt(self):
        """return coordinates of first point of first subpath in path (in pts)"""
        if self.normsubpaths:
            return self.normsubpaths[0].atbegin_pt()
        else:
            raise PathException("cannot return first point of empty path")

    def atbegin(self):
        """return coordinates of first point of first subpath in path"""
        x, y = self.atbegin_pt()
        return x * unit.t_pt, y * unit.t_pt

    def atend_pt(self):
        """return coordinates of last point of last subpath in path (in pts)"""
        if self.normsubpaths:
            return self.normsubpaths[-1].atend_pt()
        else:
            raise PathException("cannot return last point of empty path")

    def atend(self):
        """return coordinates of last point of last subpath in path"""
        x, y = self.atend_pt()
        return x * unit.t_pt, y * unit.t_pt

    def begin(self):
        """return param corresponding to begin of path"""
        if self.normsubpaths:
            return normpathparam(self, 0, 0)
        else:
            raise PathException("empty path")

    def bbox(self):
        abbox = None
        for normsubpath in self.normsubpaths:
            nbbox =  normsubpath.bbox()
            if abbox is None:
                abbox = nbbox
            elif nbbox:
                abbox += nbbox
        return abbox

    def _curveradius_pt(self, params):
        """Returns the curvature radius in pts (or None if infinite)
        at parameter param or arc length arclen.  This is the inverse
        of the curvature at this parameter

        Please note that this radius can be negative or positive,
        depending on the sign of the curvature"""

        result = [None] * len(params)
        for normsubpathindex, (indices, params) in self._distributeparams(params).items():
            for index, radius_pt in zip(indices, self.normsubpaths[normsubpathindex].curveradius_pt(params)):
                result[index] = radius_pt
        return result

    def curveradius_pt(self, params):
        """Returns the curvature radius in pts (or None if infinite)
        at parameter param or arc length arclen.  This is the inverse
        of the curvature at this parameter

        Please note that this radius can be negative or positive,
        depending on the sign of the curvature"""
        return self._curveradius_pt(self._convertparams(params, self.arclentoparam_pt))
    curveradius_pt = _valueorlistmethod(curveradius_pt)

    def curveradius(self, params):
        """Returns the curvature radius (or None if infinite) at
        parameter param or arc length arclen.  This is the inverse of
        the curvature at this parameter

        Please note that this radius can be negative or positive,
        depending on the sign of the curvature"""
        result = []
        for radius_pt in self._curveradius_pt(self._convertparams(params, self.arclentoparam)):
            if radius_pt is not None:
                result.append(radius_pt * unit.t_pt)
            else:
                result.append(None)
        return result
    curveradius = _valueorlistmethod(curveradius)

    def end(self):
        """return param corresponding to end of path"""
        if self.normsubpaths:
            return normpathparam(self, len(self)-1, len(self.normsubpaths[-1]))
        else:
            raise PathException("empty path")

    def extend(self, normsubpaths):
        for anormsubpath in normsubpaths:
            # use append to properly handle regular path items as well as normsubpaths
            self.append(anormsubpath)

    def join(self, other):
        if not self.normsubpaths:
            raise PathException("cannot join to end of empty path")
        if self.normsubpaths[-1].closed:
            raise PathException("cannot join to end of closed sub path")
        other = other.normpath()
        if not other.normsubpaths:
            raise PathException("cannot join empty path")

        # XXX insert connection line?
        self.normsubpaths[-1].normsubpathitems += other.normsubpaths[0].normsubpathitems
        self.normsubpaths += other.normsubpaths[1:]

    def joined(self, other):
        # NOTE we skip a deep copy for performance reasons
        result = normpath(self.normsubpaths)
        result.join(other)
        return result

    # << operator also designates joining
    __lshift__ = joined

    def intersect(self, other):
        """intersect self with other path

        returns a tuple of lists consisting of the parameter values
        of the intersection points of the corresponding normpath

        """
        other = other.normpath()
        
        # here we build up the result
        intersections = ([], [])

        # Intersect all normsubpaths of self with the normsubpaths of
        # other.
        for ia, normsubpath_a in enumerate(self.normsubpaths):
            for ib, normsubpath_b in enumerate(other.normsubpaths):
                for intersection in zip(*normsubpath_a.intersect(normsubpath_b)):
                    intersections[0].append(normpathparam(self, ia, intersection[0]))
                    intersections[1].append(normpathparam(other, ib, intersection[1]))
        return intersections

    def normpath(self):
        return self

    def paramtoarclen_pt(self, normpathparams):
        """returns the arc length corresponding to the normpathparams"""
        result = [None] * len(normpathparams)
        totalarclen_pt = 0
        distributeparams = self._distributeparams(normpathparams)
        for normsubpathindex in range(max(distributeparams.keys()) + 1):
            if distributeparams.has_key(normsubpathindex):
                indices, params = distributeparams[normsubpathindex]
                arclens_pt, normsubpatharclen_pt = self.normsubpaths[normsubpathindex]._paramtoarclen_pt(params)
                for index, arclen_pt in zip(indices, arclens_pt):
                    result[index] = totalarclen_pt + arclen_pt
                totalarclen_pt += normsubpatharclen_pt
            else:
                totalarclen_pt += self.normsubpaths[normsubpathindex].arclen_pt()
        return result
    paramtoarclen_pt = _valueorlistmethod(paramtoarclen_pt)

    def paramtoarclen(self, normpathparams):
        return [arclen_pt * unit.t_pt for arclen_pt in self.paramtoarclen_pt(normpathparams)]
    paramtoarclen = _valueorlistmethod(paramtoarclen)

    def reverse(self):
        """reverse path"""
        self.normsubpaths.reverse()
        for normsubpath in self.normsubpaths:
            normsubpath.reverse()

    def reversed(self):
        """return reversed path"""
        nnormpath = normpath()
        for i in range(len(self.normsubpaths)):
            nnormpath.normsubpaths.append(self.normsubpaths[-(i+1)].reversed())
        return nnormpath

    def _split(self, params):
        """split path at parameter values params and return list of normpaths

        Note that the params has to be sorted.
        """


        # check whether parameter list is really sorted
        sortedparams = list(params)
        sortedparams.sort()
        if sortedparams != list(params):
            raise ValueError("split parameter list params has to be sorted")

        distributeparams = self._distributeparams(params)

        # we construct this list of normpaths
        result = []

        # the currently built up normpath
        np = normpath()

        for index, subpath in enumerate(self.normsubpaths):
            if distributeparams.has_key(index):
                # we do not use the sorting information in distributeparams[index][0]
                splitnormsubpaths = subpath.split(distributeparams[index][1])
                np.normsubpaths.append(splitnormsubpaths[0])
                for normsubpath in splitnormsubpaths[1:]:
                    result.append(np)
                    np = normpath([normsubpath])
            else:
                np.normsubpaths.append(subpath)

        result.append(np)
        return result

    def split_pt(self, params):
        """split path at parameter values params and return a list of normpaths

        Note that the params has to be sorted..
        """
        try:
            for param in params:
                break
        except:
            params = [params]
        return self._split(self._convertparams(params, self.arclentoparam_pt))

    def split(self, params):
        """split path at parameter values params and return a list of normpaths

        Note that the params has to be sorted.
        """
        try:
            for param in params:
                break
        except:
            params = [params]
        return self._split(self._convertparams(params, self.arclentoparam))

    def _tangent(self, params, length=None):
        """return tangent vector of path at the parameter values params.
        
        If length is not None, the tangent vector will be scaled to
        the desired length.
        """
        result = [None] * len(params)
        tangenttemplate = line_pt(0, 0, 1, 0).normpath()
        for normsubpathindex, (indices, params) in self._distributeparams(params).items():
            for index, atrafo in zip(indices, self.normsubpaths[normsubpathindex].trafo(params)):
                tangentpath = tangenttemplate.transformed(atrafo)
                if length is not None:
                    sfactor = unit.topt(length)/tangentpath.arclen_pt()
                    tangentpath.transform(trafo.scale_pt(sfactor, sfactor, *tangentpath.atbegin_pt()))
                result[index] = tangentpath
        return result

    def tangent_pt(self, params, length=None):
        """return tangent vector of path at the parameter values params.
        
        If length is not None, the tangent vector will be scaled to
        the desired length.
        """

        return self._tangent(self._convertparams(params, self.arclentoparam_pt), length)
    tangent_pt = _valueorlistmethod(tangent_pt)

    def tangent(self, params, length=None):
        """return tangent vector of path at the parameter values params.
        
        If length is not None, the tangent vector will be scaled to
        the desired length.
        """

        return self._tangent(self._convertparams(params, self.arclentoparam), length)
    tangent = _valueorlistmethod(tangent)

    def transform(self, trafo):
        """transform path according to trafo"""
        for normsubpath in self.normsubpaths:
            normsubpath.transform(trafo)

    def transformed(self, trafo):
        """return path transformed according to trafo"""
        return normpath([normsubpath.transformed(trafo) for normsubpath in self.normsubpaths])

    def _trafo(self, params):
        """return transformation at parameter values param"""
        result = [None] * len(params)
        for normsubpathindex, (indices, params) in self._distributeparams(params).items():
            for index, trafo in zip(indices, self.normsubpaths[normsubpathindex].trafo(params)):
                result[index] = trafo
        return result

    def trafo_pt(self, params):
        """return transformation at parameter values param"""
        return self._trafo(self._convertparams(params, self.arclentoparam_pt))
    trafo_pt = _valueorlistmethod(trafo_pt)

    def trafo(self, params):
        """return transformation at parameter values param"""
        return self._trafo(self._convertparams(params, self.arclentoparam))
    trafo = _valueorlistmethod(trafo)

    def outputPS(self, file):
        for normsubpath in self.normsubpaths:
            normsubpath.outputPS(file)

    def outputPDF(self, file):
        for normsubpath in self.normsubpaths:
            normsubpath.outputPDF(file)
