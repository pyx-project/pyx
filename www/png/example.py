import math
from pyx import *

class phasecolorsurface(graph.style.surface):

    def midcolor(self, *c):
        return math.atan2(sum([math.sin(x) for x in c]), sum([math.cos(x) for x in c]))

g = graph.graphxyz(size=3.5, zscale=0.3, projector=graph.graphxyz.central(3, 25, 8),
                   x=graph.axis.lin(painter=None),
                   y=graph.axis.lin(painter=None),
                   z=graph.axis.lin(painter=None),
                   x2=None, y2=None)
g.plot(graph.data.file("example.dat", x=1, y=2, z=3, color=4), [phasecolorsurface(gradient=color.rgbgradient.Rainbow, coloraxis=graph.axis.lin(min=-math.pi, max=math.pi), backcolor=color.rgb.black, keygraph=None)])
g.writeEPSfile("example")
