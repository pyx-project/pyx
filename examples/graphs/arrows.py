from math import pi
from pyx import *

c = canvas.canvas()
div = lambda x, y: int(x)/int(y)
mod = lambda x, y: int(x)%int(y)
g = c.insert(graph.graphxy(width=8,
                           x=graph.linaxis(min=0, max=10),
                           y=graph.linaxis(min=0, max=10)))

g.plot(graph.paramfunction("k", 0, 120, "x, y, size, angle = mod(k, 11), div(k, 11), (1+sin(k*pi/120))/2, 3*k",
                           points=121,
                           context=locals()),
       style = graph.arrow())

c.writetofile("arrows")
