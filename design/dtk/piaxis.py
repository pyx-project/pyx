from math import pi
from pyx import *
from pyx.graph.axis import linear
from pyx.graph.axis.texter import rational

g = graph.graphxy(width=8, key=graph.key.key(pos="bl"),
                  x=linear(min=0, max=2*pi, title="$x$", divisor=pi,
                           texter=rational(suffix=r"\pi")),
                  y=linear(title="$y$"))

g.plot(graph.data.function("y(x)=sin(x)", title=r"$\sin(x)$"))
g.plot(graph.data.function("y(x)=cos(x)", title=r"$\cos(x)$"))

g.writeEPSfile("piaxis")
