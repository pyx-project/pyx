from pyx import *

c = canvas.canvas()
c.text(0, 0, r"\PyX", trafo.scale(5), color.rgb.red)
c.writetofile("logo")

