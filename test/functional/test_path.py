#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

from pyx import *
from pyx.path import *

def bboxrect(cmd):
    return cmd.bbox().rect()


def dotest(c, x, y, test):
   c2 = c.insert(canvas.canvas([trafo.translate(x, y)]))
   eval("%s(c2)" % test)
   c.stroke(bboxrect(c2))
   

class cross(path):
   def __init__(self, x, y):
       self.path=[moveto(x,y),
                  rmoveto(-0.1, -0.1), 
		  rlineto(0.2, 0.2), 
		  rmoveto(-0.1, -0.1),
                  rmoveto(-0.1, +0.1), 
		  rlineto(0.2, -0.2)]


def drawpathwbbox(c, p):
    c.stroke(p, [color.rgb.red])
    np = p.normpath()
    c.stroke(np, [color.rgb.green, style.linestyle.dashed])
    c.stroke(bboxrect(p))


def testarcs(c):
    def testarc(c, x, y, phi1, phi2):
        p=path(arc(x,y, 0.5, phi1, phi2))
        np = p.normpath()
        c.stroke(p, [color.rgb.red])
        c.stroke(np, [color.rgb.green, style.linestyle.dashed])

    def testarcn(c, x, y, phi1, phi2):
        p=path(arcn(x,y, 0.5, phi1, phi2))
        np = p.normpath()
        c.stroke(p, [color.rgb.red])
        c.stroke(np, [color.rgb.green, style.linestyle.dashed])

    def testarct(c, r, x0, y0, dx1, dy1, dx2, dy2):
        p=path(moveto(x0,y0), arct(x0+dx1,y0+dy1, x0+dx2, y0+dy2, r), rlineto(dx2-dx1, dy2-dy1), closepath())
        np = p.normpath()
        c.stroke(p, [color.rgb.red, style.linewidth.Thick])
        c.stroke(np, [color.rgb.green, style.linewidth.THin, deco.filled([color.rgb.green])])

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


def testintersectbezier(c):
    p=path(moveto(0,0), curveto(2,6,4,5,2,9)).normpath(epsilon=1e-4)
    q=path(moveto(2,0), curveto(2,6,4,12,1,6)).normpath(epsilon=1e-4)

    c.stroke(q, [style.linewidth.THIN])
    c.stroke(p, [style.linewidth.THIN])

    isect = p.intersect(q)

    for i in isect[0]:
        x, y = p.at(i)
        c.stroke(cross(x, y), [style.linewidth.THIN])

def testintersectcircle(c):
    k=circle(0, 0, 2)
    l=line(0, 0, 3, 0)
    c.stroke(k, [style.linewidth.THIN])
    c.stroke(l, [style.linewidth.THIN])

    isect = k.intersect(l)
    assert len(isect[0])==1, "double count of intersections"

    for i in isect[0]:
        x, y = k.at(i)
        c.stroke(cross(x, y), [style.linewidth.THIN])

def testintersectline(c):
    l1=line(0, 0, 1, 1)
    l2=line(0, 1, 1, 0)
    c.stroke(l1, [style.linewidth.THIN])
    c.stroke(l2, [style.linewidth.THIN])

    isect = l1.intersect(l2)

    for i in isect[0]:
        x, y = l1.at(i)
        c.stroke(circle(x, y, 0.1), [style.linewidth.THIN])


def testnormpathtrafo(c):
    p = path(moveto(0, 5),
             curveto(2, 1, 4, 0, 2, 4),
             rcurveto(-3, 2, 1, 2, 3, 6),
             rlineto(0, 3),
             closepath())

    c.stroke(p)
    c.stroke(p.normpath(), [color.rgb.green, style.linestyle.dashed])
    c.stroke(p, [trafo.translate(3, 1), color.rgb.red])
    c.insert(canvas.canvas([trafo.translate(3,1)])).stroke(p,
                                                          [color.rgb.green,
                                                          style.linestyle.dashed])

    c.stroke(p.reversed(), [color.rgb.blue, style.linestyle.dotted, style.linewidth.THick])

    c.stroke(cross(*(p.at(0))))
    c.stroke(cross(*(p.reversed().at(0))))

    p1, p2 = p.split([1.0, 2.1])
    c.stroke(p1, [color.rgb.red, style.linestyle.dashed])
    c.stroke(p2, [color.rgb.green, style.linestyle.dashed])

    circ1 = circle(0, 10, 1)
    circ2 = circle(1.7, 10, 1)

    c.stroke(circ1)
    c.stroke(circ2)

    isectcirc1, isectcirc2 = circ1.intersect(circ2)
    segment1 = circ1.split(isectcirc1)[0]
    segment2 = circ2.split(isectcirc2)[1]

    segment = segment1 << segment2
    segment[-1].close()

    c.stroke(segment, [style.linewidth.THick, deco.filled([color.rgb.green])])

def testtangent(c):
    p=path(moveto(0,5),
           curveto(2,1,4,0,2,4),
           rcurveto(-3,2,1,2,3,6),
           rlineto(2,3))+circle(5,5,1)
    c.stroke(p, [style.linewidth.THick])
    for i in range(int(p.range())*2):
        c.stroke(p.tangent(i/2.0, length=20*unit.t_pt), [color.rgb.blue, deco.earrow.normal])
        c.stroke(line(0, 0, 1, 0).transformed(p.trafo(i/2.0)), [color.rgb.green, deco.earrow.normal])
        c.stroke(line(0, 0, 0, 1).transformed(p.trafo(i/2.0)), [color.rgb.red, deco.earrow.normal])

    # test the curvature
    cc = canvas.canvas()
    cc.insert(p)
    cc = canvas.canvas([canvas.clip(cc.bbox().path())])
    for i in range(int(p.range())*2):
        radius = p.curvradius(i/2.0)
        if radius is not None:
            radius = unit.tocm(radius)
            pos = p.trafo(i/2.0).apply(0,radius*radius/abs(radius))
            cc.stroke(circle(0, 0,unit.t_cm * abs(radius)), [color.grey(0.5), trafo.translate(*pos)])
    c.insert(cc)


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
    clip=canvas.clip(rect(11,11,10,5))

    p1=path(moveto(10,10), curveto(12,16,14,15,12,19));   
    p2=path(moveto(12,12), curveto(6,18, 5,16, 7,15));  
    
    # just a simple test for clipping
    sc=c.insert(canvas.canvas([clip]))
    drawpathwbbox(sc,p1)
    drawpathwbbox(sc,p2)

    # more complicated operations
    
    # 1. transformation followed by clipping:
    # in this case, the clipping path will be evaluated in the
    # context of the already transformed canvas, so that the
    # actually displayed portion of the path should be the same
    
    sc=c.insert(canvas.canvas([trafo.translate(5,0), clip]))
    drawpathwbbox(sc,p1)
    drawpathwbbox(sc,p2)

    # 2. clipping followed by transformation 
    # in this case, the clipping path will not be transformed, so
    # that the display portionof the path should change

    sc=c.insert(canvas.canvas([clip, trafo.translate(1,1)]))
    drawpathwbbox(sc,p1)
    drawpathwbbox(sc,p2)

def testarclentoparam(c):
    curve=path(moveto(0,0), lineto(0,5), curveto(5,0,0,10,5,5), closepath(),
               moveto(5,0), lineto(10,5))
    ll = curve.arclen()
    # l=[-0.8*ll, -0.6*ll, -0.4*ll, -0.2*ll, 0, 0.1*ll, 0.3*ll, 0.5*ll, 0.7*ll, 0.9*ll]
    l=[0, 0.1*ll, 0.2*ll, 0.3*ll, 0.4*ll, 0.5*ll, 0.6*ll, 0.7*ll, 0.8*ll, 0.9*ll]
    cols=[color.gray.black, color.gray(0.3), color.gray(0.7), color.rgb.red,
          color.rgb.green, color.rgb.blue, color.cmyk(1,0,0,0),
          color.cmyk(0,1,0,0), color.cmyk(0,0,1,0), color.gray.black]
    t=curve.arclentoparam(l)
    c.stroke(curve)
    for i in range(len(t)):
        c.draw(path(circle(curve.at(t[i])[0], curve.at(t[i])[1], 0.1)), [deco.filled([cols[i]]), deco.stroked()])


c = canvas.canvas()
dotest(c, 0, 0, "testarcs")
dotest(c, 2, 12, "testintersectbezier")
dotest(c, 10,11, "testnormpathtrafo")
dotest(c, 12, -4, "testtangent")
dotest(c, 5, -4, "testintersectcircle")
dotest(c, 9, -4, "testintersectline")
dotest(c, 21, 12, "testarclentoparam")
c.writeEPSfile("test_path", paperformat="a4", rotated=0, fittosize=1)
c.writePDFfile("test_path")

c = canvas.canvas()
testarcbbox(c)
testcurvetobbox(c)
testtrafobbox(c)
testclipbbox(c)
c.writeEPSfile("test_bbox", paperformat="a4", rotated=1, fittosize=1)
c.writePDFfile("test_bbox")
#c.writeEPSfile("test_bbox")
