from pyx import *

a, b = 2, 9 # integral area

p = graph.axis.painter.regular(basepathattrs=[deco.earrow.normal],
                               titlepos=0.98, titledirection=None)
ticks = [graph.axis.tick.tick(a, label="$a$"),
         graph.axis.tick.tick(b, label="$b$")]
g = graph.graphxy(width=8, x2=None, y2=None,
                  x=graph.axis.linear(title="$x$", min=0, max=10,
                                      manualticks=ticks,
                                      parter=None, painter=p),
                  y=graph.axis.linear(title="$y$", parter=None, painter=p))
d = g.plot(graph.data.function("y(x)=(x-3)*(x-5)*(x-7)"))
g.finish()
p = d.path # the path is available after the graph is finished

pa = g.xgridpath(a)
pb = g.xgridpath(b)
(splita,), (splitpa,) = p.intersect(pa)
(splitb,), (splitpb,) = p.intersect(pb)
area = (pa.split([splitpa])[0] <<
        p.split([splita, splitb])[1] <<
        pb.split([splitpb])[0].reversed())
area[-1].close()
g.stroke(area, [deco.filled([color.gray(0.8)])])
g.text(g.pos(0.5 * (a + b), 0)[0], 1,
       r"\int_a^b f(x){\rm d}x", [text.halign.center, text.mathmode])
g.writeEPSfile()
g.writePDFfile()
g.writeSVGfile()
