#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

from pyx import *
from pyx.connector import *


startbox = box.polygon(corners=[[0,0], [1,0.2], [0.5,2]])
endbox = box.polygon(corners=[[10,3.8], [13,5.2], [12.5,4.0]])

def dotest(c, x, y, test):
   c2 = c.insert(canvas.canvas([trafo.translate(x, y)]))
   c2.stroke(startbox.path())
   c2.stroke(endbox.path())
   c2.stroke(path.circle( unit.pt * startbox.center[0], unit.pt * startbox.center[1], 0.1))
   c2.stroke(path.circle( unit.pt * endbox.center[0], unit.pt * endbox.center[1], 0.1))
   eval("%s(c2)" % test)
   c.insert(c2)


def testline(c):
    l = line(startbox, endbox)
    c.stroke(l, [style.linewidth.THICK, color.rgb.red, deco.earrow.normal])

    l = line(endbox, startbox, boxdists=[1,0])
    c.stroke(l, [color.rgb.blue, deco.earrow.normal])


def testarc(c):
    l = arc(endbox, startbox, boxdists=1)
    c.stroke(l, [color.rgb.blue, deco.earrow.normal])

    for a in [-135, -90, 0.0001, 45, 90]:
        l = arc(startbox, endbox, relangle=a, boxdists=1)
        c.stroke(l, [color.rgb.red, deco.earrow.normal])

    for b in [-1.1, -0.4, 0.01, 0.5]:
        l = arc(startbox, endbox, relbulge=b, boxdists=1)
        c.stroke(l, [color.rgb.green, deco.earrow.normal])

    l = arc(startbox, endbox, absbulge=5, relbulge=0, boxdists=1)
    c.stroke(l, [color.rgb.blue, deco.earrow.normal])


def testcurve(c):
    l = curve(endbox, startbox, boxdists=[1,0])
    c.stroke(l, [color.rgb.blue, deco.earrow.normal])

    for a in [ [ 90,  90,  1.0], \
               [-90,  90,  1.0], \
               [ 90, -90,  1.0], \
               [-90,   0,  1.0], \
               [ 20,  20,  2.0] ]:
        l = curve(startbox, endbox, boxdists=0.8,
            relangle1=a[0], relangle2=a[1], relbulge=a[2])
        c.stroke(l, [color.rgb.red, deco.earrow.normal])

    for a in [ [ 90,  90,  1.0], \
               [-90,  90,  1.0] ]:
        l = curve(startbox, endbox, boxdists=0.8,
            absangle1=a[0], absangle2=a[1], relbulge=a[2])
        c.stroke(l, [color.rgb.green, deco.earrow.normal])


def testtwolines(c):
    l = twolines(endbox, startbox, relangle1=45, relangle2=45)
    c.stroke(l, [color.rgb.blue, deco.earrow.normal])

    for a in [ [0,90], [90,0] ]:
        l = twolines(startbox, endbox, boxdists=0.8,
            absangle1=a[0], absangle2=a[1])
        c.stroke(l, [color.rgb.red, deco.earrow.normal])

    for a in range(10,20,2):
        l = twolines(startbox, endbox, boxdists=0.8,
            absangle1=45, length2=a)
        c.stroke(l, [color.rgb.green, deco.earrow.normal])

    for a in range(5,20,2):
        l = twolines(startbox, endbox, boxdists=0.8,
            relangle1=45, length1=a)
        c.stroke(l, [color.rgb.green, deco.earrow.normal])


c = canvas.canvas()
dotest(c,  0, 0, "testline")
dotest(c, 25, 0, "testarc")
dotest(c, 25,30, "testcurve")
dotest(c,  0,20, "testtwolines")
c.writeEPSfile("test_connector", paperformat="a4", rotated=0, fittosize=1)
c.writePDFfile("test_connector")

