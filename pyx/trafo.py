#!/usr/bin/env python

# affine trafos

class trafo:
    def __init__(self, matrix=((1,0),(0,1)), vector=(0,0)):
        self.matrix=matrix
        self.vector=vector

    def __mul__(self, other):
        if isinstance(other, trafo):
            matrix = ( ( self.matrix[0][0]*other.matrix[0][0] + self.matrix[0][1]*other.matrix[1][0],
                         self.matrix[0][0]*other.matrix[0][1] + self.matrix[0][1]*other.matrix[1][1] ),
                       ( self.matrix[1][0]*other.matrix[0][0] + self.matrix[1][1]*other.matrix[1][0],
                         self.matrix[1][0]*other.matrix[0][1] + self.matrix[1][1]*other.matrix[1][1] )
                     )
            vector = ( self.matrix[0][0]*other.vector[0] + self.matrix[0][1]*other.vector[1] + self.vector[0],
                       self.matrix[1][0]*other.vector[0] + self.matrix[1][1]*other.vector[1] + self.vector[1] )

            # print " ( %s * %s => %s ) "% (self, other, trafo(angle=angle, vector=vector))
		      
	    return trafo(matrix=matrix, vector=vector)
	else:
	    raise NotImplementedError, "can only multiply two trafos"
    def __rmul__(self, other):				# TODO: not needed!?
        print "!"
        return other.__mul__(self)

    def matrix():
        return self.matrix

    def vector(self):
        return self.vector

    def angle(self):
        return self.angle
    
    def translate(self,x,y):
	return trafo(vector=(x,y))*self
	
    def rotate(self,angle):
        from math import pi, cos, sin
	phi = 2*pi*angle/360
	
	matrix = (( cos(phi), sin(phi)), 
	          (-sin(phi), cos(phi)))
		  
	return trafo(matrix=matrix)*self

    def inverse(self):
        det = self.matrix[0][0]*self.matrix[1][1] - self.matrix[0][1]*self.matrix[1][0]
	# TODO: Better error handling, or is it ok to through ZeroDivisionError for singular matrices?
        matrix = ( ( self.matrix[1][1]/det, -self.matrix[0][1]/det),
	           (-self.matrix[1][0]/det,  self.matrix[0][0]/det)
		 )
        return trafo(matrix=matrix) * trafo(vector=(-self.vector[0],-self.vector[1]))
	
    def __repr__(self):
        return "matrix=%s, vector=%s" % (self.matrix, self.vector)

class translate(trafo):
    def __init__(self,x,y):
        trafo.__init__(self, vector=(x,y))
   
class rotate(trafo):
    def __init__(self,angle):
        from math import pi, cos, sin
	phi = 2*pi*angle/360
	
	matrix = (( cos(phi), sin(phi)), 
	          (-sin(phi), cos(phi)) )
		  
        trafo.__init__(self, matrix=matrix)
	
class mirror(trafo):
    def __init__(self,angle=0):
        from math import pi, cos, sin
	phi = 2*pi*angle/360

	matrix=( (cos(phi)*cos(phi)-sin(phi)*sin(phi), -2*sin(phi)*cos(phi)                ),
	         (-2*sin(phi)*cos(phi),                sin(phi)*sin(phi)-cos(phi)*cos(phi) ) )
       
        trafo.__init__(self, matrix=matrix)
        

if __name__=="__main__":
   # some invariants:
   #  trafo(angle=angle, vector=(x,y)) == translate(x,y) * rotate(angle)
   from math import pi, cos, sin
   angle = 15
   phi = 2*pi*angle/360
   matrix=((cos(phi), sin(phi)), (-sin(phi), cos(phi)))

   print translate(1,3) * rotate(15) 
   print trafo(matrix=matrix, vector=(1,3) )
   print
   
   # t*t.inverse() == 1
   t = translate(-1,-1)*rotate(72)*translate(1,1)
   print t*t.inverse()
   print trafo()
   print

   # -mirroring two times should yield identiy
   # -mirror(phi)=mirror(phi+180)

   print mirror(20)*mirror(20)
   print mirror(20)*mirror(180+20)
   print trafo()
   print
   
   # equivalent notations
   print translate(1,2).rotate(72).translate(-3,-1)
   print translate(-3,-1)*rotate(72)*translate(1,2)
   print
   
   print rotate(90).rotate(90).rotate(90).rotate(90)
   print trafo()
   print
   
  
