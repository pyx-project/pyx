#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

from pyx import *

p = lambda phi: graph.graphxyz.central(10, phi, 10)
# p = lambda phi: graph.graphxyz.parallel(phi, 10)

d = document.document()
phi = 0.123
while phi < 360:
    c = canvas.canvas()
    g = c.insert(graph.graphxyz(10.5, 10, size=6, projector=p(phi),
                                x=graph.axis.lin(painter=graph.axis.painter.regular(gridattrs=[])),
                                y=graph.axis.lin(painter=graph.axis.painter.regular(gridattrs=[])),
                                z=graph.axis.lin(painter=graph.axis.painter.regular(gridattrs=[]))))
    g.plot(graph.data.values(x=[0, 0, 0, 1], y=[0, 0, 1, 1], z=[0, 1, 0, 1], color=[0, 0.33, 0.67, 1]),
           [graph.style.gridpos(index1=1, index2=2), graph.style.surface(gridcolor=color.gray(0.9))])
    g.dodata()
    g.text(2, 2, str(phi))
    d.append(document.page(c))
    phi += 5.67

d.writePSfile("test_graph3dloop")

