import random
from pyx import *

# introduce a new symbol style where size and color are given by some data
class changesymbol(graph.style.symbol):

    def __init__(self, sizename="size", colorname="color",
                       palette=color.palette.Rainbow, **kwargs):
        # add some configuration parameters
        self.sizename = sizename
        self.colorname = colorname
        self.palette = palette
        graph.style.symbol.__init__(self, **kwargs)

    def columnnames(self, privatedata, sharedata, agraph, columnnames):
        # register the new column names
        if self.sizename not in columnnames:
            raise ValueError("column '%s' missing" % self.sizename)
        if self.colorname not in columnnames:
            raise ValueError("column '%s' missing" % self.colorname)
        return ([self.sizename, self.colorname] +
                graph.style.symbol.columnnames(self, privatedata,
                                               sharedata, agraph, columnnames))

    def drawpoint(self, privatedata, sharedata, agraph):
        # replace the original drawpoint method by a slightly revised one
        if sharedata.vposvalid and privatedata.symbolattrs is not None:
            xpos, ypos = agraph.vpos_pt(*sharedata.vpos)
            color = self.palette.getcolor(sharedata.point[self.colorname])
            privatedata.symbol(privatedata.symbolcanvas, xpos, ypos,
                               privatedata.size_pt*sharedata.point[self.sizename],
                               privatedata.symbolattrs + [color])

g = graph.graphxy(width=10)
g.plot(graph.data.list([[random.random() for i in range(4)]
                        for i in range(1000)],
                       x=1, y=2, size=3, color=4),
       [changesymbol()])
g.writeEPSfile("changesymbol")
