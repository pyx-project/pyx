# A multisubaxis allows for subtitles at a multibar
# plot. Furthermore it can handle different number of
# subbars per main baraxis.

from pyx import *

a = graph.axis.bar(multisubaxis=graph.axis.bar(dist=0))

g = graph.graphxy(width=8, x=a)
g.plot([graph.data.list([["A", 5], ["B", 6]], xname=1, y=2),
        graph.data.list([["A", 7], ["B", 8], ["C", 9]], xname=1, y=2)],
       [graph.style.barpos(fromvalue=0), graph.style.bar()])
g.writeEPSfile("multisubaxis")
