from pyx import *

g = graph.graphxy(width=8, x=graph.linaxis(min=-2, max=2))
g.plot(graph.function("y=exp(x)"))
g2 = g.insert(graph.graphxy(width=3.5, xpos=1, ypos=2,
                            x=graph.linaxis(min=0, max=3),
                            y=graph.linaxis(min=-2, max=2)))
g2.plot(graph.function("y=log(x)"))
g.writetofile("inset")
