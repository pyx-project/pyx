# Partitioners (in the code the short form parter is used) take
# care of calculating appropriate tick positions for a given axis
# range. Automatic partitioners create several tick lists, which are
# rated by an axis rater instance afterwards while manual partitioners
# create a single tick list only, which thus doesn't need to be rated.
#
# Note that the partitioning uses fractional number arithmetics. For
# that, tick instances can be initialized with floats using a fixed
# precision but also with strings as shown.

import math
from pyx import *

p = path.path(path.moveto(0, 0), path.curveto(3, 0, 1, 4, 4, 4))

myparter = graph.linparter(["1/3", "1/6"])

c = canvas.canvas()
c.insert(graph.pathaxis(p,
                        graph.linaxis(min=0, max=1, parter=myparter)))
c.insert(graph.pathaxis(p.transformed(trafo.translate(4, 0)),
                        graph.linaxis(min=0, max=1, parter=myparter,
                                      texter=graph.rationaltexter())))
c.writetofile("parter")
