import sys; sys.path.insert(0, "../..")
from pyx import *

c = canvas.canvas()
c.fill(path.rect(-1, -1, 2, 2), [color.rgb.red])
c.fill(path.circle(0, 0, 1.2), [color.transparency(0.5), color.rgb.green])
c.fill(path.rect(-2, -0.5, 4, 1), [color.transparency(0.9), color.rgb.blue])
c.writePDFfile("test_color")
