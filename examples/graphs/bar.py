from pyx import *                   # bar.dat looks like:
                                    # #month    min max
                                    # January    -5   1
                                    # Feburary   -4   3
# we prepare some stuff first                   ...
bap = graph.axis.painter.baraxispainter # just an abbreviation
a1 = graph.axis.baraxis(painter=bap(nameattrs=None)) # for single bars
a2 = graph.axis.baraxis(painter=bap(nameattrs=[trafo.rotate(45),
                                               text.halign.right],
                                               innerticklength=0.2),
                        subaxis=graph.axis.baraxis(dist=0)) # for several bars
df = data.datafile("bar.dat") # read the datafile just once
nofirst = [attr.changelist([None, color.rgb.green])] # special draw attrs

c = canvas.canvas() # we draw several plots, thus we create a main canvas
g = c.insert(graph.graphxy(ypos=4.5, width=8, height=4, x=a1))
g.plot(graph.data.data(df, xname=1, y=2, ystack1=3), graph.style.bar(barattrs=nofirst))
g2 = c.insert(graph.type.graphxy(width=8, x=a2, height=4))
g2.plot([graph.data.data(df, xname=1, y=2), graph.data.data(df, xname=1, y=3)], graph.style.bar())
c.writeEPSfile("bar")
