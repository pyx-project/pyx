from pyx import *
g = graph.graphxy(width=8, x=graph.axis.linear(min=-5, max=5),
                           y=graph.axis.logarithmic())
g.plot(graph.data.function("y(x)=exp(x)"))
g.writePDFfile()
