#!/usr/bin/env python
import sys, imp, re
sys.path.append("..")
import pyx
from pyx import *

c = canvas.canvas()
t = tex.latex()
t.define(r"\renewcommand{\familydefault}{\ttdefault}")

# positioning is quite ugly ... but it works at the moment
x = 0
y = 0
dx = 4.8
dy = -0.65
lastmodel = 0

# we could use (gray|rgb|cmyk).__dict__ to get the instances, but we
# would loose the ordering ... instead we just parse the file:
p = re.compile("(?P<id>(?P<model>[a-z]+)\\.(?P<name>[a-z]+)) += (?P=model)\\([0-9\\., ]+\\)\n", re.IGNORECASE)
lines = imp.find_module("color", pyx.__path__)[0].readlines()
for line in lines: # we yet don't use a file iterator
    m = p.match(line)
    if m:
        if lastmodel and (m.group("model") != lastmodel):
           y += dy
        myc = pyx.color.__dict__[m.group("model")].__dict__[m.group("name")]
        c.stroke(path.line(x + 0.1, y + 0.1, x + 0.4, y + 0.4), myc)
        c.stroke(path.line(x + 0.4, y + 0.1, x + 0.1, y + 0.4), myc)
        c.fill(path.rect(x + 0.5, y, 1, 0.5), myc)
        c.stroke(path.line(x + 0.6, y + 0.1, x + 0.9, y + 0.4), color.gray.black)
        c.stroke(path.line(x + 0.9, y + 0.1, x + 0.6, y + 0.4), color.gray.black)
        c.stroke(path.line(x + 1.1, y + 0.1, x + 1.4, y + 0.4), color.gray.white)
        c.stroke(path.line(x + 1.4, y + 0.1, x + 1.1, y + 0.4), color.gray.white)
        t.text(x + 1.7, y + 0.15, m.group("id"), tex.fontsize.footnotesize)
        y += dy
        lastmodel = m.group("model")
        if y < -16:
            y = 0
            x += dx

c.insert(t)
c.writetofile("colorname")
