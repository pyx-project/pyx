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

import unit, canvas, math
from math import cos, sin, pi

class PathException(Exception): pass


################################################################################
# _bpathel: element of Bezier path (coordinates in pts)
################################################################################

class _bpathel:

    """element of Bezier path (coordinates in pts)"""
    
    def __init__(self, x0, y0, x1, y1, x2, y2, x3, y3):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.x3 = x3
        self.y3 = y3

    def write(self, file):
         file.write( "%f %f moveto %f %f %f %f %f %f curveto" % \
                     ( self.x0, self.y0,
                       self.x1, self.y1,
                       self.x2, self.y2,
                       self.x3, self.y3 ) )
                     

    def __getitem__(self, t):
        """return pathel at parameter value t (0<=t<=1)"""
        assert 0 <= t <= 1, "parameter t of pathel out of range [0,1]"
        return ( "%f t pt" % ((-self.x0+3*self.x1-3*self.x2+self.x3)*t*t*t +
                              (3*self.x0-6*self.x1+3*self.x2)*t*t +
                              (-3*self.x0+3*self.x1)*t +
                              self.x0) ,
                 "%f t pt" % ((-self.y0+3*self.y1-3*self.y2+self.y3)*t*t*t +
                              (3*self.y0-6*self.y1+3*self.y2)*t*t +
                              (-3*self.y0+3*self.y1)*t +
                              self.y0)
               )
    
    def bbox(self):
        return canvas.bbox(min(self.x0, self.x1, self.x2, self.x3), 
                           min(self.y0, self.y1, self.y2, self.y3), 
                           max(self.x0, self.x1, self.x2, self.x3), 
                           max(self.y0, self.y1, self.y2, self.y3))

    def MidPointSplit(self):
        """splits bpathel at midpoint returning bpath with two bpathels"""
        
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
        
        return bpath([_bpathel(self.x0, self.y0, x01, y01, x01_12, y01_12, xmidpoint, ymidpoint),
                      _bpathel(xmidpoint, ymidpoint, x12_23, y12_23, x23, y23, self.x3, self.y3)])

                       
class bpathel(_bpathel):

    """element of Bezier path"""
    
    def __init__(self, x0, y0, x1, y1, x2, y2, x3, y3):
        _bpathel.__init__(self, 
                          unit.topt(x0), unit.topt(y0),
                          unit.topt(x1), unit.topt(y1),
                          unit.topt(x2), unit.topt(y2),
                          unit.topt(x3), unit.topt(y3))


################################################################################
# bpath: Bezier path
################################################################################

class bpath:

    """path consisting of bezier curves"""
    
    def __init__(self, bpath=[]):
        self.bpath = bpath
	
    def append(self, bpathel):
        self.bpath.append(bpathel)

    def __add__(self, bp):
        return bpath(self.bpath+bp.bpath)

    def __len__(self):
        return len(self.bpath)

    def __getitem__(self, t):
        ' return path at parameter value t '
        
#        return self.bpath[int(t)][t-math.floor(t)]
        return self.bpath[t]

    def __str__(self):
        return reduce(lambda x,y: x+"%s\n" % str(y), self.bpath, "")

    def bbox(self):
        abbox = canvas.bbox()
        for bpel in self.bpath:
           abbox = abbox + bpel.bbox()
	return abbox

    def write(self, file):
        for bpel in self.bpath:
	    bpel.write(file)
            file.write("\n")

    def pos(self, t):
        return self.bpath[int(t)][t-math.floor(t)]

    def MidPointSplit(self):
        result = []
        for bpel in self.bpath:
            sbp = bpel.MidPointSplit()
            for sbpel in sbp:
                result.append(sbpel)
        return bpath(result)

    def intersect(self, other):
        """intersect two bpaths

        returns a list of tuples consisting of the corresponding parameters of the
        two bpaths"""

        intersections = ()
        (ta, tb) = (0,0)
        maxsubdiv = 5
        
        for s_bpel in self.bpath:
            ta = ta+1
            for o_bpel in other.bpath:
                tb = tb+1
                intersections = intersections + \
                                _bpathelIntersect(s_bpel, ta-1, ta, maxsubdiv,
                                                  o_bpel, tb-1, tb, maxsubdiv)

        return intersections

    __mul__ = intersect

class _bcurve(bpath):

    """bpath consisting of one bezier curve (coordinates in pts)"""
    
    def __init__(self, x0, y0, x1, y1, x2, y2, x3, y3):
        bpath.__init__(self, [_bpathel(x0, y0, x1, y1, x2, y2, x3, y3)]) 


class bcurve(bpath):

    """bpath consisting of one bezier curve"""
    
    def __init__(self, x0, y0, x1, y1, x2, y2, x3, y3):
        bpath.__init__(self, [bpathel(x0, y0, x1, y1, x2, y2, x3, y3)]) 


class _bline(bpath):

    """bpath consisting of one straight line (coordinates in pts)"""
    
    def __init__(self, x0, y0, x1, y1):
        xa = x0+(x1-x0)/3.0
        ya = y0+(y1-y0)/3.0
        xb = x0+2.0*(x1-x0)/3.0
        yb = y0+2.0*(y1-y0)/3.0
	
        bpath.__init__(self, 
                      [_bpathel(x0, y0, xa, ya, xb, yb, x1, y1 )]) 


class bline(_bline):

    """bpath consisting of one straight line"""
    
    def __init__(self, x0, y0, x1, y1):
        _bline.__init__(self, 
                        unit.topt(x0), unit.topt(y0), 
                        unit.topt(x1), unit.topt(y1)) 


class _barc(bpath):

    """bpath consisting of arc segment (coordinates in pts)"""

    def __init__(self, x, y, r, phi1, phi2, dphimax=pi/4):
        bpath.__init__(self, [])

        phi1 = phi1*pi/180
        phi2 = phi2*pi/180

        if phi2<phi1:        
	    # guarantee that phi2>phi1 ...
	    phi2 = phi2 + (math.floor((phi1-phi2)/(2*pi))+1)*2*pi
        elif phi2>phi1+2*pi:
   	    # ... or remove unnecessary multiples of 2*pi
	    phi2 = phi2 - (math.floor((phi2-phi1)/(2*pi))-1)*2*pi
            
        if r==0 or phi1-phi2==0: return

        subdivisions = abs(int((1.0*(phi1-phi2))/dphimax))+1

        dphi=(1.0*(phi2-phi1))/subdivisions

        for i in range(subdivisions):
            self.bpath.append(_arctobpathel(x, y, r, 
                                           phi1+i*dphi, phi1+(i+1)*dphi))


class barc(_barc):

    """bpath consisting of arc segment"""

    def __init__(self, x, y, r, phi1, phi2, dphimax=pi/4):
        _barc.__init__(self, 
                       unit.topt(x), unit.topt(y), unit.topt(r), 
                       phi1, phi2, dphimax)


################################################################################
# some helper routines            
################################################################################

def _arctobpathel(x, y, r, phi1, phi2):
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
    
    return _bpathel(x0, y0, x1, y1, x2, y2, x3, y3)


def _bpathelIntersect(a, a_t0, a_t1, a_subdiv, b, b_t0, b_t1, b_subdiv):
    """intersect two bpathels

    a and b are bpathels with parameter ranges [a_t0, a_t1],
    respectively [b_t0, b_t1] and a_subdiv, respectively
    b_subdiv subdivisions left.
    
    """

    # intersection of bboxes is a necessary criterium for intersection
    if not a.bbox().intersects(b.bbox()): return ()

    if a_subdiv>0:
        (aa, ab) = a.MidPointSplit()
        a_tm = 0.5*(a_t0+a_t1)

        if b_subdiv>0:
            (ba, bb) = b.MidPointSplit()
            b_tm = 0.5*(b_t0+b_t1)

            return ( _bpathelIntersect(aa, a_t0, a_tm, a_subdiv-1,
                                       ba, b_t0, b_tm, b_subdiv-1) + 
                     _bpathelIntersect(ab, a_tm, a_t1, a_subdiv-1,
                                       ba, b_t0, b_tm, b_subdiv-1) + 
                     _bpathelIntersect(aa, a_t0, a_tm, a_subdiv-1,
                                       bb, b_tm, b_t1, b_subdiv-1) +
                     _bpathelIntersect(ab, a_tm, a_t1, a_subdiv-1,
                                       bb, b_tm, b_t1, b_subdiv-1) )
        else:
            return ( _bpathelIntersect(aa, a_t0, a_tm, a_subdiv-1,
                                       b, b_t0, b_t1, b_subdiv) +
                     _bpathelIntersect(ab, a_tm, a_t1, a_subdiv-1,
                                       b, b_t0, b_t1, b_subdiv) )
    else:
        if b_subdiv>0:
            (ba, bb) = b.MidPointSplit()
            b_tm = 0.5*(b_t0+b_t1)

            return  ( _bpathelIntersect(a, a_t0, a_t1, a_subdiv,
                                        ba, b_t0, b_t1, b_subdiv-1) +
                      _bpathelIntersect(a, a_tm, a_t1, a_subdiv,
                                        ba, b_t0, b_tm, b_subdiv-1) )
        else:
            # no more subdivisions of either a or b
            # => try to intersect a and b as straight line segments

            a_deltax = a.x3 - a.x0
            a_deltay = a.y3 - a.y0
            b_deltax = b.x3 - b.x0
            b_deltay = b.y3 - b.y0
            
            det = b_deltax*a_deltay - b_deltay*a_deltax

            # check for parallel lines
            if 1.0+det==1.0: return ()

            ba_deltax0 = b.x0 - a.x0
            ba_deltay0 = b.y0 - a.y0

            a_t = ( b_deltax*ba_deltay0 - b_deltay*ba_deltax0)/det
            b_t = ( a_deltax*ba_deltay0 - a_deltay*ba_deltax0)/det

            # check for intersections out of bound
            if not ( 0<=a_t<=1 and 0<=b_t<=1): return ()

            # return rescaled parameters of the intersection
            return ( ( a_t0 + a_t * (a_t1 - a_t0),
                       b_t0 + b_t * (b_t1 - b_t0) ),
                   )
