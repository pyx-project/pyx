import math
from pyx import *

c = canvas.canvas()

g1 = c.insert(graph.graphxy(width=8,
                            x=graph.axis.linaxis(min=0, max=1)))
g1.plot(graph.data.function("y=2*exp(-30*x)-exp(-3*x)"))

g2 = c.insert(graph.graphxy(width=8, ypos=g1.height+0.5,
                            x=g1.axes["x"].createlinkaxis()))
g2.plot(graph.data.function("y=cos(20*x)*exp(-2*x)"))

c.writeEPSfile("link")
