#!/usr/bin/env python
import sys, imp, re
sys.path.append("..")
import pyx
from pyx import *

c = canvas.canvas()
t = tex.latex()
t.define(r"\renewcommand{\familydefault}{\ttdefault}")
p = re.compile("([a-z]+)\\.([a-z]+) += ([a-z]+)\\([0-9\\., ]+\\)\n", re.IGNORECASE)
lines = imp.find_module("color", pyx.__path__)[0].readlines()
x = 0
y = 0
dx = 4.8
dy = -0.65
oldg0 = 0
for line in lines:
    m = p.match(line)
    if m:
        g = m.groups()
        if g[0] == g[2]:
            if oldg0 and (g[0] != oldg0):
                y += dy
            myc = pyx.color.__dict__[g[0]].__dict__[g[1]]
            c.draw(path.line(x + 0.1, y + 0.1, x + 0.4, y + 0.4), myc)
            c.draw(path.line(x + 0.4, y + 0.1, x + 0.1, y + 0.4), myc)
            c.fill(path.rect(x + 0.5, y, 1, 0.5), myc)
            c.draw(path.line(x + 0.6, y + 0.1, x + 0.9, y + 0.4), color.grey.black)
            c.draw(path.line(x + 0.9, y + 0.1, x + 0.6, y + 0.4), color.grey.black)
            c.draw(path.line(x + 1.1, y + 0.1, x + 1.4, y + 0.4), color.grey.white)
            c.draw(path.line(x + 1.4, y + 0.1, x + 1.1, y + 0.4), color.grey.white)
            t.text(x + 1.7, y + 0.15, "%s.%s" % (g[0], g[1]), tex.fontsize.footnotesize)
            y += dy
            oldg0 = g[0]
            if y < -16:
                y = 0
                x += dx

c.insert(t)
c.writetofile("colorname")
