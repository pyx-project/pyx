#!/usr/bin/env python
import sys
sys.path[:0] = [".."]

from pyx import *
from pyx.graph import *

c = canvas.canvas()
t = c.insert(tex.tex())
g = c.insert(graphxy(t, width=10))
g.plot(data("graph1.dat", x=1, y=2))
g.finish()
c.writetofile("graph1")
