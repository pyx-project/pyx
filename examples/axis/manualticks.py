# Ticks can be set manually in combination with automatically created
# ticks. Note that the rating takes into account the manual ticks as
# well.

import math
from pyx import *

p = path.curve(0, 0, 3, 0, 1, 4, 4, 4)

myticks = [graph.parter.tick(math.pi, label="\pi", labelattrs=[text.mathmode]),
           graph.parter.tick(2*math.pi, label="2\pi", labelattrs=[text.mathmode])]

c = canvas.canvas()
c.insert(graph.axis.pathaxis(p, graph.axis.linaxis(min=0, max=10)))
c.insert(graph.axis.pathaxis(p.transformed(trafo.translate(4, 0)),
                             graph.axis.linaxis(min=0, max=10, manualticks=myticks)))
c.writeEPSfile("manualticks")
