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

import unit, canvas

# TODO: 
# - switch to affine space description (i.e. represent transformation by
#   3x3 matrix (cf. PLRM Sect. 4.3.3)? Cooler!
#

# some helper routines

def _rmatrix(angle):
    from math import pi, cos, sin
    phi = 2*pi*angle/360
	
    return  (( cos(phi), sin(phi)), 
             (-sin(phi), cos(phi)))

def _mmatrix(angle):
    from math import pi, cos, sin
    phi = 2*pi*angle/360
    
    return ( (cos(phi)*cos(phi)-sin(phi)*sin(phi), -2*sin(phi)*cos(phi)                ),
	     (-2*sin(phi)*cos(phi),                sin(phi)*sin(phi)-cos(phi)*cos(phi) ) )

def _det(matrix):
    return matrix[0][0]*matrix[1][1] - matrix[0][1]*matrix[1][0]

# Exception

class UndefinedResultError(ArithmeticError):
    pass

# transformation: affine transformations
	     
class transformation:
    def __init__(self, matrix=((1,0),(0,1)), vector=(0,0)):
        if _det(matrix)==0:		
	    raise UndefinedResultError, "transformation matrix must not be singular" 
	else:
            self.matrix=matrix

        self.vector = ( unit.pt(vector[0]), unit.pt(vector[1]) )

    def __mul__(self, other):
        if isinstance(other, transformation):
            matrix = ( ( self.matrix[0][0]*other.matrix[0][0] + self.matrix[0][1]*other.matrix[1][0],
                         self.matrix[0][0]*other.matrix[0][1] + self.matrix[0][1]*other.matrix[1][1] ),
                       ( self.matrix[1][0]*other.matrix[0][0] + self.matrix[1][1]*other.matrix[1][0],
                         self.matrix[1][0]*other.matrix[0][1] + self.matrix[1][1]*other.matrix[1][1] )
                     )

            vector = ( self.matrix[0][0]*other.vector[0] + self.matrix[1][0]*other.vector[1] + self.vector[0],
                       self.matrix[0][1]*other.vector[0] + self.matrix[1][1]*other.vector[1] + self.vector[1] )

            # print " ( %s * %s => %s ) "% (self, other, transformation(angle=angle, vector=vector))
		      
	    return transformation(matrix=matrix, vector=("%f t pt" % vector[0], "%f t pt" % vector[1]))
	else:
	    raise NotImplementedError, "can only multiply two transformations"
    def __rmul__(self, other):				# TODO: not needed!?
        return other.__mul__(self)

    def apply(self, point):
	return (self.matrix[0][0]*point[0] + self.matrix[1][0]*point[1]+self.vector[0],
                self.matrix[0][1]*point[0] + self.matrix[1][1]*point[1]+self.vector[1])

    def matrix():
        return self.matrix

    def vector(self):
        return self.vector

    def angle(self):
        return self.angle
    
    def translate(self,x,y):
	return transformation(vector=(x,y))*self
	
    def rotate(self,angle):
	return transformation(matrix=_rmatrix(angle))*self
	
    def mirror(self,angle):
	return transformation(matrix=_mmatrix(angle))*self

    def scale(self, x, y=None):
        return transformation(matrix=((x, 0), (0,y or x)))*self

    def inverse(self):
        det = _det(self.matrix)				# shouldn't be zero, but
	try: 
          matrix = ( ( self.matrix[1][1]/det, -self.matrix[0][1]/det),
	             (-self.matrix[1][0]/det,  self.matrix[0][0]/det)
	 	   )
        except ZeroDivisionError:
	   raise UndefinedResultError, "transformation matrix must not be singular" 
        return transformation(matrix=matrix) * \
               transformation(vector=("% t pt" % -self.vector[0],"% t pt" % -self.vector[1]))

    def bbox(self, acanvas):
        # assert 0, "this shouldn't be called!"
        return canvas.bbox()

    def write(self, canvas, file):
        file.write("[%f %f %f %f %f %f] concat\n" % \
	            ( self.matrix[0][0], self.matrix[0][1], 
	              self.matrix[1][0], self.matrix[1][1], 
		      self.vector[0], self.vector[1] ) )
	

class translate(transformation):
    def __init__(self,x,y):
        transformation.__init__(self, vector=(x,y))
   
class rotate(transformation):
    def __init__(self,angle):
        transformation.__init__(self, matrix=_rmatrix(angle))
	
class mirror(transformation):
    def __init__(self,angle=0):
        transformation.__init__(self, matrix=_mmatrix(angle))

class scale(transformation):
    def __init__(self,x,y=None):
        transformation.__init__(self, matrix=((x,0),(0,y or x)))
        

if __name__=="__main__":
   # test for some invariants:

   def checkforidentity(trafo):
       u=unit.unit()
       m = max(map(abs,[trafo.matrix[0][0]-1,
                        trafo.matrix[1][0],
                        trafo.matrix[0][1],
                        trafo.matrix[1][1]-1,
	                u.pt(trafo.vector[0]),
	                u.pt(trafo.vector[1])]))
		    
       assert m<1e-7, "tests for invariants failed" 
	    

   # transformation(angle=angle, vector=(x,y)) == translate(x,y) * rotate(angle)
   checkforidentity( translate(1,3) * rotate(15)  * transformation(matrix=_rmatrix(15),vector=(1,3)).inverse())
   
   # t*t.inverse() == 1
   t = translate(-1,-1)*rotate(72)*translate(1,1)
   checkforidentity(t*t.inverse())

   # -mirroring two times should yield identiy
   # -mirror(phi)=mirror(phi+180)
   checkforidentity( mirror(20)*mirror(20)) 
   checkforidentity( mirror(20).mirror(20)) 
   checkforidentity( mirror(20)*mirror(180+20))
   
   # equivalent notations
   checkforidentity( translate(1,2).rotate(72).translate(-3,-1)*(translate(-3,-1)*rotate(72)*translate(1,2)).inverse() )
   
   checkforidentity( rotate(40).rotate(120).rotate(90).rotate(110) )

   checkforidentity( scale(2,3).scale(1/2.0, 1/3.0) )

   def applyonbasis(t):
       u=unit.unit()
       ex = (1,0)
       ey = (0,1)
       print "%s:" % t
       t=eval(t)
       esx=t.apply(ex)
       esy=t.apply(ey)
       print "  (1,0) => (%f, %f)" % (u.m(esx[0])*100, u.m(esx[1])*100)
       print "  (0,1) => (%f, %f)" % (u.m(esy[0])*100, u.m(esy[1])*100)

   applyonbasis("translate(1,0)")
   applyonbasis("translate(0,1)")
   applyonbasis("rotate(90)")
   applyonbasis("scale(0.5)")
   applyonbasis("translate(1,0)*rotate(90)")
   applyonbasis("translate(1,0)*scale(0.5)")
   applyonbasis("rotate(90)*translate(1,0)")
   applyonbasis("scale(0.5)*translate(1,0)")
   applyonbasis("translate(1,0)*rotate(90)*scale(0.5)")
   applyonbasis("translate(1,0)*scale(0.5)*rotate(90)")
   applyonbasis("rotate(90)*scale(0.5)*translate(1,0)")
   applyonbasis("scale(0.5)*rotate(90)*translate(1,0)")


