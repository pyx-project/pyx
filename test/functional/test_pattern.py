#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

from pyx import *

c = canvas.canvas()

pattern = canvas.patterncanvas()
pattern.set(canvas.linewidth.thin)
pattern.stroke(path.line(0, 0, 0.25, 0.25))
pattern.stroke(path.line(0, 0.25, 0.25, 0))

c.draw(path.circle(3, 3, 3), canvas.filled(pattern), canvas.stroked())

pyxpattern = canvas.patterncanvas()
pyxpattern.text(0.125, 0.125, r"\PyX")

c.draw(path.rect(-1, -1, 1, 1), canvas.filled(pyxpattern), canvas.stroked())

c.writetofile("test_pattern", paperformat="a4" )
