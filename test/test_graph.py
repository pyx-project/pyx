#!/usr/bin/env python
import sys
sys.path.append("..")
from pyx import *

c = canvas.canvas()
t = tex.tex()
g = c.insert(graph.graphxy(t, width=10, x=graph.logaxis(title="$W$"), y=graph.logaxis(title="$P$")))
df = graph.datafile("testdata")
g.plot(graph.data(df, x=1, y=3))
g.plot(graph.data(df, x=1, y=4))
g.plot(graph.data(df, x=1, y=5))
g.plot(graph.data(df, x=1, y=6))
g.plot(graph.data(df, x=1, y=7))
g.plot(graph.data(df, x=1, y=8))
c.insert(t)
c.writetofile("test_graph")
