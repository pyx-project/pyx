#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

from pyx import *

c=canvas.canvas()
t=c.insert(tex.latex())
t.text(0, 0, "Hello, world!")
print "width:", t.textwd("Hello, world!")
print "height:", t.textht("Hello, world!")
print "depth:", t.textdp("Hello, world!")
t.text(0, -0.5, "Hello, world!", tex.fontsize.large)
t.text(0, -1.5,
       r"\sum_{n=1}^{\infty} {1\over{n^2}} = {{\pi^2}\over 6}",
       tex.style.math)

c.stroke(path.line(5, -0.5, 9, -0.5))
c.stroke(path.line(5, -1, 9, -1))
c.stroke(path.line(5, -1.5, 9, -1.5))
c.stroke(path.line(7, -1.5, 7, 0))
t.text(7, -0.5, "left aligned") # default is tex.halign.left
t.text(7, -1, "center aligned", tex.halign.center)
t.text(7, -1.5, "right aligned", tex.halign.right)

c.stroke(path.line(0, -4, 2, -4))
c.stroke(path.line(0, -2.5, 0, -5.5))
c.stroke(path.line(2, -2.5, 2, -5.5))
t.text(0, -4,
       "a b c d e f g h i j k l m n o p q r s t u v w x y z",
       tex.valign.top(2))
c.stroke(path.line(2.5, -4, 4.5, -4))
c.stroke(path.line(2.5, -2.5, 2.5, -5.5))
c.stroke(path.line(4.5, -2.5, 4.5, -5.5))
t.text(2.5, -4,
       "a b c d e f g h i j k l m n o p q r s t u v w x y z",
       tex.valign.bottom(2))

c.stroke(path.line(5, -4, 9, -4))
c.stroke(path.line(7, -5.5, 7, -2.5))
t.text(7, -4, "horizontal")
t.text(7, -4, "vertical", tex.direction.vertical)
t.text(7, -4, "rvertical", tex.direction.rvertical)
t.text(7, -4, "upsidedown", tex.direction.upsidedown)
t.text(7.5, -3.5, "45", tex.direction(45))
t.text(6.5, -3.5, "135", tex.direction(135))
t.text(6.5, -4.5, "225", tex.direction(225))
t.text(7.5, -4.5, "315", tex.direction(315))

t.text(0, -6, "red", color.rgb.red)
t.text(3, -6, "green", color.rgb.green)
t.text(6, -6, "blue", color.rgb.blue)

t.text(0, -6.5, "example1", tex.valign.bottom(0.5))
t.text(4, -6.5, "example2", tex.valign.bottom(0.5), tex.msghandler.hidebuterror)
c.writetofile("test_latex", paperformat="a4")

