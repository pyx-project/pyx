import math, random
from pyx import *

# a xy-graph has linear x and y axes by default
# they might be overwritten and futher axes might be added as well
g = graph.graphxy(width=8, y=graph.logaxis(), y2=graph.linaxis(),
                  y3=graph.linaxis(min=0, max=1),
                  y4=graph.linaxis(min=0, max=2))

r = random.Random()
d = [(i, math.exp(0.8*i+r.random())) for i in range(1,10)]
f = lambda x, a: x*a

g.plot(graph.data(data.data(d), x=0, y=1))
g.plot(graph.function("y2=f(x, 1)", context=locals()))

g.plot(graph.function("x=5+sin(2*pi*y3)"))
g.plot(graph.function("x=5+sin(2*pi*y4)"))

g.writetofile("manyaxes")

