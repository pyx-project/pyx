import math
from pyx import *

class rgbgradient(color.lineargradient):

    def getcolor(self, x):
        return color.lineargradient.getcolor(self, x).rgb()

rgbHue = rgbgradient(color.hsb(0, 1, 1), color.hsb(1, 1, 1))

class phasecolorsurface(graph.style.surface):

    def midcolor(self, *c):
        return math.atan2(sum([math.sin(x) for x in c]), sum([math.cos(x) for x in c]))

g = graph.graphxyz(size=3.5, zscale=0.3, projector=graph.graphxyz.central(3, 25, 8),
                   x=graph.axis.lin(painter=None),
                   y=graph.axis.lin(painter=None),
                   z=graph.axis.lin(painter=None),
                   x2=None, y2=None)
g.plot(graph.data.file("example.dat", x=1, y=2, z=3, color=4), [phasecolorsurface(gradient=rgbHue, backcolor=color.rgb.black)])
g.writeEPSfile("example")
