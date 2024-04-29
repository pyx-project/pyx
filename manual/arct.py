#!/bin/python3
from pyx import *
c = canvas.canvas()
def bluedot(x, y):
    c.fill(path.circle_pt(x, y, 2), [color.rgb.blue])
c.stroke(path.path(path.moveto(0, 0), path.arct(2, 0, 1.5, 1, 0.5)))
def bluedot(x, y):
    c.fill(path.circle(x, y, 0.03), [color.rgb.blue])
bluedot(0, 0)
bluedot(2, 0)
bluedot(1.5, 1)
margin=0.1
c.text(0-margin, 0, r"current point $(0, 0)$", [text.halign.right, text.valign.baseline])
c.text(2+margin, 0, r"$(2, 0)$", [text.halign.left, text.valign.baseline])
c.text(1.5-margin, 1, r"$(1.5, 1)$", [text.halign.right, text.valign.baseline])
c.writePDFfile()
