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

import math
import base, bbox, unit

# TODO: 
# - switch to affine space description (i.e. represent transformation by
#   3x3 matrix (cf. PLRM Sect. 4.3.3)? Cooler!

# some helper routines

def _rmatrix(angle):
    phi = math.pi*angle/180.0
    
    return  (( math.cos(phi), math.sin(phi)), 
             (-math.sin(phi), math.cos(phi)))

def _rvector(angle, x, y):
    phi = math.pi*angle/180.0
    
    return  ((1-math.cos(phi))*x + math.sin(phi)    *y,
              -math.sin(phi)   *x + (1-math.cos(phi))*y)


def _mmatrix(angle):
    phi = math.pi*angle/180.0
    
    return ( (math.cos(phi)*math.cos(phi)-math.sin(phi)*math.sin(phi),
              -2*math.sin(phi)*math.cos(phi)                ),
             (-2*math.sin(phi)*math.cos(phi),
              math.sin(phi)*math.sin(phi)-math.cos(phi)*math.cos(phi) ) )

def _det(matrix):
    return matrix[0][0]*matrix[1][1] - matrix[0][1]*matrix[1][0]

# Exception

class UndefinedResultError(ArithmeticError):
    pass

# trafo: affine transformations
             
class _trafo(base.PSAttr):

    """affine transformation (coordinates in constructor in pts)

    Note that though the coordinates in the constructor are in
    pts (which is useful for internal purposes), all other
    methods only accept units in the standard user notation.
    """
    
    def __init__(self, matrix=((1,0),(0,1)), vector=(0,0)):
        if _det(matrix)==0:             
            raise UndefinedResultError, "transformation matrix must not be singular" 
        else:
            self.matrix=matrix
        self.vector = vector

    def __mul__(self, other):
        if isinstance(other, _trafo):
            matrix = ( ( self.matrix[0][0]*other.matrix[0][0] +
                         self.matrix[0][1]*other.matrix[1][0],
                         self.matrix[0][0]*other.matrix[0][1] +
                         self.matrix[0][1]*other.matrix[1][1] ),
                       ( self.matrix[1][0]*other.matrix[0][0] +
                         self.matrix[1][1]*other.matrix[1][0],
                         self.matrix[1][0]*other.matrix[0][1] +
                         self.matrix[1][1]*other.matrix[1][1] )
                     )

            vector = ( self.matrix[0][0]*other.vector[0] +
                       self.matrix[1][0]*other.vector[1] +
                       self.vector[0],
                       self.matrix[0][1]*other.vector[0] +
                       self.matrix[1][1]*other.vector[1] +
                       self.vector[1] )

            return _trafo(matrix=matrix, vector=vector)
        else:
            raise NotImplementedError, "can only multiply two transformations"

    def __str__(self):
        return "[%f %f %f %f %f %f] concat\n" % \
               ( self.matrix[0][0], self.matrix[0][1], 
                 self.matrix[1][0], self.matrix[1][1], 
                 self.vector[0], self.vector[1] ) 

    def write(self, file):
        file.write("[%f %f %f %f %f %f] concat\n" % \
                    ( self.matrix[0][0], self.matrix[0][1], 
                      self.matrix[1][0], self.matrix[1][1], 
                      self.vector[0], self.vector[1] ) )

    def bbox(self):
        return bbox.bbox()

    def _apply(self, x, y):
        """apply transformation to point (x,y) (coordinates in pts)"""
        return (self.matrix[0][0]*x +
                self.matrix[1][0]*y +
                self.vector[0],
                self.matrix[0][1]*x +
                self.matrix[1][1]*y +
                self.vector[1])

    def apply(self, x, y):
        # before the transformation, we first have to convert to
        # our internal unit (i.e. pts)
        tx, ty = self._apply(unit.topt(x), unit.topt(y))
        
        # the end result can be converted back to general lengths
        return (unit.t_pt(tx), unit.t_pt(ty))

    def inverse(self):
        det = _det(self.matrix)                       # shouldn't be zero, but
        try: 
          matrix = ( ( self.matrix[1][1]/det, -self.matrix[0][1]/det),
                     (-self.matrix[1][0]/det,  self.matrix[0][0]/det)
                   )
        except ZeroDivisionError:
           raise UndefinedResultError, "transformation matrix must not be singular" 
        return _trafo(matrix=matrix) * \
               _trafo(vector=(-self.vector[0], -self.vector[1]))

    def translate(self, x, y):
        return translate(x, y)*self

    def _translate(self, x, y):
        return _translate(x,y)*self
        
    def rotate(self, angle, x=None, y=None):
        return rotate(angle, x, y)*self

    def _rotate(self, angle, x=None, y=None):
        return _rotate(angle, x, y)*self
        
    def mirror(self, angle):
        return mirror(angle)*self

    def scale(self, sx, sy=None, x=None, y=None):
        return scale(sx, sy, x, y)*self
    
    def _scale(self, sx, sy=None, x=None, y=None):
        return _scale(sx, sy, x, y)*self


class trafo(_trafo):

    """affine transformation"""
    
    def __init__(self, matrix=((1,0),(0,1)), vector=(0,0)):
        _trafo.__init__(self,
                        matrix,
                        (unit.topt(vector[0]), unit.topt(vector[1])))


class _translate(_trafo):
    def __init__(self, x, y):
        _trafo.__init__(self, vector=(x, y))
        
        
class translate(trafo):
    def __init__(self, x, y):
        trafo.__init__(self, vector=(x, y))

   
class _rotate(_trafo):
    def __init__(self, angle, x=None, y=None):
        vector = 0, 0
        if x is not None or y is not None:
            if x is None or y is None:
                raise (UndefinedResultError, 
                       "either specify both x and y or none of them")
            vector=_rvector(angle, x, y)
            
        _trafo.__init__(self,
                       matrix=_rmatrix(angle),
                       vector=vector)


class rotate(_trafo):
    def __init__(self, angle, x=None, y=None):
        vector = 0, 0 
        if x is not None or y is not None:
            if x is None or y is None:
                raise (UndefinedResultError, 
                       "either specify both x and y or none of them")
            vector=_rvector(angle, unit.topt(x), unit.topt(y))

        _trafo.__init__(self,
                       matrix=_rmatrix(angle),
                       vector=vector)
        
        
class mirror(trafo):
    def __init__(self,angle=0):
        trafo.__init__(self, matrix=_mmatrix(angle))

class _scale(_trafo):
    def __init__(self, sx, sy=None, x=None, y=None):
        sy=sy or sx
        if not sx or not sy:
            raise (UndefinedResultError, 
                   "one scaling factor is 0")
        vector = 0, 0 
        if x is not None or y is not None:
            if x is None or y is None:
                raise (UndefinedResultError, 
                       "either specify both x and y or none of them")
            vector=(1-sx)*x, (1-sy)*y
            
        _trafo.__init__(self, matrix=((sx,0),(0,sy)), vector=vector)


class scale(trafo):
    def __init__(self, sx, sy=None, x=None, y=None):
        sy=sy or sx
        if not sx or not sy:
            raise (UndefinedResultError, 
                   "one scaling factor is 0")
        vector = 0, 0 
        if x is not None or y is not None:
            if x is None or y is None:
                raise (UndefinedResultError, 
                       "either specify both x and y or none of them")
            vector=(1-sx)*x, (1-sy)*y
            
        trafo.__init__(self, matrix=((sx,0),(0,sy)), vector=vector)

        

if __name__=="__main__":
   # test for some invariants:

   def checkforidentity(trafo):
       m = max(map(abs,[trafo.matrix[0][0]-1,
                        trafo.matrix[1][0],
                        trafo.matrix[0][1],
                        trafo.matrix[1][1]-1,
                        unit.topt(trafo.vector[0]),
                        unit.topt(trafo.vector[1])]))

       assert m<1e-7, "tests for invariants failed" 

   # trafo(angle=angle, vector=(x,y)) == translate(x,y) * rotate(angle)
   checkforidentity( translate(1,3) *
                     rotate(15) *
                     trafo(matrix=_rmatrix(15),vector=(1,3)).inverse())
   
   # t*t.inverse() == 1
   t = translate(-1,-1)*rotate(72)*translate(1,1)
   checkforidentity(t*t.inverse())

   # -mirroring two times should yield identiy
   # -mirror(phi)=mirror(phi+180)
   checkforidentity( mirror(20)*mirror(20)) 
   checkforidentity( mirror(20).mirror(20)) 
   checkforidentity( mirror(20)*mirror(180+20))
   
   # equivalent notations
   checkforidentity( rotate(72).translate(1,2)*
                     (translate(1,2)*rotate(72)).inverse())
   checkforidentity( rotate(72,1,2)*(translate(-1,-2).rotate(72).translate(1,2)).inverse())
   
   checkforidentity( translate(1,2).rotate(72).translate(-3,-1)*
                     (translate(-3,-1)*rotate(72)*translate(1,2)).inverse() )
   
   checkforidentity( rotate(40).rotate(120).rotate(90).rotate(110) )

   checkforidentity( scale(2,3).scale(1/2.0, 1/3.0) )

   def applyonbasis(t):
       print "%s:" % t
       t=eval(t)
       esx=t.apply(1,0)
       esy=t.apply(0,1)
       print "  (1,0) => (%f, %f)" % (unit.tom(esx[0])*100, unit.tom(esx[1])*100)
       print "  (0,1) => (%f, %f)" % (unit.tom(esy[0])*100, unit.tom(esy[1])*100)

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


