#!/usr/bin/env python
import sys;sys.path.insert(0, "..")
from math import *
from pyx import *
# File for invalid parametrisations of Bezier curves
# Check a-posteriori the sign of Delta y for the square-root solution of Delta x

def Dx_m(y):
    return (-1-2*y-sqrt((1+2*y)**2+3))/3.0
def Dx_p(y):
    return (-1-2*y+sqrt((1+2*y)**2+3))/3.0

con = {"Dx_m":Dx_m, "Dx_p":Dx_p}

g = graph.graphxy(width=10,
    x=graph.axis.lin(),
    y=graph.axis.lin(min=-2, max=2),
    key=graph.key.key(pos="bl"),
)
g.plot(graph.data.function("x(y)=6*y*Dx_m(y)", title="minus-sol, lhs", context=con), [graph.style.line([color.rgb.red])])
g.plot(graph.data.function("x(y)=(1-3*Dx_m(y))*(1-y-sqrt(1+y+y*y))", title="minus-sol, minus-rhs", context=con), [graph.style.line([color.rgb.blue, style.linestyle.dashed])])
g.plot(graph.data.function("x(y)=6*y*Dx_p(y)", title="plus-sol, lhs", context=con), [graph.style.line([color.rgb.green])])
g.plot(graph.data.function("x(y)=(1-3*Dx_p(y))*(1-y+sqrt(1+y+y*y))", title="plus-sol, plus-rhs", context=con), [graph.style.line([style.linestyle.dashed])])
g.plot(graph.data.function("x(y)=(1-3*Dx_p(y))*(1-y-sqrt(1+y+y*y))", title="plus-sol, minus-rhs", context=con), [graph.style.line([style.linestyle.dotted])])
g.plot(graph.data.function("x(y)=(1-3*Dx_m(y))*(1-y+sqrt(1+y+y*y))", title="minus-sol, plus-rhs", context=con), [graph.style.line([style.linestyle.dotted])])
g.writePDFfile()

