#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

from pyx import *
from pyx.path import *

c=canvas.canvas()

unit.set(uscale=1)
c.stroke(path(moveto(0,0), lineto(unit.u_cm+unit.t_cm, unit.u_cm)), [color.rgb.red])
unit.set(uscale=2)
c.stroke(path(moveto(0,0), lineto(unit.u_cm+unit.t_cm, unit.u_cm)), [color.rgb.green])
unit.set(uscale=4)
c.stroke(path(moveto(0,0), lineto(unit.u_cm+unit.t_cm, unit.u_cm)), [color.rgb.blue])

c.writeEPSfile("test_unit")

