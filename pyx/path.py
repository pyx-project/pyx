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
#       - strokepath ?
#       - nocurrentpoint exception?
#       - correct bbox for curveto and bpathel
#         (maybe we still need the current bbox implementation (then maybe called
#          cbox = control box) for bpathel for the use during the
#          intersection of bpaths) 
#       - intersection of bpaths: use estimate for number of subdivisions

import base, unit, canvas, bpath
import math
from math import cos, sin, pi


class PathException(Exception): pass

################################################################################ 
# pathel: element of a PS style path 
################################################################################

class pathel(base.PSOp):

    """element of a PS style path"""
    
    def _bbox(self, currentpoint, currentsubpath):
        """calculate bounding box of pathel

        returns tuple consisting of:
         - new currentpoint
         - new currentsubpath (i.e. first point of current subpath)
         - bounding box of pathel (using currentpoint and currentsubpath)
        
        Important note: all coordinates in bbox, currentpoint, and 
        currrentsubpath have to be floats (in the unit.topt)

        """

        pass

    def write(self, file):
        """write pathel to file in the context of canvas"""
        
        pass
        
    def _bpath(self, currentpoint, currentsubpath):
        """convert pathel to bpath 

        returns tuple consisting of:
         - new currentpoint
         - new currentsubpath (i.e. first point of current subpath)
         - bpath corresponding to pathel in the context of currentpoint and 
           currentsubpath

        """     
        
        pass

# now come the various pathels. Each one comes in two variants:
#  - one with an preceding underscore, which does no coordinate to pt conversion
#  - the other without preceding underscore, which converts to pts 


class closepath(pathel): 

    """Connect subpath back to its starting point"""

    def _bbox(self, currentpoint, currentsubpath):
        return (None,
                None, 
                canvas.bbox(min(currentpoint[0], currentsubpath[0]), 
                            min(currentpoint[1], currentsubpath[1]), 
                            max(currentpoint[0], currentsubpath[0]), 
                            max(currentpoint[1], currentsubpath[1])))

    def write(self, file):
        file.write("closepath\n")

    def _bpath(self, currentpoint, currentsubpath):
        return (None,
                None,
                bpath._bline(currentpoint[0], currentpoint[1], 
                             currentsubpath[0], currentsubpath[1]) )

#
# moveto, rmoveto
#
 
class _moveto(pathel):
    """Set current point to (x, y) (coordinates in pts)"""

    def __init__(self, x, y):
         self.x = x
         self.y = y

    def _bbox(self, currentpoint, currentsubpath):
        return ((self.x, self.y),
                (self.x, self.y),
                canvas.bbox())
         
    def write(self, file):
        file.write("%f %f moveto\n" % (self.x, self.y) )

    def _bpath(self, currentpoint, currentsubpath):
        return ((self.x, self.y),
                (self.x, self.y),
                None)

 
class moveto(_moveto):

    """Set current point to (x, y)"""

    def __init__(self, x, y):
         _moveto.__init__(self, unit.topt(x), unit.topt(y))


class _rmoveto(pathel):

    """Perform relative moveto (coordinates in pts)"""

    def __init__(self, dx, dy):
         self.dx = dx
         self.dy = dy
        
    def _bbox(self, currentpoint, currentsubpath):
        return ((self.dx+currentpoint[0], self.dy+currentpoint[1]), 
                (self.dx+currentpoint[0], self.dy+currentpoint[1]),
                canvas.bbox())

    def write(self, file):
        file.write("%f %f rmoveto\n" % (self.dx, self.dy) )
        
    def _bpath(self, currentpoint, currentsubpath):
        return ((self.dx+currentpoint[0], self.dy+currentpoint[1]), 
                (self.dx+currentpoint[0], self.dy+currentpoint[1]),
                None)


class rmoveto(_rmoveto):

    """Perform relative moveto"""

    def __init__(self, dx, dy):
        _rmoveto.__init__(self, unit.topt(dx), unit.topt(dy))
        
#
# lineto, rlineto
#

class _lineto(pathel):

    """Append straight line to (x, y) (coordinates in pts)"""

    def __init__(self, x, y):
         self.x = x
         self.y = y
         
    def _bbox(self, currentpoint, currentsubpath):
        return ((self.x, self.y),
                currentsubpath or currentpoint,
                canvas.bbox(min(currentpoint[0], self.x),
                            min(currentpoint[1], self.y), 
                            max(currentpoint[0], self.x),
                            max(currentpoint[1], self.y)))

    def write(self, file):
        file.write("%f %f lineto\n" % (self.x, self.y) )
       
    def _bpath(self, currentpoint, currentsubpath):
        return ((self.x, self.y), 
                currentsubpath or currentpoint,
                bpath._bline(currentpoint[0], currentpoint[1], self.x, self.y))


class lineto(_lineto):

    """Append straight line to (x, y)"""

    def __init__(self, x, y):
        _lineto.__init__(self, unit.topt(x), unit.topt(y))
    

class _rlineto(pathel):

    """Perform relative lineto (coordinates in pts)"""

    def __init__(self, dx, dy):
         self.dx = dx
         self.dy = dy

    def _bbox(self, currentpoint, currentsubpath):
        return ((currentpoint[0]+self.dx, currentpoint[1]+self.dy),
                currentsubpath or currentpoint,
                canvas.bbox(min(currentpoint[0], currentpoint[0]+self.dx),
                            min(currentpoint[1], currentpoint[1]+self.dy), 
                            max(currentpoint[0], currentpoint[0]+self.dx),
                            max(currentpoint[1], currentpoint[1]+self.dy)))

    def write(self, file):
        file.write("%f %f rlineto\n" % (self.dx, self.dy) )
        
    def _bpath(self, currentpoint, currentsubpath):
        return ((currentpoint[0]+self.dx, currentpoint[1]+self.dy), 
                currentsubpath or currentpoint,
                bpath._bline(currentpoint[0], currentpoint[1], 
                             currentpoint[0]+self.dx, currentpoint[1]+self.dy) )


class rlineto(_rlineto):
    """Perform relative lineto"""

    def __init__(self, dx, dy):
        _rlineto.__init__(self, unit.topt(dx), unit.topt(dy))

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

    def _bbox(self, currentpoint, currentsubpath):
        phi1=pi*self.angle1/180
        phi2=pi*self.angle2/180
        
        # starting point of arc segment
        sarcx = self.x+self.r*cos(phi1)
        sarcy = self.y+self.r*sin(phi1)

        # end point of arc segment
        earcx = self.x+self.r*cos(phi2)
        earcy = self.y+self.r*sin(phi2)

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

        if currentpoint:
             return ( (earcx, earcy),
                      currentsubpath or currentpoint,
                      canvas.bbox(min(currentpoint[0], sarcx),
                                  min(currentpoint[1], sarcy), 
                                  max(currentpoint[0], sarcx),
                                  max(currentpoint[1], sarcy))+
                      canvas.bbox(minarcx, minarcy, maxarcx, maxarcy)
                    )
        else:  # we assert that currentsubpath is also None
             return ( (earcx, earcy),
                      (sarcx, sarcy),
                      canvas.bbox(minarcx, minarcy, maxarcx, maxarcy)
                    )

                            
    def write(self, file):
        file.write("%f %f %f %f %f arc\n" % ( self.x, self.y,
                                            self.r,
                                            self.angle1,
                                            self.angle2 ) )
        
    def _bpath(self, currentpoint, currentsubpath):
        # starting point of arc segment
        sarcx = self.x+self.r*cos(pi*self.angle1/180)
        sarcy = self.y+self.r*sin(pi*self.angle1/180)

        # end point of arc segment
        earcx = self.x+self.r*cos(pi*self.angle2/180)
        earcy = self.y+self.r*sin(pi*self.angle2/180)

        # Note that if there is a currentpoint defined, we also
        # have to include the straight line from this point
        # to the first point of the arc segment
        if currentpoint:
             return ( (earcx, earcy),
                      currentsubpath or currentpoint,
                      bpath._bline(currentpoint[0], currentpoint[1], sarcx, sarcy) +
                      bpath._barc(self.x, self.y, self.r, self.angle1, self.angle2)
                    )
        else:  # we assert that currentsubpath is also None
             return ( (earcx, earcy),
                      (sarcx, sarcy),
                      bpath._barc(self.x, self.y, self.r, self.angle1, self.angle2)
                    )
        
class arc(_arc):
    """Append counterclockwise arc"""

    def __init__(self, x, y, r, angle1, angle2):
        _arc.__init__(self, unit.topt(x), unit.topt(y), unit.topt(r), 
                      angle1, angle2)


class _arcn(pathel):
    """Append clockwise arc (coordinates in pts)"""
    
    def __init__(self, x, y, r, angle1, angle2):
        self.x = x
        self.y = y
        self.r = r
        self.angle1 = angle1
        self.angle2 = angle2

    def _bbox(self, currentpoint, currentsubpath):
        # in principle, we obtain bbox of an arcn element from 
        # the bounding box of the corrsponding arc element with
        # angle1 and angle2 interchanged. Though, we have to be carefull
        # with the straight line segment, which is added if currentpoint 
        # is defined.

        # Hence, we first compute the bbox of the arc without this line:

        (earc, sarc, arcbb) = _arc(self.x, self.y, self.r, 
                                   self.angle2, 
                                   self.angle1)._bbox(None, None)

        # Then, we repeat the logic from arc.bbox, but with interchanged
        # start and end points of the arc

        if currentpoint:
             return ( (sarc[0], sarc[1]),
                      currentsubpath or currentpoint,
                      canvas.bbox(min(currentpoint[0], sarc[0]),
                                  min(currentpoint[1], sarc[1]), 
                                  max(currentpoint[0], sarc[0]),
                                  max(currentpoint[1], sarc[1]))+
                      arcbb
                    )
        else:  # we assert that currentsubpath is also None
             return ( (sarc[0], sarc[1]),
                      (earc[0], earc[1]),
                      arcbb
                    )

    def write(self, file):
        file.write("%f %f %f %f %f arcn\n" % ( self.x, self.y,
                                             self.r,
                                             self.angle1,
                                             self.angle2 ) )

    def _bpath(self, currentpoint, currentsubpath):
        # starting point of arc segment
        sarcx = self.x+self.r*cos(pi*self.angle1/180)
        sarcy = self.y+self.r*sin(pi*self.angle1/180)

        # end point of arc segment
        earcx = self.x+self.r*cos(pi*self.angle2/180)
        earcy = self.y+self.r*sin(pi*self.angle2/180)

        # Note that if there is a currentpoint defined, we also
        # have to include the straight line from this point
        # to the first point of the arc segment
        if currentpoint:
             return ( (earcx, earcy),
                      currentsubpath or currentpoint,
                      bpath._bline(currentpoint[0], currentpoint[1], sarcx, sarcy) +
                      bpath._barc(self.x, self.y, self.r, self.angle2, self.angle1)
                    )
        else:  # we assert that currentsubpath is also None
             return ( (earcx, earcy),
                      (sarcx, sarcy),
                      bpath._barc(self.x, self.y, self.r, self.angle2, self.angle1)
                    )

class arcn(_arcn):

    """Append clockwise arc"""
    
    def __init__(self, x, y, r, angle1, angle2):
        _arcn.__init__(self, 
                       unit.topt(x), unit.topt(y), unit.topt(r), 
                       angle1, angle2)


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

        this is a helper routine for _bpath and bbox, which both need this
        path. Note: we don't want to calculate the bbox from a bpath
        
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
            p = path(_moveto(currentpoint[0], currentpoint[1]))

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


    def _bbox(self, currentpoint, currentsubpath):
        (currentpoint, currentsubpath, p) = self._path(currentpoint, currentsubpath)
        
        return ( currentpoint,
                 currentsubpath,
                 p.bbox() )

    
    def _bpath(self, currentpoint, currentsubpath):
        (currentpoint, currentsubpath, p) = self._path(currentpoint, currentsubpath)
        
        return ( currentpoint,
                 currentsubpath,
                 p.bpath() )
                
class arct(_arct):

    """Append tangent arc"""

    def __init__(self, x1, y1, x2, y2, r):
        _arct.__init__(self, unit.topt(x1), unit.topt(y1),
                             unit.topt(x2), unit.topt(y2),
                             unit.topt(r))

#
# curveto, rcurveto
#
        
class _curveto(pathel):

    """Append curveto (coordinates in pts)"""

    def __init__(self, x1, y1, x2, y2, x3, y3):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.x3 = x3
        self.y3 = y3
        
    def _bbox(self, currentpoint, currentsubpath):
        return ((self.x3, self.y3),
                currentsubpath or currentpoint,
                canvas.bbox(min(currentpoint[0], self.x1, self.x2, self.x3), 
                            min(currentpoint[1], self.y1, self.y2, self.y3), 
                            max(currentpoint[0], self.x1, self.x2, self.x3), 
                            max(currentpoint[1], self.y1, self.y2, self.y3)))

    def write(self, file):
        file.write("%f %f %f %f %f %f curveto\n" % ( self.x1, self.y1,
                                                   self.x2, self.y2,
                                                   self.x3, self.y3 ) )
        
    def _bpath(self, currentpoint, currentsubpath):
        return ((self.x3, self.y3),
                currentsubpath or currentpoint, 
                bpath._bcurve(currentpoint[0], currentpoint[1],
                              self.x1, self.y1, 
                              self.x2, self.y2, 
                              self.x3, self.y3))


class curveto(_curveto):

    """Append curveto"""

    def __init__(self, x1, y1, x2, y2, x3, y3):
        _curveto.__init__(self,
                          unit.topt(x1), unit.topt(y1),
                          unit.topt(x2), unit.topt(y2),
                          unit.topt(x3), unit.topt(y3))

    
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

    def _bbox(self, currentpoint, currentsubpath):
        x1=currentpoint[0]+self.dx1
        y1=currentpoint[1]+self.dy1
        x2=currentpoint[0]+self.dx2
        y2=currentpoint[1]+self.dy2
        x3=currentpoint[0]+self.dx3
        y3=currentpoint[1]+self.dy3

        return ((x3, y3),
                currentsubpath or currentpoint,
                canvas.bbox(min(currentpoint[0], x1, x2, x3),
                            min(currentpoint[1], y1, y2, y3), 
                            max(currentpoint[0], x1, x2, x3),
                            max(currentpoint[1], y1, y2, y3)))
    
    def _bpath(self, currentpoint, currentsubpath):
        x2=currentpoint[0]+self.dx1
        y2=currentpoint[1]+self.dy1
        x3=currentpoint[0]+self.dx2
        y3=currentpoint[1]+self.dy2
        x4=currentpoint[0]+self.dx3

        y4=currentpoint[1]+self.dy3
        return ((x4, y4),
                currentsubpath or currentpoint,
                bpath._bcurve(currentpoint[0],currentpoint[1], x2, y2, x3, y3, x4, y4))


class rcurveto(_rcurveto):

    """Append rcurveto"""
        
    def __init__(self, dx1, dy1, dx2, dy2, dx3, dy3):
        _rcurveto.__init__(self,
                           unit.topt(dx1), unit.topt(dy1),
                           unit.topt(dx2), unit.topt(dy2),
                           unit.topt(dx3), unit.topt(dy3))


################################################################################
# path: PS style path 
################################################################################
        
class path(canvas.PSCommand):
    
    """PS style path"""
    
    def __init__(self, *args):
        self.path = list(args)
        
    def __add__(self, other):
        return path(*(self.path+other.path))

    def __len__(self):
        return len(self.path)

    def __getitem__(self, i):
        return self.path[i]

    def bbox(self):
        currentpoint = None
        currentsubpath = None
        abbox = canvas.bbox()
        
        for pel in self.path:
           (currentpoint, currentsubpath, nbbox) = \
                          pel._bbox(currentpoint, currentsubpath)
           if abbox: abbox = abbox+nbbox
           
        return abbox
        
    def write(self, file):
        if not (isinstance(self.path[0], _moveto) or
                isinstance(self.path[0], _arc) or
                isinstance(self.path[0], _arcn)):
            raise PathException, "first path element must be either moveto, arc, or arcn"
        for pel in self.path:
            pel.write(file)

    def append(self, pathel):
        self.path.append(pathel)

    def bpath(self):
        currentpoint = None
        currentsubpath = None
        bp = bpath.bpath()
        for pel in self.path:
            (currentpoint, currentsubpath, nbp) = \
                           pel._bpath(currentpoint, currentsubpath)
            if nbp:
                for bpel in nbp.bpath:
                    bp.append(bpel)
        return bp

# some special kinds of path, again in two variants

class _line(path):

   """straight line from (x1, y1) to (x2, y2) (coordinates in pts)"""

   def __init__(self, x1, y1, x2, y2):
       path.__init__(self, _moveto(x1,y1), _lineto(x2, y2))


class line(path):

   """straight line from (x1, y1) to (x2, y2)"""

   def __init__(self, x1, y1, x2, y2):
       path.__init__(self, moveto(x1,y1), lineto(x2, y2))
       

class _rect(path):

   """rectangle at position (x,y) with width and height (coordinates in pts)"""

   def __init__(self, x, y, width, height):
       path.__init__(self, _moveto(x,y), 
                           _rlineto(width,0), 
                           _rlineto(0,height), 
                           _rlineto(-width,0),
                           closepath())
       

class rect(path):

   """rectangle at position (x,y) with width and height"""

   def __init__(self, x, y, width, height):
       path.__init__(self, moveto(x,y), 
                           rlineto(width,0), 
                           rlineto(0,height), 
                           rlineto(-unit.length(width),0),
                           closepath())
