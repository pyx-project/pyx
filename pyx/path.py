#!/usr/bin/env python

class pathel:
    def __init__(self, command, points):
        self.command = command
	self.points = points

    def draw(self, canvas):
        canvas.PSAddCmd("%f %f " % canvas.u2p(self.points) +  self.command )

class moveto(pathel):
    def __init__(self, x, y):
        pathel.__init__(self, "moveto", (x, y))
	
class rmoveto(pathel):
    def __init__(self, x, y):
        pathel.__init__(self, "rmoveto", (x, y))
	
class lineto(pathel):
    def __init__(self, x, y):
        pathel.__init__(self, "lineto", (x, y))
	
class rlineto(pathel):
    def __init__(self, x, y):
        pathel.__init__(self, "rlineto", (x, y))
	
class path:
    def __init__(self, path):
        self.path = path
	
    def draw(self, canvas):
    	canvas.newpath()
        for pathel in self.path:
	    pathel.draw(canvas)
    	canvas.stroke()

class line(path):
   def __init__(self, x1, y1, x2, y2):
       path.__init__(self, [ moveto(x1,y1), lineto(x2, y2) ] )
