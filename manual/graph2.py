#!/usr/bin/env python
import sys
sys.path[:0] = [".."]

from pyx import *

c = canvas.canvas()

a, b = 2, 9

mypainter=graph.axispainter(baselineattrs=canvas.earrow.normal)

g = c.insert(graph.graphxy(width=10, x2=None, y2=None,
                           x=graph.linaxis(min=0, max=10,
                                           part=graph.manualpart(ticks=(graph.frac(a, 1),
                                                                        graph.frac(b, 1)),
                                                           texts=("a", "b")),
                                           painter=mypainter),
                           y=graph.linaxis(painter=mypainter, part=graph.manualpart())))

line = g.plot(graph.function("y=(x-3)*(x-5)*(x-7)")).style
g.finish()

pa = path.path(g.axes["x"].gridpath(a))
pb = path.path(g.axes["x"].gridpath(b))
(splita,), (splitpa,) = line.path.intersect(pa)
(splitb,), (splitpb,) = line.path.intersect(pb)
area = (pa.split(splitpa)[0] <<
        line.path.split(splita, splitb)[1] <<
        pb.split(splitpb)[0].reversed())
area.append(path.closepath())
g.stroke(area, canvas.linewidth.THick, canvas.filled(color.gray(0.8)))
c.text(g.pos(0.5*(a+b), 0)[0], 1, r"\int_a^b f(x) {\rm d}x", text.halign.center, text.mathmode)

c.writetofile("graph2")
