#!/usr/bin/env python
import sys; sys.path.append("..")

import pyx
from pyx import *
from pyx.path import *

def bboxrect(cmd):
   bbox=cmd.bbox()
   return rect("%f t pt" % bbox.llx,            "%f t pt" % bbox.lly,
               "%f t pt" % (bbox.urx-bbox.llx), "%f t pt" % (bbox.ury-bbox.lly))


def dotest(c, x, y, test):
   c2 = c.insert(canvas.canvas(trafo.translate(x, y)))
   eval("%s(c2)" % test)
   c.draw(bboxrect(c2))
   

class cross(path):
   def __init__(self, x, y):
       self.path=[moveto(x,y),
                  rmoveto(-0.1, -0.1), 
		  rlineto(0.2, 0.2), 
		  rmoveto(-0.1, -0.1),
                  rmoveto(-0.1, +0.1), 
		  rlineto(0.2, -0.2)]


def drawpathwbbox(c, p):
    c.draw(p, color.rgb.red)
    bp=p.bpath()
    c.draw(bp, color.rgb.green, canvas.linestyle.dashed)
    c.draw(bboxrect(p))


def testarcs(c):
    def testarc(c, x, y, phi1, phi2):
        p=path(arc(x,y, 0.5, phi1, phi2))
        bp=p.bpath()
        c.draw(p, color.rgb.red)
        c.draw(bp, color.rgb.green, canvas.linestyle.dashed)

    def testarcn(c, x, y, phi1, phi2):
        p=path(arcn(x,y, 0.5, phi1, phi2))
        bp=p.bpath()
        c.draw(p, color.rgb.red)
        c.draw(bp, color.rgb.green, canvas.linestyle.dashed)

    def testarct(c, r, x0, y0, dx1, dy1, dx2, dy2):
        p=path(moveto(x0,y0), arct(x0+dx1,y0+dy1, x0+dx2, y0+dy2, r), rlineto(dx2-dx1, dy2-dy1))
        bp=p.bpath()
        c.draw(p, color.rgb.red, canvas.linewidth.Thick)
        c.draw(bp, color.rgb.green, canvas.linewidth.THin)

    testarc(c, 1, 2, 0, 90)
    testarc(c, 2, 2, -90, 90)
    testarc(c, 3, 2, 270, 90)
    testarc(c, 4, 2, 90, -90)
    testarc(c, 5, 2, 90, 270)
    testarc(c, 4, 3, 45, -90)
    testarc(c, 2, 3, 45, -90-2*360)
    testarc(c, 1, 3, 45, +90+2*360)

    testarcn(c, 1, 5, 0, 90) 
    testarcn(c, 2, 5, -90, 90) 
    testarcn(c, 3, 5, 270, 90) 
    testarcn(c, 4, 5, 90, -90) 
    testarcn(c, 5, 5, 90, 270) 
    testarcn(c, 4, 6, 45, -90) 
    testarcn(c, 2, 6, 45, -90-360) 
    testarcn(c, 1, 6, 45, -90+360)

    testarct(c, 0.5, 1, 8, 0, 1, 1, 1)
    testarct(c, 0.5, 3, 8, 1, 1, 1, 2)
    testarct(c, 0.5, 5, 8, 1, 0, 2, 1)
    testarct(c, 0.5, 7, 8, 1, 0, 2, 0)
    testarct(c, 0.0, 9, 8, 0, 1, 1, 1)

#    testarct(c, 0.5, 11, 8, 0, 1, 0, 0) # not allowed


def testmidpointsplit(c):
   p=path(moveto(1,1), rlineto(2,2), arc(5,2,1,30,300), closepath())
   bpsplit=p.bpath().MidPointSplit()
   c.draw(p, color.rgb.red)
   c.draw(bpsplit, color.rgb.green, canvas.linestyle.dashed)


def testintersectbezier(c):
    p=path(moveto(0,0), curveto(2,6,4,5,2,9))
    q=path(moveto(2,0), curveto(2,6,4,12,1,6))

    bp=p.bpath()
    bq=q.bpath()

    c.draw(q, canvas.linewidth.THIN)
    c.draw(p, canvas.linewidth.THIN)

    isect = bp.intersect(bq, epsilon=1e-4)

    for i in isect:
        x, y = bp.pos(i[0])
        c.draw(cross(x, y), canvas.linewidth.THIN)


def testbpathtrafo(c):
    p=path(moveto(0,5),
           curveto(2,1,4,0,2,4),
           rcurveto(-3,2,1,2,3,6),
           rlineto(2,3))
    bp=p.bpath()

    c.draw(bp.transform(trafo.translate(3,1)), color.rgb.red)
    c.insert(canvas.canvas(trafo.translate(3,1))).draw(p,
                                                       color.rgb.green,
                                                       canvas.linestyle.dashed)

    c.draw(bp)
    c.draw(bp.reverse())

    c.draw(cross(*(bp.pos(0))))
    c.draw(cross(*(bp.reverse().pos(0))))

    bp1, bp2 = bp.split(1.7)
    c.draw(bp1, color.rgb.red, canvas.linestyle.dashed)
    c.draw(bp2, color.rgb.green, canvas.linestyle.dashed)


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
    sc=c.insert(canvas.canvas(trafo.translate(0,40).rotate(10)))

    p=path(moveto(10,10), curveto(12,16,14,15,12,19));   drawpathwbbox(sc,p)
    p=path(moveto(5,17), curveto(6,18, 5,16, 7,15));     drawpathwbbox(sc,p)


def testclipbbox(c):
    clip=canvas.clip(rect(11,11,10,5))

    p1=path(moveto(10,10), curveto(12,16,14,15,12,19));   
    p2=path(moveto(12,12), curveto(6,18, 5,16, 7,15));  
    
    # just a simple test for clipping
    sc=c.insert(canvas.canvas(clip))
    drawpathwbbox(sc,p1)
    drawpathwbbox(sc,p2)

    # more complicated operations
    
    # 1. transformation followed by clipping:
    # in this case, the clipping path will be evaluated in the
    # context of the already transformed canvas, so that the
    # actually displayed portion of the path should be the same
    
    sc=c.insert(canvas.canvas(trafo.translate(5,0), clip))
    drawpathwbbox(sc,p1)
    drawpathwbbox(sc,p2)

    # 2. clipping followed by transformation 
    # in this case, the clipping path will not be transformed, so
    # that the display portionof the path should change

    sc=c.insert(canvas.canvas(clip, trafo.translate(1,1)))
    drawpathwbbox(sc,p1)
    drawpathwbbox(sc,p2)


c=canvas.canvas()
dotest(c, 0, 0, "testarcs")
dotest(c, 12, 3, "testmidpointsplit")
dotest(c, 2, 12, "testintersectbezier")
dotest(c, 10,11, "testbpathtrafo")
c.writetofile("test_path", paperformat="a4", rotated=0, fittosize=1)

c=canvas.canvas()
testarcbbox(c)    
testcurvetobbox(c)
testtrafobbox(c)
testclipbbox(c)
c.writetofile("test_bbox", paperformat="a4", rotated=1, fittosize=1)
#c.writetofile("test_bbox")
