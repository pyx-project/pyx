#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

import math
from pyx import *

def drawexample(canvas, corner, linealign):
    r = 1.5
    if corner:
      canvas.stroke(path.path(path.arc(5, 5, r, 0, 360)))
    else:
      canvas.stroke(path.path(path.arc(5.5, 5+math.sqrt(3)/6, r, 0, 360)))
    phi = 0
    while phi < 2 * math.pi + 1e-10:
        if corner:
            b = box.polygon(center=(5, 5), corners=((5, 5), (6, 5), (5.5, 5+math.sqrt(3)/2)))
        else:
            b = box.polygon(center=(5.5, 5+math.sqrt(3)/6), corners=((5, 5), (6, 5), (5.5, 5+math.sqrt(3)/2)))
        if linealign:
            b.linealign(r, math.cos(phi), math.sin(phi))
        else:
            b.circlealign(r, math.cos(phi), math.sin(phi))
        if round(phi / math.pi * 2 * 100) % 100:
            canvas.stroke(b.path(centerradius=0.05))
        else:
            canvas.stroke(b.path(centerradius=0.05), [color.rgb.red])
        phi += math.pi / 50

c = canvas.canvas()
sc = c.insert(canvas.canvas([trafo.translate(0, 6)]))
drawexample(sc, 0, 0)
sc = c.insert(canvas.canvas([trafo.translate(6, 6)]))
drawexample(sc, 0, 1)
sc = c.insert(canvas.canvas([trafo.translate(0, 0)]))
drawexample(sc, 1, 0)
sc = c.insert(canvas.canvas([trafo.translate(6, 0)]))
drawexample(sc, 1, 1)
c.writeEPSfile("test_box", paperformat="a4")

