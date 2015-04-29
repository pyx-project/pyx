from pyx import *

g = graph.graphxy(width=8, key=graph.key.key())

As = [0.3, 0.6, 0.9]

d = [graph.data.join([graph.data.function("y_a(x_a)=A*sin(2*pi*x_a)", context=dict(A=A)),
                      graph.data.file("join.dat", x_b=1, y_b=i+2)],
                     title=r"$A=%g$" % A)
     for i, A in enumerate(As)]

attrs = [color.gradient.RedBlue]

g.plot(d,
       [graph.style.pos(usenames=dict(x="x_a", y="y_a")),
        graph.style.line(attrs),
        graph.style.pos(usenames=dict(x="x_b", y="y_b")),
        graph.style.symbol(graph.style.symbol.changesquare, symbolattrs=attrs, size=0.1)])

g.writeEPSfile()
g.writePDFfile()
g.writeSVGfile()
