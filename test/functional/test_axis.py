#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

import math
from pyx import *

l = unit.topt(8)

def hpaint(c, x, y, axis, reverse=0):
    x, y = map(unit.topt, (x, y))
    ticks = axis.part.defaultpart(axis.min/axis.divisor, axis.max/axis.divisor, 0, 0)
    axis._vtickpoint = lambda v, axis=axis, x=x, y=y, l=l: (x+v*l, y)
    axis.vtickdirection = lambda v, axis=axis, reverse=reverse: (0, -1 + 2*reverse)
    axis.vbaseline = lambda v1=0, v2=1, axis=axis, x=x, y=y, l=l: path._line(x+v1*l, y, x+v2*l, y)
    axis.texter.labels(ticks)
    ac = graph.axiscanvas()
    axis.painter.paint(axis, ticks, ac)
    c.insert(ac)

def vpaint(c, x, y, axis, reverse=0):
    x, y = map(unit.topt, (x, y))
    ticks = axis.part.defaultpart(axis.min/axis.divisor, axis.max/axis.divisor, 0, 0)
    axis._vtickpoint = lambda v, axis=axis, x=x, y=y, l=l: (x, y+v*l)
    axis.vtickdirection = lambda v, axis=axis, reverse=reverse: (-1 + 2*reverse, 0)
    axis.vbaseline = lambda v1=0, v2=1, axis=axis, x=x, y=y, l=l: path._line(x, y+v1*l, x, y+v2*l)
    axis.texter.labels(ticks)
    ac = graph.axiscanvas()
    axis.painter.paint(axis, ticks, ac)
    c.insert(ac)

def cpaint(c, x, y, axis):
    x, y = map(unit.topt, (x, y))
    ticks = axis.part.defaultpart(axis.min/axis.divisor, axis.max/axis.divisor, 0, 0)
    axis._vtickpoint = lambda v, axis=axis, x=x, y=y, l=l: (x+l/2*math.cos(v*2*math.pi), y+l/2*math.sin(v*2*math.pi))
    axis.vtickdirection = lambda v, axis=axis: (math.cos(v*2*math.pi), math.sin(v*2*math.pi))
    axis.vbaseline = lambda v1=0, v2=1, axis=axis, x=x, y=y, l=l: path._circle(x, y, l/2)
    axis.texter.labels(ticks)
    ac = graph.axiscanvas()
    axis.painter.paint(axis, ticks, ac)
    c.insert(ac)

c = canvas.canvas()
lintest = {"title": "axis title", "min": 0, "max": 1, "part": graph.linpart(("0.25", "0.1/0.8"))}
hpaint(c, 0, 0, graph.linaxis(**lintest))
hpaint(c, 0, 1, graph.linaxis(**lintest), reverse=1)
hpaint(c, 0, 5, graph.linaxis(painter=graph.axispainter(labelattrs=trafo.rotate(45), titleattrs=trafo.rotate(45)), **lintest))
hpaint(c, 0, 8, graph.linaxis(painter=graph.axispainter(labelattrs=(trafo.rotate(45), text.halign.right), titleattrs=trafo.rotate(-45)), **lintest))
vpaint(c, 11, 0, graph.linaxis(painter=graph.axispainter(tickattrs=color.rgb.red, innerticklengths=0, outerticklengths=graph.axispainter.defaultticklengths), **lintest))
vpaint(c, 12, 0, graph.linaxis(painter=graph.axispainter(tickattrs=(None, (color.rgb.green,))), **lintest), reverse=1)
vpaint(c, 16, 0, graph.linaxis(texter=graph.exponentialtexter(), **lintest))
vpaint(c, 18, 0, graph.linaxis(texter=graph.rationaltexter(), **lintest))
lintest = {"title": "axis title", "min": -2*math.pi, "max": 0, "divisor": math.pi, "part": graph.linpart("0.25")}
hpaint(c, 0, 11, graph.linaxis(texter=graph.rationaltexter(suffix="\pi"), **lintest))
lintest = {"title": "axis title", "min": 0, "max": 2*math.pi, "divisor": math.pi, "part": graph.linpart("0.5")}
hpaint(c, 10, 11, graph.linaxis(texter=graph.rationaltexter(enumsuffix="\pi", over="%s/%s"), **lintest))
lintest = {"min": 0, "max": 2*math.pi, "divisor": math.pi, "part": graph.linpart("0.125")}
cpaint(c, 4, 17, graph.linaxis(texter=graph.rationaltexter(suffix="\pi"), **lintest))
lintest = {"min": 0, "max": 2*math.pi, "divisor": math.pi/180, "part": graph.linpart("30")}
cpaint(c, 14, 17, graph.linaxis(painter=graph.axispainter(labeldirection=graph.paralleltext), **lintest))
c.writetofile("test_axis", paperformat="a4")

