#!/usr/bin/env python
import sys
sys.path[:0] = [".."]

import pyx
from pyx import *
from pyx.path import *


def testspeed():
    "coordinates as strings"
    
    c=canvas.canvas()
    p=path(moveto(0,0))

    for i in xrange(1000):
        p.append(lineto("%d pt" % i, "%d pt" % i))

    c.stroke(p)
    c.writetofile("testspeed")

def testspeed2():
    "coordinates in user units"

    c=canvas.canvas()
    p=path(moveto(0,0))

    for i in xrange(1000):
        p.append(lineto(i,i))

    c.stroke(p)
    c.writetofile("testspeed")

def testspeed3():
    "coordinates in pts (internal routines)"

    c=canvas.canvas()
    p=path(pyx.path.moveto_pt(0,0))

    for i in xrange(1000):
        p.append(pyx.path.lineto_pt(i, i))

    c.stroke(p)
    c.writetofile("testspeed")

def testspeedintersect():
    p=path(moveto(10,10), curveto(12,16,14,15,12,19))
    bp=normpath(p)

    for x in xrange(1,100):
        q=path(moveto(x/5.0,10), curveto(12,16,14,22,11,16))
        bq=normpath(q)
        isect = bp.intersect(bq, epsilon=1e-3)

import profile, pstats

import hotshot, hotshot.stats

def profilefunction(f):
    prof = hotshot.Profile("test.prof")
    prof.runcall(f)
    prof.close()
    stats = hotshot.stats.load("test.prof")
    stats.strip_dirs()
    stats.sort_stats('time', 'calls')
    stats.print_stats(10)

profile.run('testspeed()', 'test.prof')
pstats.Stats("test.prof").sort_stats('time').print_stats(10)

profilefunction(testspeed)

#profile.run('testspeed2()', 'test.prof')
#pstats.Stats("test.prof").sort_stats('time').print_stats(10)

#profile.run('testspeed3()', 'test.prof')
#pstats.Stats("test.prof").sort_stats('time').print_stats(10)

#profile.run('testspeedintersect()', 'test.prof')
#pstats.Stats("test.prof").sort_stats('time').print_stats(10)


