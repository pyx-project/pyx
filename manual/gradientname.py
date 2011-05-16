#!/usr/bin/env python
import sys, imp, re
sys.path[:0] = [".."]
import pyx
from pyx import *

text.set(mode="latex")
text.preamble(r"\renewcommand{\familydefault}{\ttdefault}")

c = canvas.canvas()

# data to be plotted
pf = graph.data.paramfunction("k", 0, 1, "color, xmin, xmax, ymin, ymax= k, k, 1, 0, 1")

# positioning is quite ugly ... but it works at the moment
y = 0
dy = -0.65

# we could use gradient.__dict__ to get the instances, but we
# would loose the ordering ... instead we just parse the file:

# see comment in colorname.py

p = re.compile("(?P<id>gradient\\.(?P<name>[a-z]+)) += [a-z]+gradient\\(.*\\)\n", re.IGNORECASE)
lines = imp.find_module("color", pyx.__path__)[0].readlines()
firstgraph = None
for line in lines: # we yet don't use a file iterator
    m = p.match(line)
    if m:
        if firstgraph is None:
            xaxis = graph.axis.lin(
                parter=graph.axis.parter.lin(tickdists=["0.5","0.1"], labeldists=["1"]),
                painter=graph.axis.painter.regular(
                    innerticklength=None,
                    outerticklength=graph.axis.painter.ticklength.normal),
                linkpainter=graph.axis.painter.regular(innerticklength=None, labelattrs=None))
            firstgraph = g = graph.graphxy(ypos=y, width=10, height=0.5, x2=xaxis, y=graph.axis.lin(parter=None))
        else:
            g = graph.graphxy(ypos=y, width=10, height=0.5, x2=graph.axis.linkedaxis(firstgraph.axes["x2"]), y=graph.axis.lin(parter=None))
        g.plot(pf, [graph.style.rect(getattr(pyx.color.gradient, m.group("name")))])
        g.doplot()
        g.finish()
        c.insert(g)
        c.text(10.2, y + 0.15, m.group("id"), [text.size.footnotesize])
        y += dy


c.writeEPSfile("gradientname")
c.writePDFfile("gradientname")
