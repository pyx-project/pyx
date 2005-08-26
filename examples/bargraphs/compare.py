# When plotting several bars with the same style in a bar graph,
# they are plotted side by side. You have to create a nested bar
# axis to make each position in the bar graph to contain another
# bar axis. Additionally you can see, how you can explicitly add
# the parpos style in front of the bar style to set the fromvalue
# parameter, which allows to start bars at a certain value instead
# of starting them at the baseline.

from pyx import *

bap = graph.axis.painter.bar
a = graph.axis.nestedbar(painter=bap(nameattrs=[trafo.rotate(45),
                                                text.halign.right],
                                     innerticklength=0.1))

g = graph.graphxy(width=8, x=a)
g.plot([graph.data.file("bar.dat", xname="$1, 0", y=2),
        graph.data.file("bar.dat", xname="$1, 1", y=3)],
       [graph.style.barpos(fromvalue=0), graph.style.bar()])
g.writeEPSfile("compare")
g.writePDFfile("compare")
