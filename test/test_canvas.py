#!/usr/bin/env python
import sys
sys.path[:0] = [".."]

from pyx import *

c = canvas.canvas()

p = ( path.line("10 pt", "10 pt", "40 pt", "40 pt") +
      path.line("10 pt", "40 pt", "40 pt", "10 pt") )

t1 = trafo.rotation(20)
t2 = trafo.translation(5,0)
t3 = trafo.mirroring(10)

sc = canvas.canvas(t1, t2, t3)
c.insert(sc).stroke(p)

c.stroke(c.bbox().rect())

c.stroke(p.transformed(t1*t2*t3), color.rgb.green, canvas.linestyle.dashed)

# c.stroke(p.transformed(trafo.mirroring(10)*trafo.translation(5,0)*trafo.rotation(22.5)), canvas.linestyle.dashed, color.rgb.red)


c.writetofile("test_canvas", paperformat="a4" )
