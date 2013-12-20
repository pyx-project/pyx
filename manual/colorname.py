#!/usr/bin/env python
import imp, re
import pyx
from pyx import *

text.set(text.LatexRunner)
text.preamble(r"\renewcommand{\familydefault}{\ttdefault}")
c = canvas.canvas()

# positioning is quite ugly ... but it works at the moment
x = 0
y = 0
dx = 4.8
dy = -0.65
lastmodel = 0

# we could use (gray|rgb|cmyk).__dict__ to get the instances, but we
# would loose the ordering ... instead we just parse the file:

# TODO: code something along the lines of c.l.p post cbs38g$2kp$04$1@news.t-online.com

p = re.compile("(?P<id>(?P<model>[a-z]+)\\.(?P<name>[a-z]+)) += (?P=model)\\([0-9\\., ]+\\)\n", re.IGNORECASE)
lines = imp.find_module("color", pyx.__path__)[0].readlines()
for line in lines: # we yet don't use a file iterator
    m = p.match(line)
    if m:
        if lastmodel and (m.group("model") != lastmodel):
           y += dy
        myc = pyx.color.__dict__[m.group("model")].__dict__[m.group("name")]
        c.stroke(path.line(x + 0.1, y + 0.1, x + 0.4, y + 0.4), [myc])
        c.stroke(path.line(x + 0.4, y + 0.1, x + 0.1, y + 0.4), [myc])
        c.fill(path.rect(x + 0.5, y, 1, 0.5), [myc])
        c.stroke(path.line(x + 0.6, y + 0.1, x + 0.9, y + 0.4), [color.gray.black])
        c.stroke(path.line(x + 0.9, y + 0.1, x + 0.6, y + 0.4), [color.gray.black])
        c.stroke(path.line(x + 1.1, y + 0.1, x + 1.4, y + 0.4), [color.gray.white])
        c.stroke(path.line(x + 1.4, y + 0.1, x + 1.1, y + 0.4), [color.gray.white])
        c.text(x + 1.7, y + 0.15, m.group("id"), [text.size.footnotesize])
        y += dy
        lastmodel = m.group("model")
        if y < -16.5:
            y = 0
            x += dx

c.writePDFfile()
