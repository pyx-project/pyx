# Certainly logarithmic axes are supported in PyX. By playing with
# partitioners and texters, you can easily change the base.
#
# It is left as an exercise to the reader to create a automatic
# partitioner for logarithmic axes with base 2.

import math
from pyx import *

p = path.curve(0, 0, 3, 0, 1, 4, 4, 4)

log2parter = graph.parter.logparter([graph.parter.preexp(graph.tick.frac(1), 4),
                                     graph.parter.preexp(graph.tick.frac(1), 2)])
log2texter = graph.texter.exponentialtexter(nomantissaexp=r"{2^{%s}}",
                                            mantissamax=graph.tick.frac(2))

c = canvas.canvas()
c.insert(graph.axis.pathaxis(p, graph.axis.logaxis(min=1, max=1024)))
c.insert(graph.axis.pathaxis(p.transformed(trafo.translate(4, 0)),
                             graph.axis.logaxis(min=1, max=1024, parter=log2parter)))
c.insert(graph.axis.pathaxis(p.transformed(trafo.translate(8, 0)),
                             graph.axis.logaxis(min=1, max=1024, parter=log2parter,
                                                texter=log2texter)))
c.writeEPSfile("log")
