#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

from pyx import *

c = canvas.canvas()

pattern = canvas.pattern()
pattern.set(style.linewidth.thin)
pattern.stroke(path.line(0, 0, 0.25, 0.25))
pattern.stroke(path.line(0, 0.25, 0.25, 0))

c.draw(path.circle(3, 3, 3), deco.filled(pattern), deco.stroked())

pyxpattern = canvas.pattern()
pyxpattern.text(0.125, 0.125, r"\PyX")

c.draw(path.rect(-1, -1, 1, 1), deco.filled(pyxpattern), deco.stroked())

c.writetofile("test_pattern", paperformat="a4" )
