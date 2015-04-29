from pyx import *

c = graph.axis.pathaxis(path.curve(0, 0, 3, 0, 1, 4, 4, 4),
                        graph.axis.linear(min=0, max=10))
c.writeEPSfile("minimal")
c.writePDFfile("minimal")
c.writeSVGfile("minimal")
