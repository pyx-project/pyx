#!/usr/bin/env python

from path import *
from const import *

###############################################################################
# axis part

class Axis:

    pass


class LinAxis:

    Min = -10
    Max = 10
    TickStart = -10
    TickCount = 5
    TickDist = 5

    def TickList(self):
        return map(lambda x,self=self: self.TickStart + x * self.TickDist, range(self.TickCount))

    def TickPosList(self):
        return self.ValueToVirtual(self.TickList())

    def TickPosLabelDict(self):
        result = { }
        for x in self.TickList():
            result[self.ValueToVirtual(x)] = str(x)
        return result

    def ValueToVirtual(self, Values):
        if isnumber(Values):
            return (Values - self.Min)/float(self.Max - self.Min)
        else:
            return map(lambda x,self=self: (x - self.Min)/float(self.Max - self.Min), Values)

    def VirtualToValue(self, Values):
        if isnumber(Values):
            return self.Min + Values * (self.Max - self.Min)
        else:
            return map(lambda x,self=self: self.Min + x * (self.Max - self.Min), Values)

###############################################################################
# graph part

class Graph:

    def __init__(self, canvas, tex, x, y):
        self.canvas = canvas
        self.tex = tex
        self.x = x
        self.y = y


class GraphXY(Graph):

    #plotdata = [ ]

    def __init__(self, canvas, tex, x, y, width, height):
        Graph.__init__(self, canvas, tex, x, y)
        self.width = width
        self.height = height
        self.XAxis = LinAxis()
        self.YAxis = LinAxis()

    #def plot(self, Data, style)
        #plotdata.append( {pd_data: Data, pd_style: style} )

    def XPos(self, Values):
        if isnumber(Values):
            return self.x + 1 + Values * (self.width - 1)
        else:
            return map(lambda x,self=self: self.x + 1 + x * (self.width - 1), Values)

    def YPos(self, Values):
        if isnumber(Values):
            return self.y + 1 + Values * (self.height - 1)
        else:
            return map(lambda y,self=self: self.y + 1 + y * (self.height - 1), Values)
    
    def run(self):
        self.XPos(0.0)
        p=path([moveto(self.XPos(0),self.YPos(0)),
                lineto(self.XPos(1),self.YPos(0)),
                lineto(self.XPos(1),self.YPos(1)),
                lineto(self.XPos(0),self.YPos(1)),
                closepath()])
        self.canvas.draw(p)
        for x in self.XPos(self.XAxis.TickPosList()):
             self.canvas.draw(line(x,self.YPos(0),x,self.YPos(0)+0.2))
        for x in self.XAxis.TickPosLabelDict().keys():
             self.tex.text(self.XPos(x),self.YPos(0)-0.5,self.XAxis.TickPosLabelDict()[x], halign=center)
        for y in self.YPos(self.YAxis.TickPosList()):
             self.canvas.draw(line(self.XPos(0),y,self.XPos(0)+0.2,y))
        for y in self.YAxis.TickPosLabelDict().keys():
             self.tex.text(self.XPos(0)-0.2,self.YPos(y),self.YAxis.TickPosLabelDict()[y], halign=right)
        #for pd in self.plotdata:
        #    for Data in pd[pd_data]


class GraphRPhi:

    def __init__(self, canvas, x, y, r):
        Graph.__init__(canvas, x, y)


###############################################################################
# data part
