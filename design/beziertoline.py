import sys, math
sys.path[:0] = [".."]
from pyx import *
from pyx.normpath import normpathparam

def mark(c, t, phi, x, y):
    c.stroke(path.line(x-0.1, y, x+0.1, y))
    c.stroke(path.line(x, y-0.1, x, y+0.1))
    t = text.text(x, y, t, [text.halign.center, text.vshift.mathaxis])
    t.circlealign(0.2, math.cos(phi*math.pi/180), math.sin(phi*math.pi/180))
    c.insert(t)
c = canvas.canvas()
b = path.curve(0, 0, 0, 0.5, 0, 1, 4, 4).normpath()
l = path.line(*(b.atbegin() + b.atend()))
c.draw(l, [deco.shownormpath()])
c.draw(b, [deco.shownormpath()])
mark(c, "A", 180, 0, 0)
mark(c, "B", 180, 0, 0.5)
mark(c, "C", 180, 0, 1)
mark(c, "D", 0, 4, 4)
mark(c, "Y", -45, 2, 2)
mark(c, "X", 90, *b.at(normpathparam(b, 0, 0.5)))
mark(c, "X'", 135, *b.at(0.5*b.arclen()))
c.writeEPSfile("beziertoline")
