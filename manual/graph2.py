#!/usr/bin/env python
import sys
sys.path[:0] = [".."]

from pyx import *
from pyx.graph import *

c = canvas.canvas()
t = tex.tex()

a, b = 2, 9

mypainter=axispainter(baselineattrs=canvas.earrow.normal)

g = c.insert(graphxy(t, width=10, x2=None, y2=None,
                     x=linaxis(min=0, max=10,
                               part=manualpart(ticks=(frac(a, 1),
                                                      frac(b, 1)),
                                               texts=("a", "b")),
                               painter=mypainter),
                     y=linaxis(painter=mypainter, part=manualpart())))

line = g.plot(function("y=(x-3)*(x-5)*(x-7)"))
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
t.text(g.pos(0.5*(a+b), 0)[0], 1, r"\int_a^b f(x) {\rm d}x", tex.halign.center, tex.style.math)

c.insert(t)
c.writetofile("graph2")
