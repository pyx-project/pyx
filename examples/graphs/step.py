# extend module search path - not needed when PyX is installed properly
import sys; sys.path[:0] = ["../.."]

from pyx import *

def step(x, a):
    if a > 0:
        return x

c = canvas.canvas()
g = c.insert(graph.graphxy(width = 10))
df = data.datafile("step.dat", extern={"step": step})
df.addcolumn("y1a=step(y1, y1-0.02)")
df.addcolumn("y1b=step(y1, 0.02-y1)")
df.addcolumn("y2a=step(y2, x-1)")
df.addcolumn("y2b=step(y2, 1-x)")
g.plot(graph.data(df, x=1, y="y1a"), graph.line(color.rgb.red))
g.plot(graph.data(df, x=1, y="y1b"), graph.line(color.rgb.blue))
g.plot(graph.data(df, x=1, y="y2a"), graph.line(color.rgb.red))
g.plot(graph.data(df, x=1, y="y2b"), graph.line(color.rgb.blue))
g.finish()
c.writetofile("step")

