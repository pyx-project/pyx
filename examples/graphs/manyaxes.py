import math, random
from pyx import *

# a xy-graph has linear x and y axes by default
# they might be overwritten and futher axes might be added as well
g = graph.type.graphxy(width=8, y=graph.axis.logaxis(), y2=graph.axis.linaxis(),
                       y3=graph.axis.linaxis(min=0, max=1),
                       y4=graph.axis.linaxis(min=0, max=2))

# we generate some data and a function with multiple arguments
d = [(i, math.exp(0.8*i+random.random())) for i in range(1,10)]
f = lambda x, a: x*a

g.plot(graph.data.data(data.data(d), x=0, y=1))
g.plot(graph.data.function("y2=f(x, 1)", context=locals()))

g.plot(graph.data.function("x=5+sin(2*pi*y3)"))
g.plot(graph.data.function("x=5+sin(2*pi*y4)"))

g.writeEPSfile("manyaxes")

