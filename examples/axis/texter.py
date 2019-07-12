import math
from pyx import *
from pyx.graph import axis

texter1 = axis.texter.decimal(plus="+", minus="-", equalprecision=1)
texter2 = axis.texter.rational()

class piaxis(axis.linear):

    def __init__(self, divisor=math.pi,
                 texter=axis.texter.rational(suffix=r"\pi"), **kwargs):
        axis.linear.__init__(self, divisor=divisor, texter=texter, **kwargs)

p1 = path.path(path.moveto(0, 0), path.curveto(3, 0, 1, 4, 4, 4))
p2 = p1.transformed(trafo.translate(4, 0))
p3 = p2.transformed(trafo.translate(4, 0))
p4 = p3.transformed(trafo.translate(4, 0))

c = canvas.canvas()
c.insert(axis.pathaxis(p1, axis.linear(min=0, max=1e2)))
c.insert(axis.pathaxis(p2, axis.linear(min=-0.7, max=0.4, texter=texter1)))
c.insert(axis.pathaxis(p3, axis.linear(min=-0.7, max=0.4, texter=texter2)))
c.insert(axis.pathaxis(p4, piaxis(min=0, max=2*math.pi)))
c.writeEPSfile("texter")
c.writePDFfile("texter")
c.writeSVGfile("texter")
