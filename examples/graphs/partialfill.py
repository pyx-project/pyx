# contributed by Michael Schindler

from math import sin
from pyx import *

c = canvas.canvas()

# get the lines from the graph
xax = graph.linaxis(min=-1, max=1.0, painter=None)
yax = graph.linaxis(min=-1.3, max=1.3, painter=None)
g = graph.graphxy(width=10, ratio=2, x=xax, y=yax)
fline = g.plot(graph.function("y=sin(1.0/(x**2+0.02122))", points=1001))
horiz = g.plot(graph.function("y=0.5*x", points=2))
g.dodata()

# intersect the lines
fline = path.normpath(fline.style.path)
horiz = path.normpath(horiz.style.path)
splith, splitf = horiz.intersect(fline)

# create gray area
area = horiz.split(splith[0])[0]
for i in range(0, len(splith)-2, 2):
    area = area.glue(fline.split(splitf[i], splitf[i+1])[1])
    area = area.glue(horiz.split(splith[i+1], splith[i+2])[1])
area = area.glue(fline.split(splitf[-2], splitf[-1])[1])
area = area.glue(horiz.split(splith[-1])[1])
area.append(path.lineto(*g.vpos(1, 0)))
area.append(path.lineto(*g.vpos(0, 0)))
area.append(path.closepath())

# draw first the area, then the function
c.fill(area, color.gray(0.6))
c.stroke(fline, canvas.linewidth.Thick, canvas.linejoin.round)

c.writetofile("partialfill")
