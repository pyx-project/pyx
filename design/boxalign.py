#!/usr/bin/env python
import sys, math
sys.path[:0] = [".."]
from pyx import *

c = canvas.canvas()
c.stroke(path.line(0, 0, 4, 2), deco.earrow.Large())
t = text.text(2, 1, r"$\vec p$")
t.linealign(0.1, -2/math.sqrt(20), 4/math.sqrt(20))
c.insert(t)
c.stroke(path.line(0, 0, 1, 1), deco.earrow.Large())
t = text.text(0.5, 0.5, r"$\vec a$")
t.linealign(0.1, -1/math.sqrt(2), 1/math.sqrt(2))
c.insert(t)
c.stroke(path.line(-1, 3, 3, -1), style.linestyle.dotted)
c.stroke(path.line(1, 1, 1-1/math.sqrt(2), 1+1/math.sqrt(2)), deco.earrow.Large())
t = text.text(1-1/math.sqrt(8), 1+1/math.sqrt(8), r"$\vec b$")
t.linealign(0.1, 1/math.sqrt(2), 1/math.sqrt(2))
c.insert(t)
c.writetofile("boxalignpal")

###############################################################################

c = canvas.canvas()
c.stroke(path.line(0, 0, 4, 2), deco.earrow.Large())
t = text.text(2, 1, r"$\vec p$")
t.linealign(0.1, -2/math.sqrt(20), 4/math.sqrt(20))
c.insert(t)
c.stroke(path.line(0, 0, -1, 1), deco.earrow.Large())
t = text.text(-0.5, 0.5, r"$\vec a$")
t.linealign(0.1, -1/math.sqrt(2), -1/math.sqrt(2))
c.insert(t)
c.stroke(path.path(path.arc(0, 0, math.sqrt(2), 0, 360), path.closepath()), style.linestyle.dotted)
c.writetofile("boxalignpac")

###############################################################################

c = canvas.canvas()
c.stroke(path.line(0, 0, 4, 2), deco.earrow.Large())
t = text.text(2, 1, r"$\vec e$")
t.linealign(0.1, -2/math.sqrt(20), 4/math.sqrt(20))
c.insert(t)
c.stroke(path.line(0, 0, 6, 2), deco.earrow.Large())
t = text.text(3, 1, r"$\vec f$")
t.linealign(0.1, 2/math.sqrt(60), -6/math.sqrt(60))
c.insert(t)
c.stroke(path.line(6, 2, 4, 2), deco.earrow.Large())
t = text.text(5, 2, r"$\vec g$")
t.linealign(0.1, 0, 1)
c.insert(t)
c.stroke(path.line(0, 0, -1, 1), deco.earrow.Large())
t = text.text(-0.5, 0.5, r"$\vec a$")
t.linealign(0.1, -1/math.sqrt(2), -1/math.sqrt(2))
c.insert(t)
c.stroke(path.path(path.arc(0, 0, math.sqrt(2), 0, 360), path.closepath()), style.linestyle.dotted)
c.stroke(path.line(0, 0, 0, math.sqrt(2)), deco.earrow.Large())
t = text.text(0, 1/math.sqrt(2), r"$\vec b$")
t.linealign(0.1, -1, 0)
c.insert(t)
c.writetofile("boxalignlac")

###############################################################################

def drawexample(canvas, corner, linealign):
    r = 1.5
    canvas.stroke(path.path(path.arc(0, 0, r, 0, 360)))
    phi = 0
    while phi < 2 * math.pi + 1e-10:
        if corner:
            b = box.polygon(center=(0, 0), corners=[(0, 0), (1, 0), (0.5, math.sqrt(3)/2)])
        else:
            b = box.polygon(center=(0, 0), corners=[(-0.5, -math.sqrt(3)/6), (0.5, -math.sqrt(3)/6), (0, math.sqrt(3)/3)])
        if linealign:
            b.linealign(r, math.cos(phi), math.sin(phi))
        else:
            b.circlealign(r, math.cos(phi), math.sin(phi))
        if round(phi / math.pi * 2 * 100) % 100:
            canvas.stroke(b.path())
        else:
            canvas.stroke(b.path(), color.rgb.red)
        phi += math.pi / 50

d = 6
c = canvas.canvas()
sc = c.insert(canvas.canvas(trafo.translate(0, d)))
drawexample(sc, 0, 0)
sc = c.insert(canvas.canvas(trafo.translate(d, d)))
drawexample(sc, 0, 1)
sc = c.insert(canvas.canvas(trafo.translate(0, 0)))
drawexample(sc, 1, 0)
sc = c.insert(canvas.canvas(trafo.translate(d, 0)))
drawexample(sc, 1, 1)
c.text(0, 1.5*d, "align at a circle", text.halign.center)
c.text(d, 1.5*d, "align at tangents", text.halign.center)
c.text(-0.5*d, d, "reference point at the triangle center", text.halign.center, trafo.rotate(90))
c.text(-0.5*d, 0, "reference point at a triangle corner", text.halign.center, trafo.rotate(90))
c.writetofile("boxalignexample")


