import sys, re
sys.path[:0] = [".."]
from pyx import *

text.set(text.LatexRunner)
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

firstgraph = None
p = re.compile("(?P<id>gradient\\.(?P<name>[a-z]+)) += [a-z]*gradient_[a-z]+\\(", re.IGNORECASE)
with open(color.__file__) as f:
    for line in f:
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
            g.plot(pf, [graph.style.rect(gradient=getattr(color.gradient, m.group("name")), keygraph=None)])
            g.doplot()
            g.finish()
            c.insert(g)
            c.text(10.2, y + 0.15, m.group("id"), [text.size.footnotesize])
            y += dy


c.writePDFfile()
