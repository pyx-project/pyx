from pyx import *

g = graph.graphxy(width=8,
                  x=graph.axis.linear(min=0, max=2),
                  y=graph.axis.linear(min=0, max=2),
                  key=graph.key.key(pos="br", dist=0.1))
g.plot([graph.data.function("x(y)=y**4", title=r"$x = y^4$"),
        graph.data.function("x(y)=y**2", title=r"$x = y^2$"),
        graph.data.function("x(y)=y", title=r"$x = y$"),
        graph.data.function("y(x)=x**2", title=r"$y = x^2$"),
        graph.data.function("y(x)=x**4", title=r"$y = x^4$")],
       [graph.style.line([color.gradient.Rainbow])])
g.writeEPSfile("change")
g.writePDFfile("change")
g.writeSVGfile("change")
