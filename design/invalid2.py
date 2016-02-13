#!/usr/bin/env python3
import sys;sys.path.insert(0, "..")
from math import *
from pyx import *
# File for invalid parametrisations of Bezier curves
# Draws a sketch of the areas where invalid params are to be expected

def lhs(x, y, sign1):
    if sign1 > 0:
        return -3*y*(-x + abs(x))
    else:
        return -3*y*(-x - abs(x))

def rhs(x, y, sign2):
    if sign2 > 0:
        return (1-3*x) * (1-y + sqrt(1+y+y*y))
    else:
        return (1-3*x) * (1-y - sqrt(1+y+y*y))

def f(x, y):
    xsigns = [-1, 1]
    ysigns = [-1, 1]
    if 0 < x < 1:
        xsigns = [1]
    if y > -1:
        ysigns = [-1]

    val = float("inf")
    for sign1 in xsigns:
        for sign2 in ysigns:
            val = min(val, abs(lhs(x,y,sign1) - rhs(x,y,sign2)))
    return val

xmin, xmax, xn = -2, 3, 250
xvalues = [xmin + (xmax-xmin)*i/(xn-1) for i in range(xn)]
ymin, ymax, yn = -3, 2, 250
yvalues = [ymin + (ymax-ymin)*i/(yn-1) for i in range(yn)]

d = []
for x in xvalues:
    for y in yvalues:
        d.append((x, y, log(f(x, y))))

g = graph.graphxy(width=10,
    x=graph.axis.lin(title=r"$\Delta x$", min=xmin, max=xmax),
    y=graph.axis.lin(title=r"$\Delta y$", min=ymin, max=ymax),
)
g.plot(graph.data.points(d, x=1, y=2, color=3, title=None),
       [graph.style.density(gradient=color.rgbgradient.Rainbow)])
g.dolayout()
g.plot(graph.data.function("x(y)=(-1-2*y-sqrt((1+2*y)**2+3))/3.0"), [graph.style.line([style.linestyle.dotted])])
g.plot(graph.data.function("x(y)=(-1-2*y+sqrt((1+2*y)**2+3))/3.0", max=-1), [graph.style.line([style.linestyle.dotted])])
g.writePDFfile()

