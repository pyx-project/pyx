# Ticks can be set manually in combination with automatically created
# ticks. Note that the rating takes into account the manual ticks as
# well.

import math
from pyx import *
from pyx.graph import axis

p = path.curve(0, 0, 3, 0, 1, 4, 4, 4)

myticks = [axis.tick.tick(math.pi, label="\pi", labelattrs=[text.mathmode]),
           axis.tick.tick(2*math.pi, label="2\pi", labelattrs=[text.mathmode])]

c = canvas.canvas()
c.insert(axis.pathaxis(p, axis.linear(min=0, max=10)))
c.insert(axis.pathaxis(p.transformed(trafo.translate(4, 0)),
                       axis.linear(min=0, max=10, manualticks=myticks)))
c.writeEPSfile("manualticks")
c.writePDFfile("manualticks")
