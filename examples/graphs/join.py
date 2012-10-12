from pyx import *

g = graph.graphxy(width=8, key=graph.key.key())

As = [0.3, 0.6, 0.9]

d = [graph.data.join([graph.data.function("y_anal(x_anal)=A*sin(2*pi*x_anal)", context=dict(A=A)),
                      graph.data.file("join.dat", x_sim=1, y_sim=i+2)],
                     title=r"$A=%g$" % A)
     for i, A in enumerate(As)]

attrs = [color.gradient.RedBlue]

g.plot(d,
       [graph.style.pos(usenames=dict(x="x_anal", y="y_anal")),
        graph.style.line(attrs),
        graph.style.pos(usenames=dict(x="x_sim", y="y_sim")),
        graph.style.symbol(graph.style.symbol.changesquare, symbolattrs=attrs, size=0.1)])

g.writeEPSfile()
g.writePDFfile()
