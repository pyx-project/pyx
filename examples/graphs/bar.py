from pyx import *                   # bar.dat looks like:
from pyx.graph import axis          # #month    min max
                                    # January    -5   1
                                    # Feburary   -4   3
# we prepare some stuff first                   ...
bap = axis.painter.bar # just an abbreviation
a1 = axis.bar(painter=bap(nameattrs=None)) # for single bars
a2 = axis.bar(painter=bap(nameattrs=[trafo.rotate(45),
                                     text.halign.right],
                                     innerticklength=0.2),
                        subaxis=axis.bar(dist=0)) # for several bars
nofirst = [attr.changelist([None, color.rgb.green])] # special draw attrs

c = canvas.canvas() # we draw several plots, thus we create a main canvas
g = c.insert(graph.graphxy(ypos=4.5, width=8, height=4, x=a1))
g.plot(graph.data.file("bar.dat", xname=1, y=2, ystack1=3), 
       [graph.style.bar(barattrs=nofirst)])
g2 = c.insert(graph.graphxy(width=8, x=a2, height=4))
g2.plot([graph.data.file("bar.dat", xname=1, y=2),
         graph.data.file("bar.dat", xname=1, y=3)], 
        [graph.style.bar()])
c.writeEPSfile("bar")
