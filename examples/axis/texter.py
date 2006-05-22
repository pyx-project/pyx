import math
from pyx import *
from pyx.graph import axis

class piaxis(axis.linear):

    def __init__(self, divisor=math.pi,
                 texter=axis.texter.rational(suffix="\pi"), **kwargs):
        axis.linear.__init__(self, divisor=divisor, texter=texter, **kwargs)


p = path.path(path.moveto(0, 0), path.curveto(3, 0, 1, 4, 4, 4))

c = canvas.canvas()
c.insert(axis.pathaxis(p, axis.linear(min=0, max=10)))
c.insert(axis.pathaxis(p.transformed(trafo.translate(4, 0)),
                       axis.linear(min=0, max=1e5)))
c.insert(axis.pathaxis(p.transformed(trafo.translate(8, 0)),
                       piaxis(min=0, max=2*math.pi)))
c.writeEPSfile("texter")
c.writePDFfile("texter")
