#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

import math
from pyx import *
from pyx import mathtree

text.set(mode="latex")

def test_multiaxes_data(c, x, y):
    g = c.insert(graph.type.graphxy(x, y, height=5, key=graph.key.key(pos="tl"),
                               x=graph.axis.logaxis(title="$W$", manualticks=[graph.parter.tick(math.sqrt(8)*100, label="?"), graph.parter.tick(math.sqrt(8), label="$\sqrt{8}$")]),
                               y=graph.axis.logaxis(title=r"$PPP_1$",
                                               painter=graph.painter.axispainter(titledirection=None)),
                               y2=graph.axis.logaxis(title="$P_2$"),
                               y3=graph.axis.logaxis(title="$PPP_3$",
                                                painter=graph.painter.axispainter(titledirection=graph.painter.rotatetext(45), gridattrs=[color.palette.RedGreen]),
                                                texter=graph.texter.decimaltexter(equalprecision=1)),
                               y5=graph.axis.logaxis(title="$P_5$")))
    df = data.datafile("data/testdata")
    g.plot((graph.data.data(df, x=1, y="sqrt(sqrt($3))"),
            graph.data.data(df, x=1, y2=4),
            graph.data.data(df, x=1, y3=5),
            graph.data.data(df, x=1, y5=6)),
           style=graph.style.symbol(symbolattrs=[deco.stroked.clear, color.palette.RedGreen, graph.style.symbol.changestrokedfilled], symbol=graph.style.symbol.changesquaretwice))
    g.finish()

def test_piaxis_function(c, x, y):
    xaxis=graph.axis.linaxis(min=0, max=2*math.pi, divisor=math.pi, texter=graph.texter.rationaltexter(suffix=r"\pi"))
    g = c.insert(graph.type.graphxy(x, y, height=5, x=xaxis))
    # g = c.insert(graph.type.graphxy(x, y, height=5, x=xaxis, x2=xaxis)) # TODO
    g.plot([graph.data.function("y=sin(x-i*pi/10)", context={"i": i}) for i in range(20)],
           style=graph.style.line(lineattrs=[color.palette.Hue]))
    g.finish()

def test_textaxis_errorbars(c, x, y):
    df = data.datafile("data/testdata2")
    g = c.insert(graph.type.graphxy(x, y, height=5,
                               x=graph.axis.linaxis(min=0.5, max=12.5, title="Month",
                                               parter=graph.parter.linparter("1", labels=df.getcolumn("month"), extendtick=None),
                                               painter=graph.painter.axispainter(labeldist=0.1, titledist=0, labelattrs=(trafo.rotate(45),text.halign.right, text.size.scriptsize))),
                               y=graph.axis.linaxis(min=-10, max=30, title="Temperature [$^\circ$C]"),
                               x2=graph.axis.linaxis(), y2=graph.axis.linaxis()))
    g.plot(graph.data.data(df, x=0, ymin="min", ymax="max"))
    g.plot(graph.data.paramfunction("k", 0, 2*math.pi, "x2, y2, dx2, dy2 = 0.8*sin(k), 0.8*cos(3*k), 0.05, 0.05"), style = graph.style.symbol(symbol=graph.style.symbol.triangle))
    g.finish()

def test_ownmark(c, x, y):
    div = lambda x, y: int(x)/int(y)
    mod = lambda x, y: int(x)%int(y)
    g = c.insert(graph.type.graphxy(x, y, height=5, x=graph.axis.linaxis(min=0, max=10), y=graph.axis.linaxis(min=0, max=10)))
    g.plot(graph.data.paramfunction("k", 0, 120, "x, y, size, angle = mod(k, 11), div(k, 11), (1+sin(k*pi/120))/2, 3*k", points=121, context=locals()), style = graph.style.arrow())
    line1 = g.plot(graph.data.function("y=10/x"))
    line2 = g.plot(graph.data.function("y=12*x^-1.6"))
    line3 = g.plot(graph.data.function("y=7/x"))
    line4 = g.plot(graph.data.function("y=25*x^-1.6"))
    g.plot(graph.data.data(data.data([[-1, 1], [5, 2], [11, 5], [5, 11], [4, -1]]), x=0, y=1), graph.style.line(lineattrs=[color.rgb.red]))
    g.finish()

    p1=line1.path
    p2=line2.path.reversed()
    p3=line3.path.reversed()
    p4=line4.path
    (seg1a,), (seg2a,) = p1.intersect(p2)
    (seg2b,), (seg3b,) = p2.intersect(p3)
    (seg3c,), (seg4c,) = p3.intersect(p4)
    (seg4d,), (seg1d,) = p4.intersect(p1)
    area = p1.split([seg1a, seg1d])[1] << p4.split([seg4d, seg4c])[1] << p3.split([seg3c, seg3b])[1] << p2.split([seg2b, seg2a])[1]
    area.append(path.closepath())
    g.stroke(area, [style.linewidth.THick, deco.filled([color.gray(0.5)])])

def test_allerrorbars(c, x, y):
    df = data.datafile("data/testdata3")
    g = c.insert(graph.type.graphxy(x, y, height=5, width=5))
    g.plot(graph.data.data(df, x="x", y="y", xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", text="text"), graph.style.text())
    g.finish()

def test_split(c, x, y):
    g = c.insert(graph.type.graphxy(x, y, height=5, width=5,
                               x=graph.axis.logaxis(),
                               y=graph.axis.splitaxis((graph.axis.linaxis(min=0, max=0.005, painter=graph.painter.axispainter()), graph.axis.linaxis(min=0.01, max=0.015), graph.axis.linaxis(min=0.02, max=0.025)), title="axis title", splitlist=(None, None), relsizesplitdist=0.005)))
    df = data.datafile("data/testdata")
    g.plot(graph.data.data(df, x=1, y=3))
    g.finish()

def test_split2(c, x, y):
    g = c.insert(graph.type.graphxy(x, y, height=5, width=5,
                               x=graph.axis.logaxis(),
                               y=graph.axis.splitaxis((graph.axis.linaxis(max=0.002), graph.axis.linaxis(min=0.01, max=0.015), graph.axis.linaxis(min=0.017)), splitlist=(0.15, 0.75))))
    df = data.datafile("data/testdata")
    g.plot(graph.data.data(df, x=1, y=3))
    g.finish()


c = canvas.canvas()
test_multiaxes_data(c, 0, 21)
test_piaxis_function(c, 0, 14)
test_textaxis_errorbars(c, 0, 7)
test_ownmark(c, 0, 0)
test_allerrorbars(c, -7, 0)
test_split(c, -7, 7)
test_split2(c, -7, 14)

c.writeEPSfile("test_graph", paperformat="a4")

