from pyx import *

g = graph.graphxy(width=10,
                  x=graph.axis.linear(min=0, max=2),
                  y=graph.axis.linear(min=0, max=2))
g.plot([graph.data.function("x=y**(2**(3-%i))" % i) for i in range(3)] +
       [graph.data.function("y=x**(2**%i)" % i) for i in range(4)],
       [graph.style.line([color.palette.Rainbow])])
g.writeEPSfile("change")

