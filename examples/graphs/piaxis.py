from math import pi
from pyx import *

c = canvas.canvas()
g = c.insert(graph.graphxy(width=8,
                           autokey=graph.key(pos="tr"),
                           x=graph.linaxis(min=0, max=2*pi, title="x",
                                           divisor=pi, suffix=r"\pi"),
                           y=graph.linaxis(title="y")))

g.plot(graph.function("y=sin(x)"))
g.plot(graph.function("y=cos(x)"))
c.writetofile("piaxis")
