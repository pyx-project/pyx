#!/usr/bin/env python
import sys; sys.path.append("..")

import pyx
from pyx import *
from pyx.path import *

import profile
import pstats

def testspeed():
    "coordinates as strings"
    
    c=canvas.canvas()
    p=path(moveto(0,0))

    for i in xrange(1000):
        p.append(lineto("%d pt" % i, "%d pt" % i))

    c.draw(p)
    c.writetofile("testspeed")

def testspeed2():
    "coordinates in user units"

    c=canvas.canvas()
    p=path(moveto(0,0))

    for i in xrange(1000):
        p.append(lineto(i,i))

    c.draw(p)
    c.writetofile("testspeed")

def testspeed3():
    "coordinates in pts (internal routines)"

    c=canvas.canvas()
    p=path(pyx.path._moveto(0,0))

    for i in xrange(1000):
        p.append(pyx.path._lineto(i, i))

    c.draw(p)
    c.writetofile("testspeed")

def testspeedintersect():
    p=path(moveto(10,10), curveto(12,16,14,15,12,19))
    bp=p.bpath()

    for x in xrange(1,100):
        q=path(moveto(x/5.0,10), curveto(12,16,14,22,11,16))
        bq=q.bpath()
        isect = bp.intersect(bq, epsilon=1e-3)

profile.run('testspeed()', 'test.prof')
pstats.Stats("test.prof").sort_stats('time').print_stats(10)

profile.run('testspeed2()', 'test.prof')
pstats.Stats("test.prof").sort_stats('time').print_stats(10)

profile.run('testspeed3()', 'test.prof')
pstats.Stats("test.prof").sort_stats('time').print_stats(10)

profile.run('testspeedintersect()', 'test.prof')
pstats.Stats("test.prof").sort_stats('time').print_stats(10)

