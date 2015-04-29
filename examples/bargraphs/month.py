from pyx import *

mypainter = graph.axis.painter.bar(nameattrs=[trafo.rotate(45),
                                              text.halign.right],
                                   innerticklength=0.1)
myaxis = graph.axis.bar(painter=mypainter)

g = graph.graphxy(width=8, x=myaxis)
g.plot(graph.data.file("minimal.dat", xname=1, y=2), [graph.style.bar()])
g.writeEPSfile("month")
g.writePDFfile("month")
g.writeSVGfile("month")
