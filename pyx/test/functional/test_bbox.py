#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

from pyx import *
from pyx.path import *

def bboxrect(cmd):
    return cmd.bbox().rect()

def drawpathwbbox(c, p):
    c.stroke(p, [color.rgb.red])
    np = p.normpath()
    c.stroke(np, [color.rgb.green, style.linestyle.dashed])
    c.stroke(bboxrect(p))

def testarcbbox(c):
    for phi in range(0,360,30):
       drawpathwbbox(c,path(arc(phi*0.1, phi*0.1, 1, 0, phi)))

    for phi in range(0,360,30):
       drawpathwbbox(c,path(arc(phi*0.1, 5+phi*0.1, 1, phi, 360)))

    for phi in range(0,360,30):
       drawpathwbbox(c,path(arc(phi*0.1, 10+phi*0.1, 1, phi, phi+30)))

    for phi in range(0,360,30):
       drawpathwbbox(c,path(arc(phi*0.1, 15+phi*0.1, 1, phi, phi+120)))

    for phi in range(0,360,30):
       drawpathwbbox(c,path(arc(phi*0.1, 20+phi*0.1, 1, phi, phi+210)))

    for phi in range(0,360,30):
       drawpathwbbox(c,path(arc(phi*0.1, 25+phi*0.1, 1, phi, phi+300)))

    for phi in range(0,360,30):
       drawpathwbbox(c,path(arc(phi*0.1, 30+phi*0.1, 1, phi, phi+390)))
       

    for phi in range(0,360,30):
       drawpathwbbox(c,path(moveto(20+phi*0.1, phi*0.09),
                            arc(20+phi*0.1, phi*0.1, 1, 0, phi)))

    for phi in range(0,360,30):
       drawpathwbbox(c,path(moveto(20+phi*0.1, 5+phi*0.11),
                            arc(20+phi*0.1, 5+phi*0.1, 1, 0, phi)))

    for phi in range(0,360,30):
       drawpathwbbox(c,path(moveto(20+phi*0.1, 10+phi*0.09),
                            arcn(20+phi*0.1, 10+phi*0.1, 1, 0, phi)))

    for phi in range(0,360,30):
       drawpathwbbox(c,path(moveto(20+phi*0.1, 15+phi*0.11),
                            arcn(20+phi*0.1, 15+phi*0.1, 1, 0, phi)))

    for phi in range(0,360,30):
       drawpathwbbox(c,path(moveto(50+phi*0.1, phi*0.09),
                            arc(50+phi*0.1, phi*0.1, 1, 0, phi),
                            rlineto(1,1)))

    for phi in range(0,360,30):
       drawpathwbbox(c,path(moveto(50+phi*0.1, 5+phi*0.11),
                            arc(50+phi*0.1, 5+phi*0.1, 1, 0, phi),
                            rlineto(1,1)))

    for phi in range(0,360,30):
       drawpathwbbox(c,path(moveto(50+phi*0.1, 10+phi*0.09),
                            arcn(50+phi*0.1, 10+phi*0.1, 1, 0, phi),
                            rlineto(1,1)))

    for phi in range(0,360,30):
       drawpathwbbox(c,path(moveto(50+phi*0.1, 15+phi*0.11),
                            arcn(50+phi*0.1, 15+phi*0.1, 1, 0, phi),
                            rlineto(1,1)))


def testcurvetobbox(c):
    drawpathwbbox(c,path(moveto(10,60), curveto(12,66,14,65,12,69)))


def testtrafobbox(c):
    sc=c.insert(canvas.canvas([trafo.translate(0,40).rotated(10)]))

    p=path(moveto(10,10), curveto(12,16,14,15,12,19));   drawpathwbbox(sc,p)
    p=path(moveto(5,17), curveto(6,18, 5,16, 7,15));     drawpathwbbox(sc,p)


def testclipbbox(c):
    clip = canvas.clip(rect(11,-9,10,5))

    p1 = path(moveto(10,-10), curveto(12,-4, 14,-5, 12,-1));   
    p2 = path(moveto(12,-8), curveto(6,-2, 5,-4, 7,-5));  
    
    # just a simple test for clipping
    sc = c.insert(canvas.canvas([clip]))
    drawpathwbbox(sc, p1)
    drawpathwbbox(sc, p2)

    # more complicated operations
    
    # 1. transformation followed by clipping:
    # in this case, the clipping path will be evaluated in the
    # context of the already transformed canvas, so that the
    # actually displayed portion of the path should be the same
    sc = c.insert(canvas.canvas([trafo.translate(5,0), clip]))
    drawpathwbbox(sc, p1)
    drawpathwbbox(sc, p2)

    # 2. clipping followed by transformation 
    # in this case, the clipping path will not be transformed, so
    # that the display portionof the path should change
    sc = c.insert(canvas.canvas([clip, trafo.translate(1,1)]))
    drawpathwbbox(sc, p1)
    drawpathwbbox(sc, p2)


c = canvas.canvas()
testarcbbox(c)
testcurvetobbox(c)
testtrafobbox(c)
testclipbbox(c)
c.writeEPSfile("test_bbox", paperformat=document.paperformat.A4, rotated=1, fittosize=1)
c.writePDFfile("test_bbox")
