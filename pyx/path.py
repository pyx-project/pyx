#!/usr/bin/env python

import unit, math
from math import cos, sin, pi

class PathException(Exception): pass

# 
# pathel: element of a PS style path 
#

# TODO: - reversepath ?
#       - strokepath ?
#       - check if restriction on first element of path being a moveto is really valid, e.g. arc???

class pathel:

    ' element of a PS style path '
    
    def __init__(self, command, args):
        ' new pathel of type "command" and with an argument tuple args '
        self.command = command
        self.args = args

    def draw(self, canvas):
        pass

# path elements without argument

class closepath(pathel): 
    ' Connect subpath back to its starting point '
    def __init__(self):
        pathel.__init__(self, "closepath", None)
    def draw(self, canvas):
        canvas._PSAddCmd(self.command)
    def ConvertToBezier(self, currentpoint, currentsubpath):
        return (None,
                None,
                bline(currentpoint[0], currentpoint[1], 
                       currentsubpath[0], currentsubpath[1]))
  
# path elements with 2 arguments  

class _pathel2(pathel):

    ' element of a path with args=(x,y), used for r?(move|line)to'
    def __init__(self, x, y):
         (self.x, self.y)=(x,y)
    
    def draw(self, canvas):
        canvas._PSAddCmd("%f %f %s" % (canvas.unit.pt(self.args[0]), 
                                       canvas.unit.pt(self.args[1]), 
                                       self.command ) )
        #canvas._PSAddCmd("%f %f " % (0,0) + self.command )

class moveto(_pathel2):
    ' Set current point to (x, y) '
        
    def draw(self, canvas):
        canvas._PSAddCmd("%f %f moveto" % (canvas.unit.pt(self.x), canvas.unit.pt(self.y) ) )

    def ConvertToBezier(self, currentpoint, currentsubpath):
        return ((self.x, self.y), currentsubpath, None)
	
class rmoveto(_pathel2):
    ' Perform relative moveto '
        
    def draw(self, canvas):
        canvas._PSAddCmd("%f %f rmoveto" % (canvas.unit.pt(self.x), canvas.unit.pt(self.y) ) )
        
    def ConvertToBezier(self, currentpoint, currentsubpath):
        return ((self.x+currentpoint[0], currentsubpath, self.y+currentpoint[1]), None)
	
class lineto(_pathel2):
    ' Append straight line to (x, y) '

    def draw(self, canvas):
        canvas._PSAddCmd("%f %f lineto" % (canvas.unit.pt(self.x), canvas.unit.pt(self.y) ) )
        
    def ConvertToBezier(self, currentpoint, currentsubpath):
        return (self.args, 
                currentsubpath or currentpoint,
                bline(currentpoint[0], currentpoint[1], self.x, self.y))
	
class rlineto(_pathel2):
    ' Perform relative lineto '

    def draw(self, canvas):
        canvas._PSAddCmd("%f %f rlineto" % (canvas.unit.pt(self.x), canvas.unit.pt(self.y) ) )
        
    def ConvertToBezier(self, currentpoint, currentsubpath):
        return ((self.args[0]+currentpoint[0], self.args[1]+currentpoint[1]), 
                currentsubpath or currentpoint,
                bline(currentpoint[0], currentpoint[1], 
                      currentpoint[0]+self.x, currentpoint[1]+self.y))

# path elements with 5 arguments

class _pathelarc(pathel):
    def __init__(self, x, y, r, angle1, angle2):
        (self.x, self.y, self.r, self.angle1, self.angle2) = (x, y, r, angle1, angle2)
        
 
class arc(_pathelarc):
    ' Append counterclockwise arc '

    def draw(self, canvas):
        canvas._PSAddCmd("%f %f %f %f %f arc" % ( canvas.unit.pt(self.x),
                                                  canvas.unit.pt(self.y),
                                                  canvas.unit.pt(self.r),
                                                  self.angle1,
                                                  self.angle2 ) )
        
    def ConvertToBezier(self, currentpoint, currentsubpath):
         if currentpoint:
             return ( (self.x+self.r*math.cos(self.angle2), self.y+self.r*math.sin(aself.ngle2) ),
                      currentsubpath or currentpoint,
                      bline(currentpoint[0], 
                            currentpoint[1], 
                            self.x+self.r*math.cos(math.pi*self.angle1/180), 
                            self.y+self.r*math.sin(math.pi*self.angle1/180))+
                      barc(self.x, self.y, self.r, self.angle1, self.angle2)
                    )
         else:  # we assert that curretsubpath is also None
             return ( (self.x+self.r*math.cos(math.pi*self.angle2/180), 
                       self.y+r*math.sin(math.pi*self.angle2/180)),
                      (self.x+self.r*math.cos(math.pi*self.angle1/180),
                       self.y+r*math.sin(math.pi*self.angle1/180)),
                      barc(self.x, self.y, self.r, self.angle1, self.angle2)
                    )
    
	
class arcn(_pathelarc):
    ' Append clockwise arc '

    def draw(self, canvas):
        canvas._PSAddCmd("%f %f %f %f %f arcn" % ( canvas.unit.pt(self.x),
                                                   canvas.unit.pt(self.y),
                                                   canvas.unit.pt(self.r),
                                                   self.angle1,
                                                   self.angle2 ) )

class arct(pathel):
    ' Append tangent arc '
    def __init__(self, x1, y1, x2, y2, r):
        (self.x1, self.y1, self.x2, self.y2, self.r) = (x1, y1, x2, y2, r)
    def draw(self, canvas):
        canvas._PSAddCmd("%f %f %f %f %f arct" % ( canvas.unit.pt(self.x1),
                                                   canvas.unit.pt(self.y1),
                                                   canvas.unit.pt(self.x2),
                                                   canvas.unit.pt(self.y2),
                                                   canvas.unit.pt(self.r) ) )
        
	
# path elements with 6 arguments

class _pathel6(pathel):
    def __init__(self, x1, y1, x2, y2, x3, y3):
        (self.x1, self.y1, self.x2, self.y2, self.x3, self.y3) = (x1, y1, x2, y2, x3, y3)

class curveto(_pathel6):
    def draw(self, canvas):
        canvas._PSAddCmd("%f %f %f %f %f %f curveto" % ( canvas.unit.pt(self.x1),
                                                         canvas.unit.pt(self.y1),
                                                         canvas.unit.pt(self.x2),
                                                         canvas.unit.pt(self.y2),
                                                         canvas.unit.pt(self.x3),
                                                         canvas.unit.pt(self.y3)) )
        
    def ConvertToBezier(self, currentpoint):
        return ((self.x3, self.y3), 
                bcurve(currentpoint[0], currentpoint[1],
                        self.x1, self.y1, self.x2, self.y2, self.x3, self.y3))

class rcurveto(_pathel6):
    def draw(self, canvas):
        canvas._PSAddCmd("%f %f %f %f %f %f rcurveto" % ( canvas.unit.pt(self.x1),
                                                          canvas.unit.pt(self.y1),
                                                          canvas.unit.pt(self.x2),
                                                          canvas.unit.pt(self.y2),
                                                          canvas.unit.pt(self.x3),
                                                          canvas.unit.pt(self.y3)) )
        
    def ConvertToBezier(self, currentpoint):
        x2=currenpoint(0)+self.x1
        y2=currenpoint(1)+self.y1
        x3=currenpoint(0)+self.x2
        y3=currenpoint(1)+self.y2
        x4=currenpoint(0)+self.x3
        y4=currenpoint(1)+self.y3
        return ((x4, y4), bcurve(x2, y2, x3, y3, x4, y4))

#
# path: PS style path 
#
	
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
	
    def draw(self, canvas):
	if not isinstance(self.path[0], moveto): 
	    raise PathException, "first path element must be moveto"    # TODO: also arc, arcn, arcto
        print "1"
        for pathel in self.path:
	    pathel.draw(canvas)
        print "2"

    def append(self, pathel):
        self.path.append(pathel)

#    def extend(self, pathel):
#        self.path.extend(pathel)

    def ConvertToBezier(self):
        currentpoint   = None
        currentsubpath = None
        self.bpath     = bpath()
        for pathel in self.path:
           (currentpoint, currentsubpath, bp) = pathel.ConvertToBezier(currentpoint, currentsubpath)
           if bp: self.bpath.extend(bp)

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

class bpathel:
    def __init__(self, x0, y0, x1, y1, x2, y2, x3, y3):
        self.cpoints = (x0, y0, x1, y1, x2, y2, x3, y3)

    def __str__(self):
        return "%f %f moveto %f %f %f %f %f %f curveto" % self.cpoints
        
class bpath:
    """ path consisting of bezier curves"""
    def __init__(self, bpath=[]):
        self.bpath = bpath
	
    def append(self, bpathel):
        self.bpath.append(bpathel)

#    def extend(self, bpathel):
#        self.bpath.extend(bpathel)

    def __add__(self, bp):
        return bpath(self.bpath+bp.bpath)

    def __len__(self):
        return len(self.bpath)

    def __getitem__(self, i):
        return self.bpath[i]

    def __str__(self):
        return reduce(lambda x,y: x+"%s\n" % str(y), self.bpath, "")
        
class bcurve(bpath):
    """ bpath consisting of one bezier curve"""
    def __init__(self, x0, y0, x1, y1, x2, y2, x3, y3):
        bpath.__init__(self, [bpathel(x0, y0, x1, y1, x2, y2, x3, y3)]) 

class bline(bpath):
    """ bpath consisting of one straight line"""
    def __init__(self, x0, y0, x1, y1):
        bpath.__init__(self, 
                      [bpathel(x0, y0, 
                               x0+(x1-x0)/3.0, 
                               y0+(y1-y0)/3.0,
                               x0+2.0*(x1-x0)/3.0, 
                               y0+2.0*(y1-y0)/3.0,
                               x1, y1 )]) 

class barc(bpath):
    def __init__(self, x, y, r, phi1, phi2, clockwise=0, dphimax=pi/4):

        phi1 = phi1*pi/180
        phi2 = phi2*pi/180

        if not clockwise:  
            if phi2<phi1:        
                # guarantee that phi2>phi1
                phi2 = phi2 + (math.floor((phi1-phi2)/(2*pi))+1)*2*pi
            elif phi2>phi1+2*pi:
                # remove unnecessary multiples of 2*pi
                phi2 = phi2 - (math.floor((phi2-phi1)/(2*pi))-1)*2*pi
            
        else:
            if phi1<phi2: 
                phi1 = phi1 + (math.floor((phi2-phi1)/(2*pi))+1)*2*pi
            elif phi1>phi2+2*pi:
                phi1 = phi1 - (math.floor((phi1-phi2)/(2*pi))-1)*2*pi

        if r==0 or phi1-phi2==0: return None

        subdivisions = abs(int((1.0*(phi1-phi2))/dphimax))+1

        dphi=(1.0*(phi2-phi1))/subdivisions

        self.bpath = []    

        for i in range(subdivisions):
            self.bpath.append(arctobpathel(x, y, r, phi1+i*dphi, phi1+(i+1)*dphi))

def arctobpathel(x, y, r, phi1, phi2):
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
    
    return bpathel(x0, y0, x1, y1, x2, y2, x3, y3)   

if __name__=="__main__":
    def testarc(x, y, phi1, phi2):
        print "1 0 0 setrgbcolor"
        print "newpath"
        print "%f %f 48 %f %f arc" % (x, y, phi1, phi2)
        print "stroke"
        print "0 1 0 setrgbcolor"
        print "newpath"
        print barc(x,y,50,phi1,phi2)
        print "stroke"

    def testarcn(x, y, phi1, phi2):
        print "1 0 0 setrgbcolor"
        print "newpath"
        print "%f %f 48 %f %f arcn" % (x, y, phi1, phi2)
        print "stroke"
        print "0 1 0 setrgbcolor"
        print "newpath"
        print barc(x,y,50,phi1,phi2, clockwise=1)
        print "stroke"
       
    print "%!PS-Adobe-2.0"
    #print "newpath" 
    #print arctobpath(100,100,100,0,90,dphimax=90)
    #print arctobpath(100,100,100,0,90)
    #print "stroke"

#   testarc(100, 200, 0, 90)
#   testarc(200, 200, -90, 90)
#   testarc(300, 200, 270, 90)
#   testarc(400, 200, 90, -90)
#   testarc(500, 200, 90, 270)
#   testarc(400, 300, 45, -90)
#   testarc(200, 300, 45, -90-2*360)
#   testarc(100, 300, 45, +90+2*360)
#
#   testarcn(100, 500, 0, 90) 
#   testarcn(200, 500, -90, 90) 
#   testarcn(300, 500, 270, 90) 
#   testarcn(400, 500, 90, -90) 
#   testarcn(500, 500, 90, 270) 
#   testarcn(400, 600, 45, -90) 
#   testarcn(200, 600, 45, -90-360) 
#   testarcn(100, 600, 45, -90+360) 
#
    p=path([moveto(100,100), rlineto(20,20), arc(150,120,10,30,300),closepath()])
    p.ConvertToBezier()
    print p.bpath
    print "stroke"
    p=path([arc(120,120,10,30,360)])
    p.ConvertToBezier()
    print p.bpath
    print "stroke"
    print "showpage"
