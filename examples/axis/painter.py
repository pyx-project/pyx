# The axispainter performs the painting of an axis. By default, ticks
# are stroked inside of the graph (in the path examples there is no
# graph but don't mind) while labels and the axis title are plotted
# outside. The axistitle is rotated along the axis (without writing it
# upside down), while the tick labels are not rotated. The axispainter
# takes a variety of keyword arguments to modify the default
# behaviour.

from pyx import *

ap = graph.painter.axispainter(outerticklength=graph.painter.ticklength.normal)

c = graph.axis.pathaxis(path.curve(0, 0, 3, 0, 1, 4, 4, 4),
                        graph.axis.linaxis(min=0, max=10, title="axis title",
                                           painter=ap))
c.writeEPSfile("painter")
