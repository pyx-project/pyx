#!/usr/bin/env python
#
#
# Copyright (C) 2002 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2002 André Wobst <wobsta@users.sourceforge.net>
#
# This file is part of PyX (http://pyx.sourceforge.net/).
#
# PyX is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# PyX is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyX; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from path import *
import types, re, tex

class _Map:
    def setbasepts(self, basepts):
        """base points for convertion"""
        self.basepts = basepts
        return self

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
    def _convert(self, Value):
        return self.basepts[0][1] + ((self.basepts[1][1] - self.basepts[0][1]) /
               float(self.basepts[1][0] - self.basepts[0][0])) * (Value - self.basepts[0][0])
    def _invert(self, Value):
        return self.basepts[0][0] + ((self.basepts[1][0] - self.basepts[0][0]) /
               float(self.basepts[1][1] - self.basepts[0][1])) * (Value - self.basepts[0][1])

class _LogMap(_LinMap):
    def setbasepts(self, basepts):
        """base points for convertion"""
        self.basepts = ((math.log(basepts[0][0]), basepts[0][1], ),
                        (math.log(basepts[1][0]), basepts[1][1], ), )
        return self
    def _convert(self, Value):
        return _LinMap._convert(self, math.log(Value))
    def _invert(self, Value):
        return math.exp(_LinMap._invert(self, Value))
               


###############################################################################
# axis part

class Tick:

    def __init__(self, ValuePos, VirtualPos, Label = None, LabelRep = None, TickLevel = 1, LabelLevel = 1):
        if not LabelRep:
            LapelRep = Label
        self.ValuePos = ValuePos
        self.VirtualPos = VirtualPos
        self.Label = Label
        self.LabelRep = LabelRep
        self.TickLevel = TickLevel
        self.LabelLevel = LabelLevel


class _Axis:

    def __init__(self, Title = None, Min = None, Max = None):
        self.Min = None
        self.Max = None
        self.FixMin = 0
        self.FixMax = 0
        self.Title = Title
        self.set(Min, Max)
        if Min:
            self.FixMin = 1
        if Max:
            self.FixMax = 1

    def set(self, Min = None, Max = None):
        if Min and not self.FixMax:
            self.Min = Min
        if Max and not self.FixMax:
            self.Max = Max
        if self.Min and self.Max:
            self.setbasepts(((self.Min, 0,), (self.Max, 1,)))

    def TickValPosList(self):
        TickCount = 4
        return map(lambda x, self = self, TickCount = TickCount: self._invert(x / float(TickCount)), range(TickCount + 1))

    def ValToLab(self, x):
        return "%.3f" % x

    def TickList(self):
        return map(lambda x, self=self: Tick(x, self.convert(x), self.ValToLab(x)), self.TickValPosList())


class LinAxis(_Axis, _LinMap):

    pass


class LogAxis(_Axis, _LogMap):

    pass


###############################################################################
# graph part

class Graph:

    def __init__(self, canvas, tex, xpos, ypos):
        self.canvas = canvas
        self.tex = tex
        self.xpos = xpos
        self.ypos = ypos

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

    def __init__(self, canvas, tex, xpos, ypos, width, height, **Axis):
        Graph.__init__(self, canvas, tex, xpos, ypos)
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
        self.VirMap = (_LinMap().setbasepts(((0, self.xpos + self.left, ), (1, self.xpos + self.width - self.right, ))),
                       _LinMap().setbasepts(((0, self.ypos + self.buttom, ), (1, self.ypos + self.height - self.top, ))), )

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
        # this isn't smart ... we should walk only once throu the mathtree
        self.YValues = map(lambda i, self = self: self.MT.Calc(self.XValues, i), range(self.Points + 1))

    def GetValues(self, Kind, DefaultResult = "y"):
        if (self.ResKind and (Kind == self.ResKind)) or ((not self.ResKind) and (Kind == DefaultResult)):
            return self.YValues
        return self.XValues[Kind]


class ParamFunction(Function):
    pass


###############################################################################
# key part


