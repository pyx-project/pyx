from pyx import *

def step(x, a):
    if a > 0:
        return x

c = canvas.canvas()
g = c.insert(graph.graphxy(width = 10))
df = data.datafile("step.dat")
df.addcolumn("y1a=step(y1, y1-0.02)", context=locals())
df.addcolumn("y1b=step(y1, 0.02-y1)", context=locals())
df.addcolumn("y2a=step(y2, x-1)", context=locals())
df.addcolumn("y2b=step(y2, 1-x)", context=locals())
g.plot(graph.data(df, x=1, y="y1a"), graph.line(color.rgb.red))
g.plot(graph.data(df, x=1, y="y1b"), graph.line(color.rgb.blue))
g.plot(graph.data(df, x=1, y="y2a"), graph.line(color.rgb.red))
g.plot(graph.data(df, x=1, y="y2b"), graph.line(color.rgb.blue))
c.writetofile("step")

