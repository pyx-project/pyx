from pyx import *

g = graph.graphxy(width=10,
                  x=graph.linaxis(min=0, max=2),
                  y=graph.linaxis(min=0, max=2))
g.plot([graph.function("x=y**(2**(3-%i))" % i) for i in range(3)] +
       [graph.function("y=x**(2**%i)" % i) for i in range(4)],
       graph.line([graph.changecolor.Rainbow()]))
g.writetofile("change")

