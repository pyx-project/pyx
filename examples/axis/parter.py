import math
from pyx import *

p = path.curve(0, 0, 3, 0, 1, 4, 4, 4)

myparter = graph.axis.parter.linear(["1/3", "1/6"])

c = canvas.canvas()
c.insert(graph.axis.pathaxis(p, graph.axis.linear(min=0, max=1, parter=myparter)))
c.insert(graph.axis.pathaxis(p.transformed(trafo.translate(4, 0)),
                             graph.axis.linear(min=0, max=1, parter=myparter,
                             texter=graph.axis.texter.rational())))
c.writeEPSfile("parter")
c.writePDFfile("parter")
c.writeSVGfile("parter")
