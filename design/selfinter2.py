#!/usr/bin/env python3
import sys;sys.path.insert(0, "..")
from math import *
from pyx import *
# File for invalid parametrisations of Bezier curves
# Draws a sketch of the areas where invalid params are to be expected

xmin, xmax = -2, 5
ymin, ymax = -xmax, 2

g = graph.graphxy(width=10,
    x=graph.axis.lin(title=r"$\Delta x$", min=xmin, max=xmax),
    y=graph.axis.lin(title=r"$\Delta y$", min=ymin, max=ymax),
    key=graph.key.key(pos="tr"),
)
g.plot(graph.data.function("y(x)=-1", title=None), [graph.style.line([style.linestyle.dotted])])
d1 = g.plot(graph.data.function("x(y)=(-1-2*y-sqrt((1+2*y)**2+3))/3.0", title=r"cusp ($-$)"), [graph.style.line()])
d2 = g.plot(graph.data.function("x(y)=(-1-2*y+sqrt((1+2*y)**2+3))/3.0", title=r"cusp ($+$)", max=-1), [graph.style.line([color.rgb.red])])
d3 = g.plot(graph.data.function("x(y)=1.0/(3.0*(y+1))", title=r"passes through $(0,0)$", max=-1), [graph.style.line([color.rgb.green])])
d4 = g.plot(graph.data.function("x(y)=(1+y**3)/(3.0*(1+y))", title=r"passes through $(1,0)$", max=-1), [graph.style.line([color.rgb.blue])])
g.doplot()

p = d1.path << d3.path.reversed()
p.append(path.closepath())
g.layers["filldata"].fill(p, [color.gray(0.8)])

p = d2.path << d4.path.reversed()
p.append(path.closepath())
g.layers["filldata"].fill(p, [color.gray(0.8)])

g.writePDFfile()



