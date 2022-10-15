from math import pi
from pyx import *
from pyx.graph import axis

g = graph.graphxy(width=10,
                  x_min=-4*pi, x_max=4*pi,
                  x_painter_gridattrs=[], x_divisor=pi, x_texter=axis.texter.rational(suffix=r"\pi"),
                  y_painter_gridattrs=[attr.changelist([style.linestyle.dashed, None])])

g.plot(graph.data.function("y(x)=sin(x)/x", points=200))

g.writeEPSfile()
g.writePDFfile()
g.writeSVGfile()
