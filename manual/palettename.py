#!/usr/bin/env python
import sys, imp, re
sys.path[:0] = [".."]
import pyx
from pyx import *

text.set(mode="latex")
text.preamble(r"\renewcommand{\familydefault}{\ttdefault}")

c = canvas.canvas()

# data to be plotted
pf = graph.paramfunction("k", 0, 1, "color, xmin, xmax, ymin, ymax= k, k, 1, 0, 1")

# positioning is quite ugly ... but it works at the moment
y = 0
dy = -0.65

# we could use palette.__dict__ to get the instances, but we
# would loose the ordering ... instead we just parse the file:
p = re.compile("(?P<id>palette\\.(?P<name>[a-z]+)) += palette\\(.*\\)\n", re.IGNORECASE)
lines = imp.find_module("color", pyx.__path__)[0].readlines()
skiplevel = None
for line in lines: # we yet don't use a file iterator
    m = p.match(line)
    if m:
        xaxis = graph.linaxis(part=graph.linpart(tickdist=("0.5","0.1"), labeldist="1"),
                              painter=graph.axispainter(innerticklengths=None, labelattrs=None))
        g = c.insert(graph.graphxy(ypos=y, width=10, height=0.5, x=xaxis,
                                   x2=graph.linkaxis(xaxis,
                                                     painter=graph.linkaxispainter(innerticklengths=None,
                                                                                   outerticklengths=graph.axispainter.defaultticklengths)),
                                   y=graph.linaxis(part=None)))
        g.plot(pf, graph.rect(pyx.color.palette.__dict__[m.group("name")]))
        g.dodata()
        g.finish()
        c.text(10.2, y + 0.15, m.group("id"), text.size.footnotesize)
        y += dy
        skiplevel = 0


c.writetofile("palettename", paperformat="a4")
