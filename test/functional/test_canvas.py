#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

from pyx import *

c = canvas.canvas()

p = ( path.line("10 pt", "10 pt", "40 pt", "40 pt") +
      path.line("10 pt", "40 pt", "40 pt", "10 pt") )

t1 = trafo.rotate(20)
t2 = trafo.translate(5,0)
t3 = trafo.mirror(10)

sc = canvas.canvas([t1, t2, t3])
c.insert(sc).stroke(p)

c.stroke(c.bbox().rect())

c.stroke(p.transformed(t1*t2*t3), [color.rgb.green, style.linestyle.dashed])

c.stroke(p, [color.rgb.red, style.linestyle.dotted, t3, t2, t1])

c.writeEPSfile("test_canvas", paperformat="a4")

d = canvas.document()

for nr in range(1, 10):
     page = canvas.page(pagename = "i"*nr, rotated=(nr-1)%2)
     page.text(0, 0, "page %d" % nr)
     d.append(page)

d.writePSfile("test_document")
