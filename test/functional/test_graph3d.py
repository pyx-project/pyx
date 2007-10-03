#!/usr/bin/env python
import sys; sys.path[:0] = ["../.."]

import math
from pyx import *

text.set(mode="latex")

def test_minimal(c, x, y):
    g = c.insert(graph.graphxyz(x, y, size=3))
    g.plot(graph.data.file("data/husimi_small.dat", x=1, y=2, z=3))

def test_line(c, x, y):
    g = c.insert(graph.graphxyz(x, y, size=3))
    g.plot(graph.data.file("data/husimi_small.dat", x=1, y=2, z=3), [graph.style.line()])

def test_grid(c, x, y):
    g = c.insert(graph.graphxyz(x, y, size=3))
    g.plot(graph.data.file("data/husimi_small.dat", x=1, y=2, z=3), [graph.style.grid()])

def test_surface(c, x, y):
    g = c.insert(graph.graphxyz(x, y, size=3, x=graph.axis.lin(), y=graph.axis.lin(), x2=None, y2=None))
    g.plot(graph.data.file("data/husimi_small.dat", x=1, y=2, z=3, color=4), [graph.style.surface()])
    g.dodata()

def test_surface2d(c, x, y):
    g = c.insert(graph.graphxy(x, y, width=6, height=6))
    g.plot(graph.data.file("data/husimi_small.dat", x=1, y=2, color=3), [graph.style.surface()])
    g.dodata()

c = canvas.canvas()
test_minimal(c, 0, 0)
test_line(c, 0, -8)
test_grid(c, 8, 0)
test_surface(c, 8, -8)
test_surface2d(c, -3, -20)

c.writeEPSfile("test_graph3d", paperformat=document.paperformat.A4)
c.writePDFfile("test_graph3d", paperformat=document.paperformat.A4)

