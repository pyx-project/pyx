# contributed by Michael Schindler

from pyx import *

# get the lines from the graph
xax = graph.axis.linear(min=-1, max=1.0, painter=None)
yax = graph.axis.linear(min=-1.3, max=1.3, painter=None)
g = graph.graphxy(width=10, ratio=2, x=xax, y=yax)
fline = g.plot(graph.data.function("y=sin(1.0/(x**2+0.02122))", points=1000))
horiz = g.plot(graph.data.function("y=0.5*x", points=2))
g.finish()

# convert paths to normpaths (for efficiency reasons only)
fline = fline.path.normpath()
horiz = horiz.path.normpath()
# intersect the lines
splith, splitf = horiz.intersect(fline)

# create gray area (we do not use simple clipping)
area = horiz.split([splith[0]])[0]
for i in range(0, len(splith)-2, 2):
    area = area.joined(fline.split([splitf[i], splitf[i+1]])[1])
    area = area.joined(horiz.split([splith[i+1], splith[i+2]])[1])
area = area.joined(fline.split([splitf[-2], splitf[-1]])[1])
area = area.joined(horiz.split([splith[-1]])[1])
area[-1].append(path.normline(*(area[-1].end_pt() + g.vpos_pt(1, 0))))
area[-1].append(path.normline(*(area[-1].end_pt() + g.vpos_pt(0, 0))))
area[-1].close()

c = canvas.canvas()

# draw first the area, then the function
c.fill(area, [color.gray(0.6)])
c.stroke(fline, [style.linewidth.Thick, style.linejoin.round])

c.writeEPSfile("partialfill")
