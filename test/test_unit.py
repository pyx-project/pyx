#!/usr/bin/env python

from pyx import *
from pyx.path import *

c=canvas.canvas()

unit.set(uscale=1)
c.draw(path([moveto(0,0), lineto(unit.length("1 u")+unit.length("1 t"), "1 u")]), color.rgb.red)
unit.set(uscale=2)
c.draw(path([moveto(0,0), lineto(unit.length("1 u")+unit.length("1 t"), "1 u")]), color.rgb.green)
unit.set(uscale=4)
c.draw(path([moveto(0,0), lineto(unit.length("1 u")+unit.length("1 t"), "1 u")]), color.rgb.blue)

c.writetofile("test")

