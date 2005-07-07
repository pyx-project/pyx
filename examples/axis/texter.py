# Texters create the label strings written to the ticks. There are
# texters available for decimal numbers without and with an
# exponential part as well as fractions. Internally, the partitioning
# is based on fractions to avoid any rounding problems.
#
# Although we could modify axis.linear into a piaxis "inplace", we
# define a special piaxis below to give an impression, how easy
# alternative default settings can be implemented. A more advanced
# task would be to add an appropriate special partitioner for a
# piaxis.

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
