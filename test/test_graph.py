#!/usr/bin/env python
import sys, math
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

# c = canvas.canvas()
# t = tex.tex()
# g = c.insert(graph.graphxy(t, width=10, 
#                            x=graph.logaxis(title="x-Achse"),
#                            y=graph.logaxis(title="y-Achse",
#                                            part=graph.logpart(tickshiftfracslist=(graph.autologpart.shiftfracs1, graph.autologpart.shiftfracs1to9),
#                                                               labels=("Januar", "Februar", r"M\"arz", "April")),
#                                            painter=graph.axispainter(labelstyles=(tex.direction(50),tex.halign.right))),
#                            y2=graph.logaxis(title="y2-Achse")))
# df = graph.datafile("testdata")
# #g.plot(graph.data(df, x=1, y=3), style = graph.markcircle())
# #g.plot(graph.data(df, x=1, y=3, dy=8), style = graph.markftriangle(size="0.2 cm"))
# g.plot(graph.data(df, x=1, y=3), style = graph.line())
# c.insert(t)
# c.writetofile("test_graph")

# c = canvas.canvas()
# t = c.insert(tex.tex())
# g = c.insert(graph.graphxy(t, width=10,
#                            x=graph.linaxis(min=0,
#                                            max=2*math.pi,
#                                            title="x--Achse",
#                                            factor=math.pi,
#                                            suffix=r"\pi"),
#                            y=graph.linaxis(title="y--Achse")))
# g.plot(graph.function("y=sin(x)"))
# g.plot(graph.function("y=cos(x)"))
# g.drawall()
# c.draw(g.ygridpath(g.axes["y"].convert(0)))
# c.writetofile("test_graph", paperformat="a4")

c = canvas.canvas()
t = c.insert(tex.tex())
df = datafile.datafile("testdata2")
g = c.insert(graph.graphxy(t, width=10,
                           x=graph.linaxis(min=0.5, max=12.5, title="Month",
                                           part=graph.linpart((graph.frac(1, 1),), labels=df.getcolumn("month")),
                                           painter=graph.axispainter(labelstyles=(tex.direction(45),tex.halign.right))),
                           y=graph.linaxis(min=-10, max=30, title="Temperature [$^\circ$C]")))
df.addcolumn("av=(min+max)/2")
g.plot(graph.data(df, x=0, y="av", dymin="min", dymax="max"))
g.drawall()
c.draw(g.ygridpath(g.axes["y"].convert(0)))
c.writetofile("test_graph", paperformat="a4")

# c = canvas.canvas()
# t = c.insert(tex.tex())
# g = c.insert(graph.graphxy(t, width=10))
# g.plot(graph.paramfunction("k", 0, 2*math.pi, x="sin(k)", y="cos(3*k)"))
# g.drawall()
# c.draw(g.xgridpath(g.axes["x"].convert(0)))
# c.draw(g.ygridpath(g.axes["y"].convert(0)))
# c.writetofile("test_graph", paperformat="a4")

