#!/usr/bin/env python
import sys, math
sys.path.append("..")
from pyx import *
from pyx import mathtree


def test_multiaxes_data(c, t, x, y):
    g = c.insert(graph.graphxy(t, x, y, height=5,
                               x=graph.logaxis(title="$W$"),
                               y=graph.logaxis(title=r"$PPP_1$",
                                               painter=graph.axispainter(titlestyles=tex.direction.horizontal)),
                               y2=graph.logaxis(title="$P_2$"),
                               y3=graph.logaxis(title="$PPP_3$",
                                                painter=graph.axispainter(titlestyles=tex.direction(45))),
                               y5=graph.logaxis(title="$P_5$")))
    df = datafile.datafile("testdata")
    colors = graph.colorchange(color.rgb.red, color.rgb.green)
    g.plot(graph.data(df, x=1, y=3), style=graph.mark.square(colorchange=colors))
    g.plot(graph.data(df, x=1, y2=4))
    g.plot(graph.data(df, x=1, y3=5))
    g.plot(graph.data(df, x=1, y5=6))
    g.drawall()

def test_piaxis_function(c, t, x, y):
    g = c.insert(graph.graphxy(t, x, y, height=5,
                               x=graph.linaxis(min=0, max=2*math.pi, factor=math.pi, suffix=r"\pi")))
    colors = graph.colorchange(color.hsb(0, 1, 1), color.hsb(1, 1, 1))
    g.plot(graph.function("y=sin(x)", points=1000), style=graph.line(colorchange=colors))
    for i in range(1, 20):
        g.plot(graph.function("y=sin(x-%i*pi/10)" % i))
    g.drawall()

def test_textaxis_errorbars(c, t, x, y):
    df = datafile.datafile("testdata2")
    g = c.insert(graph.graphxy(t, x, y, height=5,
                               x=graph.linaxis(min=0.5, max=12.5, title="Month",
                                               part=graph.linpart("1", labels=df.getcolumn("month")),
                                               painter=graph.axispainter(labelstyles=(tex.direction(30),tex.halign.right, tex.fontsize.scriptsize))),
                               y=graph.linaxis(min=-10, max=30, title="Temperature [$^\circ$C]"),
                               x2=graph.linaxis(), y2=graph.linaxis()))
    df.addcolumn("av=(min+max)/2")
    g.plot(graph.data(df, x=0, y="av", dymin="min", dymax="max"))
    g.plot(graph.paramfunction("k", 0, 2*math.pi, "x2, y2, dx, dy = 0.9*sin(k), 0.9*cos(3*k), 0.05, 0.05"), style = graph.mark.ftriangle())
    g.drawall()

def test_ownmark(c, t, x, y):

    class arrowmark(graph.plotstyle):

        def __init__(self, size = "0.2 cm"):
            self.size_str = size

        def setcolumns(self, graph, columns):
            self.xindex = self.yindex = self.angleindex = None
            for key, index in columns.items():
                if graph.XPattern.match(key) and self.xindex is None:
                    self.xkey = key
                    self.xindex = index
                elif graph.YPattern.match(key) and self.yindex is None:
                    self.ykey = key
                    self.yindex = index
                elif key == "angle" and self.angleindex is None:
                    self.angleindex = index
                else:
                    raise ValueError
            if None in (self.xindex, self.yindex, self.angleindex): raise ValueError

        def getranges(self, points):
            return {self.xkey: (min([point[self.xindex] for point in points]),
                                max([point[self.xindex] for point in points])),
                    self.ykey: (min([point[self.yindex] for point in points]),
                                max([point[self.yindex] for point in points]))}

        def drawpointlist(self, graph, points):
            size = unit.topt(unit.length(self.size_str, default_type="v"))
            xaxis = graph.axes[self.xkey]
            yaxis = graph.axes[self.ykey]
            for point in points:
                x = graph.xconvert(xaxis.convert(point[self.xindex]))
                y = graph.yconvert(yaxis.convert(point[self.yindex]))
                angle = point[self.angleindex]
                graph.stroke(path._line(x - 0.5 * size * math.cos(angle),
                                        y - 0.5 * size * math.sin(angle),
                                        x + 0.5 * size * math.cos(angle),
                                        y + 0.5 * size * math.sin(angle)), canvas.earrow.normal)

    class Div(mathtree.MathTreeFunc2):
        def __init__(self, *args):
            mathtree.MathTreeFunc2.__init__(self, "div", *args)
        def Calc(self, VarDict):
            return divmod(self.ArgV[0].Calc(VarDict), self.ArgV[1].Calc(VarDict))[0]

    class Mod(mathtree.MathTreeFunc2):
        def __init__(self, *args):
            mathtree.MathTreeFunc2.__init__(self, "mod", *args)
        def Calc(self, VarDict):
            return divmod(self.ArgV[0].Calc(VarDict), self.ArgV[1].Calc(VarDict))[1]

    MyFuncs = mathtree.DefaultMathTreeFuncs + (Div, Mod)

    line1 = graph.line(dodrawline = 0)
    line2 = graph.line(dodrawline = 0)
    line3 = graph.line(dodrawline = 0)
    line4 = graph.line(dodrawline = 0)

    g = c.insert(graph.graphxy(t, x, y, height=5))
    g.plot(graph.paramfunction("k", 0, 120, "x, y, angle = mod(k, 11), div(k, 11), 0.05*k", points=121, parser=mathtree.parser(MathTreeFuncs=MyFuncs)), style = arrowmark())
    g.plot(graph.function("y=10/x", xmin = 1, ymax = 10), style = line1)
    g.plot(graph.function("y=12*x^-1.6", xmin = 1, ymax = 10), style = line2)
    g.plot(graph.function("y=7/x", xmin = 1, ymax = 10), style = line3)
    g.plot(graph.function("y=25*x^-1.6", xmin = 1, ymax = 10), style = line4)
    g.drawall()

    g.stroke(line1.path, color.rgb.blue)
    g.stroke(line2.path, color.rgb.red)
    g.stroke(line3.path, color.rgb.green)
    g.stroke(line4.path, color.gray.black)
    p1=line1.path
    p2=line2.path.reversed()
    p3=line3.path.reversed()
    p4=line4.path
    seg1a, seg2a = p1.intersect(p2)[0]
    seg2b, seg3b = p2.intersect(p3)[0]
    seg3c, seg4c = p3.intersect(p4)[0]
    seg4d, seg1d = p4.intersect(p1)[0]
    g.stroke(p1.split(seg1a, seg1d)[1] <<
             p4.split(seg4d, seg4c)[1] <<
             p3.split(seg3c, seg3b)[1] <<
             p2.split(seg2b, seg2a)[1], canvas.linewidth.THick, canvas.filled(color.gray(0.5)))

c = canvas.canvas()
t = c.insert(tex.tex())
test_multiaxes_data(c, t, 0, 21)
test_piaxis_function(c, t, 0, 14)
test_textaxis_errorbars(c, t, 0, 7)
test_ownmark(c, t, 0, 0)

c.writetofile("test_graph", paperformat="a4")

