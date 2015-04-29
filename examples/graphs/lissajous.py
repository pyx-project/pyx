from math import pi
from pyx import *

g = graph.graphxy(width=8)
g.plot(graph.data.paramfunction("k", 0, 2*pi, "x, y = sin(2*k), cos(3*k)"))
g.writeEPSfile("lissajous")
g.writePDFfile("lissajous")
g.writeSVGfile("lissajous")
