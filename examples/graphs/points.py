# contributed by Chris Spencer

from pyx import *

g = graph.graphxy(width=8)
g.plot(graph.data.points(zip(range(10),range(10)), x=1, y=2))
g.writeEPSfile("points")
g.writePDFfile("points")

