#!/usr/bin/env python
import sys; sys.path.append("..")

import pyx
from pyx import *
from pyx.path import *
import math

def testarrow(c):
    c.draw(path(moveto(10,20), 
    	        curveto(12,16,14,15,12,19),
                rcurveto(-3,2,3,3,-2,4)),
           canvas.barrow.small, canvas.earrow.small)
    
    c.draw(path(arc(8,15,4,10,70)), canvas.barrow.small, canvas.earrow.normal)
    c.draw(path(arc(8,15,3,10,70)), canvas.barrow.small, canvas.earrow.normal)
    c.draw(path(arc(8,15,2,10,70)), canvas.barrow.small, canvas.earrow.normal)
    c.draw(path(arc(8,15,1,10,70)), canvas.barrow.small, canvas.earrow.normal)
    c.draw(path(arc(8,15,0.5,10,70)), canvas.barrow.small, canvas.earrow.normal)

    base = 2

    c.draw(path(moveto(5,10), rlineto(5,0)),
           canvas.barrow("%f t pt" % (base/math.sqrt(8)), constriction=None),
           canvas.earrow.SMall)
    c.draw(path(moveto(5,10.5), rlineto(5,0)),
           canvas.barrow("%f t pt" % (base/math.sqrt(4)), constriction=None),
           canvas.earrow.Small)
    c.draw(path(moveto(5,11), rlineto(5,0)),
           canvas.barrow("%f t pt" % (base/math.sqrt(2)), constriction=None),
           canvas.earrow.small)
    c.draw(path(moveto(5,11.5), rlineto(5,0)),
           canvas.barrow("%f t pt" % (base/math.sqrt(1)), constriction=None),
           canvas.earrow.normal)
    c.draw(path(moveto(5,12), rlineto(5,0)),
           canvas.barrow("%f t pt" % (base*math.sqrt(2)), constriction=None),
           canvas.earrow.large)
    c.draw(path(moveto(5,12.5), rlineto(5,0)),
           canvas.barrow("%f t pt" % (base*math.sqrt(4)), constriction=None),
           canvas.earrow.Large)
    c.draw(path(moveto(5,13), rlineto(5,0)),
           canvas.barrow("%f t pt" % (base*math.sqrt(8)), constriction=None),
           canvas.earrow.LArge)
    c.draw(path(moveto(5,13.5), rlineto(5,0)),
           canvas.barrow("%f t pt" % (base*math.sqrt(16)), constriction=None),
           canvas.earrow.LARge)
   
    lt = canvas.linewidth.THick

    c.draw(path(moveto(11,10), rlineto(5,0)),
           lt,
           canvas.barrow("%f t pt" % (base/math.sqrt(8)), constriction=None),
           canvas.earrow.SMall)
    c.draw(path(moveto(11,10.5), rlineto(5,0)),
           lt,
           canvas.barrow("%f t pt" % (base/math.sqrt(4)), constriction=None),
           canvas.earrow.Small)
    c.draw(path(moveto(11,11), rlineto(5,0)),
           lt,
           canvas.barrow("%f t pt" % (base/math.sqrt(2)), constriction=None),
           canvas.earrow.small)
    c.draw(path(moveto(11,11.5), rlineto(5,0)),
           lt,
           canvas.barrow("%f t pt" % (base/math.sqrt(1)), constriction=None),
           canvas.earrow.normal)
    c.draw(path(moveto(11,12), rlineto(5,0)),
           lt,
           canvas.barrow("%f t pt" % (base*math.sqrt(2)), constriction=None),
           canvas.earrow.large)
    c.draw(path(moveto(11,12.5), rlineto(5,0)),
           lt,
           canvas.barrow("%f t pt" % (base*math.sqrt(4)), constriction=None),
           canvas.earrow.Large)
    c.draw(path(moveto(11,13), rlineto(5,0)),
           lt,
           canvas.barrow("%f t pt" % (base*math.sqrt(8)), constriction=None),
           canvas.earrow.LArge(canvas.linestyle.dashed, color.rgb.green))
    c.draw(path(moveto(11,13.5), rlineto(5,0)),
           lt,
           canvas.barrow("%f t pt" % (base*math.sqrt(16)), constriction=None),
           canvas.earrow.LARge(color.rgb.red, 
                               canvas.stroked(canvas.linejoin.round),
                               canvas.filled(color.rgb.blue)))



c=canvas.canvas()
testarrow(c)
c.writetofile("test_arrow", paperformat="a4", rotated=0, fittosize=1)

