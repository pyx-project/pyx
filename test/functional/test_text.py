#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

from pyx import *
from pyx import text

c = canvas.canvas()
text.set(mode="latex", dvidebug=1)

c.stroke(path.line(-1, 0, 6, 0))

c.text(6.2, 0, "0", text.valign.centerline())
c.text(-1.2, 0, "abc", text.valign.centerline(), text.halign.right)

t1 = text.text(0, 0, "a b c d e f g h i j k l m n o p q r s t u v w x y z", text.valign.bottomline("2 cm"))
c.insert(t1)
c.stroke(t1.path())

t2 = c.insert(text.text(3, 0, "a b c d e f g h i j k l m n o p q r s t u v w x y z", text.valign.topline("2 cm")))
c.stroke(t2.path())

c.text(0, 3, r"\int\limits_{-\infty}^\infty \!{\rm d}x\, e^{-a x^2} = \sqrt{\pi\over a}", text.mathmode)
c.text(0, 6, r"\int\limits_{-\infty}^\infty \!{\rm d}x\, e^{-a x^2} = \sqrt{\pi\over a}", text.mathmode, text.size.LARGE)

c.stroke(c.text(1, 2, r"Hello, world!").path())
c.stroke(c.text(1, 2, r"Hello, world!", trafo.slant(1)).path())

c.writetofile("test_text", paperformat="a4")
