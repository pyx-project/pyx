#!/usr/bin/env python
import sys;sys.path.insert(0, "..")
from math import *
from pyx import *
# File for invalid parametrisations of Bezier curves
# visualise the constraints

def fx(x, sign1):
    if x < 1/3.0: # a_x > 0
        if sign1 == "upper":
            return -x + abs(x)
        else:
            return -x - abs(x)
    else:
        if sign1 == "upper":
            return x - abs(x)
        else:
            return x + abs(x)

def boundx(x):
    if x < 1/3.0:
        return 1-3*x
    else:
        return 3*x-1

def fy(y, sign2):
    if y < 0: # a_y > 0
        if sign2 == "upper":
            return 1-y + sqrt(1+y+y*y)
        else:
            return 1-y - sqrt(1+y+y*y)
    else:
        if sign2 == "upper":
            return y-1 - sqrt(1+y+y*y)
        else:
            return y-1 + sqrt(1+y+y*y)

def boundy(y):
    if y < 0:
        return -3*y
    else:
        return 3*y

def doplot(xtitle, con):
    g = graph.graphxy(width=10,
        x=graph.axis.lin(title=xtitle, min=-5, max=5),
        y=graph.axis.lin(),
        key=graph.key.key(pos="tc"),
    )
    g.plot(graph.data.function("y(x)=0", points=2, title=None), [graph.style.line()])
    g.plot(graph.data.function("y(x)=bound(x)", title=None, context=con, points=101), [graph.style.line()])
    g.plot(graph.data.function("y(x)=f(x, 'upper')", title="upper sign", context=con, points=101), [graph.style.line([color.rgb.red])])
    g.plot(graph.data.function("y(x)=f(x, 'lower')", title="lower sign", context=con, points=101), [graph.style.line([color.rgb.green])])
    return g


c1 = doplot(r"$\Delta x$", {"f":fx, "bound":boundx})
c2 = doplot(r"$\Delta y$", {"f":fy, "bound":boundy})
c1.insert(c2, [trafo.translate(0, c1.bbox().bottom() - c2.bbox().top() - 0.5)])
c1.writePDFfile()
