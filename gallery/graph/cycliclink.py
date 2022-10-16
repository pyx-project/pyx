from pyx import *

c = canvas.canvas()

g1 = c.insert(graph.graphxy(width=8,
                            x=graph.axis.linear(min=0, max=1),
                            x2=graph.axis.linkedaxis()))

g2 = c.insert(graph.graphxy(width=8, ypos=g1.height+0.5,
                            x=graph.axis.linkedaxis(),
                            x2=graph.axis.log(min=1, max=1000)))

g1.axes["x2"].setlinkedaxis(g2.axes["x2"])
g2.axes["x"].setlinkedaxis(g1.axes["x"])

g1.plot(graph.data.function("y(x)=2*exp(-30*x)-exp(-3*x)"))
g2.plot(graph.data.function("y(x)=cos(20*x)*exp(-2*x)"))

c.writeEPSfile()
c.writePDFfile()
c.writeSVGfile()
