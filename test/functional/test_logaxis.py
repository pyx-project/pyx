import sys; sys.path[:0] = ["../.."]
from pyx import *

c = canvas.canvas()

g = c.insert(graph.graphxy(ypos=6, width=7, y=graph.axis.log(parter=graph.axis.parter.log(tickpreexps=[graph.axis.parter.log.pre1exp, graph.axis.parter.log.pre1to9exp]))))
g.plot(graph.data.file("test_logaxis.dat", x=1, y=2))
g = c.insert(graph.graphxy(ypos=6, xpos=10, width=7, y=graph.axis.log(parter=graph.axis.parter.log(tickpreexps=[graph.axis.parter.log.pre1exp, graph.axis.parter.log.pre1to9exp]))))
g.plot(graph.data.file("test_logaxis.dat", x=1, y="-$2"))

g = c.insert(graph.graphxy(width=7, y=graph.axis.log()))
g.plot(graph.data.file("test_logaxis.dat", x=1, y=2))
g = c.insert(graph.graphxy(xpos=10, width=7, y=graph.axis.log()))
g.plot(graph.data.file("test_logaxis.dat", x=1, y="-$2"))

c.writeEPSfile()
c.writePDFfile()
c.writeSVGfile()
