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
#       - implement bbox and _bpath for arct
#       - correct bbox for curveto and bpathel
#         (maybe we still need the current bbox implementation (then maybe called
#          cbox = control box) for bpathel for the use during the
#          intersection of bpaths) 
#       - intersection of bpaths: use estimate for number of subdivisions

import unit, canvas, math
from math import floor, cos, sin, pi
from canvas import bbox


class PathException(Exception): pass

################################################################################ 
# pathel: element of a PS style path 
################################################################################

class pathel:

    ' element of a PS style path '
    
    def bbox(self, canvas, currentpoint, currentsubpath):
	''' calculate bounding box of pathel

        returns tuple consisting of:
         - new currentpoint
         - new currentsubpath (i.e. first point of current subpath)
         - bounding box of pathel (using currentpoint and currentsubpath)
	
	Important note: all coordinates in bbox, currentpoint, and 
	currrentsubpath have to be floats (in the unit pt)
	'''

	pass

    def write(self, canvas, file):
	' write pathel to file in the context of canvas '
	
        pass
	
    def _bpath(self, currentpoint, currentsubpath):
	''' convert pathel to bpath 

        returns tuple consisting of:
         - new currentpoint
         - new currentsubpath (i.e. first point of current subpath)
         - bpath corresponding to pathel in the context of currentpoint and 
	   currentsubpath
	'''
	
        pass


class closepath(pathel): 
    ' Connect subpath back to its starting point '

    def bbox(self, canvas, currentpoint, currentsubpath):
	return (None,
                None, 
		bbox(min(currentpoint[0], currentsubpath[0]), 
  	             min(currentpoint[1], currentsubpath[1]), 
	             max(currentpoint[0], currentsubpath[0]), 
	             max(currentpoint[1], currentsubpath[1])))

    def write(self, canvas, file):
        file.write("closepath")

    def _bpath(self, currentpoint, currentsubpath):
        return (None,
                None,
                bline("%f t pt" % currentpoint[0], "%f t pt" % currentpoint[1], 
                       "%f t pt" % currentsubpath[0], "%f t pt" % currentsubpath[1]))
 
 
class moveto(pathel):
    ' Set current point to (x, y) '

    def __init__(self, x, y):
         self.x = unit.pt(x)
         self.y = unit.pt(y)

    def bbox(self, canvas, currentpoint, currentsubpath):
        return ((self.x, self.y), (self.x, self.y) , bbox())
	 
    def write(self, canvas, file):
        file.write("%f %f moveto" % (self.x, self.y) )

    def _bpath(self, currentpoint, currentsubpath):
        return ((self.x, self.y), (self.x, self.y) , None)


class rmoveto(pathel):
    ' Perform relative moveto '

    def __init__(self, dx, dy):
         self.dx = unit.pt(dx)
         self.dy = unit.pt(dy)
        
    def bbox(self, canvas, currentpoint, currentsubpath):
        return ((self.dx+currentpoint[0], self.dy+currentpoint[1]), 
                (self.dx+currentpoint[0], self.dy+currentpoint[1]),
		bbox())

    def write(self, canvas, file):
        file.write("%f %f rmoveto" % (self.dx, self.dy) )
        
    def _bpath(self, currentpoint, currentsubpath):
        return ((self.dx+currentpoint[0], self.dy+currentpoint[1]), 
                (self.dx+currentpoint[0], self.dy+currentpoint[1]),
		None)


class lineto(pathel):
    ' Append straight line to (x, y) '

    def __init__(self, x, y):
         self.x = unit.pt(x)
         self.y = unit.pt(y)
	 
    def bbox(self, canvas, currentpoint, currentsubpath):
        return ((self.x, self.y),
                currentsubpath or currentpoint,
                bbox(min(currentpoint[0], self.x), min(currentpoint[1], self.y), 
		     max(currentpoint[0], self.x), max(currentpoint[1], self.y)))

    def write(self, canvas, file):
        file.write("%f %f lineto" % (self.x, self.y) )
       
    def _bpath(self, currentpoint, currentsubpath):
        return ((self.x, self.y), 
                currentsubpath or currentpoint,
                bline(currentpoint[0], currentpoint[1], self.x, self.y))


class rlineto(pathel):
    ' Perform relative lineto '

    def __init__(self, dx, dy):
         self.dx = unit.pt(dx)
         self.dy = unit.pt(dy)

    def bbox(self, canvas, currentpoint, currentsubpath):
        return ((currentpoint[0]+self.dx, currentpoint[1]+self.dy),
                currentsubpath or currentpoint,
                bbox(min(currentpoint[0], currentpoint[0]+self.dx),
		     min(currentpoint[1], currentpoint[1]+self.dy), 
	 	     max(currentpoint[0], currentpoint[0]+self.dx),
		     max(currentpoint[1], currentpoint[1]+self.dy)))

    def write(self, canvas, file):
        file.write("%f %f rlineto" % (self.dx, self.dy) )
        
    def _bpath(self, currentpoint, currentsubpath):
        return ((currentpoint[0]+self.dx, currentpoint[1]+self.dy), 
                currentsubpath or currentpoint,
                bline("%f t pt" % currentpoint[0], "%f t pt" % currentpoint[1], 
                      "%f t pt" % (currentpoint[0]+self.dx), "%f t pt" % (currentpoint[1]+self.dy)))


class arc(pathel):
    ' Append counterclockwise arc '

    def __init__(self, x, y, r, angle1, angle2):
        self.x = unit.pt(x)
        self.y = unit.pt(y)
        self.r = unit.pt(r)
	self.angle1 = angle1
	self.angle2 = angle2

    def bbox(self, canvas, currentpoint, currentsubpath):
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
	    phi2 = phi2 + (floor((phi1-phi2)/(2*pi))+1)*2*pi

	# next minimum of cos(phi) looking from phi1 in counterclockwise 
	# direction: 2*pi*floor((phi1-pi)/(2*pi)) + 3*pi

	if phi2<(2*floor((phi1-pi)/(2*pi))+3)*pi:
	    minarcx = min(sarcx, earcx)
	else:
            minarcx = self.x-self.r

	# next minimum of sin(phi) looking from phi1 in counterclockwise 
	# direction: 2*pi*floor((phi1-3*pi/2)/(2*pi)) + 7/2*pi

	if phi2<(2*floor((phi1-3*pi/2)/(2*pi))+7.0/2)*pi:
	    minarcy = min(sarcy, earcy)
	else:
            minarcy = self.y-self.r

	# next maximum of cos(phi) looking from phi1 in counterclockwise 
	# direction: 2*pi*floor((phi1)/(2*pi))+2*pi

	if phi2<(2*floor((phi1)/(2*pi))+2)*pi:
	    maxarcx = max(sarcx, earcx)
	else:
            maxarcx = self.x+self.r

	# next maximum of sin(phi) looking from phi1 in counterclockwise 
	# direction: 2*pi*floor((phi1-pi/2)/(2*pi)) + 1/2*pi

	if phi2<(2*floor((phi1-pi/2)/(2*pi))+5.0/2)*pi:
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
                      bbox(min(currentpoint[0], sarcx),
		                  min(currentpoint[1], sarcy), 
			          max(currentpoint[0], sarcx),
			          max(currentpoint[1], sarcy))+
	              bbox(minarcx, minarcy, maxarcx, maxarcy)
                    )
        else:  # we assert that currentsubpath is also None
             return ( (earcx, earcy),
                      (sarcx, sarcy),
	              bbox(minarcx, minarcy, maxarcx, maxarcy)
                    )

			    
    def write(self, canvas, file):
        file.write("%f %f %f %f %f arc" % ( self.x, self.y,
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
                      bline("%f t pt" % currentpoint[0], "%f t pt" % currentpoint[1],
                            "%f t pt" % sarcx, "%f t pt" % sarcy) +
                      barc("%f t pt" % self.x, "%f t pt" % self.y, 
                           "%f t pt" % self.r, self.angle1, self.angle2)
                    )
        else:  # we assert that currentsubpath is also None
             return ( (earcx, earcy),
                      (sarcx, sarcy),
                      barc("%f t pt" % self.x, "%f t pt" % self.y, 
                           "%f t pt" % self.r, self.angle1, self.angle2)
                    )
	
class arcn(pathel):
    ' Append clockwise arc '
    
    def __init__(self, x, y, r, angle1, angle2):
        self.x = unit.pt(x)
        self.y = unit.pt(y)
        self.r = unit.pt(r)
	self.angle1 = angle1
	self.angle2 = angle2

    def bbox(self, canvas, currentpoint, currentsubpath):
        return arc("%f t pt" % self.x, "%f t pt" % self.y, 
                   "%f t pt" % self.r, 
		   self.angle2, self.angle1).bbox(canvas, currentpoint, currentsubpath)

    def write(self, canvas, file):
        file.write("%f %f %f %f %f arcn" % ( self.x, self.y,
                                             self.r,
                                             self.angle1,
                                             self.angle2 ) )

    def _bpath(self, currentpoint, currentsubpath):
        return arc("%f t pt" % self.x, "%f t pt" % self.y, 
                   "%f t pt" % self.r, 
		   self.angle2, self.angle1)._bpath(currentpoint,currentsubpath)

class arct(pathel):
    ' Append tangent arc '

    def __init__(self, x1, y1, x2, y2, r):
        self.x1 = unit.pt(x1)
	self.y1 = unit.pt(y1)
	self.x2 = unit.pt(x2)
	self.y2 = unit.pt(y2)
	self.r  = unit.pt(r)

    def write(self, canvas, file):
        file.write("%f %f %f %f %f arct" % ( self.x1, self.y1,
                                             self.x2, self.y2,
                                             self.r ) )

    def bbox(self, canvas, currentpoint, currentsubpath):
        return (currentpoint, currentsubpath, bbox(100,200,150,300))
    
    def _bpath(self, currentpoint, currentsubpath):
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

        return ((xt2, yt2),
                currentsubpath or (xt2, yt2),
                bline("%f t pt" % currentpoint[0], "%f t pt" % currentpoint[1], 
                      "%f t pt" % xt1, "%f t pt" % yt1) +
                arc("%f t pt" % mx, "%f t pt" % my,
                    "%f t pt" % self.r,
                    phi-deltaphi,
                    phi+deltaphi)._bpath(None, None)[2] )

	
class curveto(pathel):

    def __init__(self, x1, y1, x2, y2, x3, y3):
        self.x1 = unit.pt(x1)
	self.y1 = unit.pt(y1)
	self.x2 = unit.pt(x2)
	self.y2 = unit.pt(y2)
	self.x3 = unit.pt(x3)
	self.y3 = unit.pt(y3)
	
    def bbox(self, canvas, currentpoint, currentsubpath):
        return ((self.x3, self.y3),
                currentsubpath or currentpoint,
                bbox(min(currentpoint[0], self.x1, self.x2, self.x3), 
                     min(currentpoint[1], self.y1, self.y2, self.y3), 
 	             max(currentpoint[0], self.x1, self.x2, self.x3), 
                     max(currentpoint[1], self.y1, self.y2, self.y3)))

    def write(self, canvas, file):
        file.write("%f %f %f %f %f %f curveto" % ( self.x1, self.y1,
                                                   self.x2, self.y2,
                                                   self.x3, self.y3 ) )
        
    def _bpath(self, currentpoint, currentsubpath):
        return ((self.x3, self.y3),
                currentsubpath or currentpoint, 
                bcurve("%f t pt" % currentpoint[0], "%f t pt" % currentpoint[1],
                        "%f t pt" % self.x1, "%f t pt" % self.y1, 
                        "%f t pt" % self.x2, "%f t pt" % self.y2, 
                        "%f t pt" % self.x3, "%f t pt" % self.y3))


class rcurveto(pathel):
	
    def __init__(self, dx1, dy1, dx2, dy2, dx3, dy3):
        self.dx1 = unit.pt(dx1)
	self.dy1 = unit.pt(dy1)
	self.dx2 = unit.pt(dx2)
	self.dy2 = unit.pt(dy2)
	self.dx3 = unit.pt(dx3)
	self.dy3 = unit.pt(dy3)
	
    def write(self, canvas, file):
        file.write("%f %f %f %f %f %f rcurveto" % ( self.dx1, self.dy1,
                                                    self.dx2, self.dy2,
                                                    self.dx3, self.dy3 ) )

    def bbox(self, canvas, currentpoint, currentsubpath):
	x1=currentpoint[0]+self.dx1
	y1=currentpoint[1]+self.dy1
	x2=currentpoint[0]+self.dx2
	y2=currentpoint[1]+self.dy2
	x3=currentpoint[0]+self.dx3
	y3=currentpoint[1]+self.dy3
        return ((x3, y3),
                currentsubpath or currentpoint,
                bbox(min(currentpoint[0], x1, x2, x3), min(currentpoint[1], y1, y2, y3), 
 	             max(currentpoint[0], x1, x2, x3), max(currentpoint[1], y1, y2, y3)))
        
    def _bpath(self, currentpoint, currentsubpath):
        x2=currentpoint[0]+self.dx1
        y2=currentpoint[1]+self.dy1
        x3=currentpoint[0]+self.dx2
        y3=currentpoint[1]+self.dy2
        x4=currentpoint[0]+self.dx3
        y4=currentpoint[1]+self.dy3
        return ((x4, y4),
                currentsubpath or currentpoint,
                bcurve("%f t pt" % x2, "%f t pt" % y2, 
                       "%f t pt" % x3, "%f t pt" % y3, 
                       "%f t pt" % x4,"%f t pt" %  y4))

################################################################################
# path: PS style path 
################################################################################
	
class path:
    """ PS style path """
    def __init__(self, path=[]):
        self.path = path
        
    def __add__(self, other):
        return path(self.path+other.path)

    def __len__(self):
        return len(self.path)

    def __getitem__(self, i):
        return self.path[i]

    def bbox(self, canvas):
        currentpoint = None
        currentsubpath = None
        abbox = bbox()
        for pathel in self.path:
           (currentpoint, currentsubpath, nbbox) = pathel.bbox(canvas, currentpoint, currentsubpath)
           if abbox: abbox = abbox+nbbox
	return abbox
	
    def write(self, canvas, file):
	if not (isinstance(self.path[0], moveto) or
	        isinstance(self.path[0], arc) or
		isinstance(self.path[0], arcn)):
	    raise PathException, "first path element must be either moveto, arc, or arcn"
        for pathel in self.path:
	    pathel.write(canvas, file)
            file.write("\n")

    def append(self, pathel):
        self.path.append(pathel)

    def bpath(self):
        currentpoint = None
        currentsubpath = None
        bp = bpath([])
        for pathel in self.path:
            (currentpoint, currentsubpath, nbp) = pathel._bpath(currentpoint, currentsubpath)
            if nbp:
                for bpel in nbp:
                    bp.append(bpel)
        return bp

# some special kinds of path 

class line(path):
   def __init__(self, x1, y1, x2, y2):
       path.__init__(self, [ moveto(x1,y1), lineto(x2, y2) ] )


class rect(path):
   def __init__(self, x, y, width, height):
       path.__init__(self, [ moveto(x,y), 
                             rlineto(width,0), 
			     rlineto(0,height), 
			     rlineto(-unit.length(width),0),
			     closepath()] )

################################################################################
# bpathel: element of Bezier path
################################################################################

class bpathel:
    def __init__(self, x0, y0, x1, y1, x2, y2, x3, y3):
        self.x0 = unit.pt(x0)
        self.y0 = unit.pt(y0)
        self.x1 = unit.pt(x1)
        self.y1 = unit.pt(y1)
        self.x2 = unit.pt(x2)
        self.y2 = unit.pt(y2)
        self.x3 = unit.pt(x3)
        self.y3 = unit.pt(y3)

    def write(self, canvas, file):
         file.write( "%f %f moveto %f %f %f %f %f %f curveto" % \
                     ( self.x0, self.y0,
                       self.x1, self.y1,
                       self.x2, self.y2,
                       self.x3, self.y3 ) )
                     

    def __getitem__(self, t):
        ' return pathel at parameter value t (0<=t<=1) '

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
    
    def bbox(self, canvas):

        return bbox(min(self.x0, self.x1, self.x2, self.x3), 
                    min(self.y0, self.y1, self.y2, self.y3), 
                    max(self.x0, self.x1, self.x2, self.x3), 
                    max(self.y0, self.y1, self.y2, self.y3))

        

    def MidPointSplit(self):
        ' splits bpathel at midpoint returning bpath with two bpathels '
        
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
        
        return bpath([bpathel("%f t pt" % self.x0, "%f t pt" % self.y0, 
                              "%f t pt" % x01, "%f t pt" %  y01,
                              "%f t pt" % x01_12, "%f t pt" % y01_12,
                              "%f t pt" % xmidpoint, "%f t pt" % ymidpoint),
                      bpathel("%f t pt" % xmidpoint, "%f t pt" % ymidpoint, 
                              "%f t pt" % x12_23, "%f t pt" % y12_23,
                              "%f t pt" % x23, "%f t pt" % y23,
                              "%f t pt" % self.x3, "%f t pt" % self.y3)])
                       

################################################################################
# bpath: Bezier path
################################################################################

class bpath:
    """ path consisting of bezier curves"""
    
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
        
#        return self.bpath[int(t)][t-floor(t)]
        return self.bpath[t]

    def __str__(self):
        return reduce(lambda x,y: x+"%s\n" % str(y), self.bpath, "")

    def bbox(self, canvas):
        abbox = bbox()
        for bpathel in self.bpath:
           abbox = abbox + bpathel.bbox(canvas)
	return abbox

    def write(self, canvas, file):
        for bpathel in self.bpath:
	    bpathel.write(canvas, file)
            file.write("\n")


    def pos(self, t):
        return self.bpath[int(t)][t-floor(t)]

    def MidPointSplit(self):
        result = []
        for bpel in self.bpath:
            sbp = bpel.MidPointSplit()
            for sbpel in sbp:
                result.append(sbpel)
        return bpath(result)

    def intersect(self, canvas, other):
        """ intersect two bpaths

        returns a list of tuples consisting of the corresponding parameters of the
        two bpaths """

        intersections = ()
        (ta, tb) = (0,0)
        maxsubdiv = 5
        
        for s_bpel in self.bpath:
            ta = ta+1
            for o_bpel in other.bpath:
                tb = tb+1
                intersections = intersections + \
                                bpathelIntersect(canvas,
                                                 s_bpel, ta-1, ta, maxsubdiv,
                                                 o_bpel, tb-1, tb, maxsubdiv)

        return intersections


class bcurve(bpath):
    """ bpath consisting of one bezier curve"""
    
    def __init__(self, x0, y0, x1, y1, x2, y2, x3, y3):
        bpath.__init__(self, [bpathel(x0, y0, x1, y1, x2, y2, x3, y3)]) 


class bline(bpath):
    """ bpath consisting of one straight line"""
    
    def __init__(self, x0, y0, x1, y1):
        x0 = unit.pt(x0)
        y0 = unit.pt(y0)
        x1 = unit.pt(x1)
        y1 = unit.pt(y1)
        xa = x0+(x1-x0)/3.0
        ya = y0+(y1-y0)/3.0
        xb = x0+2.0*(x1-x0)/3.0
        yb = y0+2.0*(y1-y0)/3.0
        bpath.__init__(self, 
                      [bpathel("%f t pt" % x0, "%f t pt" % y0, 
                               "%f t pt" % xa, "%f t pt" % ya,
                               "%f t pt" % xb, "%f t pt" % yb,
                               "%f t pt" % x1, "%f t pt" % y1 )]) 


class barc(bpath):
    def __init__(self, x, y, r, phi1, phi2, dphimax=pi/4):

        phi1 = phi1*pi/180
        phi2 = phi2*pi/180

        if phi2<phi1:        
	    # guarantee that phi2>phi1 ...
	    phi2 = phi2 + (floor((phi1-phi2)/(2*pi))+1)*2*pi
        elif phi2>phi1+2*pi:
   	    # ... or remove unnecessary multiples of 2*pi
	    phi2 = phi2 - (floor((phi2-phi1)/(2*pi))-1)*2*pi
            
        if r==0 or phi1-phi2==0: return None

        subdivisions = abs(int((1.0*(phi1-phi2))/dphimax))+1

        dphi=(1.0*(phi2-phi1))/subdivisions

        self.bpath = []    

        for i in range(subdivisions):
            self.bpath.append(arctobpathel(unit.pt(x), unit.pt(y), unit.pt(r), phi1+i*dphi, phi1+(i+1)*dphi))

################################################################################
# some helper routines            
################################################################################

def arctobpathel(x, y, r, phi1, phi2):
    ' generate the best bpathel corresponding to an arc segment '
    
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
    
    return bpathel("%f t pt" % x0, "%f t pt" % y0, 
                   "%f t pt" % x1, "%f t pt" % y1,
                   "%f t pt" % x2, "%f t pt" % y2,
                   "%f t pt" % x3, "%f t pt" % y3)

def bpathelIntersect(canvas,
                     a, a_t0, a_t1, a_subdiv,
                     b, b_t0, b_t1, b_subdiv):
    """ intersect two bpathels

    a and b are bpathels with parameter ranges [a_t0, a_t1],
    respectively [b_t0, b_t1] and a_subdiv, respectively
    b_subdiv subdivisions left. """

    # intersection of bboxes is a necessary criterium for intersection
    if not a.bbox(canvas).intersects(b.bbox(canvas)): return ()

    if a_subdiv>0:
        (aa, ab) = a.MidPointSplit()
        a_tm = 0.5*(a_t0+a_t1)

        if b_subdiv>0:
            (ba, bb) = b.MidPointSplit()
            b_tm = 0.5*(b_t0+b_t1)

            return ( bpathelIntersect(canvas,
                                      aa, a_t0, a_tm, a_subdiv-1,
                                      ba, b_t0, b_tm, b_subdiv-1) + 
                     bpathelIntersect(canvas,
                                      ab, a_tm, a_t1, a_subdiv-1,
                                      ba, b_t0, b_tm, b_subdiv-1) + 
                     bpathelIntersect(canvas,
                                      aa, a_t0, a_tm, a_subdiv-1,
                                      bb, b_tm, b_t1, b_subdiv-1) +
                     bpathelIntersect(canvas,
                                      ab, a_tm, a_t1, a_subdiv-1,
                                      bb, b_tm, b_t1, b_subdiv-1) )
        else:
            return ( bpathelIntersect(canvas,
                                      aa, a_t0, a_tm, a_subdiv-1,
                                      b, b_t0, b_t1, b_subdiv) +
                     bpathelIntersect(canvas,
                                      ab, a_tm, a_t1, a_subdiv-1,
                                      b, b_t0, b_t1, b_subdiv) )
    else:
        if b_subdiv>0:
            (ba, bb) = b.MidPointSplit()
            b_tm = 0.5*(b_t0+b_t1)

            return  ( bpathelIntersect(canvas,
                                       a, a_t0, a_t1, a_subdiv,
                                       ba, b_t0, b_t1, b_subdiv-1) +
                      bpathelIntersect(canvas,
                                       a, a_tm, a_t1, a_subdiv,
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
