#!/usr/bin/env python
import sys
sys.path.append("..")
from pyx import *

c = canvas.canvas()
# t = c.insert(tex.tex())
t = tex.tex()
g = c.insert(graph.graphxy(t, 10, 15, width=10, x=graph.logaxis()))
df = graph.datafile("testdata")
g.plot(graph.data(df, x=1, y=3))
c.writetofile("test_graph")
