import sys; sys.path[:0] = ["../.."]
from pyx import *

c = canvas.canvas()
c.stroke(path.line(0, 0, 3, 4))
c.stroke(path.curve(0, 0, 2, 0, 1, 4, 3, 4))
c.stroke(path.curve(0, 0, 2, 0, 1, 4, 3, 4), [deco.wriggle()])
c.writePDFfile("writepdf")

