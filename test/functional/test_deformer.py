#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]
from pyx import *
from pyx.deformer import *

#####  helpers  ##############################################################

def bboxrect(cmd):
   return cmd.bbox().enlarged(5*unit.t_mm).rect()

def dotest(c, x, y, test):
   c2 = c.insert(canvas.canvas([trafo.translate(x, y)]))
   eval("%s(c2)" % test)
   c.stroke(bboxrect(c2))

def drawpathwbbox(c, p):
    c.stroke(p, [color.rgb.red])
    np = p.normpath()
    c.stroke(np, [color.rgb.green, style.linestyle.dashed])
    c.stroke(bboxrect(p))

#####  tests  ################################################################

def testcycloid(c):

    # dependence on turnangle
    p = path.line(0, 0, 3, 0)
    c.stroke(p, [style.linewidth.THIN])
    cyc = cycloid(halfloops=3, skipfirst=0.5, skiplast=0.5, curvesperhloop=2)
    c.stroke(p, [cyc(turnangle=00)])
    c.stroke(p, [cyc(turnangle=22), color.rgb.red])
    c.stroke(p, [cyc(turnangle=45), color.rgb.green])
    c.stroke(p, [cyc(turnangle=67), color.rgb.blue])
    c.stroke(p, [cyc(turnangle=90), color.cmyk.Cyan])

    # dependence on curvesperloop
    p = path.curve(5, 0, 8, 0, 6, 4, 9, 4)
    c.stroke(p)
    cyc = cycloid(halfloops=16, skipfirst=0, skiplast=0, curvesperhloop=1)
    c.stroke(p, [cyc(curvesperhloop=2)])
    c.stroke(p, [cyc(curvesperhloop=3), color.rgb.red])
    c.stroke(p, [cyc(curvesperhloop=4), color.rgb.green])
    c.stroke(p, [cyc(curvesperhloop=10), color.rgb.blue])

    # extremely curved path
    p = path.curve(0,2, 0.5,5, 1,6, 2,2)
    c.stroke(p)
    cyc = cycloid(radius=0.7, halfloops=7, skipfirst=0, skiplast=0, curvesperhloop=1)
    c.stroke(p, [cyc(curvesperhloop=2)])
    c.stroke(p, [cyc(curvesperhloop=3), color.rgb.red])
    c.stroke(p, [cyc(curvesperhloop=4), color.rgb.green])
    c.stroke(p, [cyc(curvesperhloop=50), color.rgb.blue])


def testsmoothed(c):
    p = path.path(path.moveto(0,0), path.lineto(3,0), path.lineto(5,7),
    path.curveto(0,10, -2,8, 0,6),
    path.lineto(0,4), path.lineto(-5,4), path.lineto(-5,2), path.lineto(-0.2,0.2),
    path.closepath()
    ) + path.circle(0,0,2)

    c.stroke(p, [color.gray(0.8), style.linewidth.THICk])
    c.stroke(p, [smoothed(radius=0.85, softness=1, obeycurv=1), style.linewidth.Thin])
    c.stroke(p, [smoothed(radius=0.85, softness=1, obeycurv=0), color.rgb.red])
    c.stroke(p, [smoothed(radius=0.20, softness=1, obeycurv=0), color.rgb.green])
    c.stroke(p, [smoothed(radius=1.20, softness=1, obeycurv=0), color.rgb.blue])

c=canvas.canvas()
dotest(c, 0, 0, "testcycloid")
dotest(c, 15, 0, "testsmoothed")
c.writeEPSfile("test_deformer", paperformat="a4", rotated=0, fittosize=1)
c.writePDFfile("test_deformer")

