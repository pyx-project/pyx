#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

import math
from pyx import *

def test_bar(c, x, y):
    g = c.insert(graph.graphxy(x, y, height=5, width=5, x=graph.axis.bar(title="Month", painter=graph.axis.painter.bar(nameattrs=[text.halign.right, trafo.rotate(90)]))))
    g.plot(graph.data.file("data/testdata2", xname=1, y=2, text=2), [graph.style.barpos(fromvalue=0), graph.style.bar(), graph.style.text()])

def test_bar2(c, x, y):
    g = c.insert(graph.graphxy(x, y, height=5, width=5, y=graph.axis.bar(title="Month")))
    g.plot(graph.data.file("data/testdata2", x=2, dx="1", yname=1), [graph.style.bar(), graph.style.errorbar()])

def test_bar3(c, x, y):
    g = c.insert(graph.graphxy(x, y, height=5, width=12, x=graph.axis.nestedbar(painter=graph.axis.painter.bar(innerticklength=0.2)), key=graph.key.key()))
    g.plot([graph.data.file("data/testdata2", xname="$1, 0", y=2),
            graph.data.file("data/testdata2", xname="$1, 1", y=3),
            graph.data.file("data/testdata2", xname="$1, 2", y=3, title=None)], [graph.style.bar()])

def test_bar4(c, x, y):
    subbarwithtext = graph.axis.bar(dist=0,
                                    painter=graph.axis.painter.bar(basepathattrs=None),
                                    linkpainter=graph.axis.painter.bar(basepathattrs=None))
    g = c.insert(graph.graphxy(x, y, height=5, width=12,
                               x=graph.axis.nestedbar(defaultsubaxis=graph.axis.bar(subaxes={'A': graph.axis.lin(painter=None, linkpainter=None, parter=None),
                                                                                             'B': graph.axis.bar(painter=graph.axis.painter.bar(basepathattrs=None),
                                                                                                                 linkpainter=graph.axis.painter.bar(basepathattrs=None))},
                                                                                    painter=graph.axis.painter.bar(basepathattrs=None),
                                                                                    linkpainter=graph.axis.painter.bar(basepathattrs=None))),
                               key=graph.key.key()))
    g.plot([graph.data.data(graph.data.points([['x',  1, 12], ['y',  2, 11], ['z',  3, 10]], id=1, y=2, ystack1=3, title="test"), xname="id, 'A'"),
            graph.data.data(graph.data.points([['x',  4,  9], ['y',  5,  8], ['z',  6,  7]], id=1, y=2, ystack1=3, title="test"), xname="id, ('B', 'X')"),
            graph.data.data(graph.data.points([['x',  7,  6], ['y',  8,  5], ['z',  9,  4]], id=1, y=2, ystack1=3, title="test"), xname="id, ('B', 'Y')"),
            graph.data.data(graph.data.points([['x', 10,  3], ['y', 11,  2], ['z', 12,  1]], id=1, y=2, ystack1=3, title="test"), xname="id, ('B', 'Z')")],
           [graph.style.barpos(fromvalue=0), graph.style.bar(), graph.style.stackedbarpos("ystack1", addontop=1), graph.style.bar([color.gradient.ReverseRainbow])])

c = canvas.canvas()
test_bar(c, 0, 0)
test_bar2(c, 7, 0)
test_bar3(c, 0, -7)
test_bar4(c, 0, -14)
c.writeEPSfile("test_bargraph", paperformat=document.paperformat.A4)
c.writePDFfile("test_bargraph", paperformat=document.paperformat.A4)

