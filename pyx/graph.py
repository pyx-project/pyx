#!/usr/bin/env python

from path import *
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

    def TickValPosList(self):
        return map(lambda x, self=self: self.TickStart + x * self.TickDist, range(self.TickCount))

    def ValToLab(self, x):
        return str(x)

    def TickList(self):
        return map(lambda x, self=self: Tick(x, self.ValToVirt(x), self.ValToLabel(x)), self.TickValPosList())

    def ValToVirt(self, Values):
        if type(Values) in (types.IntType, types.LongType, types.FloatType, ):
            return (Values - self.Min)/float(self.Max - self.Min)
        else:
            return map(lambda x, self=self: (x - self.Min)/float(self.Max - self.Min), Values)

    def VirtToVal(self, Values):
        if type(Values) in (types.IntType, types.LongType, types.FloatType, ):
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
        self.plotdata.append(data)

    def XPos(self, Values):
        if type(Values) in (types.IntType, types.LongType, types.FloatType, ):
            return self.x + 1 + Values * (self.width - 1)
        else:
            return map(lambda x,self=self: self.x + 1 + x * (self.width - 1), Values)

    def YPos(self, Values):
        if type(Values) in (types.IntType, types.LongType, types.FloatType, ):
            return self.y + 1 + Values * (self.height - 1)
        else:
            return map(lambda y,self=self: self.y + 1 + y * (self.height - 1), Values)
    
    def run(self):
        self.XPos(0.0)
        self.canvas.draw(rect(self.XPos(0), self.YPos(0), self.XPos(1) - self.XPos(0), self.YPos(1) - self.YPos(0)))
        xranges = []
        for pd in self.plotdata:
            try:
                xranges.append(pd.GetRange("x"))
            except DataRangeUndefinedException:
                pass
        if len(xranges) == 0:
            assert 0, "xrange unknown"
        self.XAxis.Min = min( map (lambda x: x[0], xranges))
        self.XAxis.Max = max( map (lambda x: x[1], xranges))

        for pd in self.plotdata:
            pd.SetXAxis({"x": self.XAxis, })

        yranges = []
        for pd in self.plotdata:
            try:
                yranges.append(pd.GetRange("y"))
            except DataRangeUndefinedException:
                pass
        if len(yranges) == 0:
            assert 0, "yrange unknown"
        self.YAxis.Min = min( map (lambda y: y[0], yranges))
        self.YAxis.Max = max( map (lambda y: y[1], yranges))

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
            for pt in zip(self.XPos(self.XAxis.ValToVirt(pd.GetValues("x"))),
                          self.YPos(self.YAxis.ValToVirt(pd.GetValues("y")))):
                if p:
                    p.append(lineto(pt[0],pt[1]))
                else:
                    p = [moveto(pt[0],pt[1]), ]
            self.canvas.draw(path(p))
            # path.__init__(self, [ moveto(x1,y1), lineto(x2, y2) ] )
            #for i in range(201):
            #    x = (i-100)/10.0
            #    y = pd[0].MT.Calc({'x':x})
            #    xnew = self.XPos(self.XAxis.ValToVirt(x))
            #    ynew = self.YPos(self.YAxis.ValToVirt(y))
            #    if i > 0:
            #        self.canvas.draw(line(xold, yold, xnew, ynew))
            #    xold = xnew
            #    yold = ynew


###############################################################################
# data part

from fit import *
import re

CommentPattern = re.compile(r"\s*(#|!)+\s*")

class DataFile:

    def __init__(self, FileName, sep = None, titlesep = None):
        # TODO 9: title in comment above data
        self.name = FileName
        File = open(FileName, "r")
        Lines = File.readlines()
        self.Columns = 0
        self.Rows = 0
        self.data = []
        for Line in Lines:
            Match = CommentPattern.match(Line)
            if not Match:
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
            else:
                if self.Rows == 0:
                    self.titleline = Line[Match.end(): ]
                    if sep:
                        self.titles = self.titleline.split(sep)
                    else:
                        self.titles = self.titleline.split()

    def GetTitle(self, Number):
        if (Number < len(self.titles)):
            return self.titles[Number]
        else:
            return None

    def GetColumn(self, Number):
        return self.data[Number]


class DataException(Exception):
    pass

class DataKindMissingException(DataException):
    pass

class DataRangeUndefinedException(DataException):
    pass

class DataRangeAlreadySetException(DataException):
    pass

class Data:

    def __init__(self, datafile, **columns):
        self.datafile = datafile
        self.columns = columns

    def GetName(self):
        return self.datafile.name

    def GetKindList(self):
        return self.columns.keys()

    def GetTitle(self, Kind):
        return self.datafile.GetTitle(self.columns[Kind] - 1)

    def GetValues(self, Kind):
        return self.datafile.GetColumn(self.columns[Kind] - 1)
    
    def GetRange(self, Kind):
        # handle non-numeric things properly
        return (min(self.GetValues(Kind)), max(self.GetValues(Kind)), )

    def SetXAxis(self, XAxis):
        pass


AssignPattern = re.compile(r"\s*([a-z][a-z0-9_]*)\s*=", re.IGNORECASE)

class Function:

    def __init__(self, Expression, Points = 100):
        self.name = Expression
        self.Points = Points
        Match = AssignPattern.match(Expression)
        if Match:
            self.ResKind = Match.group(1)
            Expression = Expression[Match.end(): ]
        else:
            self.ResKind = "y"
        self.MT = ParseMathTree(ParseStr(Expression))
        self.VarList = self.MT.VarList()
    

    def GetName(self):
        return self.name
    
    def GetKindList(self, DefaultResult = 'y'):
        if self.ResKind:
            return self.MT.VarList() + [self.ResKind, ]
        else:
            return self.MT.VarList() + [DefaultResult, ]
    
    def GetRange(self, Kind):
        raise DataRangeUndefinedException
        # try to get y range after x range was set

    def SetXAxis(self, XAxis):
        self.XAxis = XAxis
        self.XValues = []
        for x in range(self.Points + 1):
            self.XValues.append(self.XAxis["x"].VirtToVal(x * 1.0 / self.Points))
        self.YValues = map(lambda x, self=self: self.MT.Calc({"x": x, }), self.XValues)

    def GetValues(self, Kind):
        if Kind == "x":
            return self.XValues
        if Kind == self.ResKind:
            return self.YValues
    
class ParamFunction(Function):
    pass

if __name__=="__main__":
    print Function("sin(x)").GetKindList()
    #df = DataFile("testdata")
    #for i in range(df.Columns):
    #    print df.GetTitle(i),len(df.GetColumn(i)),df.GetColumn(i)
    #d = Data(df, x=0, y=1)
    #print d.GetKindList()
    #print d.GetValues("x")
    #print d.GetValues("y")
    #print d.GetRange("x"), d.GetRange("y")
    #print d.GetName()
    #print d.GetTitle("x"), d.GetTitle("y")

