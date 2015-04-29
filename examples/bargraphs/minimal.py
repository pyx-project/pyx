from pyx import *

g = graph.graphxy(width=8, x=graph.axis.bar())
g.plot(graph.data.file("minimal.dat", xname=0, y=2), [graph.style.bar()])
g.writeEPSfile("minimal")
g.writePDFfile("minimal")
g.writeSVGfile("minimal")
