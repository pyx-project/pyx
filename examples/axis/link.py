import math
from pyx import *

c = canvas.canvas()

g1 = c.insert(graph.graphxy(width=8))
g1.plot(graph.data.function("y(x)=2*exp(-30*x)-exp(-3*x)", min=0, max=1))

g2 = c.insert(graph.graphxy(width=8, ypos=g1.height+0.5,
                            x=graph.axis.linkedaxis(g1.axes["x"])))
g2.plot(graph.data.function("y(x)=cos(20*x)*exp(-2*x)"))

c.writeEPSfile("link")
c.writePDFfile("link")
c.writeSVGfile("link")
