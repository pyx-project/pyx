#!/usr/bin/env python
import sys; sys.path.append("..")

import pyx
from pyx import *
from pyx.path import *
import math

def drawpathwarrowboth(c, p):
    c.draw(p, canvas.barrow.normal, canvas.earrow.small)

def testarrow(c):
    drawpathwarrowboth(c, 
          path(moveto(10,20), curveto(12,16,14,15,12,19), rcurveto(-3,2,3,3,-2,4)))
    
    drawpathwarrowboth(c, path(arc(8,15,4,10,70)))
    drawpathwarrowboth(c, path(arc(8,15,3,10,70)))
    drawpathwarrowboth(c, path(arc(8,15,2,10,70)))
    drawpathwarrowboth(c, path(arc(8,15,1,10,70)))
    drawpathwarrowboth(c, path(arc(8,15,0.5,10,70)))


c=canvas.canvas()
testarrow(c)
c.writetofile("test_arrow", paperformat="a4", rotated=1, fittosize=1)

