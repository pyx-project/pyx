#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]
from pyx import *

#####  helpers  ##############################################################

def bboxrect(cmd):
   return cmd.bbox().rect()

def dotest(c, x, y, test):
   c2 = c.insert(canvas.canvas([trafo.translate(x, y)]))
   eval("%s(c2)" % test)
   c.stroke(bboxrect(c2))

def drawpathwbbox(c, p):
    c.stroke(p, [color.rgb.red])
    np=normpath(p)
    c.stroke(np, [color.rgb.green, style.linestyle.dashed])
    c.stroke(bboxrect(p))

#####  tests  ################################################################

def testcycloid(c):
    p = path.line(0, 0, 3, 0)
    c.stroke(p, [color.rgb.red])
    c.stroke(p, [color.rgb.green, deco.cycloid()])

    p = path.curve(5, 0, 8, 0, 6, 4, 9, 4)
    c.stroke(p, [color.rgb.red])
    c.stroke(p, [color.rgb.green, deco.cycloid(), deco.earrow.LARge([deco.stroked.clear])])
    c.stroke(p, [color.rgb.blue, deco.cycloid(), deco.cycloid(loops=250, radius=0.1)])


def testsmoothed(c):
    p = path.path(path.moveto(0,0), path.lineto(3,0), path.lineto(5,7),
    path.curveto(0,10, -2,8, 0,6),
    path.lineto(0,4), path.lineto(-5,4), path.lineto(-5,2), path.lineto(-0.2,0.2),
    path.closepath()
    ) + path.circle(0,0,2)

    c.stroke(path.normpath(p), [color.gray(0.8), style.linewidth.THICk])
    c.stroke(p, [color.rgb.green, deco.smoothed(radius=0.85, softness=1, strict=1)])
    c.stroke(p, [color.rgb.blue, deco.smoothed(radius=0.85, softness=1, strict=0)])
    c.stroke(p, [color.rgb.blue, deco.smoothed(radius=0.2, softness=1, strict=0)])
    c.stroke(p, [color.rgb.green, deco.smoothed(radius=1.2, softness=1, strict=0)])

c=canvas.canvas()
dotest(c, 0, 0, "testcycloid")
dotest(c, 15, 0, "testsmoothed")
c.writeEPSfile("test_deco", paperformat="a4", rotated=0, fittosize=1)
c.writePDFfile("test_deco")
