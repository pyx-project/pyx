#!/usr/bin/env python
import sys
sys.path[:0] = [".."]
from pyx import *
from pyx import tex


c = canvas.canvas()
t = c.insert(tex.tex())
t.text(0, 0, "Hello, world!")
print "width:", t.textwd("Hello, world!")
print "height:", t.textht("Hello, world!")
print "depth:", t.textdp("Hello, world!")
c.writetofile("tex1.eps")

