#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

from pyx import *

text.set(text.UnicodeEngine)

c = canvas.canvas()
c.text(0, 2, "Hello, world!")
c.text(0, 4, "Hello, world!", [color.rgb.red])
c.text(0, 6, "Hello, world!", [trafo.rotate(90)])

c.writeEPSfile()
c.writePDFfile()
c.writeSVGfile()
