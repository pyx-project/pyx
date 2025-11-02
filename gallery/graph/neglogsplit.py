from math import pi
from pyx import *

g = graph.graphxy(width=10, key=graph.key.key(),
                  x_divisor=pi, x_texter=graph.axis.texter.rational(suffix=r'\pi'),
                  y=graph.axis.split(reverse=1, subaxes={-1: graph.axis.log(min=-100),
                                                         1: graph.axis.log(max=100)}))
g.plot(graph.data.function("y(x)=(sgn(sin(x)), abs(sin(x)) > 0.001 and 1/sin(x) or None)",
                           min=0, max=6*pi, points=10001, title="y(x)=1/sin(x)"))
g.writeEPSfile()
g.writePDFfile()
g.writeSVGfile()
