#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

from pyx import *

c = canvas.canvas()

pa1= pattern.pattern(attrs=[style.linewidth.thin])
pa1.stroke(path.line(0, 0, 0.25, 0.25))
pa1.stroke(path.line(0, 0.25, 0.25, 0))

#c.draw(path.circle(3, 3, 3), [deco.filled([pa1])])
c.draw(path.circle(3, 3, 3), [deco.filled([pa1]), deco.stroked])
c.draw(path.circle(5, 1, 1), [deco.filled([pa1]), deco.stroked])

pa2 = pattern.pattern()
pa2.text(0.125, 0.125, r"\PyX")

c.draw(path.rect(-1, -1, 1, 1), [deco.filled([pa2]), deco.stroked])

c.writeEPSfile("test_pattern", paperformat=document.paperformat.A4)
c.writePDFfile("test_pattern", paperformat=document.paperformat.A4)
