# When plotting several bars with the same style in a bar graph,
# they are plotted side by side. You have to create a nested bar
# axis to make each position in the bar graph to contain another
# bar axis.

from pyx import *

bap = graph.axis.painter.bar
a = graph.axis.nestedbar(painter=bap(nameattrs=[trafo.rotate(45),
                                          text.halign.right],
                                     innerticklength=0.2))

g = graph.graphxy(width=8, x=a)
g.plot([graph.data.file("bar.dat", xname=1, y=2),
        graph.data.file("bar.dat", xname=1, y=3)],
       [graph.style.bar()])
g.writeEPSfile("compare")
