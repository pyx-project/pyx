#!/usr/bin/env python

###############################################################################
# axis part

###############################################################################
# graph part

class Graph:

    def __init__(self, canvas, x, y):
        self.canvas = canvas
        self.x = x
        self.y = y


class GraphXY:

    plotdata = [ ]

    def __init__(self, canvas, x, y, width, height):
        Graph.__init__(canvas, x, y)
        self.width = width
        self.height = height

    def plot(self, Data, style)
        plotdata.append( {pd_data: Data, pd_style: style} )

    def run(self)
        for pd in self.plotdata:
            for Data in pd[pd_data]


class GraphRPhi:

    def __init__(self, canvas, x, y, r):
        Graph.__init__(canvas, x, y)


###############################################################################
# data part
