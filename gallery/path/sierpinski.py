# Sierpinski triangle
# contributed by Gerhard Schmid

from math import sqrt
from pyx import *

# triangle geometry
l = 10
h = 0.5 * sqrt(3) * l

# base triangle path
p = path.path(path.moveto(0, 0),
              path.lineto(l, 0),
              path.lineto(0.5 * l, h),
              path.closepath())

for i in range(6):
    # path is scaled down ...
    p = p.transformed(trafo.scale(0.5))
    # ... and three times plotted (translated accordingly)
    p += ( p.transformed(trafo.translate(0.5 * l, 0)) +
           p.transformed(trafo.translate(0.25 * l, 0.5 * h)))

c = canvas.canvas()
c.stroke(p, [style.linewidth.Thin])
c.writeEPSfile()
c.writePDFfile()
c.writeSVGfile()
