from pyx import *

mypainter = graph.axis.painter.regular(outerticklength=graph.axis.painter.ticklength.normal,
                                       basepathattrs=[style.linewidth.THick, deco.earrow.large])

c = graph.axis.pathaxis(path.curve(0, 0, 3, 0, 1, 4, 4, 4),
                        graph.axis.linear(min=0, max=11, title="axis title", painter=mypainter))
c.writeEPSfile("painter")
c.writePDFfile("painter")
c.writeSVGfile("painter")
