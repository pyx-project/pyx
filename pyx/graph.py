#!/usr/bin/env python

from path import *
from const import *
import types

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
    TickCount = 0
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
        self.XAxis.Min = 0
        self.XAxis.Max = 30
        self.YAxis.Min = 0
        self.YAxis.Max = 0.01

    def plot(self, data, style = None):
        self.plotdata.append((data, style))

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
             self.tex.text(x, self.YPos(0)-0.5, l, halign=halign.center)
        for tick in self.YAxis.TickList():
             yv = tick.VirtualPos
             l = tick.Label
             y = self.YPos(yv)
             self.canvas.draw(line(self.XPos(0), y, self.XPos(0)+0.2, y))
             self.tex.text(self.XPos(0)-0.2, y, l, halign=halign.right)
        for pd in self.plotdata:
             p = None
             for pt in zip(self.XPos(self.XAxis.ValueToVirtual(pd[0].GetValues("x"))),
                           self.YPos(self.YAxis.ValueToVirtual(pd[0].GetValues("y")))):
                 if p:
                     p.append(lineto(pt[0],pt[1]))
                 else:
                     p = [moveto(pt[0],pt[1]), ]
             print p
             self.canvas.draw(path(p))
             # path.__init__(self, [ moveto(x1,y1), lineto(x2, y2) ] )
             #for i in range(201):
             #    x = (i-100)/10.0
             #    y = pd[0].MT.Calc({'x':x})
             #    xnew = self.XPos(self.XAxis.ValueToVirtual(x))
             #    ynew = self.YPos(self.YAxis.ValueToVirtual(y))
             #    if i > 0:
             #        self.canvas.draw(line(xold, yold, xnew, ynew))
             #    xold = xnew
             #    yold = ynew


###############################################################################
# data part

from fit import *
import re

CommentPattern = re.compile(r"\s*(#|!)")
EntryPattern = re.compile(r"\s+")

KindTypeColumn = 1

class DataFile:

    def __init__(self, FileName, sep = None, titlesep = None):
        # TODO 9: title in comment above data
        # read data file -> create KindTypeColumn
        self.FileName = FileName
        File = open(FileName, "r")
        Lines = File.readlines()
        self.Columns = 0
        self.Rows = 0
        self.data = []
        for Line in Lines:
            if not CommentPattern.match(Line):
                if sep:
                    Row = Line.split(sep)
                else:
                    Row = Line.split()
                if self.Columns < len(Row):
                    for i in range(self.Columns, len(Row)):
                        # create new lists for each column in order to avoid side effects in append
                        self.data.append(reduce(lambda x,y: x + [None, ], range(self.Rows), []))
                    self.Columns = len(Row)
                for i in range(len(Row)):
                    try:
                        self.data[i].append(float(Row[i]))
                    except ValueError:
                        self.data[i].append(Row[i])
                for i in range(len(Row), self.Columns):
                    self.data[i].append(None)
                self.Rows = self.Rows + 1
        self.HasTitles = 0
        for i in range(self.Columns):
            if type(self.data[i][0]) in (types.IntType, types.LongType, types.FloatType, ):
                break
        else:
            self.HasTitles = 1
        if self.HasTitles:
            self.titles = []
            for i in range(self.Columns):
                self.titles.append(self.data[i][0])
                del self.data[i][0]
        else:
            self.titles = reduce(lambda x,y: x + [None, ], range(self.Columns), [])

    def GetTitle(self, Number):
        return self.titles[Number]

    def GetColumn(self, Number):
        return self.data[Number]

KindTypeX = 1
KindTypeY = 2
KindTypeDX = 3
KindTypeDY = 4

class Data:

    def __init__(self, datafile, **columns):
        self.datafile = datafile
        self.columns = columns

    def GetKindList(self):
        return self.columns.keys()

    def GetValues(self, Kind):
        return self.datafile.GetColumn(self.columns[Kind])

    def GetRange(self, Kind):
        return (min(self.GetValues(Kind)), max(self.GetValues(Kind)), )

    def GetName(self):
        return self.datafile.FileName

    def GetTitle(self, Kind):
        return self.datafile.GetTitle(self.columns[Kind])

class Function:

    def __init__(self, Expression):
        self.MT = ParseMathTree(ParseStr(Expression))


if __name__=="__main__":
    df = DataFile("testdata")
    for i in range(df.Columns):
        print df.GetTitle(i),len(df.GetColumn(i)),df.GetColumn(i)
    d = Data(df, x=0, y=1)
    print d.GetKindList()
    print d.GetValues("x")
    print d.GetValues("y")
    print d.GetRange("x"), d.GetRange("y")
    print d.GetName()
    print d.GetTitle("x"), d.GetTitle("y")

