#!/usr/bin/env python
import sys
sys.path.append("..")
from pyx import *

# c = canvas.canvas()
# t = tex.tex()
# g = c.insert(graph.graphxy(t, width=10, x=graph.logaxis(title="$W$"),
#                                         y=graph.logaxis(title=r"$PPPPPPPPPPPPPPPPP_1$", titlestyles=(tex.direction.vertical,)),
#                                         y2=graph.logaxis(title="$P_2$"),
#                                         y3=graph.logaxis(title="$PPPPPPPPPPPPPPPPP_3$"),
#                                         y4=graph.logaxis(title="$P_4$"),
#                                         y5=graph.logaxis(title="$P_5$"),
#                                         y6=graph.logaxis(title="$P_6$")))
# df = graph.datafile("testdata")
# g.plot(graph.data(df, x=1, y=3))
# g.plot(graph.data(df, x=1, y2=4))
# g.plot(graph.data(df, x=1, y3=5))
# g.plot(graph.data(df, x=1, y4=6))
# g.plot(graph.data(df, x=1, y5=7))
# g.plot(graph.data(df, x=1, y6=8))
# c.insert(t)
# c.writetofile("test_graph")

c = canvas.canvas()
t = tex.tex()
g = c.insert(graph.graphxy(t, width=10, 
                           x=graph.logaxis(title="x-Achse"),
                           y=graph.logaxis(title="y-Achse",
                                           part=graph.logpart(tickshiftfracslist=(graph.autologpart.shiftfracs1, graph.autologpart.shiftfracs1to9),
                                                              labeltext=("Januar", "Februar", r"M\"arz", "April")),
                                           painter=graph.axispainter(labelstyles=(tex.direction(50),tex.halign.right))),
                           y2=graph.linaxis(title="y2-Achse", factor = 0.01, suffix = "\,\pi")))
df = graph.datafile("testdata")
g.plot(graph.data(df, x=1, y=3))
g.plot(graph.data(df, x=1, y2=4))
c.insert(t)
c.writetofile("test_graph")
