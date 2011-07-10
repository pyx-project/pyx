from pyx import *
g = graph.graphxy(width=8)
g.plot(graph.data.file("graph.dat", x=1, y=2))
g.writePDFfile()
