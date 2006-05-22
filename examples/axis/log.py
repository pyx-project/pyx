import math
from pyx import *
from pyx.graph import axis

p = path.curve(0, 0, 3, 0, 1, 4, 4, 4)

log2parter = axis.parter.log([axis.parter.preexp([axis.tick.rational(1)], 4),
                              axis.parter.preexp([axis.tick.rational(1)], 2)])
log2texter = axis.texter.exponential(nomantissaexp=r"{2^{%s}}",
                                     mantissamax=axis.tick.rational(2))

c = canvas.canvas()
c.insert(axis.pathaxis(p, axis.log(min=1, max=1024)))
c.insert(axis.pathaxis(p.transformed(trafo.translate(4, 0)),
                       axis.log(min=1, max=1024, parter=log2parter)))
c.insert(axis.pathaxis(p.transformed(trafo.translate(8, 0)),
                       axis.log(min=1, max=1024, parter=log2parter,
                                texter=log2texter)))
c.writeEPSfile("log")
c.writePDFfile("log")
