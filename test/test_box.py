#!/usr/bin/env python
import sys
sys.path[:0] = [".."]

import math
from pyx import *

def drawexample(canvas, corner, linealign):
    if corner:
        b = graph.alignbox((0, 0), (0, 0), (1, 0), (0.5, math.sqrt(3)/2))
    else:
        b = graph.alignbox((0.5, math.sqrt(3)/6), (0, 0), (1, 0), (0.5, math.sqrt(3)/2))
    r = 1.5
    canvas.stroke(path.path(path.arc(0, 0, r, 0, 360)))
    phi = 0
    while phi < 2 * math.pi + 1e-10:
        if linealign:
            b.linealign(r, math.cos(phi), math.sin(phi))
        else:
            b.circlealign(r, math.cos(phi), math.sin(phi))
        if round(phi / math.pi * 2 * 100) % 100:
            canvas.stroke(b.path())
        else:
            canvas.stroke(b.path(), color.rgb.red)
        phi += math.pi / 50

def distances():
    print "test distance measurement ...",
    b1 = graph.alignbox((0.5, math.sqrt(3)/6), (0, 0), (1, 0), (0.5, math.sqrt(3)/2))
    b2 = graph.alignbox((0.5, math.sqrt(3)/6), (0, 0), (1, 0), (0.5, math.sqrt(3)/2)).transform(trafo.translation(3, 0))
    b3 = graph.alignbox((0.5, math.sqrt(3)/6), (0, 0), (1, 0), (0.5, math.sqrt(3)/2)).transform(trafo.translation(3, 3 * math.tan(math.pi/6)))
    b4 = graph.alignbox((0.5, math.sqrt(3)/6), (0, 0), (1, 0), (0.5, math.sqrt(3)/2)).transform(trafo.translation(0, 3))
    b5 = graph.alignbox((0.5, math.sqrt(3)/6), (0, 0), (1, 0), (0.5, math.sqrt(3)/2)).transform(trafo.translation(0.5, 0.5))
    assert abs(unit.topt(b1.boxdistance(b2) - unit.t_cm(2))) < 1e-10
    assert abs(unit.topt(b1.boxdistance(b3) - unit.t_cm(math.sqrt(9*(1 + math.tan(math.pi/6)**2)) - math.sqrt(3)/2))) < 1e-10
    assert abs(unit.topt(b1.boxdistance(b4) - unit.t_cm(3 - math.sqrt(3)/2))) < 1e-10
    assert abs(unit.topt(b2.boxdistance(b1) - unit.t_cm(2))) < 1e-10
    assert abs(unit.topt(b3.boxdistance(b1) - unit.t_cm(math.sqrt(9*(1 + math.tan(math.pi/6)**2)) - math.sqrt(3)/2))) < 1e-10
    assert abs(unit.topt(b4.boxdistance(b1) - unit.t_cm(3 - math.sqrt(3)/2))) < 1e-10
    try:
        b1.boxdistance(b5)
        assert 0, "BoxCrossError expected"
    except graph.BoxCrossError: pass
    try:
        b5.boxdistance(b1)
        assert 0, "BoxCrossError expected"
    except graph.BoxCrossError: pass
    print "ok"

c = canvas.canvas()
sc = c.insert(canvas.canvas(trafo.translation(0, 6)))
drawexample(sc, 0, 0)
sc = c.insert(canvas.canvas(trafo.translation(6, 6)))
drawexample(sc, 0, 1)
sc = c.insert(canvas.canvas(trafo.translation(0, 0)))
drawexample(sc, 1, 0)
sc = c.insert(canvas.canvas(trafo.translation(6, 0)))
drawexample(sc, 1, 1)
distances()
c.writetofile("test_box", paperformat="a4")

