from pyx import *

a, b = 2, 9 # integral area

p = graph.axispainter(basepathattrs=deco.earrow.normal(),
                      titlepos=0.98, titledirection=None)
g = graph.graphxy(width=8, x2=None, y2=None,
                  x=graph.linaxis(title="$x$", min=0, max=10,
                                  part=[graph.tick(a, label="$a$"),
                                        graph.tick(b, label="$b$")],
                                  painter=p),
                  y=graph.linaxis(title="$y$",
                                  part=None, painter=p))
style = g.plot(graph.function("y=(x-3)*(x-5)*(x-7)")).style
g.finish()

pa = g.xgridpath(a)
pb = g.xgridpath(b)
(splita,), (splitpa,) = style.path.intersect(pa)
(splitb,), (splitpb,) = style.path.intersect(pb)
area = (pa.split(splitpa)[0] <<
        style.path.split(splita, splitb)[1] <<
        pb.split(splitpb)[0].reversed())
area.append(path.closepath())
g.stroke(area, deco.filled(color.gray(0.8)))
g.text(g.pos(0.5 * (a + b), 0)[0], 1,
       r"\int_a^b f(x){\rm d}x", text.halign.center, text.mathmode)
g.writetofile("integral")

