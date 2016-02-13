from pyx import *

g = graph.graphxy(width=8)
g.plot(graph.data.file("errorbar.dat", x=1, y=2, dy=3),
       [graph.style.symbol(), graph.style.errorbar()])
g.writeEPSfile("errorbar")
g.writePDFfile("errorbar")
g.writeSVGfile("errorbar")
