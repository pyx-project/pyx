#!/usr/bin/env python

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
        canvas.PSAddCmd(self.command)
  
# path elements with 2 arguments  

class _pathel2(pathel):

    ' element of a path with args=(x,y), used for r?(move|line)to'
    
    def draw(self, canvas):
        canvas.PSAddCmd("%f %f " % canvas.u2p(self.args) + self.command )

class moveto(_pathel2):
    ' Set current point to (x, y) '
    def __init__(self, x, y):
        pathel.__init__(self, "moveto", (x, y))
	
class rmoveto(_pathel2):
    ' Perform relative moveto '
    def __init__(self, x, y):
        pathel.__init__(self, "rmoveto", (x, y))
	
class lineto(_pathel2):
    ' Append straight line to (x, y) '
    def __init__(self, x, y):
        pathel.__init__(self, "lineto", (x, y))
	
class rlineto(_pathel2):
    ' Perform relative lineto '
    def __init__(self, x, y):
        pathel.__init__(self, "rlineto", (x, y))

# path elements with 5 arguments

class _pathelarc(pathel):
    def draw(self, canvas):
        canvas.PSAddCmd("%f %f %f " % canvas.u2p(self.args[:3]) + "%f %f " % self.args[3:] + self.command )
 
class arc(_pathelarc):
    ' Append counterclockwise arc '
    def __init__(self, x, y, r, angle1, angle2):
        pathel.__init__(self, "arc", (x, y, r, angle1, angle2))
	
class arcn(_pathelarc):
    ' Append clockwise arc '
    def __init__(self, x, y, r, angle1, angle2):
        pathel.__init__(self, "arcn", (x, y, r, angle1, angle2))

class arct(pathel):
    ' Append tangent arc '
    def __init__(self, x1, y1, x2, y2, r):
        pathel.__init__(self, "arct", (x1, y1, x2, y2, r))
    def draw(self, canvas):
        canvas.PSAddCmd("%f %f %f %f " % canvas.u2p(self.args[:4]) + "%f " % self.args[4] + self.command )
	
# path elements with 6 arguments

class _pathel6(pathel):
    def draw(self, canvas):
        canvas.PSAddCmd("%f %f %f %f %f %f " %  canvas.u2p(self.args) + self.command )

class curveto(_pathel6):
    def __init__(self, x1, y1, x2, y2, x3, y3):
        pathel.__init__(self, "curveto", (x1, y1, x2, y2, x3, y3))

class rcurveto(_pathel6):
    def __init__(self, x1, y1, x2, y2, x3, y3):
        pathel.__init__(self, "rcurveto", (x1, y1, x2, y2, x3, y3))

#
# path: PS style path 
#
	
class path:
    """ PS style path """
    def __init__(self, path):
        self.path = path
	
    def draw(self, canvas):
	if not isinstance(self.path[0], moveto): 
	    raise PathException, "first path element must be moveto"
        for pathel in self.path:
	    pathel.draw(canvas)

class line(path):
   def __init__(self, x1, y1, x2, y2):
       path.__init__(self, [ moveto(x1,y1), lineto(x2, y2) ] )

class rect(path):
   def __init__(self, x, y, width, height):
       path.__init__(self, [ moveto(x,y), 
                             rlineto(width,0), 
			     rlineto(0,height), 
			     rlineto(-width,0),
			     closepath()] )
