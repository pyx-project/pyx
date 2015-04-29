#!/usr/bin/env python
from pyx import *

g = graph.graphxyz(size=4, x2=None, y2=None)
g.plot(graph.data.file("surface.dat", x=1, y=2, z=3), [graph.style.surface()])
g.writeEPSfile("surface")
g.writePDFfile("surface")
g.writeSVGfile("surface")
