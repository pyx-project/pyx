import random
import sys; sys.path[:0] = ["../.."]
from pyx import *

d1 = graph.data.points([(1.5, 1, 0.3),
                      (3, 0.5, 0.5),
                      (4, 0.5, 0.2),
                      (None, 0.5, 0.8),
                      (6, None, 0.9),
                      (7, 0.5, None),
                      (10, 2.5, 0.8),
                      (13, 0.5, -0.2),
                      (14, 0.5, 0.4)], x=1, dx=2, y=3)
d2 = graph.data.data(d1, y="x", dy="dx", x="y", copy=0)
d3 = graph.data.points([(1, 0.3),
                      (2, 0.5),
                      (3, -0.2),
                      (4, 0.8),
                      (5, 0.5)], x=1, y=2)
d4 = graph.data.data(d3, y="x", x="y")

c = canvas.canvas()

def draw(d, xpos, ypos, autohistogramaxisindex=0, autohistogrampointpos=0, fillablesteps=0, **kwargs):
    g = c.insert(graph.graphxy(xpos, ypos, width=8, **kwargs))
    g.plot(d, [graph.style.histogram(fillable=1, steps=fillablesteps, lineattrs=[color.rgb.green, style.linewidth.THIck, deco.filled([color.rgb.blue])],
                                     autohistogramaxisindex=autohistogramaxisindex, autohistogrampointpos=autohistogrampointpos)])
    g.plot(d, [graph.style.histogram(steps=1, lineattrs=[color.rgb.red, style.linewidth.Thick],
                                     autohistogramaxisindex=autohistogramaxisindex, autohistogrampointpos=autohistogrampointpos)])
    g.plot(d, [graph.style.histogram(steps=0,
                                     autohistogramaxisindex=autohistogramaxisindex, autohistogrampointpos=autohistogrampointpos)])

draw(d1, 10, 0)
draw(d2, 0, 0)
draw(d3, 10, 7, autohistogramaxisindex=0, autohistogrampointpos=0)
draw(d4, 0, 7, autohistogramaxisindex=1, autohistogrampointpos=1)
draw(d1, 10, 14, x=graph.axis.lin(min=3, max=14), y=graph.axis.lin(min=-0.1, max=0.45))
draw(d2, 0, 14, y=graph.axis.lin(min=3, max=14), x=graph.axis.lin(min=-0.1, max=0.45))
draw(d1, 10, 21, fillablesteps=1, x=graph.axis.lin(min=3, max=14), y=graph.axis.lin(min=-0.1, max=0.45))
draw(d2, 0, 21, fillablesteps=1, y=graph.axis.lin(min=3, max=14), x=graph.axis.lin(min=-0.1, max=0.45))
c.writeEPSfile("test_histogram")
c.writePDFfile("test_histogram")
