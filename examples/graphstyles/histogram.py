from pyx import *

d = graph.data.points([(1,  0.3),
                       (2, -0.7),
                       (3, -0.3),
                       (4,  0.8),
                       (5,  0.5)], x=1, y=2)

g = graph.graphxy(width=8)
g.plot(d, [graph.style.histogram()])
g.writeEPSfile("histogram")
g.writePDFfile("histogram")
g.writeSVGfile("histogram")
