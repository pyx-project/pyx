#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

import math
from pyx import *
from pyx import mathtree, attr

text.set(mode="latex")

df = data.datafile("data/testdata2")

def test_bar(c, x, y):
    g = c.insert(graph.graphxy(x, y, height=5, width=5, x=graph.baraxis(title="Month", painter=graph.baraxispainter(nameattrs=[text.halign.right, trafo.rotate(90)]))))
    g.plot(graph.data(df, xname=1, y=2), graph.bar(fromvalue=0))

def test_bar2(c, x, y):
    g = c.insert(graph.graphxy(x, y, height=5, width=5, y=graph.baraxis(title="Month")))
    g.plot(graph.data(df, x=2, yname=1), graph.bar())

def test_bar3(c, x, y):
    g = c.insert(graph.graphxy(x, y, height=5, width=12, x=graph.baraxis(multisubaxis=graph.baraxis(dist=0), painter=graph.baraxispainter(innerticklength=0.2))))
    g.plot([graph.data(df, xname=1, y=2), graph.data(df, xname=1, y=3), graph.data(df, xname=1, y=3)], graph.bar())

def test_bar4(c, x, y):
    g = c.insert(graph.graphxy(x, y, height=5, width=12, x=graph.baraxis(graph.baraxis(dist=0)), key=graph.key()))
    g.plot([graph.data(df, xname=0, y=2, ystack1=3), graph.data(df, xname=0, y=2), graph.data(df, xname=0, y=3)], graph.bar(barattrs=[attr.changelist([attr.changelist([color.rgb.red, color.rgb.green]), color.rgb.blue, color.cmyk.Cyan])]))

c = canvas.canvas()
test_bar(c, 0, 0)
test_bar2(c, 7, 0)
test_bar3(c, 0, -7)
test_bar4(c, 0, -14)
c.writetofile("test_bargraph", paperformat="a4")

