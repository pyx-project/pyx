#!/usr/bin/env python
import sys, math
sys.path.append("..")
from pyx import *

c = canvas.canvas()
t = c.insert(tex.tex())
g = c.insert(graph.graphxy(t, width=10, x=graph.logaxis(title="$W$"),
                                        y=graph.logaxis(title=r"$PPPPPPPPPPPPPPPPP_1$", painter=graph.axispainter(titlestyles=tex.direction.horizontal)),
                                        y2=graph.logaxis(title="$P_2$"),
                                        y3=graph.logaxis(title="$PPPPPPPPPPPPPPPPP_3$"),
                                        y4=graph.logaxis(title="$P_4$"),
                                        y5=graph.logaxis(title="$P_5$"),
                                        y6=graph.logaxis(title="$P_6$")))
df = datafile.datafile("testdata")
g.plot(graph.data(df, x=1, y=3), style=graph.mark.square(colorchange=graph.colorchange(color.rgb.red, color.rgb.green)))
g.plot(graph.data(df, x=1, y2=4))
g.plot(graph.data(df, x=1, y3=5))
g.plot(graph.data(df, x=1, y4=6))
g.plot(graph.data(df, x=1, y5=7))
g.plot(graph.data(df, x=1, y6=8))
g.drawall()
c.writetofile("test_graph")

# c = canvas.canvas()
# t = c.insert(tex.tex())
# g = c.insert(graph.graphxy(t, width=10,
#                            x=graph.linaxis(min=-2*math.pi,
#                                            max=2*math.pi,
#                                            title="x--Achse",
#                                            factor=math.pi,
#                                            suffix=r"\pi"),
#                            y=graph.linaxis(part=graph.linpart("0.5"), title="y--Achse")))
# g.plot(graph.function("y=sin(x)", points=1000), style = graph.line(colorchange=graph.colorchange(color.rgb.red, color.rgb.green)))
# g.plot(graph.function("y=cos(x)"))
# g.plot(graph.function("y=sin(x+pi)"))
# g.plot(graph.function("y=cos(x+pi)"))
# g.drawall()
# g.drawall()
# c.draw(g.ygridpath(g.axes["y"].convert(0)))
# c.writetofile("test_graph", paperformat="a4")

# from pyx import mathtree
# 
# class MathTreeFunc1Cumulate(mathtree.MathTreeFunc1):
# 
#     def __init__(self, *args):
#         mathtree.MathTreeFunc1.__init__(self, "cumulate", *args)
#         self.sum = 0
# 
#     def Calc(self, VarDict):
#         self.sum += self.ArgV[0].Calc(VarDict)
#         return self.sum
# 
# MyMathTreeFuncs = mathtree.DefaultMathTreeFuncs + (MathTreeFunc1Cumulate,)
# 
# c = canvas.canvas()
# t = c.insert(tex.tex())
# df = datafile.datafile("testdata2", parser=mathtree.parser(MathTreeFuncs=MyMathTreeFuncs))
# g = c.insert(graph.graphxy(t, width=10,
#                            x=graph.linaxis(min=0.5, max=12.5, title="Month",
#                                            part=graph.linpart("1", labels=df.getcolumn("month")),
#                                            painter=graph.axispainter(labelstyles=(tex.direction(45),tex.halign.right))),
#                            y=graph.linaxis(min=-10, max=30, title="Temperature [$^\circ$C]")))
# df.addcolumn("av=(min+max)/2")
# df.addcolumn("sum=cumulate(av)")
# g.plot(graph.data(df, x=0, y="av", dymin="min", dymax="max"))
# g.plot(graph.data(df, x=0, y="sum"))
# g.drawall()
# c.draw(g.ygridpath(g.axes["y"].convert(0)))
# c.writetofile("test_graph", paperformat="a4")

# c = canvas.canvas()
# t = c.insert(tex.tex())
# g = c.insert(graph.graphxy(t, width=10))
# g.plot(graph.paramfunction("k", 0, 2*math.pi, "x, y, dx, dy = sin(k), cos(3*k), 0.05, 0.05"), style = graph.mark.ftriangle())
# g.drawall()
# c.draw(g.xgridpath(g.axes["x"].convert(0)))
# c.draw(g.ygridpath(g.axes["y"].convert(0)))
# c.writetofile("test_graph", paperformat="a4")

