from pyx import *

g = graph.graphxy(width=8)
g.plot(graph.data.file("minimal.dat", x=1, y=2))
g.writeEPSfile("minimal")
g.writePDFfile("minimal")
g.writeSVGfile("minimal")
