from math import pi
from pyx import *
from pyx.graph import axis

xgridpainter = axis.painter.regular(gridattrs=[])
ygridpainter = axis.painter.regular(gridattrs=[attr.changelist([style.linestyle.dashed, None])])

g = graph.graphxy(width=10,
                  x=axis.lin(painter=xgridpainter,
                             divisor=pi, texter=axis.texter.rational(suffix=r"\pi"), min=-4*pi, max=4*pi),
                  y=axis.lin(painter=ygridpainter))

g.plot(graph.data.function("y(x)=sin(x)/x", points=200))

g.writeEPSfile()
g.writePDFfile()
g.writeSVGfile()
