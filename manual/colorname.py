#!/usr/bin/env python
import sys, imp, re
sys.path.append("..")
import pyx
from pyx import *

c = canvas.canvas()
t = tex.latex()
t.define(r"\renewcommand{\familydefault}{\ttdefault}")
# colorlist = filter(lambda (x, y): isinstance(y, color.cmyk),
#                    color.cmyk.__dict__.items())
# colorlist.sort(lambda x, y: cmp(x[1].sort, y[1].sort))
p = re.compile("([a-z]+)\\.([a-z]+) += ([a-z]+)\\([0-9\\., ]+\\)\n", re.IGNORECASE)
lines = imp.find_module("color", pyx.__path__)[0].readlines()
x = 0
y = 0
dx = 5
dy = 0.68
for line in lines:
    m = p.match(line)
    if m:
        g = m.groups()
        if g[0] == g[2]:
            c.fill(path.rect(x, y, 0.5, 0.5), pyx.color.__dict__[g[0]].__dict__[g[1]])
            t.text(x+1, y, "%s.%s" % (g[0], g[1]))
            y += dy
            if y > 16.5:
                y = 0
                x += dx

c.insert(t)
c.writetofile("colorname")
