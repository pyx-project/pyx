from pyx import *

g = graph.type.graphxy(width=8, x=graph.axis.linaxis(min=-2, max=2))
g.plot(graph.data.function("y=exp(x)"))
g2 = g.insert(graph.type.graphxy(width=3.5, xpos=1, ypos=2,
                                 x=graph.axis.linaxis(min=0, max=3),
                                 y=graph.axis.linaxis(min=-2, max=2)))
g2.plot(graph.data.function("y=log(x)"))
g.writeEPSfile("inset")
