#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

from pyx import *

c = canvas.canvas()

pattern = canvas.patterncanvas()
pattern.set(canvas.linewidth.thin)
pattern.stroke(path.line(0, 0, 0.25, 0.25))
pattern.stroke(path.line(0, 0.25, 0.25, 0))
pattern.text(0.125, 0.125, "PyX")

c.draw(path.circle(0, 0, 5), canvas.filled(pattern), canvas.stroked())

c.writetofile("test_pattern", paperformat="a4" )
