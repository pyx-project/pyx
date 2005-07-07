# This is the basic example how to draw an axis along an arbitrary
# path. The function pathaxis from the graph.axis module takes a path
# and returns a canvas. Different from the typical usecase in graphs,
# we must fix the axis range by appropriate min and max arguments,
# because of missing data. In graphs the range can be adjusted
# automatically.

from pyx import *

c = graph.axis.pathaxis(path.curve(0, 0, 3, 0, 1, 4, 4, 4),
                        graph.axis.linear(min=0, max=10))
c.writeEPSfile("simple")
c.writePDFfile("simple")
