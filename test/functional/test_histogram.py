import random
from pyx import *

d1 = graph.data.list([(1.5, 1, 0.3),
                      (3, 0.5, 0.5),
                      (4, 0.5, 0.2),
                      (None, 0.5, 0.8),
                      (6, None, 0.9),
                      (7, 0.5, None),
                      (10, 2.5, 0.8),
                      (13, 0.5, -0.2),
                      (14, 0.5, 0.4)], x=1, dx=2, y=3)
d2 = graph.data.data(d1, y="x", dy="dx", x="y")
d3 = graph.data.list([(1, 0.3),
                      (2, 0.5),
                      (3, -0.2),
                      (4, 0.8),
                      (5, 0.5)], x=1, y=2)
d4 = graph.data.data(d3, y="x", x="y")

c = canvas.canvas()
g1 = c.insert(graph.graphxy(10, 0, width=8))
g1.plot(d1, [graph.style.histogram(steps=1, lineattrs=[color.rgb.red, style.linewidth.Thick])])
g1.plot(d1, [graph.style.histogram(steps=0)])
g2 = c.insert(graph.graphxy(0, 0, width=8))
g2.plot(d2, [graph.style.histogram(steps=1, lineattrs=[color.rgb.red, style.linewidth.Thick])])
g2.plot(d2, [graph.style.histogram(steps=0)])
g3 = c.insert(graph.graphxy(10, 7, width=8))
g3.plot(d3, [graph.style.histogram(steps=1, lineattrs=[color.rgb.red, style.linewidth.Thick], autohistogrampointpos=0)])
g3.plot(d3, [graph.style.histogram(steps=0, autohistogrampointpos=0)])
g4 = c.insert(graph.graphxy(0, 7, width=8))
g4.plot(d4, [graph.style.histogram(steps=1, lineattrs=[color.rgb.red, style.linewidth.Thick], autohistogramaxisindex=1, autohistogrampointpos=1)])
g4.plot(d4, [graph.style.histogram(steps=0, autohistogramaxisindex=1, autohistogrampointpos=1)])
g5 = c.insert(graph.graphxy(10, 14, width=8, x=graph.axis.lin(min=3, max=14), y=graph.axis.lin(min=-0.1, max=0.45)))
g5.plot(d1, [graph.style.histogram(steps=1, lineattrs=[color.rgb.red, style.linewidth.Thick])])
g5.plot(d1, [graph.style.histogram(steps=0)])
g6 = c.insert(graph.graphxy(0, 14, width=8, y=graph.axis.lin(min=3, max=14), x=graph.axis.lin(min=-0.1, max=0.45)))
g6.plot(d2, [graph.style.histogram(steps=1, lineattrs=[color.rgb.red, style.linewidth.Thick])])
g6.plot(d2, [graph.style.histogram(steps=0)])
c.writeEPSfile("test_histogram")
