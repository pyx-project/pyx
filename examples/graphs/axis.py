from pyx import *

g = graph.graphxy(width=8,
                  x=graph.axis.log(min=1e-1, max=1e4, title=r"$x$-axis"),
                  y=graph.axis.lin(max=5, title=r"$y$-axis"))
g.plot(graph.data.function("y(x)=tan(log(1/x))**2"))
g.writeEPSfile("axis")
g.writePDFfile("axis")
g.writeSVGfile("axis")
