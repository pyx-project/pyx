#!/usr/bin/env python
#
#
# Copyright (C) 2002 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2002 André Wobst <wobsta@users.sourceforge.net>
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

# TODO: - reversepath ?
#       - nocurrentpoint exception?
#       - correct bbox for curveto and bpathel
#         (maybe we still need the current bbox implementation (then maybe called
#          cbox = control box) for bpathel for the use during the
#          intersection of bpaths) 
#       - intersection of bpaths: use estimate for number of subdivisions

import math
from math import cos, sin, pi
import base, bbox, unit, bpath


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
        currrentsubpath have to be floats (in the unit.topt)

        """

        pass

    def _normalized(self, context):
        """returns tupel consisting of normalized version of pathel

        context: context of pathel

        returns list consisting of corresponding normalized pathels
        _moveto, _lineto, _curveto, closepath in given context

        """

        pass

    def write(self, file):
        """write pathel to file in the context of canvas"""

        pass

################################################################################ 
# normpathel: normalized element of a PS style path 
################################################################################

class normpathel(pathel):

    """normalized element of a PS style path"""

    def _bpathel(self, context):
        """convert normpathel to bpathel

        context: context of pathel

        return bpathel corresponding to pathel in the given context

        """

        pass

    def transform(self, trafo):
        """return transformed normpathel according to trafo"""

        pass

# first come the various normpathels. Each one comes in two variants:
#  - one with an preceding underscore, which does no coordinate to pt conversion
#  - the other without preceding underscore, which converts to pts 


class closepath(normpathel): 

    """Connect subpath back to its starting point"""

    def _updatecontext(self, context):
        context.currentpoint = None
        context.currentsubpath = None

    def _bbox(self, context):
        cpx, cpy = context.currentpoint
        csx, csy = context.currentsubpath

        return bbox.bbox(min(cpx, csx), min(cpy, csy), 
                         max(cpx, csx), max(cpy, csy))

    def _bpathel(self, context):
        cpx, cpy = context.currentpoint
        csx, csy = context.currentsubpath

        return bpath._blineel(cpx, cpy, csx, csy)

    def _normalized(self, context):
        return [closepath()]

    def _reverse(self, context):
        return _lineto(*context.currentsubpath)

    def write(self, file):
        file.write("closepath\n")

    def transform(self, trafo):
        return closepath()


class _moveto(normpathel):

    """Set current point to (x, y) (coordinates in pts)"""

    def __init__(self, x, y):
         self.x = x
         self.y = y

    def _updatecontext(self, context):
        context.currentpoint = self.x, self.y
        context.currentsubpath = self.x, self.y

    def _bbox(self, context):
        return bbox.bbox()

    def _bpathel(self, context):
        return None

    def _normalized(self, context):
        return [_moveto(self.x, self.y)]

    def _reverse(self, context):
        return None

    def write(self, file):
        file.write("%f %f moveto\n" % (self.x, self.y) )

    def transform(self, trafo):
        return _moveto(*trafo._apply(self.x, self.y))

class _lineto(normpathel):

    """Append straight line to (x, y) (coordinates in pts)"""

    def __init__(self, x, y):
         self.x = x
         self.y = y

    def _updatecontext(self, context):
        context.currentsubpath = context.currentsubpath or context.currentpoint
        context.currentpoint = self.x, self.y

    def _bbox(self, context):
        return bbox.bbox(min(context.currentpoint[0], self.x),
                         min(context.currentpoint[1], self.y), 
                         max(context.currentpoint[0], self.x),
                         max(context.currentpoint[1], self.y))

    def _bpathel(self, context):
        return bpath._blineel(context.currentpoint[0], context.currentpoint[1],
                              self.x, self.y)

    def _normalized(self, context):
        return [_lineto(self.x, self.y)]

    def _reverse(self, context):
        return _lineto(*context.currentpoint)

    def write(self, file):
        file.write("%f %f lineto\n" % (self.x, self.y) )

    def transform(self, trafo):
        return _lineto(*trafo._apply(self.x, self.y))


class _curveto(normpathel):

    """Append curveto (coordinates in pts)"""

    def __init__(self, x1, y1, x2, y2, x3, y3):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.x3 = x3
        self.y3 = y3

    def _updatecontext(self, context):
        context.currentsubpath = context.currentsubpath or context.currentpoint
        context.currentpoint = self.x3, self.y3

    def _bbox(self, context):
        return bbox.bbox(min(context.currentpoint[0], self.x1, self.x2, self.x3),
                         min(context.currentpoint[1], self.y1, self.y2, self.y3),
                         max(context.currentpoint[0], self.x1, self.x2, self.x3),
                         max(context.currentpoint[1], self.y1, self.y2, self.y3))

    def _bpathel(self, context):
        return bpath._bpathel(context.currentpoint[0], context.currentpoint[1],
                              self.x1, self.y1,
                              self.x2, self.y2,
                              self.x3, self.y3)

    def _normalized(self, context):
        return [_curveto(self.x1, self.y1,
                         self.x2, self.y2,
                         self.x3, self.y3)]

    def _reverse(self, context):
        return _curveto(self.x2, self.y2,
                        self.x1, self.y1,
                        context.currentpoint[0], context.currentpoint[1])

    def write(self, file):
        file.write("%f %f %f %f %f %f curveto\n" % ( self.x1, self.y1,
                                                     self.x2, self.y2,
                                                     self.x3, self.y3 ) )

    def transform(self, trafo):
        return _curveto(*(trafo._apply(self.x1, self.y1)+
                          trafo._apply(self.x2, self.y2)+
                          trafo._apply(self.x3, self.y3)))

#
# now the versions that convert from user coordinates to pts
#

class moveto(_moveto):

    """Set current point to (x, y)"""

    def __init__(self, x, y):
         _moveto.__init__(self, unit.topt(x), unit.topt(y))


class lineto(_lineto):

    """Append straight line to (x, y)"""

    def __init__(self, x, y):
        _lineto.__init__(self, unit.topt(x), unit.topt(y))


class curveto(_curveto):

    """Append curveto"""

    def __init__(self, x1, y1, x2, y2, x3, y3):
        _curveto.__init__(self,
                          unit.topt(x1), unit.topt(y1),
                          unit.topt(x2), unit.topt(y2),
                          unit.topt(x3), unit.topt(y3))

#
# now come the pathels, again in two versions
#

class _rmoveto(pathel):

    """Perform relative moveto (coordinates in pts)"""

    def __init__(self, dx, dy):
         self.dx = dx
         self.dy = dy

    def _updatecontext(self, context):
        context.currentpoint = (context.currentpoint[0] + self.dx,
                                context.currentpoint[1] + self.dy)
        context.currentsubpath = context.currentpoint

    def _bbox(self, context):
        return bbox.bbox()

    def _normalized(self, context):
        x = context.currentpoint[0]+self.dx
        y = context.currentpoint[1]+self.dy

        return [_moveto(x, y)]

    def write(self, file):
        file.write("%f %f rmoveto\n" % (self.dx, self.dy) )


class _rlineto(pathel):

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
        return bbox.bbox(min(context.currentpoint[0], x),
                         min(context.currentpoint[1], y),
                         max(context.currentpoint[0], x),
                         max(context.currentpoint[1], y))

    def _normalized(self, context):
        x = context.currentpoint[0] + self.dx
        y = context.currentpoint[1] + self.dy

        return [_lineto(x, y)]

    def write(self, file):
        file.write("%f %f rlineto\n" % (self.dx, self.dy) )


class _rcurveto(pathel):

    """Append rcurveto (coordinates in pts)"""

    def __init__(self, dx1, dy1, dx2, dy2, dx3, dy3):
        self.dx1 = dx1
        self.dy1 = dy1
        self.dx2 = dx2
        self.dy2 = dy2
        self.dx3 = dx3
        self.dy3 = dy3

    def write(self, file):
        file.write("%f %f %f %f %f %f rcurveto\n" % ( self.dx1, self.dy1,
                                                    self.dx2, self.dy2,
                                                    self.dx3, self.dy3 ) )

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
        return bbox.bbox(min(context.currentpoint[0], x1, x2, x3),
                         min(context.currentpoint[1], y1, y2, y3),
                         max(context.currentpoint[0], x1, x2, x3),
                         max(context.currentpoint[1], y1, y2, y3))

    def _normalized(self, context):
        x2 = context.currentpoint[0]+self.dx1
        y2 = context.currentpoint[1]+self.dy1
        x3 = context.currentpoint[0]+self.dx2
        y3 = context.currentpoint[1]+self.dy2
        x4 = context.currentpoint[0]+self.dx3
        y4 = context.currentpoint[1]+self.dy3

        return [_curveto(x2, y2, x3, y3, x4, y4)]

#
# arc, arcn, arct
#

class _arc(pathel):

    """Append counterclockwise arc (coordinates in pts)"""

    def __init__(self, x, y, r, angle1, angle2):
        self.x = x
        self.y = y
        self.r = r
        self.angle1 = angle1
        self.angle2 = angle2

    def _sarc(self):
        """Return starting point of arc segment"""
        return (self.x+self.r*cos(pi*self.angle1/180),
                self.y+self.r*sin(pi*self.angle1/180))

    def _earc(self):
        """Return end point of arc segment"""
        return (self.x+self.r*cos(pi*self.angle2/180),
                self.y+self.r*sin(pi*self.angle2/180))

    def _updatecontext(self, context):
        if context.currentpoint:
            context.currentsubpath = context.currentsubpath or context.currentpoint
        else:
            # we assert that currentsubpath is also None
            context.currentsubpath = self._sarc()

        context.currentpoint = self._earc()

    def _bbox(self, context):
        phi1=pi*self.angle1/180
        phi2=pi*self.angle2/180

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
            return (bbox.bbox(min(context.currentpoint[0], sarcx),
                              min(context.currentpoint[1], sarcy),
                              max(context.currentpoint[0], sarcx),
                              max(context.currentpoint[1], sarcy)) +
                    bbox.bbox(minarcx, minarcy, maxarcx, maxarcy)
                    )
        else:
            return  bbox.bbox(minarcx, minarcy, maxarcx, maxarcy)

    def _normalized(self, context):
        # get starting and end point of arc segment and bpath corresponding to arc
        sarcx, sarcy = self._sarc()
        earcx, earcy = self._earc()
        barc = bpath._barc(self.x, self.y, self.r, self.angle1, self.angle2)

        # convert to list of curvetos omitting movetos
        nbarc = []

        for bpathel in barc:
            nbarc.append(_curveto(bpathel.x1, bpathel.y1,
                                  bpathel.x2, bpathel.y2,
                                  bpathel.x3, bpathel.y3))

        # Note that if there is a currentpoint defined, we also
        # have to include the straight line from this point
        # to the first point of the arc segment.
        # Otherwise, we have to add a moveto at the beginning
        if context.currentpoint:
            return [_lineto(sarcx, sarcy)] + nbarc
        else:
            return [_moveto(sarcx, sarcy)] + nbarc


    def write(self, file):
        file.write("%f %f %f %f %f arc\n" % ( self.x, self.y,
                                            self.r,
                                            self.angle1,
                                            self.angle2 ) )


class _arcn(pathel):

    """Append clockwise arc (coordinates in pts)"""

    def __init__(self, x, y, r, angle1, angle2):
        self.x = x
        self.y = y
        self.r = r
        self.angle1 = angle1
        self.angle2 = angle2

    def _sarc(self):
        """Return starting point of arc segment"""
        return (self.x+self.r*cos(pi*self.angle1/180),
                self.y+self.r*sin(pi*self.angle1/180))

    def _earc(self):
        """Return end point of arc segment"""
        return (self.x+self.r*cos(pi*self.angle2/180),
                self.y+self.r*sin(pi*self.angle2/180))

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

        a = _arc(self.x, self.y, self.r, 
                 self.angle2, 
                 self.angle1)

        sarc = self._sarc()
        arcbb = a._bbox(_pathcontext())

        # Then, we repeat the logic from arc.bbox, but with interchanged
        # start and end points of the arc

        if context.currentpoint:
            return  bbox.bbox(min(context.currentpoint[0], sarc[0]),
                              min(context.currentpoint[1], sarc[1]),
                              max(context.currentpoint[0], sarc[0]),
                              max(context.currentpoint[1], sarc[1]))+ arcbb
        else:
            return arcbb

    def _normalized(self, context):
        # get starting and end point of arc segment and bpath corresponding to arc
        sarcx, sarcy = self._sarc()
        earcx, earcy = self._earc()
        barc = bpath._barc(self.x, self.y, self.r, self.angle2, self.angle1).reverse()

        # convert to list of curvetos omitting movetos
        nbarc = []

        for bpathel in barc:
            nbarc.append(_curveto(bpathel.x1, bpathel.y1,
                                  bpathel.x2, bpathel.y2,
                                  bpathel.x3, bpathel.y3))

        # Note that if there is a currentpoint defined, we also
        # have to include the straight line from this point
        # to the first point of the arc segment.
        # Otherwise, we have to add a moveto at the beginning
        if context.currentpoint:
            return [_lineto(sarcx, sarcy)] + nbarc
        else:
            return [_moveto(sarcx, sarcy)] + nbarc


    def write(self, file):
        file.write("%f %f %f %f %f arcn\n" % ( self.x, self.y,
                                             self.r,
                                             self.angle1,
                                             self.angle2 ) )


class _arct(pathel):

    """Append tangent arc (coordinates in pts)"""

    def __init__(self, x1, y1, x2, y2, r):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.r  = r

    def write(self, file):
        file.write("%f %f %f %f %f arct\n" % ( self.x1, self.y1,
                                             self.x2, self.y2,
                                             self.r ) )
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
                phi = math.atan(ry/rx)/math.pi*180
            else:
                phi = math.atan(rx/ry)/math.pi*180+180

            # half angular width of arc 
            deltaphi = 90*(1-alpha/math.pi)

            # center position of arc
            mx = self.x1-rx*self.r/(lr*sin(alpha/2))
            my = self.y1-ry*self.r/(lr*sin(alpha/2))

            # now we are in the position to construct the path
            p = path(_moveto(*currentpoint))

            if phi<0:
                p.append(_arc(mx, my, self.r, phi-deltaphi, phi+deltaphi))
            else:
                p.append(_arcn(mx, my, self.r, phi+deltaphi, phi-deltaphi))

            return ( (xt2, yt2) ,
                     currentsubpath or (xt2, yt2),
                     p )

        else:
            # we need no arc, so just return a straight line to currentpoint to x1, y1
            return  ( (self.x1, self.y1),
                      currentsubpath or (self.x1, self.y1),
                      _line(currentpoint[0], currentpoint[1], self.x1, self.y1) )

    def _updatecontext(self, context):
        r = self._path(context.currentpoint,
                       context.currentsubpath)

        context.currentpoint, context.currentsubpath = r[:2]

    def _bbox(self, context):
        return self._path(context.currentpoint,
                          context.currentsubpath)[2].bbox()

    def _normalized(self, context):
        return _normalizepath(self._path(context.currentpoint,
                              context.currentsubpath)[2])

#
# the user coordinates versions...
#

class rmoveto(_rmoveto):

    """Perform relative moveto"""

    def __init__(self, dx, dy):
        _rmoveto.__init__(self, unit.topt(dx), unit.topt(dy))


class rlineto(_rlineto):

    """Perform relative lineto"""

    def __init__(self, dx, dy):
        _rlineto.__init__(self, unit.topt(dx), unit.topt(dy))


class rcurveto(_rcurveto):

    """Append rcurveto"""

    def __init__(self, dx1, dy1, dx2, dy2, dx3, dy3):
        _rcurveto.__init__(self,
                           unit.topt(dx1), unit.topt(dy1),
                           unit.topt(dx2), unit.topt(dy2),
                           unit.topt(dx3), unit.topt(dy3))


class arcn(_arcn):

    """Append clockwise arc"""

    def __init__(self, x, y, r, angle1, angle2):
        _arcn.__init__(self, 
                       unit.topt(x), unit.topt(y), unit.topt(r), 
                       angle1, angle2)


class arc(_arc):

    """Append counterclockwise arc"""

    def __init__(self, x, y, r, angle1, angle2):
        _arc.__init__(self, unit.topt(x), unit.topt(y), unit.topt(r), 
                      angle1, angle2)


class arct(_arct):

    """Append tangent arc"""

    def __init__(self, x1, y1, x2, y2, r):
        _arct.__init__(self, unit.topt(x1), unit.topt(y1),
                             unit.topt(x2), unit.topt(y2),
                             unit.topt(r))

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

    def __len__(self):
        return len(self.path)

    def __getitem__(self, i):
        return self.path[i]

    def append(self, pathel):
        self.path.append(pathel)

    def bbox(self):
        context = _pathcontext()
        abbox = bbox.bbox()

        for pel in self.path:
            nbbox =  pel._bbox(context)
            pel._updatecontext(context)
            if abbox: abbox = abbox+nbbox

        return abbox

    def bpath(self):
        return normpath(self).bpath()

    def reversed(self):
        """return reversed path"""
        return normpath(self).reversed()

    def transformed(self, trafo):
        """return transformed path"""
        return normpath(self).transformed(trafo)

    def write(self, file):
        if not (isinstance(self.path[0], _moveto) or
                isinstance(self.path[0], _arc) or
                isinstance(self.path[0], _arcn)):
            raise PathException, "first path element must be either moveto, arc, or arcn"
        for pel in self.path:
            pel.write(file)

################################################################################
# normpath: normalized PS style path 
################################################################################

# helper routine for the normalization of a path

def _normalizepath(path):
    context = _pathcontext()
    np = []
    for pel in path:
        npels = pel._normalized(context)
        pel._updatecontext(context)
        if npels:
            for npel in npels:
                np.append(npel)
    return np

class normpath(path):

    """normalized PS style path"""

    def __init__(self, *args):
        if len(args)==1 and isinstance(args[0], path):
            path.__init__(self, *_normalizepath(args[0].path))
        else:
            print args
            path.__init__(self, *_normalizepath(args))

    def append(self, pathel):
        self.path.append(pathel)
        self.path = _normalizepath(self.path)

    def bpath(self):
        context = _pathcontext()
        bp = bpath.bpath()

        for pel in self.path:
            bpathel = pel._bpathel(context)
            pel._updatecontext(context)
            if bpathel:
                bp.append(bpathel)

        return bp

    def reversed(self):
        """return reversed path"""

        context = _pathcontext()
        subpath = []
        np = normpath()

        # we append a _moveto operation at the end to end the last
        # subpath explicitely.
        for pel in self.path+[_moveto(0,0)]:
            subpath.append(pel._reverse(context))

            if subpath and (isinstance(pel, _moveto) or isinstance(pel, closepath)):
                subpath.append(_moveto(*context.currentpoint))
                subpath.reverse()
                if isinstance(pel, closepath):
                     subpath.append(closepath())
                np = np + path(*subpath) 
                subpath = []

            pel._updatecontext(context)

        return np

    def transformed(self, trafo):
        """return transformed path"""
        return normpath(*map(lambda x, trafo=trafo: x.transform(trafo), self.path))

#
# some special kinds of path, again in two variants
#

# straight lines

class _line(normpath):

   """straight line from (x1, y1) to (x2, y2) (coordinates in pts)"""

   def __init__(self, x1, y1, x2, y2):
       normpath.__init__(self, _moveto(x1, y1), _lineto(x2, y2))


class line(_line):

   """straight line from (x1, y1) to (x2, y2)"""

   def __init__(self, x1, y1, x2, y2):
       _line.__init__(self,
                      unit.topt(x1), unit.topt(y1),
                      unit.topt(x2), unit.topt(y2)
                      )

# bezier curves

class _curve(normpath):

   """Bezier curve with control points (x0, y1),..., (x3, y3)
   (coordinates in pts)"""

   def __init__(self, x0, y0, x1, y1, x2, y2, x3, y3):
       normpath.__init__(self,
                         _moveto(x0, y0),
                         _curveto(x1, y1, x2, y2, x3, y3))

class curve(_curve):

   """Bezier curve with control points (x0, y1),..., (x3, y3)"""

   def __init__(self, x0, y0, x1, y1, x2, y2, x3, y3):
       _curve.__init__(self,
                       unit.topt(x0), unit.topt(y0),
                       unit.topt(x1), unit.topt(y1),
                       unit.topt(x2), unit.topt(y2),
                       unit.topt(x3), unit.topt(y3)
                      )

# rectangles

class _rect(path):

   """rectangle at position (x,y) with width and height (coordinates in pts)"""

   def __init__(self, x, y, width, height):
       path.__init__(self, _moveto(x, y), 
                           _rlineto(width, 0), 
                           _rlineto(0, height), 
                           _rlineto(-width, 0),
                           closepath())


class rect(_rect):

   """rectangle at position (x,y) with width and height"""

   def __init__(self, x, y, width, height):
       _rect.__init__(self,
                      unit.topt(x), unit.topt(y),
                      unit.topt(width), unit.topt(height))

# circles

class _circle(path):

   """circle with center (x,y) and radius"""

   def __init__(self, x, y, radius):
       path.__init__(self, _arc(x, y, radius, 0, 360),
                           closepath())


class circle(_circle):

   """circle with center (x,y) and radius"""

   def __init__(self, x, y, radius):
       _circle.__init__(self,
                        unit.topt(x), unit.topt(y),
                        unit.topt(radius))


