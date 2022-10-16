from math import pi
from pyx import *
from pyx.graph import axis

g = graph.graphxy(width=8, key=graph.key.key(pos="bl"),
        x=axis.linear(min=0, max=2*pi, title="$x$", divisor=pi,
                           texter=axis.texter.rational(suffix=r"\pi")),
        y=axis.linear(title="$y$"))

g.plot(graph.data.function("y(x)=sin(x)", title=r"$\sin(x)$"))
g.plot(graph.data.function("y(x)=cos(x)", title=r"$\cos(x)$"))

g.finish()
g.stroke(g.ygridpath(0))

g.writeEPSfile()
g.writePDFfile()
g.writeSVGfile()
