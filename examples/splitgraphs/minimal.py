# In the most simple case we create a data column
# containing a tuple and use a splitaxis.

from pyx import *

g = graph.graphxy(width=8, x=graph.axis.split())
g.plot(graph.data.list([((0, 0.1), 0.1),
                        ((0, 0.5), 0.2),
                        ((0, 0.9), 0.3),
                        ((1, 101), 0.7),
                        ((1, 105), 0.8),
                        ((1, 109), 0.9)], x=1, y=2))
g.writeEPSfile("minimal")
