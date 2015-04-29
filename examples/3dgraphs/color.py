#!/usr/bin/env python
from pyx import *

g = graph.graphxyz(size=4, projector=graph.graphxyz.parallel(170, 45))
g.plot(graph.data.file("color.dat", x=1, y=2, z=3, color=3),
       [graph.style.surface(gradient=color.gradient.RedGreen,
                            gridcolor=color.rgb.black,
                            backcolor=color.rgb.black)])
g.writeEPSfile("color")
g.writePDFfile("color")
g.writeSVGfile("color")
