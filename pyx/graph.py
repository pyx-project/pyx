#!/usr/bin/env python

from path import *
import types, re

###############################################################################
# axis part

class Tick:

    def __init__(self, ValuePos, VirtualPos, Label=None, TickLevel=1, LabelLevel=1):
        self.ValuePos = ValuePos
        self.VirtualPos = VirtualPos
        self.Label = Label
        self.TickLevel = TickLevel
        self.LabelLevel = LabelLevel


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

_XPattern = re.compile(r"x([2-9]|[1-9][0-9]+)?$")
_YPattern = re.compile(r"y([2-9]|[1-9][0-9]+)?$")
_DXPattern = re.compile(r"dx([2-9]|[1-9][0-9]+)?$")
_DYPattern = re.compile(r"dy([2-9]|[1-9][0-9]+)?$")

class GraphXY(Graph):

    plotdata = [ ]

    def __init__(self, canvas, tex, x, y, width, height, **Axis):
        Graph.__init__(self, canvas, tex, x, y)
        self.width = width
        self.height = height
        if "x" not in Axis.keys():
            Axis["x"] = LinAxis()
        if "y" not in Axis.keys():
            Axis["y"] = LinAxis()
        self.Axis = Axis

    def plot(self, data, style = None):
        self.plotdata.append(data)

    def VirToXPos(self, Values):
        if type(Values) in (types.IntType, types.LongType, types.FloatType, ):
            return self.x + 1 + Values * (self.width - 1)
        else:
            return map(lambda x, self = self: self.x + 1 + x * (self.width - 1), Values)

    def VirToYPos(self, Values):
        if type(Values) in (types.IntType, types.LongType, types.FloatType, ):
            return self.y + 1 + Values * (self.height - 1)
        else:
            return map(lambda y, self = self: self.y + 1 + y * (self.height - 1), Values)
    
    def run(self):
        self.VirToXPos(0.0)
        self.canvas.draw(rect(self.VirToXPos(0), self.VirToYPos(0), self.VirToXPos(1) - self.VirToXPos(0), self.VirToYPos(1) - self.VirToYPos(0)))

        for key in self.Axis.keys():
            ranges = []
            for pd in self.plotdata:
                try:
                    ranges.append(pd.GetRange(key))
                except DataRangeUndefinedException:
                    pass
            if len(ranges) == 0:
                assert 0, "range for %s unknown" % key
            self.Axis[key].Min = min( map (lambda x: x[0], ranges))
            self.Axis[key].Max = max( map (lambda x: x[1], ranges))
            print key, self.Axis[key].Min, self.Axis[key].Max

        for pd in self.plotdata:
            pd.SetAxis(self.Axis)

        #for tick in self.XAxis.TickList():
        #     xv = tick.VirtualPos
        #     l = tick.Label
        #     x = self.VirToXPos(xv)
        #     self.canvas.draw(line(x, self.VirToYPos(0), x, self.VirToYPos(0)+0.2))
        #     self.tex.text(x, self.VirToYPos(0)-0.5, l, halign=halign.center)
        #for tick in self.YAxis.TickList():
        #     yv = tick.VirtualPos
        #     l = tick.Label
        #     y = self.VirToYPos(yv)
        #     self.canvas.draw(line(self.VirToXPos(0), y, self.VirToXPos(0)+0.2, y))
        #     self.tex.text(self.VirToXPos(0)-0.2, y, l, halign=halign.right)

        for pd in self.plotdata:
            p = [ ]
            (xkey, ) = filter(lambda x: _XPattern.match(x), pd.GetKindList())
            (ykey, ) = filter(lambda y: _YPattern.match(y), pd.GetKindList())
            for pt in zip(self.VirToXPos(self.Axis[xkey].ValToVirt(pd.GetValues(xkey))),
                          self.VirToYPos(self.Axis[ykey].ValToVirt(pd.GetValues(ykey)))):
                if p:
                    p.append(lineto(pt[0],pt[1]))
                else:
                    p = [moveto(pt[0],pt[1]), ]
                pass
            # the following line is extremly time consuming !!!
            self.canvas.draw(path(p))


###############################################################################
# data part

from fit import *
import re

CommentPattern = re.compile(r"\s*(#|!)+\s*")

class DataFile:

    def __init__(self, FileName, sep = None, titlesep = None):
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
        if Kind not in self.columns.keys():
            raise DataRangeUndefinedException
        return (min(self.GetValues(Kind)), max(self.GetValues(Kind)), )

    def SetAxis(self, Axis):
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
            self.ResKind = None
        self.MT = ParseMathTree(ParseStr(Expression))
        self.VarList = self.MT.VarList()
    

    def GetName(self):
        return self.name
    
    def GetKindList(self, DefaultResult = "y"):
        if self.ResKind:
            return self.MT.VarList() + [self.ResKind, ]
        else:
            return self.MT.VarList() + [DefaultResult, ]
    
    def GetRange(self, Kind):
        raise DataRangeUndefinedException

    def SetAxis(self, Axis, DefaultResult = "y"):
        if self.ResKind:
            self.YAxis = Axis[self.ResKind]
        else:
            self.YAxis = Axis[DefaultResult]
        self.XAxis = { }
        self.XValues = { }
        for key in self.MT.VarList():
            self.XAxis[key] = Axis[key]
            values = []
            for x in range(self.Points + 1):
                values.append(self.XAxis[key].VirtToVal(x * 1.0 / self.Points))
            self.XValues[key] = values
        # this isn't smart ... we should try to make self.MT.Calc(..., i) faster (walk only once throu the tree)
        self.YValues = map(lambda i, self = self: self.MT.Calc(self.XValues, i), range(self.Points + 1))

    def GetValues(self, Kind, DefaultResult = "y"):
        if (self.ResKind and (Kind == self.ResKind)) or ((not self.ResKind) and (Kind == DefaultResult)):
            return self.YValues
        return self.XValues[Kind]


class ParamFunction(Function):
    pass

