#!/usr/bin/env python
import sys
sys.path[:0] = [".."]

from pyx import *
from pyx.graph import *

c = canvas.canvas()
g = c.insert(graphxy(width=10))
g.plot(data("graph1.dat", x=1, y=2))
c.writetofile("graph1")
