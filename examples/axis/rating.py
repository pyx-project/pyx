from pyx import *

p2 = path.curve(0, 0, 3, 0, 1, 4, 4, 4)
p1 = p2.transformed(trafo.translate(-4, 0).scaled(0.75))
p3 = p2.transformed(trafo.scale(1.25).translated(4, 0))

myaxis = graph.axis.linear(min=0, max=10)

c = canvas.canvas()
c.insert(graph.axis.pathaxis(p1, myaxis))
c.insert(graph.axis.pathaxis(p2, myaxis))
c.insert(graph.axis.pathaxis(p3, myaxis))
c.writeEPSfile("rating")
c.writePDFfile("rating")
c.writeSVGfile("rating")
