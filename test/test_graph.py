#!/usr/bin/env python
import sys, math
sys.path[:0] = [".."]

from pyx import *
from pyx import mathtree


def test_multiaxes_data(c, t, x, y):
    g = c.insert(graph.graphxy(t, x, y, height=7,
                               x=graph.logaxis(title="$W$", part=graph.autologpart(mix=graph.manualpart(ticks="2.2360679775", texts="$\sqrt{5}$").part())),
                               y=graph.logaxis(title=r"$PPP_1$",
                                               painter=graph.axispainter(titleattrs=tex.direction.horizontal)),
                               y2=graph.logaxis(title="$P_2$"),
                               y3=graph.logaxis(title="$PPP_3$",
                                                painter=graph.axispainter(titleattrs=tex.direction(45))),
                               y5=graph.logaxis(title="$P_5$")))
    df = data.datafile("testdata")
    g.plot((graph.data(df, x=1, y="sqrt(sqrt($3))"),
            graph.data(df, x=1, y2=4),
            graph.data(df, x=1, y3=5),
            graph.data(df, x=1, y5=6)),
           style=graph.symbol(symbolattrs=(graph.changecolor.RedGreen(), graph.changestrokedfilled()), symbol=graph.changesymbol.squaretwice()))
    g.finish()

def test_piaxis_function(c, t, x, y):
    g = c.insert(graph.graphxy(t, x, y, height=5,
                               x=graph.linaxis(min=0, max=2*math.pi, divisor=math.pi, suffix=r"\pi")))
    g.plot([graph.function("y=sin(x-i*pi/10)", extern={"i": i}) for i in range(20)],
           style=graph.line(lineattrs=(graph.changecolor.Hue(), graph.changelinestyle())))
    g.finish()

def test_textaxis_errorbars(c, t, x, y):
    df = data.datafile("testdata2")
    g = c.insert(graph.graphxy(t, x, y, height=5,
                               x=graph.linaxis(min=0.5, max=12.5, title="Month",
                                               part=graph.linpart("1", texts=df.getcolumn("month"), extendtick=None),
                                               painter=graph.axispainter(labeldist=0.1, titledist=0, labelattrs=(tex.direction(45),tex.halign.right, tex.fontsize.scriptsize))),
                               y=graph.linaxis(min=-10, max=30, title="Temperature [$^\circ$C]"),
                               x2=graph.linaxis(), y2=graph.linaxis()))
    g.plot(graph.data(df, x=0, ymin="min", ymax="max"))
    g.plot(graph.paramfunction("k", 0, 2*math.pi, "x2, y2, dx2, dy2 = 0.8*sin(k), 0.8*cos(3*k), 0.05, 0.05"), style = graph.symbol(symbol=graph.symbol.triangle))
    g.finish()

def test_ownmark(c, t, x, y):
    div = lambda x, y: int(x)/int(y)
    mod = lambda x, y: int(x)%int(y)
    g = c.insert(graph.graphxy(t, x, y, height=5, x=graph.linaxis(min=0, max=10), y=graph.linaxis(min=0, max=10)))
    g.plot(graph.paramfunction("k", 0, 120, "x, y, size, angle = mod(k, 11), div(k, 11), (1+sin(k*pi/120))/2, 3*k", points=121, extern=locals()), style = graph.arrow())
    line1 = g.plot(graph.function("y=10/x"))
    line2 = g.plot(graph.function("y=12*x^-1.6"))
    line3 = g.plot(graph.function("y=7/x"))
    line4 = g.plot(graph.function("y=25*x^-1.6"))
    g.finish()

    p1=line1.path
    p2=line2.path.reversed()
    p3=line3.path.reversed()
    p4=line4.path
    (seg1a,), (seg2a,) = p1.intersect(p2)
    (seg2b,), (seg3b,) = p2.intersect(p3)
    (seg3c,), (seg4c,) = p3.intersect(p4)
    (seg4d,), (seg1d,) = p4.intersect(p1)
    area = p1.split(seg1a, seg1d)[1] << p4.split(seg4d, seg4c)[1] << p3.split(seg3c, seg3b)[1] << p2.split(seg2b, seg2a)[1]
    area.append(path.closepath())
    g.stroke(area, canvas.linewidth.THick, canvas.filled(color.gray(0.5)))

def test_allerrorbars(c, t, x, y):
    df = data.datafile("testdata3")
    g = c.insert(graph.graphxy(t, x, y, height=5, width=4))
    g.plot(graph.data(df, x="x", y="y", xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", text="text"), graph.text())
    g.finish()

def test_3d(c, t, x, y):

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

    g = c.insert(graph.graphxyz(t, x, y, height=5, width=5, depth=5,
                                x=graph.linaxis(min=0, max=10, painter=graph.axispainter(baselineattrs=color.rgb.red)),
                                y=graph.linaxis(min=0, max=10, painter=graph.axispainter(baselineattrs=color.rgb.green)),
                                z=graph.linaxis(min=0, max=10, painter=graph.axispainter(baselineattrs=color.rgb.blue))))
    g.plot(graph.paramfunction("k", 0, 120, "x, y, z = mod(k, 11), div(k, 11), exp(-0.1*(mod(k, 11)-5)*(mod(k, 11)-5)-0.1*(div(k, 11)-5)*(div(k, 11)-5))", points=121, parser=mathtree.parser(MathTreeFuncs=MyFuncs)), style = graph.surface())
    g.finish()

def test_split(c, t, x, y):
    #g = c.insert(graph.graphxy(t, x, y, height=5, y2=None,
    #                           y=graph.splitaxis((graph.linaxis(max=0.002), graph.splitaxis((graph.linaxis(min=0.01, max=0.015), graph.linaxis(min=0.019)))))))
    #df = data.datafile("testdata2")
    #g.plot(graph.data(df, x=0, y=2), graph.bar())
    #g.finish()
    g = c.insert(graph.graphxy(t, x, y, height=5, width=5, x2=None,
                               x=graph.splitaxis([graph.linaxis(min=-0.2, max=1.2) for x in range(12)], None)))
    df = data.datafile("testdata2")
    g.plot(graph.data(df, x=0, y=2), graph.bar())
    g.finish()

c = canvas.canvas()
t = c.insert(tex.tex())
test_multiaxes_data(c, t, 0, 21)
test_piaxis_function(c, t, 0, 14)
test_textaxis_errorbars(c, t, 0, 7)
test_ownmark(c, t, 0, 0)
test_allerrorbars(c, t, -7, 0)
#test_3d(c, t, -7, 7)
test_split(c, t, -7, 7)

c.writetofile("test_graph", paperformat="a4")

