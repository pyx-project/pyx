#rrrrrrr!/usr/bin/env python
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

# TODO: - glue -> glue & glued
#       - nocurrentpoint exception?
#       - correct bbox for curveto and bpathel
#         (maybe we still need the current bbox implementation (then maybe called
#          cbox = control box) for bpathel for the use during the
#          intersection of bpaths)

import copy, math, bisect
from math import cos, sin, pi
try:
    from math import radians, degrees
except ImportError:
    # fallback implementation for Python 2.1 and below
    def radians(x): return x*pi/180
    def degrees(x): return x*180/pi
import base, bbox, trafo, unit, helper

try:
    sum([])
except NameError:
    # fallback implementation for Python 2.2. and below
    def sum(list):
        return reduce(lambda x, y: x+y, list, 0)

try:
    enumerate([])
except NameError:
    # fallback implementation for Python 2.2. and below
    def enumerate(list):
        return zip(xrange(len(list)), list)
    
################################################################################
# Bezier helper functions
################################################################################

def _arctobcurve(x, y, r, phi1, phi2):
    """generate the best bpathel corresponding to an arc segment"""

    dphi=phi2-phi1

    if dphi==0: return None

    # the two endpoints should be clear 
    (x0, y0) = ( x+r*cos(phi1), y+r*sin(phi1) )
    (x3, y3) = ( x+r*cos(phi2), y+r*sin(phi2) )

    # optimal relative distance along tangent for second and third
    # control point
    l = r*4*(1-cos(dphi/2))/(3*sin(dphi/2))

    (x1, y1) = ( x0-l*sin(phi1), y0+l*cos(phi1) )
    (x2, y2) = ( x3+l*sin(phi2), y3-l*cos(phi2) )

    return normcurve(x0, y0, x1, y1, x2, y2, x3, y3)


def _arctobezierpath(x, y, r, phi1, phi2, dphimax=45):
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

    if r==0 or phi1-phi2==0: return []

    subdivisions = abs(int((1.0*(phi1-phi2))/dphimax))+1

    dphi=(1.0*(phi2-phi1))/subdivisions

    for i in range(subdivisions):
        apath.append(_arctobcurve(x, y, r, phi1+i*dphi, phi1+(i+1)*dphi))

    return apath


def _bcurvesIntersect(a, a_t0, a_t1, b, b_t0, b_t1, epsilon=1e-5):
    """ returns list of intersection points for list of bpathels """
    # XXX: unused, remove?

    bbox_a = a[0].bbox()
    for aa in a[1:]:
        bbox_a += aa.bbox()
    bbox_b = b[0].bbox()
    for bb in b[1:]:
        bbox_b += bb.bbox()

    if not bbox_a.intersects(bbox_b): return []

    if a_t0+1!=a_t1:
        a_tm = (a_t0+a_t1)/2
        aa = a[:a_tm-a_t0]
        ab = a[a_tm-a_t0:]

        if b_t0+1!=b_t1:
            b_tm = (b_t0+b_t1)/2
            ba = b[:b_tm-b_t0]
            bb = b[b_tm-b_t0:]

            return ( _bcurvesIntersect(aa, a_t0, a_tm,
                                       ba, b_t0, b_tm, epsilon) + 
                     _bcurvesIntersect(ab, a_tm, a_t1,
                                       ba, b_t0, b_tm, epsilon) + 
                     _bcurvesIntersect(aa, a_t0, a_tm,
                                       bb, b_tm, b_t1, epsilon) +
                     _bcurvesIntersect(ab, a_tm, a_t1,
                                       bb, b_tm, b_t1, epsilon) )
        else:
            return ( _bcurvesIntersect(aa, a_t0, a_tm,
                                       b, b_t0, b_t1, epsilon) +
                     _bcurvesIntersect(ab, a_tm, a_t1,
                                       b, b_t0, b_t1, epsilon) )
    else:
        if b_t0+1!=b_t1:
            b_tm = (b_t0+b_t1)/2
            ba = b[:b_tm-b_t0]
            bb = b[b_tm-b_t0:]

            return  ( _bcurvesIntersect(a, a_t0, a_t1,
                                       ba, b_t0, b_tm, epsilon) +
                      _bcurvesIntersect(a, a_t0, a_t1,
                                       bb, b_tm, b_t1, epsilon) )
        else:
            # no more subdivisions of either a or b
            # => intersect bpathel a with bpathel b
            assert len(a)==len(b)==1, "internal error"
            return _intersectnormcurves(a[0], a_t0, a_t1,
                                    b[0], b_t0, b_t1, epsilon)


#
# we define one exception
#

class PathException(Exception): pass

################################################################################
# _pathcontext: context during walk along path
################################################################################

class _pathcontext:

    """context during walk along path"""

    def __init__(self, currentpoint=None, currentsubpath=None):
        """ initialize context

        currentpoint:   position of current point
        currentsubpath: position of first point of current subpath

        """

        self.currentpoint = currentpoint
        self.currentsubpath = currentsubpath

################################################################################ 
# pathel: element of a PS style path 
################################################################################

class pathel(base.PSOp):

    """element of a PS style path"""

    def _updatecontext(self, context):
        """update context of during walk along pathel

        changes context in place
        """


    def _bbox(self, context):
        """calculate bounding box of pathel

        context: context of pathel

        returns bounding box of pathel (in given context)

        Important note: all coordinates in bbox, currentpoint, and 
        currrentsubpath have to be floats (in unit.topt)

        """

        pass

    def _normalized(self, context):
        """returns list of normalized version of pathel

        context: context of pathel

        returns list consisting of corresponding normalized pathels
        normline and normcurve as well as the two pathels moveto_pt and
        closepath

        """

        pass

    def outputPS(self, file):
        """write PS code corresponding to pathel to file"""
        pass

    def outputPDF(self, file):
        """write PDF code corresponding to pathel to file"""
        pass

#
# various pathels
#
# Each one comes in two variants:
#  - one which requires the coordinates to be already in pts (mainly
#    used for internal purposes)
#  - another which accepts arbitrary units

class closepath(pathel): 

    """Connect subpath back to its starting point"""

    def __str__(self):
        return "closepath"

    def _updatecontext(self, context):
        context.currentpoint = None
        context.currentsubpath = None

    def _bbox(self, context):
        x0, y0 = context.currentpoint
        x1, y1 = context.currentsubpath

        return bbox._bbox(min(x0, x1), min(y0, y1), 
                          max(x0, x1), max(y0, y1))

    def _normalized(self, context):
        return [closepath()]

    def outputPS(self, file):
        file.write("closepath\n")

    def outputPDF(self, file):
        file.write("h\n")


class moveto_pt(pathel):

    """Set current point to (x, y) (coordinates in pts)"""

    def __init__(self, x, y):
         self.x = x
         self.y = y

    def __str__(self):
        return "%g %g moveto" % (self.x, self.y)

    def _updatecontext(self, context):
        context.currentpoint = self.x, self.y
        context.currentsubpath = self.x, self.y

    def _bbox(self, context):
        return None

    def _normalized(self, context):
        return [moveto_pt(self.x, self.y)]

    def outputPS(self, file):
        file.write("%g %g moveto\n" % (self.x, self.y) )

    def outputPDF(self, file):
        file.write("%g %g m\n" % (self.x, self.y) )


class lineto_pt(pathel):

    """Append straight line to (x, y) (coordinates in pts)"""

    def __init__(self, x, y):
         self.x = x
         self.y = y

    def __str__(self):
        return "%g %g lineto" % (self.x, self.y)

    def _updatecontext(self, context):
        context.currentsubpath = context.currentsubpath or context.currentpoint
        context.currentpoint = self.x, self.y

    def _bbox(self, context):
        return bbox._bbox(min(context.currentpoint[0], self.x),
                          min(context.currentpoint[1], self.y), 
                          max(context.currentpoint[0], self.x),
                          max(context.currentpoint[1], self.y))

    def _normalized(self, context):
        return [normline(context.currentpoint[0], context.currentpoint[1], self.x, self.y)]

    def outputPS(self, file):
        file.write("%g %g lineto\n" % (self.x, self.y) )

    def outputPDF(self, file):
        file.write("%g %g l\n" % (self.x, self.y) )


class curveto_pt(pathel):

    """Append curveto (coordinates in pts)"""

    def __init__(self, x1, y1, x2, y2, x3, y3):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.x3 = x3
        self.y3 = y3

    def __str__(self):
        return "%g %g %g %g %g %g curveto" % (self.x1, self.y1,
                                              self.x2, self.y2,
                                              self.x3, self.y3)

    def _updatecontext(self, context):
        context.currentsubpath = context.currentsubpath or context.currentpoint
        context.currentpoint = self.x3, self.y3

    def _bbox(self, context):
        return bbox._bbox(min(context.currentpoint[0], self.x1, self.x2, self.x3),
                          min(context.currentpoint[1], self.y1, self.y2, self.y3),
                          max(context.currentpoint[0], self.x1, self.x2, self.x3),
                          max(context.currentpoint[1], self.y1, self.y2, self.y3))

    def _normalized(self, context):
        return [normcurve(context.currentpoint[0], context.currentpoint[1],
                          self.x1, self.y1,
                          self.x2, self.y2,
                          self.x3, self.y3)]

    def outputPS(self, file):
        file.write("%g %g %g %g %g %g curveto\n" % ( self.x1, self.y1,
                                                     self.x2, self.y2,
                                                     self.x3, self.y3 ) )

    def outputPDF(self, file):
        file.write("%g %g %g %g %g %g c\n" % ( self.x1, self.y1,
                                               self.x2, self.y2,
                                               self.x3, self.y3 ) )


class rmoveto_pt(pathel):

    """Perform relative moveto (coordinates in pts)"""

    def __init__(self, dx, dy):
         self.dx = dx
         self.dy = dy

    def _updatecontext(self, context):
        context.currentpoint = (context.currentpoint[0] + self.dx,
                                context.currentpoint[1] + self.dy)
        context.currentsubpath = context.currentpoint

    def _bbox(self, context):
        return None

    def _normalized(self, context):
        x = context.currentpoint[0]+self.dx
        y = context.currentpoint[1]+self.dy
        return [moveto_pt(x, y)]

    def outputPS(self, file):
        file.write("%g %g rmoveto\n" % (self.dx, self.dy) )

    # TODO: outputPDF


class rlineto_pt(pathel):

    """Perform relative lineto (coordinates in pts)"""

    def __init__(self, dx, dy):
         self.dx = dx
         self.dy = dy

    def _updatecontext(self, context):
        context.currentsubpath = context.currentsubpath or context.currentpoint
        context.currentpoint = (context.currentpoint[0]+self.dx,
                                context.currentpoint[1]+self.dy)

    def _bbox(self, context):
        x = context.currentpoint[0] + self.dx
        y = context.currentpoint[1] + self.dy
        return bbox._bbox(min(context.currentpoint[0], x),
                          min(context.currentpoint[1], y),
                          max(context.currentpoint[0], x),
                          max(context.currentpoint[1], y))

    def _normalized(self, context):
        x0 = context.currentpoint[0]
        y0 = context.currentpoint[1]
        return [normline(x0, y0, x0+self.dx, y0+self.dy)]

    def outputPS(self, file):
        file.write("%g %g rlineto\n" % (self.dx, self.dy) )

    # TODO: outputPDF


class rcurveto_pt(pathel):

    """Append rcurveto (coordinates in pts)"""

    def __init__(self, dx1, dy1, dx2, dy2, dx3, dy3):
        self.dx1 = dx1
        self.dy1 = dy1
        self.dx2 = dx2
        self.dy2 = dy2
        self.dx3 = dx3
        self.dy3 = dy3

    def outputPS(self, file):
        file.write("%g %g %g %g %g %g rcurveto\n" % ( self.dx1, self.dy1,
                                                    self.dx2, self.dy2,
                                                    self.dx3, self.dy3 ) )

    # TODO: outputPDF

    def _updatecontext(self, context):
        x3 = context.currentpoint[0]+self.dx3
        y3 = context.currentpoint[1]+self.dy3

        context.currentsubpath = context.currentsubpath or context.currentpoint
        context.currentpoint = x3, y3


    def _bbox(self, context):
        x1 = context.currentpoint[0]+self.dx1
        y1 = context.currentpoint[1]+self.dy1
        x2 = context.currentpoint[0]+self.dx2
        y2 = context.currentpoint[1]+self.dy2
        x3 = context.currentpoint[0]+self.dx3
        y3 = context.currentpoint[1]+self.dy3
        return bbox._bbox(min(context.currentpoint[0], x1, x2, x3),
                          min(context.currentpoint[1], y1, y2, y3),
                          max(context.currentpoint[0], x1, x2, x3),
                          max(context.currentpoint[1], y1, y2, y3))

    def _normalized(self, context):
        x0 = context.currentpoint[0]
        y0 = context.currentpoint[1]
        return [normcurve(x0, y0, x0+self.dx1, y0+self.dy1, x0+self.dx2, y0+self.dy2, x0+self.dx3, y0+self.dy3)]


class arc_pt(pathel):

    """Append counterclockwise arc (coordinates in pts)"""

    def __init__(self, x, y, r, angle1, angle2):
        self.x = x
        self.y = y
        self.r = r
        self.angle1 = angle1
        self.angle2 = angle2

    def _sarc(self):
        """Return starting point of arc segment"""
        return (self.x+self.r*cos(radians(self.angle1)),
                self.y+self.r*sin(radians(self.angle1)))

    def _earc(self):
        """Return end point of arc segment"""
        return (self.x+self.r*cos(radians(self.angle2)),
                self.y+self.r*sin(radians(self.angle2)))

    def _updatecontext(self, context):
        if context.currentpoint:
            context.currentsubpath = context.currentsubpath or context.currentpoint
        else:
            # we assert that currentsubpath is also None
            context.currentsubpath = self._sarc()

        context.currentpoint = self._earc()

    def _bbox(self, context):
        phi1 = radians(self.angle1)
        phi2 = radians(self.angle2)

        # starting end end point of arc segment
        sarcx, sarcy = self._sarc()
        earcx, earcy = self._earc()

        # Now, we have to determine the corners of the bbox for the
        # arc segment, i.e. global maxima/mimima of cos(phi) and sin(phi)
        # in the interval [phi1, phi2]. These can either be located
        # on the borders of this interval or in the interior.

        if phi2<phi1:
            # guarantee that phi2>phi1
            phi2 = phi2 + (math.floor((phi1-phi2)/(2*pi))+1)*2*pi

        # next minimum of cos(phi) looking from phi1 in counterclockwise
        # direction: 2*pi*floor((phi1-pi)/(2*pi)) + 3*pi

        if phi2<(2*math.floor((phi1-pi)/(2*pi))+3)*pi:
            minarcx = min(sarcx, earcx)
        else:
            minarcx = self.x-self.r

        # next minimum of sin(phi) looking from phi1 in counterclockwise
        # direction: 2*pi*floor((phi1-3*pi/2)/(2*pi)) + 7/2*pi

        if phi2<(2*math.floor((phi1-3.0*pi/2)/(2*pi))+7.0/2)*pi:
            minarcy = min(sarcy, earcy)
        else:
            minarcy = self.y-self.r

        # next maximum of cos(phi) looking from phi1 in counterclockwise 
        # direction: 2*pi*floor((phi1)/(2*pi))+2*pi

        if phi2<(2*math.floor((phi1)/(2*pi))+2)*pi:
            maxarcx = max(sarcx, earcx)
        else:
            maxarcx = self.x+self.r

        # next maximum of sin(phi) looking from phi1 in counterclockwise 
        # direction: 2*pi*floor((phi1-pi/2)/(2*pi)) + 1/2*pi

        if phi2<(2*math.floor((phi1-pi/2)/(2*pi))+5.0/2)*pi:
            maxarcy = max(sarcy, earcy)
        else:
            maxarcy = self.y+self.r

        # Finally, we are able to construct the bbox for the arc segment.
        # Note that if there is a currentpoint defined, we also
        # have to include the straight line from this point
        # to the first point of the arc segment

        if context.currentpoint:
            return (bbox._bbox(min(context.currentpoint[0], sarcx),
                              min(context.currentpoint[1], sarcy),
                              max(context.currentpoint[0], sarcx),
                              max(context.currentpoint[1], sarcy)) +
                    bbox._bbox(minarcx, minarcy, maxarcx, maxarcy)
                    )
        else:
            return  bbox._bbox(minarcx, minarcy, maxarcx, maxarcy)

    def _normalized(self, context):
        # get starting and end point of arc segment and bpath corresponding to arc
        sarcx, sarcy = self._sarc()
        earcx, earcy = self._earc()
        barc = _arctobezierpath(self.x, self.y, self.r, self.angle1, self.angle2)

        # convert to list of curvetos omitting movetos
        nbarc = []

        for bpathel in barc:
            nbarc.append(normcurve(bpathel.x0, bpathel.y0,
                                   bpathel.x1, bpathel.y1,
                                   bpathel.x2, bpathel.y2,
                                   bpathel.x3, bpathel.y3))

        # Note that if there is a currentpoint defined, we also
        # have to include the straight line from this point
        # to the first point of the arc segment.
        # Otherwise, we have to add a moveto at the beginning
        if context.currentpoint:
            return [normline(context.currentpoint[0], context.currentpoint[1], sarcx, sarcy)] + nbarc
        else:
            return nbarc


    def outputPS(self, file):
        file.write("%g %g %g %g %g arc\n" % ( self.x, self.y,
                                            self.r,
                                            self.angle1,
                                            self.angle2 ) )

    # TODO: outputPDF


class arcn_pt(pathel):

    """Append clockwise arc (coordinates in pts)"""

    def __init__(self, x, y, r, angle1, angle2):
        self.x = x
        self.y = y
        self.r = r
        self.angle1 = angle1
        self.angle2 = angle2

    def _sarc(self):
        """Return starting point of arc segment"""
        return (self.x+self.r*cos(radians(self.angle1)),
                self.y+self.r*sin(radians(self.angle1)))

    def _earc(self):
        """Return end point of arc segment"""
        return (self.x+self.r*cos(radians(self.angle2)),
                self.y+self.r*sin(radians(self.angle2)))

    def _updatecontext(self, context):
        if context.currentpoint:
            context.currentsubpath = context.currentsubpath or context.currentpoint
        else:  # we assert that currentsubpath is also None
            context.currentsubpath = self._sarc()

        context.currentpoint = self._earc()

    def _bbox(self, context):
        # in principle, we obtain bbox of an arcn element from 
        # the bounding box of the corrsponding arc element with
        # angle1 and angle2 interchanged. Though, we have to be carefull
        # with the straight line segment, which is added if currentpoint 
        # is defined.

        # Hence, we first compute the bbox of the arc without this line:

        a = arc_pt(self.x, self.y, self.r, 
                 self.angle2, 
                 self.angle1)

        sarc = self._sarc()
        arcbb = a._bbox(_pathcontext())

        # Then, we repeat the logic from arc.bbox, but with interchanged
        # start and end points of the arc

        if context.currentpoint:
            return  bbox._bbox(min(context.currentpoint[0], sarc[0]),
                               min(context.currentpoint[1], sarc[1]),
                               max(context.currentpoint[0], sarc[0]),
                               max(context.currentpoint[1], sarc[1]))+ arcbb
        else:
            return arcbb

    def _normalized(self, context):
        # get starting and end point of arc segment and bpath corresponding to arc
        sarcx, sarcy = self._sarc()
        earcx, earcy = self._earc()
        barc = _arctobezierpath(self.x, self.y, self.r, self.angle2, self.angle1)
        barc.reverse()

        # convert to list of curvetos omitting movetos
        nbarc = []

        for bpathel in barc:
            nbarc.append(normcurve(bpathel.x3, bpathel.y3,
                                   bpathel.x2, bpathel.y2,
                                   bpathel.x1, bpathel.y1,
                                   bpathel.x0, bpathel.y0))

        # Note that if there is a currentpoint defined, we also
        # have to include the straight line from this point
        # to the first point of the arc segment.
        # Otherwise, we have to add a moveto at the beginning
        if context.currentpoint:
            return [normline(context.currentpoint[0], context.currentpoint[1], sarcx, sarcy)] + nbarc
        else:
            return nbarc


    def outputPS(self, file):
        file.write("%g %g %g %g %g arcn\n" % ( self.x, self.y,
                                             self.r,
                                             self.angle1,
                                             self.angle2 ) )

    # TODO: outputPDF


class arct_pt(pathel):

    """Append tangent arc (coordinates in pts)"""

    def __init__(self, x1, y1, x2, y2, r):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.r  = r

    def outputPS(self, file):
        file.write("%g %g %g %g %g arct\n" % ( self.x1, self.y1,
                                             self.x2, self.y2,
                                             self.r ) )

    # TODO: outputPDF

    def _path(self, currentpoint, currentsubpath):
        """returns new currentpoint, currentsubpath and path consisting
        of arc and/or line which corresponds to arct

        this is a helper routine for _bbox and _normalized, which both need
        this path. Note: we don't want to calculate the bbox from a bpath

        """

        # direction and length of tangent 1
        dx1  = currentpoint[0]-self.x1
        dy1  = currentpoint[1]-self.y1
        l1   = math.sqrt(dx1*dx1+dy1*dy1)

        # direction and length of tangent 2
        dx2  = self.x2-self.x1
        dy2  = self.y2-self.y1
        l2   = math.sqrt(dx2*dx2+dy2*dy2)

        # intersection angle between two tangents
        alpha = math.acos((dx1*dx2+dy1*dy2)/(l1*l2))

        if math.fabs(sin(alpha))>=1e-15 and 1.0+self.r!=1.0:
            cotalpha2 = 1.0/math.tan(alpha/2)

            # two tangent points
            xt1 = self.x1+dx1*self.r*cotalpha2/l1
            yt1 = self.y1+dy1*self.r*cotalpha2/l1
            xt2 = self.x1+dx2*self.r*cotalpha2/l2
            yt2 = self.y1+dy2*self.r*cotalpha2/l2

            # direction of center of arc 
            rx = self.x1-0.5*(xt1+xt2)
            ry = self.y1-0.5*(yt1+yt2)
            lr = math.sqrt(rx*rx+ry*ry)

            # angle around which arc is centered

            if rx==0:
                phi=90
            elif rx>0:
                phi = degrees(math.atan(ry/rx))
            else:
                phi = degrees(math.atan(rx/ry))+180

            # half angular width of arc 
            deltaphi = 90*(1-alpha/pi)

            # center position of arc
            mx = self.x1-rx*self.r/(lr*sin(alpha/2))
            my = self.y1-ry*self.r/(lr*sin(alpha/2))

            # now we are in the position to construct the path
            p = path(moveto_pt(*currentpoint))

            if phi<0:
                p.append(arc_pt(mx, my, self.r, phi-deltaphi, phi+deltaphi))
            else:
                p.append(arcn_pt(mx, my, self.r, phi+deltaphi, phi-deltaphi))

            return ( (xt2, yt2) ,
                     currentsubpath or (xt2, yt2),
                     p )

        else:
            # we need no arc, so just return a straight line to currentpoint to x1, y1
            return  ( (self.x1, self.y1),
                      currentsubpath or (self.x1, self.y1),
                      line_pt(currentpoint[0], currentpoint[1], self.x1, self.y1) )

    def _updatecontext(self, context):
        r = self._path(context.currentpoint,
                       context.currentsubpath)

        context.currentpoint, context.currentsubpath = r[:2]

    def _bbox(self, context):
        return self._path(context.currentpoint,
                          context.currentsubpath)[2].bbox()

    def _normalized(self, context):
        # XXX TODO
        return normpath(self._path(context.currentpoint,
                                   context.currentsubpath)[2]).subpaths[0].normpathels

#
# now the pathels that convert from user coordinates to pts
#

class moveto(moveto_pt):

    """Set current point to (x, y)"""

    def __init__(self, x, y):
         moveto_pt.__init__(self, unit.topt(x), unit.topt(y))


class lineto(lineto_pt):

    """Append straight line to (x, y)"""

    def __init__(self, x, y):
        lineto_pt.__init__(self, unit.topt(x), unit.topt(y))


class curveto(curveto_pt):

    """Append curveto"""

    def __init__(self, x1, y1, x2, y2, x3, y3):
        curveto_pt.__init__(self,
                          unit.topt(x1), unit.topt(y1),
                          unit.topt(x2), unit.topt(y2),
                          unit.topt(x3), unit.topt(y3))

class rmoveto(rmoveto_pt):

    """Perform relative moveto"""

    def __init__(self, dx, dy):
        rmoveto_pt.__init__(self, unit.topt(dx), unit.topt(dy))


class rlineto(rlineto_pt):

    """Perform relative lineto"""

    def __init__(self, dx, dy):
        rlineto_pt.__init__(self, unit.topt(dx), unit.topt(dy))


class rcurveto(rcurveto_pt):

    """Append rcurveto"""

    def __init__(self, dx1, dy1, dx2, dy2, dx3, dy3):
        rcurveto_pt.__init__(self,
                           unit.topt(dx1), unit.topt(dy1),
                           unit.topt(dx2), unit.topt(dy2),
                           unit.topt(dx3), unit.topt(dy3))


class arcn(arcn_pt):

    """Append clockwise arc"""

    def __init__(self, x, y, r, angle1, angle2):
        arcn_pt.__init__(self, 
                       unit.topt(x), unit.topt(y), unit.topt(r), 
                       angle1, angle2)


class arc(arc_pt):

    """Append counterclockwise arc"""

    def __init__(self, x, y, r, angle1, angle2):
        arc_pt.__init__(self, unit.topt(x), unit.topt(y), unit.topt(r), 
                      angle1, angle2)


class arct(arct_pt):

    """Append tangent arc"""

    def __init__(self, x1, y1, x2, y2, r):
        arct_pt.__init__(self, unit.topt(x1), unit.topt(y1),
                             unit.topt(x2), unit.topt(y2),
                             unit.topt(r))

#
# "combined" pathels provided for performance reasons
#

class multilineto_pt(pathel):

    """Perform multiple linetos (coordinates in pts)"""

    def __init__(self, points):
         self.points = points

    def _updatecontext(self, context):
        context.currentsubpath = context.currentsubpath or context.currentpoint
        context.currentpoint = self.points[-1]

    def _bbox(self, context):
        xs = [point[0] for point in self.points]
        ys = [point[1] for point in self.points]
        return bbox._bbox(min(context.currentpoint[0], *xs),
                          min(context.currentpoint[1], *ys),
                          max(context.currentpoint[0], *xs),
                          max(context.currentpoint[1], *ys))

    def _normalized(self, context):
        result = []
        x0, y0 = context.currentpoint
        for x, y in self.points:
            result.append(normline(x0, y0, x, y))
            x0, y0 = x, y
        return result

    def outputPS(self, file):
        for x, y in self.points:
            file.write("%g %g lineto\n" % (x, y) )

    def outputPDF(self, file):
        for x, y in self.points:
            file.write("%g %g l\n" % (x, y) )


class multicurveto_pt(pathel):

    """Perform multiple curvetos (coordinates in pts)"""

    def __init__(self, points):
         self.points = points

    def _updatecontext(self, context):
        context.currentsubpath = context.currentsubpath or context.currentpoint
        context.currentpoint = self.points[-1]

    def _bbox(self, context):
        xs = [point[0] for point in self.points] + [point[2] for point in self.points] + [point[2] for point in self.points]
        ys = [point[1] for point in self.points] + [point[3] for point in self.points] + [point[5] for point in self.points]
        return bbox._bbox(min(context.currentpoint[0], *xs),
                          min(context.currentpoint[1], *ys),
                          max(context.currentpoint[0], *xs),
                          max(context.currentpoint[1], *ys))

    def _normalized(self, context):
        result = []
        x0, y0 = context.currentpoint
        for point in self.points:
            result.append(normcurve(x0, y0, *point))
            x0, y0 = point[4:]
        return result

    def outputPS(self, file):
        for point in self.points:
            file.write("%g %g %g %g %g %g curveto\n" % tuple(point))

    def outputPDF(self, file):
        for point in self.points:
            file.write("%g %g %g %g %g %g c\n" % tuple(point))


################################################################################
# path: PS style path
################################################################################

class path(base.PSCmd):

    """PS style path"""

    def __init__(self, *args):
        if len(args)==1 and isinstance(args[0], path):
            self.path = args[0].path
        else:
            self.path = list(args)

    def __add__(self, other):
        return path(*(self.path+other.path))

    def __iadd__(self, other):
        self.path += other.path
        return self

    def __getitem__(self, i):
        return self.path[i]

    def __len__(self):
        return len(self.path)

    def append(self, pathel):
        self.path.append(pathel)

    def arclen_pt(self, epsilon=1e-5):
        """returns total arc length of path in pts with accuracy epsilon"""
        return normpath(self).arclen_pt(epsilon)

    def arclen(self, epsilon=1e-5):
        """returns total arc length of path with accuracy epsilon"""
        return normpath(self).arclen(epsilon)

    def arclentoparam(self, lengths, epsilon=1e-5):
        """returns the parameter value(s) matching the given length(s)"""
        return normpath(self).arclentoparam(lengths, epsilon)

    def at_pt(self, t):
        """return coordinates in pts of corresponding normpath at parameter value t"""
        return normpath(self).at_pt(t)

    def at(self, t):
        """return coordinates of corresponding normpath at parameter value t"""
        return normpath(self).at(t)

    def bbox(self):
        context = _pathcontext()
        abbox = None

        for pel in self.path:
            nbbox =  pel._bbox(context)
            pel._updatecontext(context)
            if abbox is None:
                abbox = nbbox
            elif nbbox: 
                abbox += nbbox

        return abbox

    def begin_pt(self):
        """return coordinates of first point of first subpath in path (in pts)"""
        return normpath(self).begin_pt()

    def begin(self):
        """return coordinates of first point of first subpath in path"""
        return normpath(self).begin()

    def end_pt(self):
        """return coordinates of last point of last subpath in path (in pts)"""
        return normpath(self).end_pt()

    def end(self):
        """return coordinates of last point of last subpath in path"""
        return normpath(self).end()

    def glue(self, other):
        """return path consisting of self and other glued together"""
        return normpath(self).glue(other)

    # << operator also designates glueing
    __lshift__ = glue

    def intersect(self, other, epsilon=1e-5):
        """intersect normpath corresponding to self with other path"""
        return normpath(self).intersect(other, epsilon)

    def range(self):
        """return maximal value for parameter value t for corr. normpath"""
        return normpath(self).range()

    def reversed(self):
        """return reversed path"""
        return normpath(self).reversed()

    def split(self, parameters):
        """return corresponding normpaths split at parameter value t"""
        return normpath(self).split(parameters)

    def tangent(self, t, length=None):
        """return tangent vector at parameter value t of corr. normpath"""
        return normpath(self).tangent(t, length)

    def transformed(self, trafo):
        """return transformed path"""
        return normpath(self).transformed(trafo)

    def outputPS(self, file):
        if not (isinstance(self.path[0], moveto_pt) or
                isinstance(self.path[0], arc_pt) or
                isinstance(self.path[0], arcn_pt)):
            raise PathException("first path element must be either moveto, arc, or arcn")
        for pel in self.path:
            pel.outputPS(file)

    def outputPDF(self, file):
        if not (isinstance(self.path[0], moveto_pt) or
                isinstance(self.path[0], arc_pt) or # outputPDF
                isinstance(self.path[0], arcn_pt)): # outputPDF
            raise PathException("first path element must be either moveto, arc, or arcn")
        for pel in self.path:
            pel.outputPDF(file)

################################################################################
# normpath and corresponding classes
################################################################################

# two helper functions for the intersection of normpathels

def _intersectnormcurves(a, a_t0, a_t1, b, b_t0, b_t1, epsilon=1e-5):
    """intersect two bpathels

    a and b are bpathels with parameter ranges [a_t0, a_t1],
    respectively [b_t0, b_t1].
    epsilon determines when the bpathels are assumed to be straight

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

            a_deltax = a.x3 - a.x0
            a_deltay = a.y3 - a.y0
            b_deltax = b.x3 - b.x0
            b_deltay = b.y3 - b.y0

            det = b_deltax*a_deltay - b_deltay*a_deltax

            ba_deltax0 = b.x0 - a.x0
            ba_deltay0 = b.y0 - a.y0

            try:
                a_t = ( b_deltax*ba_deltay0 - b_deltay*ba_deltax0)/det
                b_t = ( a_deltax*ba_deltay0 - a_deltay*ba_deltax0)/det
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

    a_deltax = a.x1 - a.x0
    a_deltay = a.y1 - a.y0
    b_deltax = b.x1 - b.x0
    b_deltay = b.y1 - b.y0

    det = b_deltax*a_deltay - b_deltay*a_deltax

    ba_deltax0 = b.x0 - a.x0
    ba_deltay0 = b.y0 - a.y0

    try:
        a_t = ( b_deltax*ba_deltay0 - b_deltay*ba_deltax0)/det
        b_t = ( a_deltax*ba_deltay0 - a_deltay*ba_deltax0)/det
    except ArithmeticError:
        return []

    # check for intersections out of bound
    if not (0<=a_t<=1 and 0<=b_t<=1): return []

    # return parameters of the intersection
    return [( a_t, b_t)]




#
# normpathel: normalized element
#

class normpathel:

    """element of a normalized sub path"""

    def at_pt(self, t):
        """returns coordinates of point in pts at parameter t (0<=t<=1) """
        pass

    def arclen_pt(self, epsilon=1e-5):
        """returns arc length of normpathel in pts with given accuracy epsilon"""
        pass

    def bbox(self):
        """return bounding box of normpathel"""
        pass

    def intersect(self, other, epsilon=1e-5):
        """intersect self with other normpathel"""
        pass

    def _arclentoparam_pt(self, lengths, epsilon=1e-5):
        """returns tuple (t,l) with
          t the parameter where the arclen of normpathel is length and
          l the total arclen

        length:  length (in pts) to find the parameter for
        epsilon: epsilon controls the accuracy for calculation of the
                 length of the Bezier elements
        """
        # Note: _arclentoparam returns both, parameters and total lengths
        # while  arclentoparam returns only parameters
        pass

    def reversed(self):
        """return reversed normpathel"""
        pass

    def split(self, parameters):
        """splits normpathel

        parameters: list of parameter values (0<=t<=1) at which to split

        returns None or list of tuple of normpathels corresponding to 
        the orginal normpathel.

        """

        pass

    def tangent_pt(self, t):
        """returns tangent vector of normpathel in pts at parameter t (0<=t<=1)"""
        pass

    def transformed(self, trafo):
        """return transformed normpathel according to trafo"""
        pass

    def outputPS(self, file):
        """write PS code corresponding to normpathel to file"""
        pass

    def outputPS(self, file):
        """write PDF code corresponding to normpathel to file"""
        pass

#
# there are only two normpathels: normline and normcurve
#

class normline(normpathel):

    """Straight line from (x0, y0) to (x1, y1) (coordinates in pts)"""

    def __init__(self, x0, y0, x1, y1):
         self.x0 = x0
         self.y0 = y0
         self.x1 = x1
         self.y1 = y1

    def __str__(self):
        return "normline(%g, %g, %g, %g)" % (self.x0, self.y0, self.x1, self.y1)

    def _normcurve(self):
        """ return self as equivalent normcurve """
        xa = self.x0+(self.x1-self.x0)/3.0
        ya = self.y0+(self.y1-self.y0)/3.0
        xb = self.x0+2.0*(self.x1-self.x0)/3.0
        yb = self.y0+2.0*(self.y1-self.y0)/3.0
        return normcurve(self.x0, self.y0, xa, ya, xb, yb, self.x1, self.y1)

    def arclen_pt(self,  epsilon=1e-5):
        return math.sqrt((self.x0-self.x1)*(self.x0-self.x1)+(self.y0-self.y1)*(self.y0-self.y1))
    
    def at_pt(self, t):
        return (self.x0+(self.x1-self.x0)*t, self.y0+(self.y1-self.y0)*t)

    def bbox(self):
        return bbox._bbox(min(self.x0, self.x1), min(self.y0, self.y1), 
                          max(self.x0, self.x1), max(self.y0, self.y1))

    def begin_pt(self):
        return self.x0, self.y0

    def end_pt(self):
        return self.x1, self.y1

    def intersect(self, other, epsilon=1e-5):
	if isinstance(other, normline):
            return _intersectnormlines(self, other)
        else:
            return  _intersectnormcurves(self._normcurve(), 0, 1, other, 0, 1, epsilon)

    def _arclentoparam_pt(self, lengths, epsilon=1e-5):
        l = self.arclen_pt(epsilon)
        return ([max(min(1.0*length/l,1),0) for length in lengths], l)

    def reverse(self):
        self.x0, self.y0, self.x1, self.y1 = self.x1, self.y1, self.x0, self.y0

    def reversed(self):
        return normline(self.x1, self.y1, self.x0, self.y0)

    def split(self, parameters):
        x0, y0 = self.x0, self.y0
        x1, y1 = self.x1, self.y1
        if parameters:
            xl, yl = x0, y0
            result = []

            if parameters[0] == 0:
                result.append(None)
                parameters = parameters[1:]

            if parameters:
                for t in parameters:
                    xs, ys = x0 + (x1-x0)*t, y0 + (y1-y0)*t
                    result.append(normline(xl, yl, xs, ys))
                    xl, yl = xs, ys

                if parameters[-1]!=1:
                    result.append(normline(xs, ys, x1, y1))
                else:
                    result.append(None)
            else:
                result.append(normline(x0, y0, x1, y1))
        else:
            result = []
        return result

    def tangent_pt(self, t):
        return (self.x1-self.x0, self.y1-self.y0)

    def transformed(self, trafo):
        return normline(*(trafo._apply(self.x0, self.y0) + trafo._apply(self.x1, self.y1)))

    def outputPS(self, file):
        file.write("%g %g lineto\n" % (self.x1, self.y1))

    def outputPDF(self, file):
        file.write("%g %g l\n" % (self.x1, self.y1))


class normcurve(normpathel):

    """Bezier curve with control points x0, y0, x1, y1, x2, y2, x3, y3 (coordinates in pts)"""

    def __init__(self, x0, y0, x1, y1, x2, y2, x3, y3):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.x3 = x3
        self.y3 = y3

    def __str__(self):
        return "normcurve(%g, %g, %g, %g, %g, %g, %g, %g)" % (self.x0, self.y0, self.x1, self.y1,
                                                              self.x2, self.y2, self.x3, self.y3)

    def arclen_pt(self, epsilon=1e-5):
        """computes arclen of bpathel in pts using successive midpoint split"""
        if self.isstraight(epsilon):
            return math.sqrt((self.x3-self.x0)*(self.x3-self.x0)+
                             (self.y3-self.y0)*(self.y3-self.y0))
        else:
            (a, b) = self.midpointsplit()
            return a.arclen_pt(epsilon) + b.arclen_pt(epsilon)

    def at_pt(self, t):
        xt = (  (-self.x0+3*self.x1-3*self.x2+self.x3)*t*t*t +
               (3*self.x0-6*self.x1+3*self.x2        )*t*t +
              (-3*self.x0+3*self.x1                  )*t +
              self.x0)
        yt = (  (-self.y0+3*self.y1-3*self.y2+self.y3)*t*t*t +
               (3*self.y0-6*self.y1+3*self.y2        )*t*t +
              (-3*self.y0+3*self.y1                  )*t +
              self.y0)
        return (xt, yt)

    def bbox(self):
        return bbox._bbox(min(self.x0, self.x1, self.x2, self.x3),
                          min(self.y0, self.y1, self.y2, self.y3),
                          max(self.x0, self.x1, self.x2, self.x3),
                          max(self.y0, self.y1, self.y2, self.y3))

    def begin_pt(self):
        return self.x0, self.y0

    def end_pt(self):
        return self.x3, self.y3

    def intersect(self, other, epsilon=1e-5):
	if isinstance(other, normline):
            return  _intersectnormcurves(self, 0, 1, other._normcurve(), 0, 1, epsilon)
        else:
            return  _intersectnormcurves(self, 0, 1, other, 0, 1, epsilon)


    def isstraight(self, epsilon=1e-5):
        """check wheter the normcurve is approximately straight"""

        # just check, whether the modulus of the difference between
        # the length of the control polygon
        # (i.e. |P1-P0|+|P2-P1|+|P3-P2|) and the length of the
        # straight line between starting and ending point of the
        # normcurve (i.e. |P3-P1|) is smaller the epsilon
        return abs(math.sqrt((self.x1-self.x0)*(self.x1-self.x0)+
                             (self.y1-self.y0)*(self.y1-self.y0)) +
                   math.sqrt((self.x2-self.x1)*(self.x2-self.x1)+
                             (self.y2-self.y1)*(self.y2-self.y1)) +
                   math.sqrt((self.x3-self.x2)*(self.x3-self.x2)+
                             (self.y3-self.y2)*(self.y3-self.y2)) -
                   math.sqrt((self.x3-self.x0)*(self.x3-self.x0)+
                             (self.y3-self.y0)*(self.y3-self.y0)))<epsilon

    def _arclentoparam_pt(self, lengths, epsilon=1e-5):
        return self._normcurve()._arclentoparam_pt(lengths, epsilon)

    def midpointsplit(self):
        """splits bpathel at midpoint returning bpath with two bpathels"""

        # for efficiency reason, we do not use self.split(0.5)!

        # first, we have to calculate the  midpoints between adjacent
        # control points
        x01 = 0.5*(self.x0+self.x1)
        y01 = 0.5*(self.y0+self.y1)
        x12 = 0.5*(self.x1+self.x2)
        y12 = 0.5*(self.y1+self.y2)
        x23 = 0.5*(self.x2+self.x3)
        y23 = 0.5*(self.y2+self.y3)

        # In the next iterative step, we need the midpoints between 01 and 12
        # and between 12 and 23 
        x01_12 = 0.5*(x01+x12)
        y01_12 = 0.5*(y01+y12)
        x12_23 = 0.5*(x12+x23)
        y12_23 = 0.5*(y12+y23)

        # Finally the midpoint is given by
        xmidpoint = 0.5*(x01_12+x12_23)
        ymidpoint = 0.5*(y01_12+y12_23)

        return (normcurve(self.x0, self.y0,
                          x01, y01,
                          x01_12, y01_12,
                          xmidpoint, ymidpoint),
                normcurve(xmidpoint, ymidpoint,
                          x12_23, y12_23,
                          x23, y23,
                          self.x3, self.y3))

    def reverse(self):
        self.x0, self.y0, self.x1, self.y1, self.x2, self.y2, self.x3, self.y3 = \
        self.x3, self.y3, self.x2, self.y2, self.x1, self.y1, self.x0, self.y0

    def reversed(self):
        return normcurve(self.x3, self.y3, self.x2, self.y2, self.x1, self.y1, self.x0, self.y0)

    def seglengths(self, paraminterval, epsilon=1e-5):
        """returns the list of segment line lengths (in pts) of the bpathel
           together with the length of the parameterinterval"""

        # lower and upper bounds for the arclen
        lowerlen = \
            math.sqrt((self.x3-self.x0)*(self.x3-self.x0) + (self.y3-self.y0)*(self.y3-self.y0))
        upperlen = \
            math.sqrt((self.x1-self.x0)*(self.x1-self.x0) + (self.y1-self.y0)*(self.y1-self.y0)) + \
            math.sqrt((self.x2-self.x1)*(self.x2-self.x1) + (self.y2-self.y1)*(self.y2-self.y1)) + \
            math.sqrt((self.x3-self.x2)*(self.x3-self.x2) + (self.y3-self.y2)*(self.y3-self.y2))

        # instead of isstraight method:
        if abs(upperlen-lowerlen)<epsilon:
            return [( 0.5*(upperlen+lowerlen), paraminterval )]
        else:
            (a, b) = self.midpointsplit()
            return a.seglengths(0.5*paraminterval, epsilon) + b.seglengths(0.5*paraminterval, epsilon)

    def _arclentoparam_pt(self, lengths, epsilon=1e-5):
        """computes the parameters [t] of bpathel where the given lengths (in pts) are assumed
        returns ( [parameters], total arclen)
        A negative length gives a parameter 0"""

        # create the list of accumulated lengths
        # and the length of the parameters
        cumlengths = self.seglengths(1, epsilon)
        l = len(cumlengths)
        parlengths = [cumlengths[i][1] for i in range(l)]
        cumlengths[0] = cumlengths[0][0]
        for i in range(1,l):
            cumlengths[i] = cumlengths[i][0] + cumlengths[i-1]

        # create the list of parameters to be returned
        params = []
        for length in lengths:
            # find the last index that is smaller than length
            try:
                lindex = bisect.bisect_left(cumlengths, length)
            except: # workaround for python 2.0
                lindex = bisect.bisect(cumlengths, length)
                while lindex and (lindex >= len(cumlengths) or
                                  cumlengths[lindex] >= length):
                    lindex -= 1
            if lindex == 0:
                param = length * 1.0 / cumlengths[0]
                param *= parlengths[0]
            elif lindex >= l-2:
                param = 1
            else:
                param = (length - cumlengths[lindex]) * 1.0 / (cumlengths[lindex+1] - cumlengths[lindex])
                param *= parlengths[lindex+1]
                for i in range(lindex+1):
                    param += parlengths[i]
            param = max(min(param,1),0)
            params.append(param)
        return [params, cumlengths[-1]]
	
    def _split(self, parameters):
        """return list of normcurve corresponding to split at parameters"""

        # first, we calculate the coefficients corresponding to our
        # original bezier curve. These represent a useful starting
        # point for the following change of the polynomial parameter
        a0x = self.x0
        a0y = self.y0
        a1x = 3*(-self.x0+self.x1)
        a1y = 3*(-self.y0+self.y1)
        a2x = 3*(self.x0-2*self.x1+self.x2)
        a2y = 3*(self.y0-2*self.y1+self.y2)
        a3x = -self.x0+3*(self.x1-self.x2)+self.x3
        a3y = -self.y0+3*(self.y1-self.y2)+self.y3

        if parameters[0]!=0:
            parameters = [0] + parameters
        if parameters[-1]!=1:
            parameters = parameters + [1]

        result = []

        for i in range(len(parameters)-1):
            t1 = parameters[i]
            dt = parameters[i+1]-t1

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
            # (x0, y0) the control point (x3, y3) from the previous
            # Bezier curve

            x0 = a0x + a1x*t1 + a2x*t1*t1 + a3x*t1*t1*t1 
            y0 = a0y + a1y*t1 + a2y*t1*t1 + a3y*t1*t1*t1 
            x1 = (a1x+2*a2x*t1+3*a3x*t1*t1)*dt/3.0 + x0
            y1 = (a1y+2*a2y*t1+3*a3y*t1*t1)*dt/3.0 + y0
            x2 = (a2x+3*a3x*t1)*dt*dt/3.0 - x0 + 2*x1
            y2 = (a2y+3*a3y*t1)*dt*dt/3.0 - y0 + 2*y1
            x3 = a3x*dt*dt*dt + x0 - 3*x1 + 3*x2
            y3 = a3y*dt*dt*dt + y0 - 3*y1 + 3*y2

            result.append(normcurve(x0, y0, x1, y1, x2, y2, x3, y3))

        return result

    def split(self, parameters):
        if parameters:
            # we need to split
            bps = self._split(list(parameters))

            if parameters[0]==0:
                result = [None]
            else:
                bp0 = bps[0]
                result = [normcurve(self.x0, self.y0, bp0.x1, bp0.y1, bp0.x2, bp0.y2, bp0.x3, bp0.y3)]
                bps = bps[1:]

            for bp in bps:
                result.append(normcurve(bp.x0, bp.y0, bp.x1, bp.y1, bp.x2, bp.y2, bp.x3, bp.y3))

            if parameters[-1]==1:
                result.append(None)
        else:
            result = []
        return result

    def tangent_pt(self, t):
        tvectx = (3*(  -self.x0+3*self.x1-3*self.x2+self.x3)*t*t +
                  2*( 3*self.x0-6*self.x1+3*self.x2        )*t +
                    (-3*self.x0+3*self.x1                  ))
        tvecty = (3*(  -self.y0+3*self.y1-3*self.y2+self.y3)*t*t +
                  2*( 3*self.y0-6*self.y1+3*self.y2        )*t +
                    (-3*self.y0+3*self.y1                  ))
        return (tvectx, tvecty)

    def transform(self, trafo):
        self.x0, self.y0 = trafo._apply(self.x0, self.y0)
        self.x1, self.y1 = trafo._apply(self.x1, self.y1)
        self.x2, self.y2 = trafo._apply(self.x2, self.y2)
        self.x3, self.y3 = trafo._apply(self.x3, self.y3)

    def transformed(self, trafo):
        return normcurve(*(trafo._apply(self.x0, self.y0)+
                           trafo._apply(self.x1, self.y1)+
                           trafo._apply(self.x2, self.y2)+
                           trafo._apply(self.x3, self.y3)))

    def outputPS(self, file):
        file.write("%g %g %g %g %g %g curveto\n" % (self.x1, self.y1, self.x2, self.y2, self.x3, self.y3))

    def outputPDF(self, file):
        file.write("%g %g %g %g %g %g c\n" % (self.x1, self.y1, self.x2, self.y2, self.x3, self.y3))

#
# normpaths are made up of normsubpaths, which represent connected line segments
#

class normsubpath:

    """sub path of a normalized path

    A subpath consists of a list of normpathels, i.e., lines and bcurves
    and can either be closed or not.

    Some invariants, which have to be obeyed:
    - The last point of a normpathel and the first point of the next
    element have to be equal.
    - When the path is closed, the last normpathel has to be a
    normline and the last point of this normline has to be equal
    to the first point of the first normpathel

    """

    def __init__(self, normpathels, closed):
        self.normpathels = normpathels
        self.closed = closed

    def __str__(self):
        return "subpath(%s, [%s])" % (self.closed and "closed" or "open",
                                    ", ".join(map(str, self.normpathels)))

    def arclen_pt(self, epsilon=1e-5):
        """returns total arc length of normsubpath in pts with accuracy epsilon"""
        return sum([npel.arclen_pt(epsilon) for npel in self.normpathels])

    def at_pt(self, t):
        """return coordinates in pts of sub path at parameter value t

        Negative values of t count from the end of the path. The absolute
        value of t must be smaller or equal to the number of segments in
        the normpath, otherwise None is returned.
        
        """
        if t<0:
            t += self.range()
        if 0<=t<self.range():
            return self.normpathels[int(t)].at_pt(t-int(t))
        if t==self.range():
            return self.end_pt()

    def bbox(self):
        if self.normpathels:
            abbox = self.normpathels[0].bbox()
            for anormpathel in self.normpathels[1:]:
                abbox += anormpathel.bbox()
            return abbox
        else:
            return None

    def begin_pt(self):
        return self.normpathels[0].begin_pt()

    def end_pt(self):
        return self.normpathels[-1].end_pt()

    def intersect(self, other, epsilon=1e-5):
        """intersect self with other normsubpath

        returns a tuple of lists consisting of the parameter values
        of the intersection points of the corresponding normsubpath

        """
        intersections = ([], [])
        # Intersect all subpaths of self with the subpaths of other
        for t_a, pel_a  in enumerate(self.normpathels):
            for t_b, pel_b in enumerate(other.normpathels):
                for intersection in pel_a.intersect(pel_b, epsilon):
                    # check whether an intersection occurs at the end
                    # of a closed subpath. If yes, we don't include it
                    # in the list of intersections to prevent a
                    # duplication of intersection points
                    if not ((self.closed and self.range()-intersection[0]-t_a<epsilon) or
                            (other.closed and other.range()-intersection[1]-t_b<epsilon)):
                        intersections[0].append(intersection[0]+t_a)
                        intersections[1].append(intersection[1]+t_b)
        return intersections

    def _arclentoparam_pt(self, lengths, epsilon=1e-5):
        """returns [t, l] where t are parameter value(s) matching given length(s)
        and l is the total length of the normsubpath
        The parameters are with respect to the normsubpath: t in [0, self.range()]
        lengths that are < 0 give parameter 0"""

        allarclen = 0
        allparams = [0]*len(lengths)
        rests = [length for length in lengths]

        for pel in self.normpathels:
            params, arclen = pel._arclentoparam_pt(rests, epsilon)
            allarclen += arclen
            for i in range(len(rests)):
                if rests[i] >= 0:
                    rests[i] -= arclen
                    allparams[i] += params[i]

        return [allparams, allarclen]

    def range(self):
        """return maximal parameter value, i.e. number of line/curve segments"""
        return len(self.normpathels)

    def reverse(self):
        self.normpathels.reverse()
        for npel in self.normpathels:
            npel.reverse()

    def reversed(self):
        nnormpathels = []
        for i in range(len(self.normpathels)):
            nnormpathels.append(self.normpathels[-(i+1)].reversed())
        return normsubpath(nnormpathels, self.closed)

    def split(self, ts):
        """split normsubpath at list of parameter values ts and return list
        of normsubpaths

        Negative values of t count from the end of the sub path.
        After taking this rule into account, the parameter list ts has
        to be sorted and all parameters t have to fulfil
        0<=t<=self.range().  Note that each element of the resulting
        list is an _open_ normsubpath.
        
        """

        for i in range(len(ts)):
            if ts[i]<0:
                ts[i] += self.range()
            if not (0<=ts[i]<=self.range()):
                raise RuntimeError("parameter for split of subpath out of range")

        result = []
        npels = None
        for t, pel in enumerate(self.normpathels):
            # determine list of splitting parameters relevant for pel
            nts = []
            for nt in ts:
                if t+1 >= nt:
                    nts.append(nt-t)
                    ts = ts[1:]

            # now we split the path at the filtered parameter values
            # This yields a list of normpathels and possibly empty
            # segments marked by None
            splitresult = pel.split(nts)
            if splitresult:
                # first split?
                if npels is None:
                    if splitresult[0] is None:
                        # mark split at the beginning of the normsubpath
                        result = [None]
                    else:
                        result.append(normsubpath([splitresult[0]], 0))
                else:
                    npels.append(splitresult[0])
                    result.append(normsubpath(npels, 0))
                for npel in splitresult[1:-1]:
                    result.append(normsubpath([npel], 0))
                if len(splitresult)>1 and splitresult[-1] is not None:
                    npels = [splitresult[-1]]
                else:
                    npels = []
            else:
                if npels is None:
                    npels = [pel]
                else:
                    npels.append(pel)

        if npels:
            result.append(normsubpath(npels, 0))
        else:
            # mark split at the end of the normsubpath
            result.append(None)
            
        # glue last and first segment together if the normsubpath was originally closed 
        if self.closed:
            if result[0] is None:
                result = result[1:]
            elif result[-1] is None:
                result = result[:-1]
            else:
                result[-1].normpathels.extend(result[0].normpathels)
                result = result[1:]
        return result

    def tangent_pt(self, t):
        if t<0:
            t += self.range()
        if 0<=t<self.range():
            return self.normpathels[int(t)].tangent_pt(t-int(t))
        if t==self.range():
            return self.normpathels[-1].tangent_pt(1)

    def transform(self, trafo):
        """transform sub path according to trafo"""
        for pel in self.normpathels:
            pel.transform(trafo)

    def transformed(self, trafo):
        """return sub path transformed according to trafo"""
        nnormpathels = []
        for pel in self.normpathels:
            nnormpathels.append(pel.transformed(trafo))
        return normsubpath(nnormpathels, self.closed)

    def outputPS(self, file):
        # if the normsubpath is closed, we must not output the last normpathel
        if self.closed:
            normpathels = self.normpathels[:-1]
        else:
            normpathels = self.normpathels
        if normpathels:
            file.write("%g %g moveto\n" % self.begin_pt())
            for anormpathel in normpathels:
                anormpathel.outputPS(file)
        if self.closed:
            file.write("closepath\n")

    def outputPDF(self, file):
        # if the normsubpath is closed, we must not output the last normpathel
        if self.closed:
            normpathels = self.normpathels[:-1]
        else:
            normpathels = self.normpathels
        if normpathels:
            file.write("%g %g m\n" % self.begin_pt())
            for anormpathel in normpathels:
                anormpathel.outputPDF(file)
        if self.closed:
            file.write("closepath\n")

#
# the normpath class
#

class normpath(path):

    """normalized path

    a normalized path consits of a list of normsubpaths

    """

    def __init__(self, arg=[]):
        """ construct a normpath from another normpath passed as arg,
        a path or a list of normsubpaths """
        if isinstance(arg, normpath):
            self.subpaths = copy.copy(arg.subpaths)
            return
        elif isinstance(arg, path):
            # split path in sub paths
            self.subpaths = []
            currentsubpathels = []
            context = _pathcontext()
            for pel in arg.path:
                for npel in pel._normalized(context):
                    if isinstance(npel, moveto_pt):
                        if currentsubpathels:
                            # append open sub path
                            self.subpaths.append(normsubpath(currentsubpathels, 0))
                        # start new sub path
                        currentsubpathels = []
                    elif isinstance(npel, closepath):
                        if currentsubpathels:
                            # append closed sub path
                            currentsubpathels.append(normline(context.currentpoint[0], context.currentpoint[1],
                                                              context.currentsubpath[0], context.currentsubpath[1]))
                        self.subpaths.append(normsubpath(currentsubpathels, 1))
                        currentsubpathels = []
                    else:
                        currentsubpathels.append(npel)
                pel._updatecontext(context)

            if currentsubpathels:
                # append open sub path
                self.subpaths.append(normsubpath(currentsubpathels, 0))
        else:
            # we expect a list of normsubpaths
            self.subpaths = list(arg)

    def __add__(self, other):
        result = normpath(other)
        result.subpaths = self.subpaths + result.subpaths
        return result

    def __iadd__(self, other):
        self.subpaths += normpath(other).subpaths
        return self

    def __len__(self):
        # XXX ok?
        return len(self.subpaths)

    def __str__(self):
        return "normpath(%s)" % ", ".join(map(str, self.subpaths))

    def _findsubpath(self, t):
        """return a tuple (subpath, relativet),
        where subpath is the subpath containing the parameter value t and t is the
        renormalized value of t in this subpath

        Negative values of t count from the end of the path.  At
        discontinuities in the path, the limit from below is returned.
        None is returned, if the parameter t is out of range.
        """

        if t<0:
            t += self.range()

        spt = 0
        for sp in self.subpaths:
            sprange = sp.range()
            if spt <= t <= sprange+spt:
                return sp, t-spt
            spt += sprange
        return None

    def append(self, pathel):
        # XXX factor parts of this code out
        if self.subpaths[-1].closed:
            context = _pathcontext(self.end_pt(), None)
            currentsubpathels = []
        else:
            context = _pathcontext(self.end_pt(), self.subpaths[-1].begin_pt())
            currentsubpathels = self.subpaths[-1].normpathels
            self.subpaths = self.subpaths[:-1]
        for npel in pathel._normalized(context):
            if isinstance(npel, moveto_pt):
                if currentsubpathels:
                    # append open sub path
                    self.subpaths.append(normsubpath(currentsubpathels, 0))
                # start new sub path
                currentsubpathels = []
            elif isinstance(npel, closepath):
                if currentsubpathels:
                    # append closed sub path
                    currentsubpathels.append(normline(context.currentpoint[0], context.currentpoint[1],
                                                      context.currentsubpath[0], context.currentsubpath[1]))
                    self.subpaths.append(normsubpath(currentsubpathels, 1))
                currentsubpathels = []
            else:
                currentsubpathels.append(npel)
                
        if currentsubpathels:
            # append open sub path
            self.subpaths.append(normsubpath(currentsubpathels, 0))
        
    def arclen_pt(self, epsilon=1e-5):
        """returns total arc length of normpath in pts with accuracy epsilon"""
        return sum([sp.arclen_pt(epsilon) for sp in self.subpaths])

    def arclen(self, epsilon=1e-5):
        """returns total arc length of normpath with accuracy epsilon"""
        return unit.t_pt(self.arclen_pt(epsilon))

    def at_pt(self, t):
        """return coordinates in pts of path at parameter value t

        Negative values of t count from the end of the path. The absolute
        value of t must be smaller or equal to the number of segments in
        the normpath, otherwise None is returned.
        At discontinuities in the path, the limit from below is returned

        """
        result = self._findsubpath(t)
        if result:
            return result[0].at_pt(result[1])
        else:
            return None

    def at(self, t):
        """return coordinates of path at parameter value t

        Negative values of t count from the end of the path. The absolute
        value of t must be smaller or equal to the number of segments in
        the normpath, otherwise None is returned.
        At discontinuities in the path, the limit from below is returned

        """
        result = self.at_pt(t)
        if result:
            return unit.t_pt(result[0]), unit.t_pt(result[1])
        else:
            return result

    def bbox(self):
        abbox = None
        for sp in self.subpaths:
            nbbox =  sp.bbox()
            if abbox is None:
                abbox = nbbox
            elif nbbox: 
                abbox += nbbox
        return abbox

    def begin_pt(self):
        """return coordinates of first point of first subpath in path (in pts)"""
        if self.subpaths:
            return self.subpaths[0].begin_pt()
        else:
            return None

    def begin(self):
        """return coordinates of first point of first subpath in path"""
        result = self.begin_pt()
        if result:
            return unit.t_pt(result[0]), unit.t_pt(result[1])
        else:
            return result

    def end_pt(self):
        """return coordinates of last point of last subpath in path (in pts)"""
        if self.subpaths:
            return self.subpaths[-1].end_pt()
        else:
            return None

    def end(self):
        """return coordinates of last point of last subpath in path"""
        result = self.end_pt()
        if result:
            return unit.t_pt(result[0]), unit.t_pt(result[1])
        else:
            return result

    def glue(self, other):
        if not self.subpaths:
            raise PathException("cannot glue to end of empty path")
        if self.subpaths[-1].closed:
            raise PathException("cannot glue to end of closed sub path")
        other = normpath(other)
        if not other.subpaths:
            raise PathException("cannot glue empty path")

        self.subpaths[-1].normpathels += other.subpaths[0].normpathels
        self.subpaths += other.subpaths[1:]
        return self

    def intersect(self, other, epsilon=1e-5):
        """intersect self with other path

        returns a tuple of lists consisting of the parameter values
        of the intersection points of the corresponding normpath

        """
        if not isinstance(other, normpath):
            other = normpath(other)

        # here we build up the result
        intersections = ([], [])

        # Intersect all subpaths of self with the subpaths of
        # other. Here, st_a, st_b are the parameter values
        # corresponding to the first point of the subpaths sp_a and
        # sp_b, respectively.
        st_a = 0          
        for sp_a in self.subpaths:
            st_b =0
            for sp_b in other.subpaths:
                for intersection in zip(*sp_a.intersect(sp_b, epsilon)):
                    intersections[0].append(intersection[0]+st_a)
                    intersections[1].append(intersection[1]+st_b)
                st_b += sp_b.range()
            st_a += sp_a.range()
        return intersections

    def arclentoparam(self, lengths, epsilon=1e-5):
        """returns the parameter value(s) matching the given length(s)"""

        # split the list of lengths apart for positive and negative values
        rests = [[],[]] # first the positive then the negative lengths
        remap = [] # for resorting the rests into lengths
        for length in helper.ensuresequence(lengths):
            length = unit.topt(length)
            if length >= 0.0:
                rests[0].append(length)
                remap.append([0,len(rests[0])-1])
            else:
                rests[1].append(-length)
                remap.append([1,len(rests[1])-1])

        allparams = [[0]*len(rests[0]),[0]*len(rests[1])]

        # go through the positive lengths
        for sp in self.subpaths:
            # we need arclen for knowing when all the parameters are done
            # for lengths that are done: rests[i] is negative
            # sp._arclentoparam has to ignore such lengths
            params, arclen = sp._arclentoparam_pt(rests[0], epsilon)
            finis = 0 # number of lengths that are done
            for i in range(len(rests[0])):
                if rests[0][i] >= 0:
                  rests[0][i] -= arclen
                  allparams[0][i] += params[i]
                else:
                    finis += 1
            if finis == len(rests[0]): break

        # go through the negative lengths
        for sp in self.reversed().subpaths:
            params, arclen = sp._arclentoparam_pt(rests[1], epsilon)
            finis = 0
            for i in range(len(rests[1])):
                if rests[1][i] >= 0:
                  rests[1][i] -= arclen
                  allparams[1][i] -= params[i]
                else:
                    finis += 1
            if finis==len(rests[1]): break

        # re-sort the positive and negative values into one list
        allparams = [allparams[p[0]][p[1]] for p in remap]
        if not helper.issequence(lengths): allparams = allparams[0]

        return allparams

    def range(self):
        """return maximal value for parameter value t"""
        return sum([sp.range() for sp in self.subpaths])

    def reverse(self):
        """reverse path"""
        self.subpaths.reverse()
        for sp in self.subpaths:
            sp.reverse()

    def reversed(self):
        """return reversed path"""
        nnormpath = normpath()
        for i in range(len(self.subpaths)):
            nnormpath.subpaths.append(self.subpaths[-(i+1)].reversed())
        return nnormpath

    def split(self, parameters):
        """split path at parameter values parameters

        Note that the parameter list has to be sorted.

        """

        # XXX support negative arguments
        # XXX None at the end of last subpath is not handled correctly

        # check whether parameter list is really sorted
        sortedparams = list(parameters)
        sortedparams.sort()
        if sortedparams!=list(parameters):
            raise ValueError("split parameters have to be sorted")

        # we build up this list of normpaths
        result = []

        # the currently built up normpath
        np = normpath()

        t0 = 0
        for subpath in self.subpaths:
            tf = t0+subpath.range()
            if parameters and tf>=parameters[0]:
                # split this subpath
                # determine the relevant splitting parameters
                for i in range(len(parameters)):
                    if parameters[i]>tf: break
                else:
                    i = len(parameters)

                splitsubpaths = subpath.split([x-t0 for x in parameters[:i]])
                # handle first element, which may be None, separately
                if splitsubpaths[0] is None:
                    if not np.subpaths:
                        result.append(None)
                    else:
                        result.append(np)
                        np = normpath()
                    splitsubpaths.pop(0)

                for sp in splitsubpaths[:-1]:
                    np.subpaths.append(sp)
                    result.append(np)
                    np = normpath()

                # handle last element which may be None, separately
                if splitsubpaths:
                    if splitsubpaths[-1] is None:
                        if np.subpaths:
                            result.append(np)
                            np = normpath()
                    else:
                        np.subpaths.append(splitsubpaths[-1])

                parameters = parameters[i:]
            else:
                # append whole subpath to current normpath
                np.subpaths.append(subpath)
            t0 = tf

        if np.subpaths:
            result.append(np)
        else:
            # mark split at the end of the normsubpath
            result.append(None)

        return result

    def tangent_pt(self, t, length=None):
        """return tuple in pts corresponding to tangent vector of path at parameter value t

        Negative values of t count from the end of the path. The absolute
        value of t must be smaller or equal to the number of segments in
        the normpath, otherwise None is returned.
        At discontinuities in the path, the limit from below is returned

        if length is not None, the tangent vector will be scaled to
        the desired length

        """
        result = self._findsubpath(t)
        if result:
            tdx, tdy = result[0].tangent_pt(result[1])
            tlen = math.sqrt(tdx*tdx + tdy*tdy)
            if not (length is None or tlen==0):
                sfactor = unit.topt(length)/tlen
                tdx *= sfactor
                tdy *= sfactor
            return (tdx, tdy)
        else:
            return None

    def tangent(self, t, length=None):
        """return tuple corresponding to tangent vector of path at parameter value t

        Negative values of t count from the end of the path. The absolute
        value of t must be smaller or equal to the number of segments in
        the normpath, otherwise None is returned.
        At discontinuities in the path, the limit from below is returned

        if length is not None, the tangent vector will be scaled to
        the desired length

        """
        tvec = self.tangent_pt(t, length)
        if tvec:
            return (unit.t_pt(tvec[0]), unit.t_pt(tvec[1]))
        else:
            return None

    def transform(self, trafo):
        """transform path according to trafo"""
        for sp in self.subpaths:
            sp.transform(trafo)

    def transformed(self, trafo):
        """return path transformed according to trafo"""
        return normpath([sp.transformed(trafo) for sp in self.subpaths])

    def outputPS(self, file):
        for sp in self.subpaths:
            sp.outputPS(file)

    def outputPDF(self, file):
        for sp in self.subpaths:
            sp.outputPDF(file)

################################################################################
# some special kinds of path, again in two variants
################################################################################

class line_pt(path):

   """straight line from (x1, y1) to (x2, y2) (coordinates in pts)"""

   def __init__(self, x1, y1, x2, y2):
       path.__init__(self, moveto_pt(x1, y1), lineto_pt(x2, y2))


class curve_pt(path):

   """Bezier curve with control points (x0, y1),..., (x3, y3)
   (coordinates in pts)"""

   def __init__(self, x0, y0, x1, y1, x2, y2, x3, y3):
       path.__init__(self,
                     moveto_pt(x0, y0),
                     curveto_pt(x1, y1, x2, y2, x3, y3))


class rect_pt(path):

   """rectangle at position (x,y) with width and height (coordinates in pts)"""

   def __init__(self, x, y, width, height):
       path.__init__(self, moveto_pt(x, y), 
                           lineto_pt(x+width, y), 
                           lineto_pt(x+width, y+height), 
                           lineto_pt(x, y+height),
                           closepath())


class circle_pt(path):

   """circle with center (x,y) and radius"""

   def __init__(self, x, y, radius):
       path.__init__(self, arc_pt(x, y, radius, 0, 360),
                           closepath())


class line(line_pt):

   """straight line from (x1, y1) to (x2, y2)"""

   def __init__(self, x1, y1, x2, y2):
       line_pt.__init__(self,
                      unit.topt(x1), unit.topt(y1),
                      unit.topt(x2), unit.topt(y2)
                      )


class curve(curve_pt):

   """Bezier curve with control points (x0, y1),..., (x3, y3)"""

   def __init__(self, x0, y0, x1, y1, x2, y2, x3, y3):
       curve_pt.__init__(self,
                       unit.topt(x0), unit.topt(y0),
                       unit.topt(x1), unit.topt(y1),
                       unit.topt(x2), unit.topt(y2),
                       unit.topt(x3), unit.topt(y3)
                      )


class rect(rect_pt):

   """rectangle at position (x,y) with width and height"""

   def __init__(self, x, y, width, height):
       rect_pt.__init__(self,
                        unit.topt(x), unit.topt(y),
                        unit.topt(width), unit.topt(height))


class circle(circle_pt):

   """circle with center (x,y) and radius"""

   def __init__(self, x, y, radius):
       circle_pt.__init__(self,
                        unit.topt(x), unit.topt(y),
                        unit.topt(radius))
