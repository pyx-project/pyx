#!/usr/bin/env python

from path import *
import types, re, tex

class _Map:
    def convert(self, Values):
        if type(Values) in (types.IntType, types.LongType, types.FloatType, ):
            return self._convert(Values)
        else:
            return map(lambda x, self = self: self._convert(x), Values)

    def invert(self, Values):
        if type(Values) in (types.IntType, types.LongType, types.FloatType, ):
            return self._invert(Values)
        else:
            return map(lambda x, self = self: self._invert(x), Values)

class _LinMap(_Map):
    def set(self, m, n):
        self.m = float(m)
        self.n = float(n)
        return self
    def _convert(self, Value):
        return self.m * Value + self.n
    def _invert(self, Value):
        return (Value - self.n) / self.m


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


class LinAxis(_LinMap):

    def __init__(self, Min = None, Max = None):
        self.Min = None
        self.Max = None
        if Min:
            self.Min = Min
            self.InitMin = 1
        else:
            self.InitMin = 0
        if Max:
            self.Max = Max
            self.InitMax = 1
        else:
            self.InitMax = 0
        self.set(self.Min, self.Max)

    def set(self, Min = None, Max = None):
        if Min and not self.InitMax:
            self.Min = Min
        if Max and not self.InitMax:
            self.Max = Max
        if self.Min and self.Max:
            _LinMap.set(self, 1 / float(self.Max - self.Min), -self.Min / float(self.Max - self.Min))

    def TickValPosList(self):
        self.TickStart = self.Min
        self.TickCount = 5
        self.TickDist = (self.Max - self.Min) / float(self.TickCount - 1)
        return map(lambda x, self=self: self.TickStart + x * self.TickDist, range(self.TickCount))

    def ValToLab(self, x):
        return "%.3f" % x

    def TickList(self):
        return map(lambda x, self=self: Tick(x, self.convert(x), self.ValToLab(x)), self.TickValPosList())


###############################################################################
# graph part

class Graph:

    def __init__(self, canvas, tex, x, y):
        self.canvas = canvas
        self.tex = tex
        self.x = x
        self.y = y

class _PlotData:
    def __init__(self, Data, PlotStyle):
        self.Data = Data
        self.PlotStyle = PlotStyle

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

    def plot(self, Data, PlotStyle = None):
        if not PlotStyle:
            PlotStyle = Data.DefaultPlotStyle
        self.plotdata.append(_PlotData(Data, PlotStyle))
    
    def run(self):

        for key in self.Axis.keys():
            ranges = []
            for pd in self.plotdata:
                try:
                    ranges.append(pd.Data.GetRange(key))
                except DataRangeUndefinedException:
                    pass
            if len(ranges) == 0:
                assert 0, "range for %s-axis unknown" % key
            self.Axis[key].set(min( map (lambda x: x[0], ranges)),
                               max( map (lambda x: x[1], ranges)))

        for pd in self.plotdata:
            pd.Data.SetAxis(self.Axis)

        # this should be done after axis-size calculation
        self.left = 1   # convert everything to plain numbers here already, no length !!!
        self.buttom = 1 # should we use the final postscript points already ???
        self.top = 0
        self.right = 0
        self.VirMap = (_LinMap().set(self.width - self.left - self.right, self.x + self.left),
                       _LinMap().set(self.height - self.buttom - self.left, self.y + self.buttom), )

        self.canvas.draw(rect(self.VirMap[0].convert(0),
                              self.VirMap[1].convert(0),
                              self.VirMap[0].convert(1) - self.VirMap[0].convert(0),
                              self.VirMap[1].convert(1) - self.VirMap[1].convert(0)))

        for key in self.Axis.keys():
            if _XPattern.match(key):
                Type = 0
            elif _YPattern.match(key):
                Type = 1
            else:
                assert 0, "Axis key %s not allowed" % key
            for tick in self.Axis[key].TickList():
                xv = tick.VirtualPos
                l = tick.Label
                x = self.VirMap[Type].convert(xv)
                if Type == 0:
                    self.canvas.draw(line(x, self.VirMap[1].convert(0), x, self.VirMap[1].convert(0) + 0.2))
                    self.tex.text(x, self.VirMap[1].convert(0)-0.5, l, tex.halign.center)
                if Type == 1:
                    self.canvas.draw(line(self.VirMap[0].convert(0), x, self.VirMap[0].convert(0) + 0.2, x))
                    self.tex.text(self.VirMap[0].convert(0)-0.5, x, l, tex.halign.right)

        for pd in self.plotdata:
            pd.PlotStyle.LoopOverPoints(self, pd.Data)

    def VirToPos(self, Type, List):
        return self.VirMap[Type].convert(List)

    def ValueList(self, Pattern, Type, Data):
        (key, ) = filter(lambda x, Pattern = Pattern: Pattern.match(x), Data.GetKindList())
        return self.VirToPos(Type, self.Axis[key].convert(Data.GetValues(key)))



###############################################################################
# draw styles -- planed are things like:
#     * chain
#         just connect points by lines
#     * mark
#         place markers at the points
#         there is a hole lot of specialized markers (derived from mark):
#             * text-mark (put a text (additional column!) there)
#             * fill/size-mark (changes filling or size of the marker by an additional column)
#             * vector-mark (puts a small vector with direction given by an additional column)
#     * bar

class _PlotStyle:

    pass

class chain(_PlotStyle):

    def LoopOverPoints(self, Graph, Data):
        p = [ ]
        for pt in zip(Graph.ValueList(_XPattern, 0, Data),
                      Graph.ValueList(_YPattern, 1, Data)):
            if p:
                p.append(lineto(pt[0],pt[1]))
            else:
                p = [moveto(pt[0],pt[1]), ]
        Graph.canvas.draw(path(p))

class mark(_PlotStyle):

    def __init__(self, size = 0.05):
        self.size = size

    def LoopOverPoints(self, Graph, Data):
        for pt in zip(Graph.ValueList(_XPattern, 0, Data),
                      Graph.ValueList(_YPattern, 1, Data)):
            Graph.canvas.draw(path([moveto(pt[0] - self.size, pt[1] - self.size),
                                    lineto(pt[0] + self.size, pt[1] + self.size),
                                    moveto(pt[0] - self.size, pt[1] + self.size),
                                    lineto(pt[0] + self.size, pt[1] - self.size), ]))

###############################################################################
# data part

from mathtree import *
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

    DefaultPlotStyle = mark()

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

    DefaultPlotStyle = chain()
    
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
                values.append(self.XAxis[key].invert(x * 1.0 / self.Points))
            self.XValues[key] = values
        # this isn't smart ... we should try to make self.MT.Calc(..., i) faster (walk only once throu the tree)
        self.YValues = map(lambda i, self = self: self.MT.Calc(self.XValues, i), range(self.Points + 1))

    def GetValues(self, Kind, DefaultResult = "y"):
        if (self.ResKind and (Kind == self.ResKind)) or ((not self.ResKind) and (Kind == DefaultResult)):
            return self.YValues
        return self.XValues[Kind]


class ParamFunction(Function):
    pass


