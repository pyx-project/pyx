#!/usr/bin/env python
import pyx
from pyx import *
from pyx.path import *


class cross(path):
   def __init__(self, x, y):
       self.path=[moveto(x,y),
                  rmoveto(-0.1, -0.1), 
		  rlineto(0.2, 0.2), 
		  rmoveto(-0.1, -0.1),
                  rmoveto(-0.1, +0.1), 
		  rlineto(0.2, -0.2)]


def testarrow(c):
    p=path([moveto(10,20), curveto(12,16,14,15,12,19), rcurveto(-3,2,3,3,-2,4)])
    bp=p.bpath()

    c.draw(p)

    aangle = 25
    alen   = 0.02 
    ilen   = alen*0.8

    end = bp.split(len(bp)-alen)[1]
    ex, ey = bp.pos(len(bp))
    mx, my = bp.pos(len(bp)-ilen)
    arrow1 = end.transform(trafo.rotate(-aangle, ex, ey)) 
    arrow2 = end.transform(trafo.rotate( aangle, ex, ey)) 
    arrow3 = bpath.bline(*(arrow2.pos(0)+arrow1.pos(0)))
    arrow3a= bpath.bline(*(arrow2.pos(0)+(mx,my)))
    arrow3b= bpath.bline(*((mx,my)+arrow1.pos(0)))
    arrow  = arrow1+arrow2.reverse()+arrow3a+arrow3b
    c.draw(arrow, canvas.linejoin.round)
    c.fill(arrow)


c=canvas.canvas()
testarrow(c)
c.writetofile("test_arrow")

