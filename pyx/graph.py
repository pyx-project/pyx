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


import types, re, math
import bbox, canvas, path, tex, unit
from math import log, exp, sqrt, pow


goldenrule = 0.5 * (sqrt(5) + 1)


################################################################################
# maps
################################################################################

class _map:

    def setbasepts(self, basepts):
        """base points for convertion"""
        self.basepts = basepts
        return self

    def convert(self, values):
        if type(values) in (types.IntType, types.LongType, types.FloatType, ):
            return self._convert(values)
        else:
            return map(lambda x, self = self: self._convert(x), values)

    def invert(self, values):
        if type(values) in (types.IntType, types.LongType, types.FloatType, ):
            return self._invert(values)
        else:
            return map(lambda x, self = self: self._invert(x), values)


class _linmap(_map):

    def _convert(self, value):
        return self.basepts[0][1] + ((self.basepts[1][1] - self.basepts[0][1]) /
               float(self.basepts[1][0] - self.basepts[0][0])) * (value - self.basepts[0][0])

    def _invert(self, value):
        return self.basepts[0][0] + ((self.basepts[1][0] - self.basepts[0][0]) /
               float(self.basepts[1][1] - self.basepts[0][1])) * (value - self.basepts[0][1])


class _logmap(_linmap):

    def setbasepts(self, basepts):
        """base points for convertion"""
        self.basepts = ((log(basepts[0][0]), basepts[0][1], ),
                        (log(basepts[1][0]), basepts[1][1], ), )
        return self

    def _convert(self, value):
        return _linmap._convert(self, log(value))

    def _invert(self, value):
        return exp(_linmap._invert(self, value))



################################################################################
# tick list = partition
################################################################################

class frac:

    def __init__(self, enum, denom, power=None):
        assert type(enum) in (types.IntType, types.LongType, )
        assert type(denom) in (types.IntType, types.LongType, )
        assert denom != 0
        if power != None:
            if power > 0:
                self.enum = self._powi(long(enum), power)
                self.denom = self._powi(long(denom), power)
            elif power < 0:
                self.enum = self._powi(long(denom), -power)
                self.denom = self._powi(long(enum), -power)
            else:
                self.enum = 1
                self.denom = 1
        else:
            self.enum = enum
            self.denom = denom

    def _powi(self, x, y):
        assert type(y) == types.IntType
        assert y >= 0
        if y:
            y2 = y / 2 # integer division!
            yr = y % 2
            res = self._powi(x, y2)
            if yr:
                return x * res * res
            else: 
                return res * res
        else: 
            return 1  

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
        return "frac(%r, %r)" % (self.enum, self.denom) # I want to see the "L"


class tick(frac):

    def __init__(self, enum, denom, ticklevel=0, labellevel=0):
        # ticklevel and labellevel are allowed to be None (in order to skip ticks or labels)
        frac.__init__(self, enum, denom)
        self.ticklevel = ticklevel
        self.labellevel = labellevel

    def __repr__(self):
        return "tick(%r, %r, %s, %s)" % (self.enum, self.denom, self.ticklevel, self.labellevel)

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
                   i += 1
                   j += 1
                if list2[j] == list1[i]: # merge tick
                   list1[i].merge(list2[j])
                   j += 1
                i += 1
        except IndexError:
            if j < len(list2):
                list1 += list2[j:]
        return list1


class linpart(anypart):

    def __init__(self, tickfracs=None, labelfracs=None,
                 extendtoticklevel=0, extendtolabellevel=None, epsilon=1e-10):
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
        self.epsilon = epsilon

    def extendminmax(self, min, max, frac):
        return (float(frac) * math.floor(min / float(frac) + self.epsilon),
                float(frac) * math.ceil(max / float(frac) - self.epsilon))

    def getticklist(self, min, max, frac, ticklevel=None, labellevel=None):
        ticks = []
        imin = int(math.ceil(min / float(frac) - 0.5 * self.epsilon))
        imax = int(math.floor(max / float(frac) + 0.5 * self.epsilon))
        for i in range(imin, imax + 1):
            ticks.append(tick(long(i) * frac.enum, frac.denom, ticklevel = ticklevel, labellevel = labellevel))
        return ticks

    def getticks(self, min, max, tickfracs=None, labelfracs=None):
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
    defaulttickfracslist = ((frac(1, 1), frac(1, 2)),
                            (frac(2, 1), frac(1, 1)),
                            (frac(5, 2), frac(5, 4)),
                            (frac(5, 1), frac(5, 2)))

    def __init__(self, minticks=0.5, maxticks=25, tickfracslist=defaulttickfracslist, minpower=-5, maxpower=5, **args):
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

    def __init__(self, tickshiftfracslist=None, labelshiftfracslist=None,
                 extendtoticklevel=0, extendtolabellevel=None, epsilon=1e-10):
        """
        For the parameters tickshiftfracslist and labelshiftfracslist apply
        rules like for tickfracs and labelfracs in linpart.
        """
        self.tickshiftfracslist = tickshiftfracslist
        self.labelshiftfracslist = labelshiftfracslist
        self.extendtoticklevel = extendtoticklevel
        self.extendtolabellevel = extendtolabellevel
        self.epsilon = epsilon

    def extendminmax(self, min, max, shiftfracs):
        minpower = None
        maxpower = None
        for i in xrange(len(shiftfracs.fracs)):
            imin = int(math.floor(log(min / float(shiftfracs.fracs[i])) / log(shiftfracs.shift) + 0.5 * self.epsilon)) + 1
            imax = int(math.ceil(log(max / float(shiftfracs.fracs[i])) / log(shiftfracs.shift) - 0.5 * self.epsilon)) - 1
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

    def getticklist(self, min, max, shiftfracs, ticklevel=None, labellevel=None):
        ticks = []
        minimin = 0
        maximax = 0
        for f in shiftfracs.fracs:
            fracticks = []
            imin = int(math.ceil(log(min / float(f)) / log(shiftfracs.shift) - 0.5 * self.epsilon))
            imax = int(math.floor(log(max / float(f)) / log(shiftfracs.shift) + 0.5 * self.epsilon))
            for i in range(imin, imax + 1):
                pos = f * frac(shiftfracs.shift, 1, i)
                fracticks.append(tick(pos.enum, pos.denom, ticklevel = ticklevel, labellevel = labellevel))
            ticks = self.mergeticklists(ticks, fracticks)
        return ticks

    def getticks(self, min, max, tickshiftfracslist=None, labelshiftfracslist=None):
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

    defaultshiftfracslists = (((shiftfracs1,      # ticks
                                shiftfracs1to9),  # subticks
                               (shiftfracs1,      # labels
                                shiftfracs125)),  # sublevels

                              ((shiftfracs1,      # ticks
                                shiftfracs1to9),  # subticks
                               None),             # labels like ticks

                              ((shiftfracs1,      # ticks
                                shiftfracs1258),  # subticks
                               None))             # labels like ticks

    def __init__(self, shiftfracslists=defaultshiftfracslists, **args):
        logpart.__init__(self, **args)
        self.shiftfracslists = shiftfracslists

    def getparts(self, min, max):
        parts = []
        for (tickshiftfracslist, labelshiftfracslist, ) in self.shiftfracslists:
            parts.append(self.getticks(min, max, tickshiftfracslist, labelshiftfracslist))
        return parts


#print linpart((frac(1, 3), frac(1, 4)), extendtoticklevel=None, extendtolabellevel=0).getticks(0, 1.9)
#print autolinpart().getparts(0, 1.9)
#print logpart((autologpart.shiftfracs1, autologpart.shiftfracs1to9),
#              (autologpart.shiftfracs1, autologpart.shiftfracs125), extendtoticklevel=1).getticks(0.0432, 24.623)
#print autologpart().getparts(0.0432, 24.623)


class favorautolinpart(autolinpart):
    """favorfixfrac - shift - frac - partitioning"""
    # TODO: just to be done ... throw out parts within the favor region -- or what else to do?
    degreefracs = ((frac( 15, 1), frac(  5, 1)),
                   (frac( 30, 1), frac( 15, 1)),
                   (frac( 45, 1), frac( 15, 1)),
                   (frac( 60, 1), frac( 30, 1)),
                   (frac( 90, 1), frac( 30, 1)),
                   (frac( 90, 1), frac( 45, 1)),
                   (frac(180, 1), frac( 45, 1)),
                   (frac(180, 1), frac( 90, 1)),
                   (frac(360, 1), frac( 90, 1)),
                   (frac(360, 1), frac(180, 1)))
    # favouring some fixed fracs, e.g. partitioning of an axis in degree
    def __init__(self, fixfracs, fixfavor = 2, **args):
        sfpart.__init__(self, **args)
        self.fixfracs = fixfracs
        self.fixfavor = fixfavor


class timepart:
    """partitioning of times and dates"""
    # TODO: this will be a difficult subject ...
    pass



################################################################################
# rate partitions
################################################################################

class ratepart:

    def __init__(self, part, rate):
        self.part = part
        self.rate = rate

    def __repr__(self):
        return "%f, %s" % (self.rate, repr(self.part), )


class momrate:
    """min - opt - max - rating of axes partitioning"""

    class momrateparam:
        """mom rate parameter set"""

        def __init__(self, optfactor, minoffset, minfactor, maxoffset, maxfactor, weight=1):
            self.optfactor = optfactor
            self.minoffset = minoffset
            self.minfactor = minfactor
            self.maxoffset = maxoffset
            self.maxfactor = maxfactor
            self.weight = weight

        def min(self, stretch):
            return self.minoffset + self.minfactor * (stretch - 1.0) * self.optfactor

        def opt(self, stretch):
            return float(self.optfactor * stretch)

        def max(self, stretch):
            return self.maxoffset + self.maxfactor * (stretch - 1.0) * self.optfactor

    lindefaulttickrateparams = (momrateparam(4, 1, 1, 20, 5), momrateparam(10, 2, 1, 100, 10, 0.5), )
    lindefaultlabelrateparams = (momrateparam(4, 1, 1, 16, 4), )
    logdefaulttickrateparams = (momrateparam(5, 1, 1, 30, 6), momrateparam(25, 5, 1, 100, 4, 0.5), )
    logdefaultlabelrateparams = (momrateparam(5, 1, 1, 20, 4), momrateparam(3, -3, -1, 9, 3, 0.5), )

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
        # sum up tick/label-counts of lower levels
        tickcounts = reduce(lambda x, y: x and (x + [ x[-1] + y, ]) or [y, ] , tickcounts, [])
        labelcounts = reduce(lambda x, y: x and (x + [ x[-1] + y, ]) or [y, ] , labelcounts, [])
        return (tickcounts, labelcounts, )

    def evalrate(self, val, stretch, rateparam):
        opt = rateparam.opt(stretch)
        min = rateparam.min(stretch)
        max = rateparam.max(stretch)
        rate = ((opt - min) * log((opt - min) / (val - min)) +
                (max - opt) * log((max - opt) / (max - val))) / (max - min)
        return rate

    def getrate(self, part, stretch):
        rate = 0
        weight = 0
        (tickcounts, labelcounts, ) = self.getcounts(part)
        try:
            for (tickcount, rateparam, ) in zip(tickcounts, self.tickrateparams, ):
                rate += self.evalrate(tickcount, stretch, rateparam) * rateparam.weight
                weight += rateparam.weight
            for (labelcount, rateparam, ) in zip(labelcounts, self.labelrateparams, ):
                rate += self.evalrate(labelcount, stretch, rateparam) * rateparam.weight
                weight += rateparam.weight
            rate /= weight
        except (ZeroDivisionError, ValueError):
            rate = None
        return rate

#min = 1
#for i in range(1, 10000):
#    max = min * pow(1.5, i)
#    if max > 1e10:
#        break
#    print max/min,
#    for part in autologpart(extendtoticklevel = None).getparts(min, max):
#        rate = momrate(momrate.logdefaulttickrateparams,
#                       momrate.logdefaultlabelrateparams).getrate(part, 1)
#        print rate,
#    print




################################################################################
# painter
################################################################################

class tickpainter:

    def __init__(self, value, factor = goldenrule, drawgrid = 0, gridstyles = canvas.linestyle.dotted):
        self.value = value
        self.factor = factor
        self.drawgrid = drawgrid
        if type(gridstyles) not in (types.TupleType, types.ListType):
            self.gridstyles = (gridstyles, )
        else:
            self.gridstyles = gridstyles

    def length(self, power):
        return pow(self.factor, power) * unit.topt(self.value)

    def paint(self, graph, x, y, dx, dy, tick, gridpath):
        graph.draw(path._line(x, y, x + dx * self.length(-tick.ticklevel), y + dy * self.length(-tick.ticklevel)))
        if self.drawgrid:
            graph.draw(gridpath, *self.gridstyles)

_base=0.2

tickpainter.SHORT  = tickpainter("%f v cm" % (_base/math.sqrt(64)))
tickpainter.SHORt  = tickpainter("%f v cm" % (_base/math.sqrt(32)))
tickpainter.SHOrt  = tickpainter("%f v cm" % (_base/math.sqrt(16)))
tickpainter.SHort  = tickpainter("%f v cm" % (_base/math.sqrt(8)))
tickpainter.Short  = tickpainter("%f v cm" % (_base/math.sqrt(4)))
tickpainter.short  = tickpainter("%f v cm" % (_base/math.sqrt(2)))
tickpainter.normal = tickpainter("%f v cm" % _base)
tickpainter.long   = tickpainter("%f v cm" % (_base*math.sqrt(2)))
tickpainter.Long   = tickpainter("%f v cm" % (_base*math.sqrt(4)))
tickpainter.LOng   = tickpainter("%f v cm" % (_base*math.sqrt(8)))
tickpainter.LONg   = tickpainter("%f v cm" % (_base*math.sqrt(16)))
tickpainter.LONG   = tickpainter("%f v cm" % (_base*math.sqrt(32)))


class labelpainter:

    def __init__(self):
        pass

    def gcd(self, m, n):
        if m < n:
            m, n = n, m
        while n > 0:
            m, n = n, m % n
        return m

    def decimalfrac(self, m, n):
        # XXX ensure integer division!
        gcd = self.gcd(m, n)
        m, n = int(m / gcd), int(n / gcd)
        frac = str(m / n)
        rest = m % n
        if rest:
            frac += "."
        while (rest):
            rest *= 10
            frac += str(rest / n)
            rest = rest % n
        return frac

    def paint(self, graph, x, y, dx, dy, tick):
        graph.tex._text(x - 10 * dx, y - 10 * dy, self.decimalfrac(tick.enum, tick.denom))


labelpainter.normal = labelpainter()


#print labelpainter.normal.decimalfrac(32, 33)
#assert 0

################################################################################
# axes
################################################################################

class _axis:

    def __init__(self, min=None, max=None, reverse=0, title=None, titleattr=None, tickpainter = tickpainter.normal, labelpainter = labelpainter.normal):
        self.fixmin = min is not None
        self.fixmax = max is not None
        self.min = min
        self.max = max
        self.reverse = reverse
        self.title = title
        self.titleattr = titleattr
        self.tickpainter = tickpainter
        self.labelpainter = labelpainter
        self.setrange()

    def setrange(self, min=None, max=None):
        if (not self.fixmin) and (min is not None):
            self.min = min
        if (not self.fixmax) and (max is not None):
            self.max = max
        if (self.min is not None) and (self.max is not None):
            if self.reverse:
                self.setbasepts(((self.min, 1), (self.max, 0)))
            else:
                self.setbasepts(((self.min, 0), (self.max, 1)))

    def saverange(self):
        return (self.min, self.max)

    def restorerange(self, savedrange):
        self.min, self.max = savedrange
        self.setrange()


class linaxis(_axis, _linmap):

    def __init__(self, part=autolinpart(), rate=momrate(), **args):
        _axis.__init__(self, **args)
        self.part = part
        self.rate = rate


class logaxis(_axis, _logmap):

    def __init__(self, part=autologpart(), rate=momrate(momrate.logdefaulttickrateparams, momrate.logdefaultlabelrateparams), **args):
        _axis.__init__(self, **args)
        self.part = part
        self.rate = rate



################################################################################
# graph
################################################################################

class _PlotData:

    def __init__(self, data, style):
        self.data = data
        self.style = style


_XPattern = re.compile(r"x([2-9]|[1-9][0-9]+)?$")
_YPattern = re.compile(r"y([2-9]|[1-9][0-9]+)?$")
_DXPattern = re.compile(r"dx([2-9]|[1-9][0-9]+)?$")
_DYPattern = re.compile(r"dy([2-9]|[1-9][0-9]+)?$")


class graphxy(canvas.canvas):

    plotdata = [ ]

    def __init__(self, tex, xpos=0, ypos=0, width=None, height=None, ratio=goldenrule, **axes):
        canvas.canvas.__init__(self)
        self.tex = tex
        self.xpos = unit.topt(xpos)
        self.ypos = unit.topt(ypos)
        if (width is not None) and (height is None):
             height = width / ratio
        if (height is not None) and (width is None):
             width = height * ratio
        assert width > 0
        assert height > 0
        self.width = unit.topt(width)
        self.height = unit.topt(height)
        if "x" not in axes.keys():
            axes["x"] = linaxis()
        if "y" not in axes.keys():
            axes["y"] = linaxis()
        self.axes = axes
        self._drawstate = self.drawlayout

    def plot(self, Data, PlotStyle = None):
        if self._drawstate != self.drawlayout:
            raise PyxGraphDrawstateError
        if not PlotStyle:
            PlotStyle = Data.DefaultPlotStyle
        self.plotdata.append(_PlotData(Data, PlotStyle))

    def bbox(self):
        return bbox.bbox(self.xpos, self.ypos, self.xpos + self.width, self.ypos + self.height)

    def gatherranges(self):
        ranges = {}
        for pd in self.plotdata:
            pdranges = pd.data.ranges()
            for kind in pdranges.keys():
                if kind not in ranges.keys():
                    ranges[kind] = pdranges[kind]
                else:
                    ranges[kind] = (min(ranges[kind][0], pdranges[kind][0]),
                                    max(ranges[kind][1], pdranges[kind][1]))
        return ranges

    def drawlayout(self):
        if self._drawstate != self.drawlayout:
            raise PyxGraphDrawstateError

        # create list of ranges
        # 1. gather ranges
        ranges = self.gatherranges()
        # 2. calculate additional ranges out of known ranges
        for pd in self.plotdata:
            pd.data.newranges(ranges)
        # 3. gather ranges again
        ranges = self.gatherranges()

        # set axes ranges
        for key, axis in self.axes.items():
            axis.setrange(min=ranges[key][0], max=ranges[key][1])

        for key, axis in self.axes.items():
            axis.parts = axis.part.getparts(axis.min, axis.max) # TODO: make use of stretch
            if len(axis.parts) > 1:
                axis.bestnum = 0
                axis.rates = []
                bestrate = None
                for i in range(len(axis.parts)):
                    rate = axis.rate.getrate(axis.parts[i], 1) # TODO: make use of stretch
                    axis.rates.append(rate)
                    if (bestrate is None) or ((rate is not None) and (bestrate > rate)):
                        axis.bestnum = i
                        bestrate = rate
            else:
                axis.rates = [0, ]
                axis.bestnum = 0

            # axis.savedrange = axis.saverange()
            # TODO: Additional ratings (spacing of text etc.)
            axis.bestpart = axis.parts[axis.bestnum]
            axis.setrange(min=float(axis.bestpart[0]),
                          max=float(axis.bestpart[-1]))

        self.xmap = _linmap().setbasepts(((0, self.xpos), (1, self.xpos + self.width)))
        self.ymap = _linmap().setbasepts(((0, self.ypos), (1, self.ypos + self.height)))
        self._drawstate = self.drawbackground

    def drawbackground(self):
        if self._drawstate != self.drawbackground:
            raise PyxGraphDrawstateError
        self.draw(path._rect(self.xmap.convert(0),
                             self.ymap.convert(0),
                             self.xmap.convert(1) - self.xmap.convert(0),
                             self.ymap.convert(1) - self.ymap.convert(0)))
        self._drawstate = self.drawaxes

    def drawaxes(self):
        if self._drawstate != self.drawaxes:
            raise PyxGraphDrawstateError
        for key, axis in self.axes.items():
            if _XPattern.match(key):
                for tick in axis.bestpart:
                    x = self.xmap.convert(axis.convert(float(tick)))
                    if tick.ticklevel is not None:
                        axis.tickpainter.paint(self, x, self.ymap.convert(0), 0, 1, tick,
                                               path._line(x, self.ymap.convert(0), x, self.ymap.convert(1)))
                    if tick.labellevel is not None:
                        axis.labelpainter.paint(self, x, self.ymap.convert(0), 0, 1, tick)
            elif _YPattern.match(key):
                for tick in axis.bestpart:
                    y = self.ymap.convert(axis.convert(float(tick)))
                    if tick.ticklevel is not None:
                        axis.tickpainter.paint(self, self.xmap.convert(0), y, 1, 0, tick,
                                               path._line(self.xmap.convert(0), y, self.xmap.convert(1), y))
                    if tick.labellevel is not None:
                        axis.labelpainter.paint(self, self.xmap.convert(0), y, 1, 0, tick)
            else:
                assert 0, "Axis key %s not allowed" % key
        self._drawstate = self.drawdata

    def drawdata(self):
        if self._drawstate != self.drawdata:
            raise PyxGraphDrawstateError
        for pd in self.plotdata:
            pd.data.loop(self, pd.style)
        self._drawstate = None

    def bbox(self):
        while self._drawstate is not None:
            self._drawstate()
        return canvas.canvas.bbox(self)

    def write(self, file):
        while self._drawstate is not None:
            self._drawstate()
        canvas.canvas.write(self, file)

#    def VirToPos(self, Type, List):
#        return self.VirMap[Type].convert(List)
#
#    def ValueList(self, Pattern, Type, Data):
#        (key, ) = filter(lambda x, Pattern = Pattern: Pattern.match(x), Data.GetKindList())
#        return self.VirToPos(Type, self.Axis[key].convert(Data.GetValues(key)))



################################################################################
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
################################################################################

class _PlotStyle:

    pass


#class line(_PlotStyle):
#
#    def LoopOverPoints(self, Graph, Data):
#        p = [ ]
#        for pt in zip(Graph.ValueList(_XPattern, 0, Data),
#                      Graph.ValueList(_YPattern, 1, Data)):
#            if p:
#                p.append(path._lineto(pt[0],pt[1]))
#            else:
#                p = [path._moveto(pt[0],pt[1]), ]
#        Graph.canvas.draw(path(*p))


class mark(_PlotStyle):

    def __init__(self, size = 1):
        self.size = size

    def draw(self, graph, keys, data):
        if _XPattern.match(keys[0]): xindex, yindex = 0, 1
        if _XPattern.match(keys[1]): xindex, yindex = 1, 0
        xaxis = graph.axes[keys[xindex]]
        yaxis = graph.axes[keys[yindex]]
        for pt in data:
            graph.draw(path.path(path._moveto(graph.xmap.convert(xaxis.convert(pt[xindex])) - self.size,
                                              graph.ymap.convert(yaxis.convert(pt[yindex])) - self.size),
                                 path._lineto(graph.xmap.convert(xaxis.convert(pt[xindex])) + self.size,
                                              graph.ymap.convert(yaxis.convert(pt[yindex])) + self.size),
                                 path._moveto(graph.xmap.convert(xaxis.convert(pt[xindex])) - self.size,
                                              graph.ymap.convert(yaxis.convert(pt[yindex])) + self.size),
                                 path._lineto(graph.xmap.convert(xaxis.convert(pt[xindex])) + self.size,
                                              graph.ymap.convert(yaxis.convert(pt[yindex])) - self.size)))


################################################################################
# data
################################################################################

from mathtree import *
import re

CommentPattern = re.compile(r"\s*(#|!)+\s*")

class datafile:

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


class data:

    DefaultPlotStyle = mark()

    def __init__(self, datafile, **columns):
        self.datafile = datafile
        self.columns = columns

    def ranges(self):
        result = {}
        for kind, key in self.columns.items():
            result[kind] = (min(self.datafile.data[key - 1]), max(self.datafile.data[key - 1]))
        return result

    def newranges(self, ranges):
        pass

    def GetName(self):
        return self.datafile.name

    def GetKindList(self):
        return self.columns.keys()

    def GetTitle(self, Kind):
        return self.datafile.GetTitle(self.columns[Kind] - 1)

    def GetValues(self, Kind):
        return self.datafile.GetColumn(self.columns[Kind] - 1)

    def loop(self, graph, style):
        columns = {}
        for kind in self.GetKindList():
            columns[kind] = self.GetValues(kind)
        style.draw(graph, columns.keys(), zip(*columns.values()))

#    def GetRange(self, Kind):
#        # handle non-numeric things properly
#        if Kind not in self.columns.keys():
#            raise DataRangeUndefinedException
#        return (min(self.GetValues(Kind)), max(self.GetValues(Kind)), )


AssignPattern = re.compile(r"\s*([a-z][a-z0-9_]*)\s*=", re.IGNORECASE)


class Function:

    #DefaultPlotStyle = chain()
    DefaultPlotStyle = mark()

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

#    def GetRange(self, Kind):
#        raise DataRangeUndefinedException
#
#    def SetAxis(self, Axis, DefaultResult = "y"):
#        if self.ResKind:
#            self.YAxis = Axis[self.ResKind]
#        else:
#            self.YAxis = Axis[DefaultResult]
#        self.XAxis = { }
#        self.XValues = { }
#        for key in self.MT.VarList():
#            self.XAxis[key] = Axis[key]
#            values = []
#            for x in range(self.Points + 1):
#                values.append(self.XAxis[key].invert(x * 1.0 / self.Points))
#            self.XValues[key] = values
#        # this isn't smart ... we should walk only once throu the mathtree
#        self.YValues = map(lambda i, self = self: self.MT.Calc(self.XValues, i), range(self.Points + 1))

    def GetValues(self, Kind, DefaultResult = "y"):
        if (self.ResKind and (Kind == self.ResKind)) or ((not self.ResKind) and (Kind == DefaultResult)):
            return self.YValues
        return self.XValues[Kind]


class ParamFunction(Function):
    # TODO: to be written
    pass



################################################################################
# key
################################################################################

# to be written
