#!/usr/bin/env python
from pyx import *
from pyx.path import *

import profile
import pstats

def drawpathwbbox(c, p):
    c.draw(p)
    bbox=p.bbox(c)
    c.draw(rect("%f t pt" % bbox.llx,            "%f t pt" % bbox.lly,
   	        "%f t pt" % (bbox.urx-bbox.llx), "%f t pt" % (bbox.ury-bbox.lly)))

def test1():
    c1=canvas.canvas()

    p=path([moveto(0,0)])

    for i in xrange(1000):
        p.append(lineto("%d pt" % i, "%d pt" % i))

    c1.draw(p)

    c1.writetofile("test")

def testarcbbox():

    c=canvas.canvas()

    for phi in range(0,360,30):
       drawpathwbbox(c,path([arc(phi*0.1, phi*0.1, 1, 0, phi)]))

    for phi in range(0,360,30):
       drawpathwbbox(c,path([arc(phi*0.1, 5+phi*0.1, 1, phi, 360)]))

    for phi in range(0,360,30):
       drawpathwbbox(c,path([arc(phi*0.1, 10+phi*0.1, 1, phi, phi+30)]))

    for phi in range(0,360,30):
       drawpathwbbox(c,path([arc(phi*0.1, 15+phi*0.1, 1, phi, phi+120)]))

    for phi in range(0,360,30):
       drawpathwbbox(c,path([arc(phi*0.1, 20+phi*0.1, 1, phi, phi+210)]))

    for phi in range(0,360,30):
       drawpathwbbox(c,path([arc(phi*0.1, 25+phi*0.1, 1, phi, phi+300)]))

    for phi in range(0,360,30):
       drawpathwbbox(c,path([arc(phi*0.1, 30+phi*0.1, 1, phi, phi+390)]))

    c.writetofile("test")


def testcurvetobbox():

    c=canvas.canvas()

    drawpathwbbox(c,path([moveto(10,10), curveto(12,16,14,15,12,19)]))

    c.writetofile("test")


testarcbbox()    
#testcurvetobbox()    

#test()
#profile.run('test()', 'test.prof')
#pstats.Stats("test.prof").sort_stats('time').print_stats(10)
