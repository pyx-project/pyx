#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

from pyx import *
from pyx import text

c = canvas.canvas()
text.set(mode="latex", dvidebug=1, usefiles="test_text.dvi")

c.stroke(path.line(-1, 0, 6, 0))

c.stroke(path.line(6, 5, 6.99, 5), canvas.linewidth.THIN)
c.stroke(path.line(6, 6, 6.99, 6), canvas.linewidth.THIN)
c.stroke(path.line(8.01, 5, 9, 5), canvas.linewidth.THIN)
c.stroke(path.line(8.01, 6, 9, 6), canvas.linewidth.THIN)
c.stroke(path.line(7, 4, 7, 4.99), canvas.linewidth.THIN)
c.stroke(path.line(8, 4, 8, 4.99), canvas.linewidth.THIN)
c.stroke(path.line(7, 6.01, 7, 7), canvas.linewidth.THIN)
c.stroke(path.line(8, 6.01, 8, 7), canvas.linewidth.THIN)
c.text(7, 5, "\\vrule width1truecm height1truecm")

c.text(6.2, 0, "0", text.vshift.middlezero)
c.text(-1.2, 0, "abc", text.vshift.mathaxis, text.halign.right)

t1 = text.text(0, 0, "a b c d e f g h i j k l m n o p q r s t u v w x y z", text.vbox(2), text.valign.bottombaseline)
c.insert(t1)
c.stroke(t1.path())

t2 = c.insert(text.text(3, 0, "a b c d e f g h i j k l m n o p q r s t u v w x y z", text.vbox(2)))
c.stroke(t2.path())

c.text(0, 3, r"\int\limits_{-\infty}^\infty \!{\rm d}x\, e^{-a x^2} = \sqrt{\pi\over a}", text.mathmode)
c.text(0, 6, r"\int\limits_{-\infty}^\infty \!{\rm d}x\, e^{-a x^2} = \sqrt{\pi\over a}", text.size.LARGE, text.mathmode)

c.stroke(c.text(1, 2, r"Hello, world!").path())
c.stroke(c.text(1, 2, r"Hello, world!", trafo.slant(1)).path())

c.writetofile("test_text", paperformat="a4")
