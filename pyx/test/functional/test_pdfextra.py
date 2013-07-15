#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
import sys; sys.path[:0] = ["../.."]

import pyx
from pyx import *
from pyx.font.font import PDFTimesBold
from pyx.pdfextra import *


def texttest():
    c = canvas.canvas()
    d = 0.0

    llx, lly, w, h = 0, 0, 5, 1
    c.text(llx, lly+h, "first textfield:", [text.vshift(-0.5)])
    c.stroke(path.rect(llx-d, lly-d, w+2*d, h+2*d))
    c.insert(textfield(llx, lly, w, h, name="textfield", defaultvalue="hallo", multiline=1,
      font=PDFTimesBold))

    llx, lly, w, h = 0, -2, 1, 1
    c.text(llx, lly+h, "second textfield:", [text.vshift(-0.5)])
    c.stroke(path.rect(llx-d, lly-d, w+2*d, h+2*d))
    c.insert(textfield(llx, lly, w, h, name="another"))

    return c

def checkboxtest():
    c = canvas.canvas()

    c.text(0, 0, "first checkbox:", [text.vshift(-0.5)])
    c.insert(checkbox(0, -0.5, name="checkbox", defaulton=1))

    return c

def radiotest():
    c = canvas.canvas()

    c.text(0, 0, "first radiobuttons:", [text.vshift(-0.5)])
    pos = [(0, -0.5), (0, -1.0), (0, -1.5)]
    values = ["One", "Two", "Three"]
    for (x, y), value in zip(pos, values):
        c.text(x+12*unit.x_pt, y, value)
    c.insert(radiobuttons(pos, name="button", values=values, defaultvalue=values[0]))

    # XXX : default entry is activated with the others

    return c

def choicetest():
    c = canvas.canvas()
    d = 0.0

    llx, lly, w, h = 0, 0, 5, 1
    values = ["One", "Two", "Three"]
    c.text(llx, lly+h, "first choicefield:", [text.vshift(-0.5)])
    c.stroke(path.rect(llx-d, lly-d, w+2*d, h+2*d))
    c.insert(choicefield(llx, lly, w, h, name="choicefield", values=values, defaultvalue=values[0],
        font=PDFTimesBold))

    return c

# write all test into one canvas
c = canvas.canvas()
for cc in [texttest(), checkboxtest(), radiotest(), choicetest()]:
    if not c:
        t = []
    else:
        t = [trafo.translate(0, c.bbox().bottom() - cc.bbox().top() - 1)]
    c.insert(cc, t)
    #c.stroke(cc.bbox().path(), t + [color.rgb.red, style.linestyle.dotted])

# test the transformation behaviour:
cc = canvas.canvas([trafo.scale(0.3)])#, trafo.rotate(90)])
cc.fill(c.bbox().path(), [color.gray(0.9)])
cc.insert(c)
d = document.document([document.page(cc, bboxenlarge=1)])
d.writePDFfile("test_pdfextra", compress=0)

# vim:syntax=python
# vim:fdm=marker:fmr=<<<,>>>:
