from math import pi
from pyx import *

g = graph.type.graphxy(width=8, key=graph.key.key(pos="bl"),
        x=graph.axis.linaxis(min=0, max=2*pi, title="$x$", divisor=pi,
                         texter=graph.texter.rationaltexter(suffix=r"\pi")),
        y=graph.axis.linaxis(title="$y$"))

g.plot(graph.data.function("y=sin(x)", title=r"$\sin(x)$"))
g.plot(graph.data.function("y=cos(x)", title=r"$\cos(x)$"))

g.finish()
g.stroke(g.ygridpath(0))

g.writeEPSfile("piaxis")
