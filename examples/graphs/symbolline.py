# contributed by Francisco Borges

from pyx import *
from pyx.graph import graphxy, data, axis
from pyx.graph.axis import painter, tick
from pyx.deco import earrow

range = 2.5

p = painter.regular(basepathattrs=[earrow.normal], titlepos=0.9,
                    titledirection=None) # Text always horizontal

g = graphxy(width=10,
            x2=None, y2=None, # Deleting some axis.
            x=axis.linear(title="$x$", min=-range, max=+range, painter=p,
                          manualticks=[tick.tick(range, None, None)]),
                          # suppress some ticks by overwriting
            y=axis.linear(title=r"$x\sin(x^2)$", painter=p,
                          manualticks=[tick.tick(3, None, None)]))

g.plot(data.function("y=x*sin(x**2)"),
       # Line style is set before symbol style -> symbols will be draw
       # above the line.
       [graph.style.line([style.linewidth.Thin, style.linestyle.solid]),
        graph.style.symbol(graph.style.symbol.circle, size=0.1,
                           symbolattrs=[deco.filled([color.rgb.green]),
                                        deco.stroked([color.rgb.red])])])

g.writeEPSfile(__file__[:-3])
