# This is the basic example how to draw an axis along an arbitrary
# path. The function pathaxis from the graph module takes a path and
# an axis and returns "something", which can be inserted into a
# canvas. Different from the typical usecase in graphs, we must fix
# the axis range by appropriate min and max arguments, because of
# missing data. In graphs the range can be adjusted automatically.

from pyx import *

c = canvas.canvas()
c.insert(graph.pathaxis(path.curve(0, 0, 3, 0, 1, 4, 4, 4),
                        graph.linaxis(min=0, max=10)))
c.writetofile("simple")
