# suggested by Chris Spencer

from pyx import *

g = graph.graphxy(width=8)
# either provide lists of the individual coordinates
g.plot(graph.data.values(x=range(10), y=range(10)))
# or provide one list containing the whole points
g.plot(graph.data.points(zip(range(10), range(10)), x=1, y=2))
g.writeEPSfile("points")
g.writePDFfile("points")

