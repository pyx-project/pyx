# For a minimal bar plot you have set an bar axis
# in the graph constructor and provide Xname column
# data (X stands for the bar axis to be used).
# Furthermore you need to specify the graph style,
# since the default graph styles symbol and function
# (depending on the data type) are not appropriate
# for this case.

from pyx import *

g = graph.graphxy(width=8, x=graph.axis.bar())
g.plot(graph.data.file("bar.dat", xname=0, y=2), [graph.style.bar()])
g.writeEPSfile("minimal")
