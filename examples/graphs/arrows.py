from math import pi, sqrt, atan2
from pyx import *

z1 = 2.5 + 4.5j
z2 = 7.5 + 5.5j

# we abuse a parametric function below, so we express everything in terms of a parameter k
x = lambda k: int(k)/11
y = lambda k: int(k)%11
z = lambda k: x(k) + y(k) * 1j
f = lambda k: 1/(z(k)-z1)/(z(k)-z2)                # function to be plotted
s = lambda k: 5*sqrt(f(k).real**2 + f(k).imag**2)  # norm of the function
a = lambda k: 180/pi*atan2(f(k).imag, f(k).real)   # direction of the function

g = graph.graphxy(width=8,
                  x=graph.linaxis(min=0, max=10),
                  y=graph.linaxis(min=0, max=10))
g.plot(graph.paramfunction("k", 0, 120,
                           "x, y, size, angle = x(k), y(k), s(k), a(k)",
                           points=121, context=locals()),
       style=graph.arrow())
g.writetofile("arrows")
