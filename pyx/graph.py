#!/usr/bin/env python
#
# $Header$
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


import pyx, types, re, tex, unit, math, path
from math import log, exp, sqrt, pow


class _ticklength(unit.length):

    _base      = 0.15
    _factor    = sqrt(2)

    def __init__(self, l = _base, power = 0, factor = _factor):
        self.factor = factor
        unit.length.__init__(self, l = l * pow(self.factor, power), default_type="v")

    def increment(self, power = 1):
        return pow(self.factor, power) * self


class ticklength(_ticklength):

    SHORT      = _ticklength(power = -6)
    SHORt      = _ticklength(power = -5)
    SHOrt      = _ticklength(power = -4)
    SHort      = _ticklength(power = -3)
    Short      = _ticklength(power = -2)
    short      = _ticklength(power = -1)
    normal     = _ticklength()
    long       = _ticklength(power = 1)
    Long       = _ticklength(power = 2)
    LOng       = _ticklength(power = 3)
    LONg       = _ticklength(power = 4)
    LONG       = _ticklength(power = 5)


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
        self.basepts = ((log(basepts[0][0]), basepts[0][1], ),
                        (log(basepts[1][0]), basepts[1][1], ), )
        return self
    def _convert(self, Value):
        return _LinMap._convert(self, log(Value))
    def _invert(self, Value):
        return exp(_LinMap._invert(self, Value))
               


###############################################################################
# axis part

epsilon = 1e-10

def _powi(x, y):
    assert type(y) == types.IntType
    assert y >= 0
    if y:
        y2 = y / 2 # integer division!
        yr = y % 2
        res = _powi(x, y2)
        if yr:
            return x * res * res
        else: 
            return res * res
    else: 
        return 1  

class frac:

    def __init__(self, enum, denom, power = None):
        assert type(enum) in (types.IntType, types.LongType, )
        assert type(denom) in (types.IntType, types.LongType, )
        assert denom != 0
        if power != None:
            if power > 0:
                self.enum = _powi(long(enum), power)
                self.denom = _powi(long(denom), power)
            elif power < 0:
                self.enum = _powi(long(denom), -power)
                self.denom = _powi(long(enum), -power)
            else:
                self.enum = 1
                self.denom = 1
        else:
            self.enum = enum
            self.denom = denom

    def __cmp__(self, other):
        if other == None:
            return 1
        return cmp(self.enum * other.denom, other.enum * self.denom)

    def __mul__(self, other):
        return frac(self.enum * other.enum, self.denom * other.denom)

    def __float__(self):
        return float(self.enum) / self.denom

    def __str__(self):
        return "%i/%i" % (self.enum, self.denom)

    def __repr__(self):
        return "frac(%s, %s)" % (repr(self.enum), repr(self.denom)) # I want to see the "L"


class tick(frac):

    def __init__(self, enum, denom, ticklevel = 0, labellevel = 0):
        # ticklevel and labellevel are allowed to be None (in order to skip ticks or labels)
        frac.__init__(self, enum, denom)
        self.ticklevel = ticklevel
        self.labellevel = labellevel

    def __repr__(self):
        return "tick(%s, %s, %s, %s)" % (repr(self.enum), repr(self.denom), self.ticklevel, self.labellevel)

    def merge(self, other):
        assert self == other
        if (self.ticklevel == None) or ((other.ticklevel != None) and (other.ticklevel < self.ticklevel)):
            self.ticklevel = other.ticklevel
        if (self.labellevel == None) or ((other.labellevel != None) and (other.labellevel < self.labellevel)):
            self.labellevel = other.labellevel


class anypart:

    def mergeticklists(self, list1, list2):
        # caution: side effects
        i = 0
        j = 0
        try:
            while 1: # we keep on going until we reach an index error
                while list2[j] < list1[i]: # insert tick
                   list1.insert(i, list2[j])
                   i = i + 1
                   j = j + 1
                if list2[j] == list1[i]: # merge tick
                   list1[i].merge(list2[j])
                   j = j + 1
                i = i + 1
        except IndexError:
            if j < len(list2):
                list1 += list2[j:]
        return list1


class linpart(anypart):

    def __init__(self, tickfracs = None, labelfracs = None, extendtoticklevel = 0, extendtolabellevel = None):
        """
        zero-level labelfracs are created out of the zero-level tickfracs when labelfracs are None
        all-level tickfracs are created out of the all-level labelfracs when tickfracs are None
        get ticks but avoid labels by labelfracs = ()
        get labels but avoid ticks by tickfracs = ()

        We do not perform the adjustment of tickfracs or labelfracs within this
        constructor, but later in getticks in order to allow for a change by
        parameters of getticks. That can be used to create other partition schemes
        (which create several posibilities) by derivating this class.
        """
        self.tickfracs = tickfracs
        self.labelfracs = labelfracs
        self.extendtoticklevel = extendtoticklevel
        self.extendtolabellevel = extendtolabellevel

    def extendminmax(self, min, max, frac):
        return (float(frac) * math.floor(min / float(frac) + epsilon),
                float(frac) * math.ceil(max / float(frac) - epsilon))

    def getticklist(self, min, max, frac, ticklevel = None, labellevel = None):
        ticks = []
        imin = int(math.ceil(min / float(frac) - 0.5 * epsilon))
        imax = int(math.floor(max / float(frac) + 0.5 * epsilon))
        for i in range(imin, imax + 1):
            ticks.append(tick(long(i) * frac.enum, frac.denom, ticklevel = ticklevel, labellevel = labellevel))
        return ticks

    def getticks(self, min, max, tickfracs = None, labelfracs = None):
        """
        When tickfracs or labelfracs are set, they will be taken instead of the
        values provided to the constructor. It is not allowed to provide something
        to tickfracs and labelfracs here and at the constructor at the same time.
        """
        if (tickfracs == None) and (labelfracs == None):
            tickfracs = self.tickfracs
            labelfracs = self.labelfracs
        else:
            assert self.tickfracs == None
            assert self.labelfracs == None
        if tickfracs == None:
            if labelfracs == None:
                tickfracs = ()
            else:
                tickfracs = labelfracs
        if labelfracs == None:
            if len(tickfracs):
                labelfracs = (tickfracs[0], )
            else:
                labelfracs = ()

        if self.extendtoticklevel != None:
            (min, max, ) = self.extendminmax(min, max, tickfracs[self.extendtoticklevel])
        if self.extendtolabellevel != None:
            (min, max, ) = self.extendminmax(min, max, labelfracs[self.extendtolabellevel])

        ticks = []
        for i in range(len(tickfracs)):
            ticks = self.mergeticklists(ticks, self.getticklist(min, max, tickfracs[i], ticklevel = i))
        for i in range(len(labelfracs)):
            ticks = self.mergeticklists(ticks, self.getticklist(min, max, labelfracs[i], labellevel = i))

        return ticks

    def getparts(self, min, max):
        return [getticks(self, min, max), ]


class autolinpart(linpart):
    defaulttickfracslist = ((frac(1, 1), frac(1, 2), ),
                            (frac(2, 1), frac(1, 1), ),
                            (frac(5, 2), frac(5, 4), ),
                            (frac(5, 1), frac(5, 2), ), )

    def __init__(self, minticks = 0.5, maxticks = 25, tickfracslist = defaulttickfracslist, minpower = -5, maxpower = 5, **args):
        linpart.__init__(self, **args)
        self.minticks = minticks
        self.maxticks = maxticks
        self.tickfracslist = tickfracslist
        self.minpower = minpower
        self.maxpower = maxpower

    def getparts(self, min, max):
        parts = []
        e = int(log(max - min) / log(10))
        for shift in range(e + self.minpower, e + self.maxpower + 1):
            basefrac = frac(10L, 1, shift)
            for tickfracs in self.tickfracslist:
                tickcount = (max - min) / float(tickfracs[0] * basefrac)
                if (tickcount > self.minticks) and (tickcount < self.maxticks):
                    parts.append(self.getticks(min, max, map(lambda f, bf = basefrac: f * bf, tickfracs)))
        return parts


class shiftfracs:
    def __init__(self, shift, *fracs):
         self.shift = shift
         self.fracs = fracs

class logpart(anypart):

    """
    This class looks like code duplication of linpart. However, it is not,
    because logaxis use shiftfracs instead of fracs all the time.
    """

    def __init__(self, tickshiftfracslist = None, labelshiftfracslist = None, extendtoticklevel = 0, extendtolabellevel = None):
        """
        For the parameters tickshiftfracslist and labelshiftfracslist apply
        rules like for tickfracs and labelfracs in linpart.
        """
        self.tickshiftfracslist = tickshiftfracslist
        self.labelshiftfracslist = labelshiftfracslist
        self.extendtoticklevel = extendtoticklevel
        self.extendtolabellevel = extendtolabellevel

    def extendminmax(self, min, max, shiftfracs):
        minpower = None
        maxpower = None
        for i in xrange(len(shiftfracs.fracs)):
            imin = int(math.floor(log(min / float(shiftfracs.fracs[i])) / log(shiftfracs.shift) + 0.5 * epsilon)) + 1
            imax = int(math.ceil(log(max / float(shiftfracs.fracs[i])) / log(shiftfracs.shift) - 0.5 * epsilon)) - 1
            if (minpower == None) or (imin < minpower):
                (minpower, minindex, ) = (imin, i, )
            if (maxpower == None) or (imax >= maxpower):
                (maxpower, maxindex, ) = (imax, i, )
        if minindex:
            minfrac = shiftfracs.fracs[minindex - 1]
        else:
            minfrac = shiftfracs.fracs[-1]
            minpower -= 1
        if maxindex != len(shiftfracs.fracs) - 1:
            maxfrac = shiftfracs.fracs[maxindex + 1]
        else:
            maxfrac = shiftfracs.fracs[0]
            maxpower += 1
        return (float(minfrac) * pow(10, minpower),
                float(maxfrac) * pow(10, maxpower), )

    def getticklist(self, min, max, shiftfracs, ticklevel = None, labellevel = None):
        ticks = []
        minimin = 0
        maximax = 0
        for f in shiftfracs.fracs:
            fracticks = []
            imin = int(math.ceil(log(min / float(f)) / log(shiftfracs.shift) - 0.5 * epsilon))
            imax = int(math.floor(log(max / float(f)) / log(shiftfracs.shift) + 0.5 * epsilon))
            for i in range(imin, imax + 1):
                pos = f * frac(shiftfracs.shift, 1, i)
                fracticks.append(tick(pos.enum, pos.denom, ticklevel = ticklevel, labellevel = labellevel))
            ticks = self.mergeticklists(ticks, fracticks)
        return ticks

    def getticks(self, min, max, tickshiftfracslist = None, labelshiftfracslist = None):
        """
        For the parameters tickshiftfracslist and labelshiftfracslist apply
        rules like for tickfracs and labelfracs in linpart.
        """
        if (tickshiftfracslist == None) and (labelshiftfracslist == None):
            tickshiftfracslist = self.tickshiftfracslist
            labelshiftfracslist = self.labelshiftfracslist
        else:
            assert self.tickshiftfracslist == None
            assert self.labelshiftfracslist == None
        if tickshiftfracslist == None:
            if labelshiftfracslist == None:
                tickshiftfracslist = (shiftfracs(10), )
            else:
                tickshiftfracslist = labelshiftfracslist
        if labelshiftfracslist == None:
            if len(tickshiftfracslist):
                labelshiftfracslist = (tickshiftfracslist[0], )
            else:
                labelshiftfracslist = ()

        if self.extendtoticklevel != None:
            (min, max, ) = self.extendminmax(min, max, tickshiftfracslist[self.extendtoticklevel])
        if self.extendtolabellevel != None:
            (min, max, ) = self.extendminmax(min, max, labelshiftfracslist[self.extendtolabellevel])

        ticks = []
        for i in range(len(tickshiftfracslist)):
            ticks = self.mergeticklists(ticks, self.getticklist(min, max, tickshiftfracslist[i], ticklevel = i))
        for i in range(len(labelshiftfracslist)):
            ticks = self.mergeticklists(ticks, self.getticklist(min, max, labelshiftfracslist[i], labellevel = i))

        return ticks

    def getparts(self, min, max):
        return [getticks(self, min, max), ]

class autologpart(logpart):
    shiftfracs1    = shiftfracs(10, frac(1, 10))
    shiftfracs125  = shiftfracs(10, frac(1, 10), frac(2, 10), frac(5, 10))
    shiftfracs1258 = shiftfracs(10, frac(1, 10), frac(2, 10), frac(5, 10), frac(8, 10))
    shiftfracs1to9 = shiftfracs(10, *list(map(lambda x: frac(x, 10), range(1, 10))))
    #         ^- we always include 1 in order to get extendto(tick|label)level to work as expected

    defaultshiftfracslists = (((shiftfracs1,          # ticks
                                shiftfracs1to9, ),    # subticks
                               (shiftfracs1,          # labels
                                shiftfracs125, ), ),  # sublevels

                              ((shiftfracs1,          # ticks
                                shiftfracs1to9, ),    # subticks
                               None),                 # labels like ticks

                              ((shiftfracs1,          # ticks
                                shiftfracs1258, ),    # subticks
                               None), )               # labels like ticks

    def __init__(self, shiftfracslists = defaultshiftfracslists, **args):
        logpart.__init__(self, **args)
        self.shiftfracslists = shiftfracslists

    def getparts(self, min, max):
        parts = []
        for (tickshiftfracslist, labelshiftfracslist, ) in self.shiftfracslists:
            parts.append(self.getticks(min, max, tickshiftfracslist, labelshiftfracslist))
        return parts


#print linpart((frac(1, 3), frac(1, 4), ), extendtoticklevel = None, extendtolabellevel = 0).getticks(0, 1.9)
#print autolinpart().getparts(0, 1.9)
#print logpart((autologpart.shiftfracs1, autologpart.shiftfracs1to9, ),
#              (autologpart.shiftfracs1, autologpart.shiftfracs125, ), extendtotlevel = 1).getticks(0.0432, 24.623)
#print autologpart().getparts(0.0432, 24.623)

class favorautolinpart(autolinpart):
    """favorfixfrac - shift - frac - partitioning"""
    # TODO: just to be done ... throw out parts within the favor region -- or what else to do?
    degreefracs = ((frac( 15, 1), frac(  5, 1), ),
                   (frac( 30, 1), frac( 15, 1), ),
                   (frac( 45, 1), frac( 15, 1), ),
                   (frac( 60, 1), frac( 30, 1), ),
                   (frac( 90, 1), frac( 30, 1), ),
                   (frac( 90, 1), frac( 45, 1), ),
                   (frac(180, 1), frac( 45, 1), ),
                   (frac(180, 1), frac( 90, 1), ),
                   (frac(360, 1), frac( 90, 1), ),
                   (frac(360, 1), frac(180, 1), ), )
    # favouring some fixed fracs, e.g. partitioning of axis in degree
    def __init__(self, fixfracs, fixfavor = 2, **args):
        sfpart.__init__(self, **args)
        self.fixfracs = fixfracs
        self.fixfavor = fixfavor


class timepart:
    """partitioning of times and dates"""
    # TODO: this will be a difficult subject ...
    pass


class ratepart:

    def __init__(self, part, rate):
        self.part = part
        self.rate = rate
    def __repr__(self):
        return "%f, %s" % (self.rate, repr(self.part), )

class momrate:
    """min - opt - max - rating of axes partitioning"""

    class rateparam:
        """mom rate parameter set"""
        def __init__(self, min = None, opt = None, max = None, factor = 1):
            self.min = float(min)
            self.max = float(max)
            self.opt = float(opt)
            self.factor = float(factor)

    lindefaulttickrateparams = (rateparam(1, 4, 25), rateparam(1, 10, 100, 0.5), )
    lindefaultlabelrateparams = (rateparam(1, 4, 15), )
    logdefaulttickrateparams = (rateparam(1, 4, 25), rateparam(1, 25, 100, 0.5), )
    logdefaultlabelrateparams = (rateparam(1, 4, 15), rateparam(-2.5, 2.5, 10, 0.5), )

    def __init__(self, tickrateparams = lindefaulttickrateparams, labelrateparams = lindefaultlabelrateparams):
        self.tickrateparams = tickrateparams
        self.labelrateparams = labelrateparams

    def getcounts(self, ticks):
        tickcounts = map(lambda x: 0, self.tickrateparams)
        labelcounts = map(lambda x: 0, self.labelrateparams)
        for tick in ticks:
            if (tick.ticklevel != None) and (tick.ticklevel < len(self.tickrateparams)):
                tickcounts[tick.ticklevel] += 1
            if (tick.labellevel != None) and (tick.labellevel < len(self.labelrateparams)):
                labelcounts[tick.labellevel] += 1
        return (tickcounts, labelcounts, )

    def evalrate(self, val, rateparam):
        opt = rateparam.opt
        min = rateparam.min
        max = rateparam.max
        rate = ((opt - min) * log((opt - min) / (val - min)) +
                (max - opt) * log((max - opt) / (max - val))) / (max - min)
        return rate
    
    def getrate(self, part):
        rate = 0
        (tickcounts, labelcounts, ) = self.getcounts(part)
        try:
            for (tickcount, rateparam, ) in zip(tickcounts, self.tickrateparams, ):
                rate += self.evalrate(tickcount, rateparam)
            for (labelcount, rateparam, ) in zip(labelcounts, self.labelrateparams, ):
                rate += self.evalrate(labelcount, rateparam)
        except (ZeroDivisionError, ValueError, ):
            rate = None
        return rate
    
    def getrateparts(self, parts):
        rateparts = []
        for part in parts:
            rate = self.getrate(part)
            if rate != None:
                rateparts.append(ratepart(part, rate))
        return rateparts

#min = 1
#for i in range(1, 10000):
#    max = min * pow(1.05, i)
#    if max > 1e10:
#        break
#    print max/min,
#    for part in autologpart(extendtoticklevel = None).getparts(min, max):
#        rate = momrate(momrate.logdefaulttickrateparams,
#                       momrate.logdefaultlabelrateparams).getrate(part)
#        print rate,
#    print


class Tick:

    def __init__(self, ValuePos, VirtualPos, Label = None, LabelRep = None, TickLevel = 0, LabelLevel = 0):
        if not LabelRep:
            LapelRep = Label
        self.ValuePos = ValuePos
        self.VirtualPos = VirtualPos
        self.Label = Label
        self.LabelRep = LabelRep
        self.TickLevel = TickLevel
        self.LabelLevel = LabelLevel


class _Axis:

    def __init__(self, min = None, max = None, reverse = 0, title = None):
        self.fixmin = (min != None)
        self.fixmax = (max != None)
        self.min = min
        self.max = max
        self.title = title
        self.reverse = reverse
        self.setrange()

    def setrange(self, min = None, max = None):
        if (not self.fixmin) and (min != None):
            self.min = min
        if (not self.fixmax) and (max != None):
            self.max = max
        if (self.min != None) and (self.max != None):
            if self.reverse:
                self.setbasepts(((self.min, 1,), (self.max, 0,)))
            else:
                self.setbasepts(((self.min, 0,), (self.max, 1,)))

    def TickValPosList(self):
        TickCount = 4
        return map(lambda x, self = self, TickCount = TickCount: self._invert(x / float(TickCount)), range(TickCount + 1))

    def ValToLab(self, x):
        return "%.3f" % x

    def createrateparts(self):
        parts = self.part.getparts(self.min, self.max)
        rateparts = self.rate.getrateparts(parts)
        self.bestratepart = rateparts[0]
        for ratepart in rateparts[1:]:
            if self.bestratepart.rate > ratepart.rate:
                self.bestratepart = ratepart
        self.setrange(float(self.bestratepart.part[0]), float(self.bestratepart.part[-1]))

    def TickList(self):
        ticklist = []
        for tick in self.bestratepart.part:
            ticklist.append(Tick(float(tick), self.convert(float(tick)), self.ValToLab(float(tick)), TickLevel = tick.ticklevel, LabelLevel = tick.labellevel))
        return ticklist



class LinAxis(_Axis, _LinMap):

    def __init__(self, part = autolinpart(), rate = momrate(), **args):
        _Axis.__init__(self, **args)
        self.part = part
        self.rate = rate


class LogAxis(_Axis, _LogMap):

    def __init__(self, part = autologpart(), rate = momrate(momrate.logdefaulttickrateparams, momrate.logdefaultlabelrateparams), **args):
        _Axis.__init__(self, **args)
        self.part = part
        self.rate = rate


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
            self.Axis[key].setrange(min( map (lambda x: x[0], ranges)),
                                    max( map (lambda x: x[1], ranges)))

        for pd in self.plotdata:
            pd.Data.SetAxis(self.Axis)

        # this should be done after axis-size calculation
        self.left = 1
        self.buttom = 1
        self.top = 0
        self.right = 0
        self.VirMap = (_LinMap().setbasepts(((0, unit.topt(self.xpos + self.left), ),
                                             (1, unit.topt(self.xpos + self.width - self.right), ))),
                       _LinMap().setbasepts(((0, unit.topt(self.ypos + self.buttom), ),
                                             (1, unit.topt(self.ypos + self.height - self.top), ))), )

        self.canvas.draw(path._rect(self.VirMap[0].convert(0),
                                    self.VirMap[1].convert(0),
                                    self.VirMap[0].convert(1) - self.VirMap[0].convert(0),
                                    self.VirMap[1].convert(1) - self.VirMap[1].convert(0)))

        for key in self.Axis.keys():
            self.Axis[key].createrateparts()

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
                    self.canvas.draw(path._line(x, self.VirMap[1].convert(0),
                                                x, self.VirMap[1].convert(0)+10))
                                                # + ticklength.normal.increment(-tick.TickLevel)))
                    if tick.LabelLevel == 0:
                        self.tex._text(x, self.VirMap[1].convert(0)-10, l, tex.halign.center)
                if Type == 1:
                    self.canvas.draw(path._line(self.VirMap[0].convert(0), x,
                                                self.VirMap[0].convert(0)+10, x))
                                                # + ticklength.normal.increment(-tick.TickLevel), x))
                    if tick.LabelLevel == 0:
                        self.tex._text(self.VirMap[0].convert(0)-10, x, l, tex.halign.right)

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
                p.append(path._lineto(pt[0],pt[1]))
            else:
                p = [path._moveto(pt[0],pt[1]), ]
        Graph.canvas.draw(path(*p))

class mark(_PlotStyle):

    def __init__(self, size = 0.05):
        self.size = size

    def LoopOverPoints(self, Graph, Data):
        for pt in zip(Graph.ValueList(_XPattern, 0, Data),
                      Graph.ValueList(_YPattern, 1, Data)):
            Graph.canvas.draw(path.path(path._moveto(pt[0] - self.size, pt[1] - self.size),
                                        path._lineto(pt[0] + self.size, pt[1] + self.size),
                                        path._moveto(pt[0] - self.size, pt[1] + self.size),
                                        path._lineto(pt[0] + self.size, pt[1] - self.size)))

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


