from math import pi, atan2
from pyx import *

z1 = 2.5 + 4.5j
z2 = 7.5 + 5.5j

# we abuse a parametric function below, so we express everything in terms of a parameter k
x = lambda k: int(k)//11
y = lambda k: int(k)%11
z = lambda k: x(k) + y(k) * 1j
f = lambda k: 1/(z(k)-z1)/(z(k)-z2)                # function to be plotted
s = lambda k: 5*abs(f(k))                          # magnitude of function value
a = lambda k: 180/pi*atan2(f(k).imag, f(k).real)   # direction of function value

g = graph.graphxy(width=8,
                  x=graph.axis.linear(min=0, max=10),
                  y=graph.axis.linear(min=0, max=10))
g.plot(graph.data.paramfunction("k", 0, 120,
                                "x, y, size, angle = x(k), y(k), s(k), a(k)",
                                points=121, context=locals()),# access extern
       [graph.style.arrow()])                                 # variables&functions
                                                              # by passing a context
g.writeEPSfile()
g.writePDFfile()
g.writeSVGfile()
