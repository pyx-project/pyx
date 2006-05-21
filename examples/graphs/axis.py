from pyx import *

g = graph.graphxy(width=8,
                  x=graph.axis.log(min=1e-1, max=1e4),
                  y=graph.axis.lin(min=-5, max=5))
g.plot(graph.data.function("y(x)=tan(log(1/x))"))
g.writeEPSfile("axis")
g.writePDFfile("axis")
