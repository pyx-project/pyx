#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

from pyx import *

p = lambda phi: graph.graphxyz.central(10, phi, 10-phi/18.0)
# p = lambda phi: graph.graphxyz.parallel(phi, 10/18.0)

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
    g.doplot()
    g.text(2, 2, str(phi))
    def vrect(vx1, vy1, vz1, vx2, vy2, vz2):
        assert len([v1_v2 for v1_v2 in [(vx1, vx2), (vy1, vy2), (vz1, vz2)] if v1_v2[0] == v1_v2[1]]) == 1
        if vz1 == vz2:
            return path.path(path.moveto_pt(*g.vpos_pt(vx1, vy1, vz1)),
                             path.lineto_pt(*g.vpos_pt(vx1, vy2, vz1)),
                             path.lineto_pt(*g.vpos_pt(vx2, vy2, vz1)),
                             path.lineto_pt(*g.vpos_pt(vx2, vy1, vz1)),
                             path.closepath())
        if vy1 == vy2:
            return path.path(path.moveto_pt(*g.vpos_pt(vx1, vy1, vz1)),
                             path.lineto_pt(*g.vpos_pt(vx1, vy1, vz2)),
                             path.lineto_pt(*g.vpos_pt(vx2, vy1, vz2)),
                             path.lineto_pt(*g.vpos_pt(vx2, vy1, vz1)),
                             path.closepath())
        if vx1 == vx2:
            return path.path(path.moveto_pt(*g.vpos_pt(vx1, vy1, vz1)),
                             path.lineto_pt(*g.vpos_pt(vx1, vy2, vz1)),
                             path.lineto_pt(*g.vpos_pt(vx1, vy2, vz2)),
                             path.lineto_pt(*g.vpos_pt(vx1, vy1, vz2)),
                             path.closepath())
    g.fill(vrect(0.4, 0.4, 0, 0.6, 0.6, 0), [g.pz0show and color.rgb.green or color.rgb.red])
    g.fill(vrect(0.4, 0.4, 1, 0.6, 0.6, 1), [g.pz1show and color.rgb.green or color.rgb.red])
    g.fill(vrect(0.4, 0, 0.4, 0.6, 0, 0.6), [g.py0show and color.rgb.green or color.rgb.red])
    g.fill(vrect(0.4, 1, 0.4, 0.6, 1, 0.6), [g.py1show and color.rgb.green or color.rgb.red])
    g.fill(vrect(0, 0.4, 0.4, 0, 0.6, 0.6), [g.px0show and color.rgb.green or color.rgb.red])
    g.fill(vrect(1, 0.4, 0.4, 1, 0.6, 0.6), [g.px1show and color.rgb.green or color.rgb.red])
    for axis in list(g.axes.values()):
        g.stroke(axis.basepath(), [axis.hidden and color.rgb.red or color.rgb.green])
    d.append(document.page(c))
    phi += 5.67

d.writePSfile("test_graph3dloop")
d.writePDFfile("test_graph3dloop")

