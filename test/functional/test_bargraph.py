#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

import math
from pyx import *
from pyx import mathtree, attr

def test_bar(c, x, y):
    g = c.insert(graph.graphxy(x, y, height=5, width=5, x=graph.axis.bar(title="Month", painter=graph.axis.painter.bar(nameattrs=[text.halign.right, trafo.rotate(90)]))))
    g.plot(graph.data.file("data/testdata2", xname=1, y=2, text=2), [graph.style.barpos(fromvalue=0), graph.style.bar(), graph.style.text()])

def test_bar2(c, x, y):
    g = c.insert(graph.graphxy(x, y, height=5, width=5, y=graph.axis.bar(title="Month")))
    g.plot(graph.data.file("data/testdata2", x=2, dx="1", yname=1), [graph.style.bar(), graph.style.errorbar()])

def test_bar3(c, x, y):
    g = c.insert(graph.graphxy(x, y, height=5, width=12, x=graph.axis.bar(multisubaxis=graph.axis.bar(dist=0), painter=graph.axis.painter.bar(innerticklength=0.2)), key=graph.key.key()))
    g.plot([graph.data.file("data/testdata2", xname=1, y=2),
            graph.data.file("data/testdata2", xname=1, y=3),
            graph.data.file("data/testdata2", xname=1, y=3, title=None)], [graph.style.bar()])

def test_bar4(c, x, y):
    g = c.insert(graph.graphxy(x, y, height=5, width=12, x=graph.axis.bar(graph.axis.bar(dist=0)), key=graph.key.key()))
    g.plot([graph.data.file("data/testdata2", xname=0, y=2, ystack1=3, title="test"),
            graph.data.file("data/testdata2", xname=0, y="$2-1", ystack1=3)],
           [graph.style.bar(), graph.style.stackedbarpos("ystack1"), graph.style.bar([color.palette.ReverseRainbow])])

c = canvas.canvas()
#test_bar(c, 0, 0)
#test_bar2(c, 7, 0)
#test_bar3(c, 0, -7)
test_bar4(c, 0, -14)
c.writeEPSfile("test_bargraph", paperformat="a4")

