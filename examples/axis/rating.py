# In the example below, several axes with the same parameters are
# plotted on a path scaled in 3 different sizes. Note that the axes
# adjust the ticks appropriately to the available space. The rating
# mechanism takes into account the number of ticks and subticks, but
# also the distances between the labels. Thus, the example in the
# middle has less ticks than the smallest version, because there is
# not enough room for labels with a decimal place.
#
# The rating mechanism is configurable and exchangeable by the axis
# keyword argument "rater". Instead of reconfiguring the rating
# mechanism, simple adjustments to favour more or less ticks are
# possible by the axis keyword argument "density".

from pyx import *
from pyx.graph import axis

p = path.curve(0, 0, 3, 0, 1, 4, 4, 4)

c = canvas.canvas()
c.insert(axis.pathaxis(p.transformed(trafo.translate(-4, 0).scaled(0.75)),
                       axis.linear(min=0, max=10)))
c.insert(axis.pathaxis(p, axis.linear(min=0, max=10)))
c.insert(axis.pathaxis(p.transformed(trafo.scale(1.25).translated(4, 0)),
                       axis.linear(min=0, max=10)))
c.writeEPSfile("rating")
