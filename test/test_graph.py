#!/usr/bin/env python
import sys
sys.path.append("..")
from pyx import *

c = canvas.canvas()
t = tex.tex()
g = c.insert(graph.graphxy(t, width=10, x=graph.logaxis(), y2=graph.linaxis()))
df = graph.datafile("testdata")
g.plot(graph.data(df, x=1, y=3))
g.plot(graph.data(df, x=1, y2=8))
c.insert(t)
c.writetofile("test_graph")
