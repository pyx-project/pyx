from pyx import *

g = graph.graphxy(width=14, height=6, x=graph.axis.bar())
g.plot(graph.data.file("minimal.dat", xname=0, y=2, stack=3),
       [graph.style.bar(),
        graph.style.text("y"),
        graph.style.stackedbarpos("stack"),
        graph.style.bar([color.rgb.green]),
        graph.style.text("stack")])
g.writeEPSfile("stacked")
g.writePDFfile("stacked")
g.writeSVGfile("stacked")
