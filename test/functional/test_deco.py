#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

from pyx import *

c = canvas.canvas()

p = path.line(0, 0, 3, 0)
c.stroke(p, [color.rgb.red])
c.stroke(p, [color.rgb.green, deco.wriggle()])

p = path.curve(5, 0, 8, 0, 6, 4, 9, 4)
c.stroke(p, [color.rgb.red])
c.stroke(p, [color.rgb.green, deco.wriggle(), deco.earrow.LARge([deco.stroked.clear])])
c.stroke(p, [color.rgb.blue, deco.wriggle(), deco.wriggle(loops=250, radius=0.1)])

c.writeEPSfile("test_deco")

