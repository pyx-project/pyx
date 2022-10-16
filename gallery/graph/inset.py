from pyx import *

g = graph.graphxy(width=8, x=graph.axis.linear(min=-2, max=2))
g.plot(graph.data.function("y(x)=exp(x)"))
g2 = g.insert(graph.graphxy(width=3.5, xpos=1, ypos=2,
                            x=graph.axis.linear(min=0, max=3),
                            y=graph.axis.linear(min=-2, max=2)))
g2.plot(graph.data.function("y(x)=log(x)"))
g.writeEPSfile()
g.writePDFfile()
g.writeSVGfile()
