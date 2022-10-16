from math import pi, sin, cos
from pyx import *

def vector(x1, y1, x2, y2, t, pos=0.5, distance=0.1):
    c = canvas.canvas()
    c.stroke(path.line(x1, y1, x2, y2), [deco.earrow.normal])
    textbox = text.text((1-pos)*x1 + pos*x2, (1-pos)*y1 + pos*y2, t,
                        [text.halign.center, text.vshift.mathaxis])
    if distance < 0:
        textbox.linealign(-distance, y1 - y2, x2 - x1)
    else:
        textbox.linealign(distance, y2 - y1, x1 - x2)
    c.insert(textbox)
    return c

r = 1.5
a = 150

c = canvas.canvas()
dx, dy = cos(a * pi / 180), sin(a * pi / 180)
x, y = r * dx, r * dy
c.stroke(path.circle(0, 0, r))
c.insert(vector(0, 0, x, y, r"$\vec r$"))
c.insert(vector(x, y, x - dy, y + dx, r"$\vec t$", pos=0.7))
c.insert(vector(x, y, x + dx, y + dy, r"$\vec n$", pos=0.7))
c.writeEPSfile()
c.writePDFfile()
c.writeSVGfile()
