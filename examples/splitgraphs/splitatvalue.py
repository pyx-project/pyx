# You can use the splitatvalue function to split data at
# certain values. When splitting at several positions, the
# splitatvalue function marks odd regions to be a "None",
# which will in the end be ignored by a splitaxis.

from pyx import *

pf = graph.data.paramfunction

g = graph.graphxy(width=8, x=graph.axis.split())
g.plot(pf("k", -1, 1,
          "x, y = splitatvalue(k, -0.9, 0.9), k**100",
          points=1000))
g.writeEPSfile("splitatvalue")
