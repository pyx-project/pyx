# When stacking bars on top of each other you can
# either specify the end values of the bars (default)
# or set the addontop argument of the stackedbarpos
# style as shown in this example.

from pyx import *

g = graph.graphxy(width=8, x=graph.axis.bar())
g.plot(graph.data.list([(i, i, 1) for i in range(1, 10)],
                       xname=1, y=2, stack=3),
       [graph.style.bar(),
        graph.style.stackedbarpos("stack", addontop=1),
        graph.style.bar([color.rgb.green])])
g.writeEPSfile("addontop")
