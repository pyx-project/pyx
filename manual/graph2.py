from pyx import *
g = graph.graphxy(width=10)
g.plot(graph.data.function("y=x**2"))
g.plot(graph.data.file("graph.dat", x=1, y=2))
g.writeEPSfile("graph2")
