import sys; sys.path[:0] = ["../.."]
from pyx import *

c = canvas.canvas()
#c.stroke(path.line(0, 0, 3, 4), [style.linewidth.THIN, color.rgb.red])
#c.stroke(path.curve(0, 0, 2, 0, 1, 4, 3, 4), [deco.wriggle(), color.rgb.blue])
#c.stroke(path.curve(0, 0, 2, 0, 1, 4, 3, 4), [style.linestyle.dotted, color.rgb.green])
b = 0.75
for h in range(11):
    for s in range(11):
        c.fill(path.rect(h, s, 1, 1), [color.hsb(h/10.0, s/10.0, b)])
c.writePDFfile("writepdf")
c.writeEPSfile("writepdf")

