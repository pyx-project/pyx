#!/usr/bin/env python
import sys
sys.path[:0] = [".."]
from pyx import *

c = canvas.canvas()
t = tex.latex()
t.define(r"\renewcommand{\familydefault}{\ttdefault}")

# positioning is quite ugly ... but it works at the moment
x = 0
y = 0
dx = 6
dy = -0.65
length = 0.8

def drawdeco(name, showpath=0, default=0):
    global x,y
    p = path.path(path.moveto(x + 0.1, y+0.1 ),
                       path.rlineto(length/2.0, 0.3),
                       path.rlineto(length/2.0, -0.3))
    c.stroke(p, [style.linewidth.THIck,  eval("deco."+name)])
    if showpath:
        c.stroke(p, [style.linewidth.Thin, color.gray.white])
    if default:
        name = name + r"\rm\quad (default)"
    t.text(x + 1.5, y + 0.15, name, tex.fontsize.footnotesize)
    y += dy
    if y < -16:
        y = 0
        x += dx

drawdeco("earrow.SMall")
drawdeco("earrow.Small")
drawdeco("earrow.small")
drawdeco("earrow.normal")
drawdeco("earrow.large")
drawdeco("earrow.Large")
drawdeco("earrow.LArge")

y += dy

drawdeco("barrow.normal")

y += dy

drawdeco("earrow.Large([deco.filled([color.rgb.red]), style.linewidth.normal])")
drawdeco("earrow.normal(constriction=0)")
drawdeco("earrow.Large([style.linejoin.round])")

c.insert(t)
c.writetofile("arrows")
