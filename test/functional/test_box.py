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
            canvas.stroke(b.path(centerradius=0.05), color.rgb.red)
        phi += math.pi / 50

def distances():
    print "test distance measurement ...",
    b1 = box.polygon(center=(0.5, math.sqrt(3)/6), corners=((0, 0), (1, 0), (0.5, math.sqrt(3)/2)))
    b2 = box.polygon(center=(0.5, math.sqrt(3)/6), corners=((0, 0), (1, 0), (0.5, math.sqrt(3)/2)))
    b2.transform(trafo.translate(3, 0))
    b3 = box.polygon(center=(0.5, math.sqrt(3)/6), corners=((0, 0), (1, 0), (0.5, math.sqrt(3)/2)))
    b3.transform(trafo.translate(3, 3 * math.tan(math.pi/6)))
    b4 = box.polygon(center=(0.5, math.sqrt(3)/6), corners=((0, 0), (1, 0), (0.5, math.sqrt(3)/2)))
    b4.transform(trafo.translate(0, 3))
    b5 = box.polygon(center=(0.5, math.sqrt(3)/6), corners=((0, 0), (1, 0), (0.5, math.sqrt(3)/2)))
    b5.transform(trafo.translate(0.5, 0.5))
    assert abs(unit.topt(b1.boxdistance(b2) - unit.t_cm(2))) < 1e-10
    assert abs(unit.topt(b1.boxdistance(b3) - unit.t_cm(math.sqrt(9*(1 + math.tan(math.pi/6)**2)) - math.sqrt(3)/2))) < 1e-10
    assert abs(unit.topt(b1.boxdistance(b4) - unit.t_cm(3 - math.sqrt(3)/2))) < 1e-10
    assert abs(unit.topt(b2.boxdistance(b1) - unit.t_cm(2))) < 1e-10
    assert abs(unit.topt(b3.boxdistance(b1) - unit.t_cm(math.sqrt(9*(1 + math.tan(math.pi/6)**2)) - math.sqrt(3)/2))) < 1e-10
    assert abs(unit.topt(b4.boxdistance(b1) - unit.t_cm(3 - math.sqrt(3)/2))) < 1e-10
    try:
        b1.boxdistance(b5)
        assert 0, "BoxCrossError expected"
    except box.BoxCrossError: pass
    try:
        b5.boxdistance(b1)
        assert 0, "BoxCrossError expected"
    except box.BoxCrossError: pass
    print "ok"

c = canvas.canvas()
sc = c.insert(canvas.canvas(trafo.translate(0, 6)))
drawexample(sc, 0, 0)
sc = c.insert(canvas.canvas(trafo.translate(6, 6)))
drawexample(sc, 0, 1)
sc = c.insert(canvas.canvas(trafo.translate(0, 0)))
drawexample(sc, 1, 0)
sc = c.insert(canvas.canvas(trafo.translate(6, 0)))
drawexample(sc, 1, 1)
#distances()
#b = box.polygon(center=(0.5, math.sqrt(3)/6), corners=((0, 0), (1, 0), (0.5, math.sqrt(3)/2)))
#c.stroke(b.path(beziercorner=0.1))
#b = box.polygon(center=(0.5, math.sqrt(3)/6), corners=((0, 0), (1, 0), (1, 1), (0, 1)))
#b.transform(trafo.translate(2, 0))
#c.stroke(b.path(beziercorner=0.1))
c.writetofile("test_box", paperformat="a4")

