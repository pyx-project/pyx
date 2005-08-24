# You can build a nested bar axis yourself. Compared to the
# default nestedbar axis, we keep the original bar axis painter
# for the subaxes to include their names. Note also, that each
# of the subaxes can have different number of bars.

from pyx import *

mynestedbaraxis = graph.axis.bar(defaultsubaxis=graph.axis.bar(dist=0))

g = graph.graphxy(width=8, x=mynestedbaraxis)
g.plot([graph.data.list([[("A", "x"), 5], [("B", "x"), 6]], xname=1, y=2),
        graph.data.list([[("A", "y"), 7], [("B", "y"), 8], [("C", "y"), 9]], xname=1, y=2)],
       [graph.style.barpos(fromvalue=0), graph.style.bar()])
g.writeEPSfile("multisubaxis")
g.writePDFfile("multisubaxis")
