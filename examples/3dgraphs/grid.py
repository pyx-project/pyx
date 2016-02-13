#!/usr/bin/env python
from pyx import *

g = graph.graphxyz(size=4, z=graph.axis.lin(min=0.001))
g.plot(graph.data.file("grid.dat", x=1, y=2, z=3), [graph.style.grid()])
g.writeEPSfile("grid")
g.writePDFfile("grid")
g.writeSVGfile("grid")
