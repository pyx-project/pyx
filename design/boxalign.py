#!/usr/bin/env python
import sys, math
sys.path.append("..")
from pyx import *

c = canvas.canvas()
t = c.insert(tex.tex())
c.draw(path.line(0, 0, 4, 2), canvas.earrow.Large)
graph.textbox(t, r"$\vec p$").linealign(0.1, -2/math.sqrt(20), 4/math.sqrt(20)).printtext(2, 1)
c.draw(path.line(0, 0, 1, 1), canvas.earrow.Large)
graph.textbox(t, r"$\vec a$").linealign(0.1, -1/math.sqrt(2), 1/math.sqrt(2)).printtext(0.5, 0.5)
c.draw(path.line(-1, 3, 3, -1), canvas.linestyle.dotted)
c.draw(path.line(1, 1, 1-1/math.sqrt(2), 1+1/math.sqrt(2)), canvas.earrow.Large)
graph.textbox(t, r"$\vec b$").linealign(0.1, 1/math.sqrt(2), 1/math.sqrt(2)).printtext(1-1/math.sqrt(8), 1+1/math.sqrt(8))
c.writetofile("boxalignpal")

###############################################################################

c = canvas.canvas()
t = c.insert(tex.tex())
c.draw(path.line(0, 0, 4, 2), canvas.earrow.Large)
graph.textbox(t, r"$\vec p$").linealign(0.1, -2/math.sqrt(20), 4/math.sqrt(20)).printtext(2, 1)
c.draw(path.line(0, 0, -1, 1), canvas.earrow.Large)
graph.textbox(t, r"$\vec a$").linealign(0.1, -1/math.sqrt(2), -1/math.sqrt(2)).printtext(-0.5, 0.5)
c.draw(path.path(path.arc(0, 0, math.sqrt(2), 0, 360), path.closepath()), canvas.linestyle.dotted)
c.writetofile("boxalignpac")

###############################################################################

c = canvas.canvas()
t = c.insert(tex.tex())
c.draw(path.line(0, 0, 4, 2), canvas.earrow.Large)
graph.textbox(t, r"$\vec e$").linealign(0.1, -2/math.sqrt(20), 4/math.sqrt(20)).printtext(2, 1)
c.draw(path.line(0, 0, 6, 2), canvas.earrow.Large)
graph.textbox(t, r"$\vec f$").linealign(0.1, 2/math.sqrt(60), -6/math.sqrt(60)).printtext(3, 1)
c.draw(path.line(6, 2, 4, 2), canvas.earrow.Large)
graph.textbox(t, r"$\vec g$").linealign(0.1, 0, 1).printtext(5, 2)
c.draw(path.line(0, 0, -1, 1), canvas.earrow.Large)
graph.textbox(t, r"$\vec a$").linealign(0.1, -1/math.sqrt(2), -1/math.sqrt(2)).printtext(-0.5, 0.5)
c.draw(path.path(path.arc(0, 0, math.sqrt(2), 0, 360), path.closepath()), canvas.linestyle.dotted)
c.draw(path.line(0, 0, 0, math.sqrt(2)), canvas.earrow.Large)
graph.textbox(t, r"$\vec b$").linealign(0.1, -1, 0).printtext(0, 1/math.sqrt(2))
c.writetofile("boxalignlac")

###############################################################################

def drawexample(canvas, corner, linealign):
    if corner:
        b = graph.alignbox((0, 0), (0, 0), (1, 0), (0.5, math.sqrt(3)/2))
    else:
        b = graph.alignbox((0.5, math.sqrt(3)/6), (0, 0), (1, 0), (0.5, math.sqrt(3)/2))
    r = 1.5
    canvas.draw(path.path(path.arc(0, 0, r, 0, 360)))
    phi = 0
    while phi < 2 * math.pi + 1e-10:
        if linealign:
            b.linealign(r, math.cos(phi), math.sin(phi))
        else:
            b.circlealign(r, math.cos(phi), math.sin(phi))
        if round(phi / math.pi * 2 * 100) % 100:
            canvas.draw(b.path())
        else:
            canvas.draw(b.path(), color.rgb.red)
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
t = c.insert(tex.tex())
t.text(0, 1.5*d, "align at a circle", tex.halign.center)
t.text(d, 1.5*d, "align at tangents", tex.halign.center)
t.text(-0.5*d, d, "reference point at the triangle center", tex.halign.center, tex.direction.vertical)
t.text(-0.5*d, 0, "reference point at a triangle corner", tex.halign.center, tex.direction.vertical)
c.writetofile("boxalignexample")


