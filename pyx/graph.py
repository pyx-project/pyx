#!/usr/bin/env python

from path import *
from const import *

###############################################################################
# axis part

class Tick:

    def __init__(self, ValuePos, VirtualPos, Label=None, TickLevel=1, LabelLevel=1):
        self.ValuePos = ValuePos
        self.VirtualPos = VirtualPos
        self.TickLevel = TickLevel
        self.Label = Label


class Axis:

    pass


class LinAxis:

    Min = -10
    Max = 10
    TickStart = -10
    TickCount = 5
    TickDist = 5

    def TickValuePosList(self):
        return map(lambda x, self=self: self.TickStart + x * self.TickDist, range(self.TickCount))

    def ValueToLabel(self, x):
        return str(x)

    def TickList(self):
        return map(lambda x, self=self: Tick(x, self.ValueToVirtual(x), self.ValueToLabel(x)), self.TickValuePosList())

    def ValueToVirtual(self, Values):
        if isnumber(Values):
            return (Values - self.Min)/float(self.Max - self.Min)
        else:
            return map(lambda x, self=self: (x - self.Min)/float(self.Max - self.Min), Values)

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

    plotdata = [ ]

    def __init__(self, canvas, tex, x, y, width, height):
        Graph.__init__(self, canvas, tex, x, y)
        self.width = width
        self.height = height
        self.XAxis = LinAxis()
        self.YAxis = LinAxis()

    def plot(self, data, style = None):
        self.plotdata.append( {'pd_data': data, 'pd_style': style} )

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
        for tick in self.XAxis.TickList():
             xv = tick.VirtualPos
             l = tick.Label
             x = self.XPos(xv)
             self.canvas.draw(line(x, self.YPos(0), x, self.YPos(0)+0.2))
             self.tex.text(x, self.YPos(0)-0.5, l, halign=center)
        for tick in self.YAxis.TickList():
             yv = tick.VirtualPos
             l = tick.Label
             y = self.YPos(yv)
             self.canvas.draw(line(self.XPos(0), y, self.XPos(0)+0.2, y))
             self.tex.text(self.XPos(0)-0.2, y, l, halign=right)
        for pd in self.plotdata:
             for i in range(201):
                 x = (i-100)/10.0
                 y = pd['pd_data'].MT.Calc({'x':x})
                 xnew = self.XPos(self.XAxis.ValueToVirtual(x))
                 ynew = self.YPos(self.YAxis.ValueToVirtual(y))
                 if i > 0:
                     self.canvas.draw(line(xold, yold, xnew, ynew))
                 xold = xnew
                 yold = ynew

class GraphRPhi:

    def __init__(self, canvas, x, y, r):
        Graph.__init__(canvas, x, y)


###############################################################################
# data part

from fit import *

class Function:

    def __init__(self, Expression):
        self.MT = ParseMathTree(ParseStr(Expression))

