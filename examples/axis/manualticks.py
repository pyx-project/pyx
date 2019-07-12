import math
from pyx import *

p1 = path.curve(0, 0, 3, 0, 1, 4, 4, 4)
p2 = p1.transformed(trafo.translate(4, 0))

myticks = [graph.axis.tick.tick(math.pi, label=r"\pi", labelattrs=[text.mathmode]),
           graph.axis.tick.tick(2*math.pi, label=r"2\pi", labelattrs=[text.mathmode])]

c = canvas.canvas()
c.insert(graph.axis.pathaxis(p1, graph.axis.linear(min=0, max=10)))
c.insert(graph.axis.pathaxis(p2, graph.axis.linear(min=0, max=10, manualticks=myticks)))
c.writeEPSfile("manualticks")
c.writePDFfile("manualticks")
c.writeSVGfile("manualticks")
