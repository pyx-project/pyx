#!/usr/bin/env python
import sys; sys.path.append("..")

import pyx
from pyx import *
from pyx.path import *
import math


class cross(path):
   def __init__(self, x, y):
       self.path=[moveto(x,y),
                  rmoveto(-0.1, -0.1), 
		  rlineto(0.2, 0.2), 
		  rmoveto(-0.1, -0.1),
                  rmoveto(-0.1, +0.1), 
		  rlineto(0.2, -0.2)]

def drawarrow(c, bp, alen=4, aangle=25, cfactor=0.8):
    lbpel = bp[-1]

    etlen = math.sqrt((lbpel.x3-lbpel.x2)*(lbpel.x3-lbpel.x2)+
                      (lbpel.y3-lbpel.y2)*(lbpel.y3-lbpel.y2))

    alen = 0.5*alen/etlen
    ilen   = cfactor*alen
		 
    ex, ey = lbpel[1]
    mx, my = lbpel[1-ilen]
    
    end = lbpel.split(1-alen)[1]
    arrow1 = bpath.bpath([end.transform(trafo.rotate(-aangle, ex, ey))])
    arrow2 = bpath.bpath([end.transform(trafo.rotate( aangle, ex, ey))])
    arrow3 = bpath.bline(*(arrow2.pos(0)+arrow1.pos(0)))
    arrow3a= bpath.bline(*(arrow2.pos(0)+(mx,my)))
    arrow3b= bpath.bpath([bpath.bline(*((mx,my)+arrow1.pos(0)))[0].close()])
    arrow  = arrow1+arrow2.reverse()+arrow3a+arrow3b
    
    c.draw(arrow, canvas.linejoin.round)
    c.fill(arrow)

def drawpathwarrowboth(c, p):
    bp=p.bpath()
    c.draw(p)
    drawarrow(c, bp)
    drawarrow(c, bp.reverse())


def testarrow(c):
    drawpathwarrowboth(c, 
          path([moveto(10,20), curveto(12,16,14,15,12,19), rcurveto(-3,2,3,3,-2,4)]))
    

    drawpathwarrowboth(c, path([arc(8,15,4,10,70)]))
    drawpathwarrowboth(c, path([arc(8,15,3,10,70)]))
    drawpathwarrowboth(c, path([arc(8,15,2,10,70)]))
    drawpathwarrowboth(c, path([arc(8,15,1,10,70)]))
    drawpathwarrowboth(c, path([arc(8,15,0.5,10,70)]))



c=canvas.canvas()
testarrow(c)
c.writetofile("test_arrow")

