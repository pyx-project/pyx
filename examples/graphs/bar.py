from pyx import *                   # bar.dat looks like:
                                    # #month    min max
                                    # January    -5   1
                                    # Feburary   -4   3
# we prepare some stuff first                   ...
bap = graph.baraxispainter # just a abbreviation
a1 = graph.baraxis(painter=bap(nameattrs=None)) # for single bars
a2 = graph.baraxis(painter=bap(nameattrs=(trafo.rotate(45),
                                          text.halign.right),
                                          innerticklength=0.2),
                   subaxis=graph.baraxis(dist=0)) # for several bars
df = data.datafile("bar.dat") # read the datafile just once
d = [graph.data(df, x="month", y="min"), graph.data(df, x=1, y=3)]
nofirst = (graph.changesequence(None, canvas.stroked(color.gray.black)),
           graph.changesequence(None, color.rgb.green)) # special draw attrs

c = canvas.canvas() # we draw several plots, thus we create a main canvas
g = c.insert(graph.graphxy(ypos=4.5, width=8, height=4, x=a1))
g.plot(d, graph.bar(stacked=1, barattrs=nofirst))
g.finish() # we explicitly finish the plot allow for a reuse of "d"
g2 = c.insert(graph.graphxy(width=8, x=a2, height=4))
g2.plot(d, graph.bar())
c.writetofile("bar")
