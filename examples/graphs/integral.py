from pyx import *

a, b = 2, 9 # integral area

p = graph.painter.axispainter(basepathattrs=[deco.earrow.normal],
                              titlepos=0.98, titledirection=None)
g = graph.type.graphxy(width=8, x2=None, y2=None,
                       x=graph.axis.linaxis(title="$x$", min=0, max=10,
                                            manualticks=[graph.parter.tick(a, label="$a$"),
                                                         graph.parter.tick(b, label="$b$")],
                                            parter=None,
                                            painter=p),
                  y=graph.axis.linaxis(title="$y$", parter=None, painter=p))
d = g.plot(graph.data.function("y=(x-3)*(x-5)*(x-7)"))
g.finish()
p = d.path # the path is available after the graph is finished

pa = g.xgridpath(a)
pb = g.xgridpath(b)
(splita,), (splitpa,) = p.intersect(pa)
(splitb,), (splitpb,) = p.intersect(pb)
area = (pa.split([splitpa])[0] <<
        p.split([splita, splitb])[1] <<
        pb.split([splitpb])[0].reversed())
area.append(path.closepath())
g.stroke(area, [deco.filled([color.gray(0.8)])])
g.text(g.pos(0.5 * (a + b), 0)[0], 1,
       r"\int_a^b f(x){\rm d}x", [text.halign.center, text.mathmode])
g.writeEPSfile("integral")

