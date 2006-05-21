from pyx import *

g = graph.graphxy(width=8,
                  x=graph.axis.linear(min=0, max=2),
                  y=graph.axis.linear(min=0, max=2),
                  key=graph.key.key(pos="br", dist=0.1))
g.plot([graph.data.function("x(y)=y**(2**%i)" % i, title=r"$x = y^{%g}$" % (2**i)) 
        for i in range(2, 0, -1)] +
       [graph.data.function("x(y)=y", title=r"$x = y$")] +
       [graph.data.function("y(x)=x**(2**%i)" % i, title=r"$y = x^{%g}$" % (2**i)) 
        for i in range(1, 3)],
       [graph.style.line([color.palette.Rainbow])])
g.writeEPSfile("change")
g.writePDFfile("change")
