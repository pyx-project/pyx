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


import types, re, math, string, sys
import bbox, canvas, path, tex, unit, mathtree, trafo, attrlist

goldenrule = 0.5 * (math.sqrt(5) + 1)


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
        self.basepts = ((math.log(basepts[0][0]), basepts[0][1], ),
                        (math.log(basepts[1][0]), basepts[1][1], ), )
        return self

    def _convert(self, value):
        return _linmap._convert(self, math.log(value))

    def _invert(self, value):
        return math.exp(_linmap._invert(self, value))



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

    def __init__(self, labeltext=None):
        self.labeltext = labeltext

    def mergeticklists(self, list1, list2):
        # TODO: could be improved??? (read python cookbook carefully)
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

    def setlabeltext(self, part):
        if self.labeltext is not None:
            for tick, label in zip([tick for tick in part if tick.labellevel == 0], self.labeltext):
                tick.text = label

class linpart(anypart):

    def __init__(self, tickfracs=None, labelfracs=None,
                 extendtoticklevel=0, extendtolabellevel=None, epsilon=1e-10, **args):
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
        anypart.__init__(self, **args)

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
        if tickfracs is None and tickfracs is None:
            tickfracs = self.tickfracs
            labelfracs = self.labelfracs
        else:
            assert self.tickfracs is None
            assert self.labelfracs is None
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

        self.setlabeltext(ticks)
        return ticks

    def getparts(self, min, max):
        return [self.getticks(min, max), ]


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
        e = int(math.log(max - min) / math.log(10))
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
                 extendtoticklevel=0, extendtolabellevel=None, epsilon=1e-10, **args):
        """
        For the parameters tickshiftfracslist and labelshiftfracslist apply
        rules like for tickfracs and labelfracs in linpart.
        """
        self.tickshiftfracslist = tickshiftfracslist
        self.labelshiftfracslist = labelshiftfracslist
        self.extendtoticklevel = extendtoticklevel
        self.extendtolabellevel = extendtolabellevel
        self.epsilon = epsilon
        anypart.__init__(self, **args)

    def extendminmax(self, min, max, shiftfracs):
        minpower = None
        maxpower = None
        for i in xrange(len(shiftfracs.fracs)):
            imin = int(math.floor(math.log(min / float(shiftfracs.fracs[i])) /
                                  math.log(shiftfracs.shift) + 0.5 * self.epsilon)) + 1
            imax = int(math.ceil(math.log(max / float(shiftfracs.fracs[i])) /
                                 math.log(shiftfracs.shift) - 0.5 * self.epsilon)) - 1
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
        return (float(minfrac) * math.pow(10, minpower),
                float(maxfrac) * math.pow(10, maxpower), )

    def getticklist(self, min, max, shiftfracs, ticklevel=None, labellevel=None):
        ticks = []
        minimin = 0
        maximax = 0
        for f in shiftfracs.fracs:
            fracticks = []
            imin = int(math.ceil(math.log(min / float(f)) /
                                 math.log(shiftfracs.shift) - 0.5 * self.epsilon))
            imax = int(math.floor(math.log(max / float(f)) /
                                  math.log(shiftfracs.shift) + 0.5 * self.epsilon))
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

        self.setlabeltext(ticks)
        return ticks

    def getparts(self, min, max):
        return [self.getticks(min, max), ]

class autologpart(logpart):
    shift5fracs1   = shiftfracs(100000, frac(1, 10))
    shift4fracs1   = shiftfracs(10000, frac(1, 10))
    shift3fracs1   = shiftfracs(1000, frac(1, 10))
    shift2fracs1   = shiftfracs(100, frac(1, 10))
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

                              ((shift2fracs1,     # ticks
                                shiftfracs1),     # subticks
                               None),             # labels like ticks

                              ((shift3fracs1,     # ticks
                                shiftfracs1),     # subticks
                               None),             # labels like ticks

                              ((shift4fracs1,     # ticks
                                shiftfracs1),     # subticks
                               None),             # labels like ticks

                              ((shift5fracs1,     # ticks
                                shiftfracs1),     # subticks
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
    def __init__(self, fixfracs, **args):
        sfpart.__init__(self, **args)
        self.fixfracs = fixfracs


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

        def min(self, pinch):
            return self.minoffset + self.minfactor * (pinch - 1.0) * self.optfactor

        def opt(self, pinch):
            return float(self.optfactor * pinch)

        def max(self, pinch):
            return self.maxoffset + self.maxfactor * (pinch - 1.0) * self.optfactor

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

    def evalrate(self, val, pinch, rateparam):
        opt = rateparam.opt(pinch)
        min = rateparam.min(pinch)
        max = rateparam.max(pinch)
        rate = ((opt - min) * math.log((opt - min) / (val - min)) +
                (max - opt) * math.log((max - opt) / (max - val))) / (max - min)
        return rate

    def getrate(self, ticks, pinch):
        rate = 0
        weight = 0
        (tickcounts, labelcounts, ) = self.getcounts(ticks)
        try:
            for (tickcount, rateparam, ) in zip(tickcounts, self.tickrateparams, ):
                rate += self.evalrate(tickcount, pinch, rateparam) * rateparam.weight
                weight += rateparam.weight
            for (labelcount, rateparam, ) in zip(labelcounts, self.labelrateparams, ):
                rate += self.evalrate(labelcount, pinch, rateparam) * rateparam.weight
                weight += rateparam.weight
            rate /= weight
        except (ZeroDivisionError, ValueError):
            rate = None
        return rate

#min = 1
#for i in range(1, 10000):
#    max = min * math.pow(1.5, i)
#    if max > 1e10:
#        break
#    print max/min,
#    for ticks in autologpart(extendtoticklevel = None).getparts(min, max):
#        rate = momrate(momrate.logdefaulttickrateparams,
#                       momrate.logdefaultlabelrateparams).getrate(ticks, 1)
#        print rate,
#    print


################################################################################
# box alignment, connections, distances ...
# (we may create a box drawing module and move all this stuff there)
################################################################################

class _alignbox:

    def __init__(self, *points):
        self.points = len(points) - 1
        self.x, self.y = zip(*points)

    def path(self, centerradius = "0.05 v cm"):
        r = unit.topt(unit.length(centerradius, default_type="v"))
        pathels = [path._arc(self.x[0], self.y[0], r, 0, 360)]
        pathels.append(path._moveto(self.x[1], self.y[1]))
        for x, y in zip(self.x, self.y)[2:]:
            pathels.append(path._lineto(x, y))
        pathels.append(path.closepath())
        return path.path(*pathels)

    def transform(self, trafo):
        self.x, self.y = zip(*map(lambda i, trafo=trafo, x=self.x, y=self.y:
                                      trafo._apply(x[i], y[i]), range(self.points + 1)))

    def successivepoints(self):
        return map(lambda i, max = self.points: i and (i, i + 1) or (max, 1), range(self.points))

    def _circlealignlinevector(self, a, dx, dy, ex, ey, fx, fy, epsilon=1e-10):
        cx, cy = self.x[0], self.y[0]
        gx, gy = ex - fx, ey - fy # direction vector
        if gx*gx + gy*gy < epsilon: # zero line length
            return None             # no solution -> return None
        rsplit = (dx*gx + dy*gy) * 1.0 / (gx*gx + gy*gy)
        bx, by = dx - gx * rsplit, dy - gy * rsplit
        if bx*bx + by*by < epsilon: # zero projection
            return None             # no solution -> return None
        if bx*gy - by*gx < 0: # half space
            return None       # no solution -> return None
        sfactor = math.sqrt((dx*dx + dy*dy) / (bx*bx + by*by))
        bx, by = a * bx * sfactor, a * by * sfactor
        alpha = ((bx+cx-ex)*dy - (by+cy-ey)*dx) * 1.0 / (gy*dx - gx*dy)
        if alpha > 0 - epsilon and alpha < 1 + epsilon:
                beta = ((ex-bx-cx)*gy - (ey-by-cy)*gx) * 1.0 / (gx*dy - gy*dx)
                return beta*dx - cx, beta*dy - cy # valid solution -> return align tuple
        # crossing point at the line, but outside a valid range
        if alpha < 0:
            return 0 # crossing point outside e
        return 1 # crossing point outside f

    def _linealignlinevector(self, a, dx, dy, ex, ey, fx, fy, epsilon=1e-10):
        cx, cy = self.x[0], self.y[0]
        gx, gy = ex - fx, ey - fy # direction vector
        if gx*gx + gy*gy < epsilon: # zero line length
            return None             # no solution -> return None
        if gy*dx - gx*dy < -epsilon: # half space
            return None              # no solution -> return None
        if dx*gx + dy*gy > epsilon or dx*gx + dy*gy < -epsilon:
            if dx*gx + dy*gy < 0: # angle bigger 90 degree
                return 0 # use point e
            return 1 # use point f
        # a and g are othorgonal
        alpha = ((a*dx+cx-ex)*dy - (a*dy+cy-ey)*dx) * 1.0 / (gy*dx - gx*dy)
        if alpha > 0 - epsilon and alpha < 1 + epsilon:
            beta = ((ex-a*dx-cx)*gy - (ey-a*dy-cy)*gx) * 1.0 / (gx*dy - gy*dx)
            return beta*dx - cx, beta*dy - cy # valid solution -> return align tuple
        # crossing point at the line, but outside a valid range
        if alpha < 0:
            return 0 # crossing point outside e
        return 1 # crossing point outside f

    def _circlealignpointvector(self, a, dx, dy, px, py, epsilon=1e-10):
        if a*a < epsilon:
            return None
        cx, cy = self.x[0], self.y[0]
        p = 2 * ((px-cx)*dx + (py-cy)*dy)
        q = ((px-cx)*(px-cx) + (py-cy)*(py-cy) - a*a)
        if p*p/4 - q < 0:
            return None
        if a > 0:
            alpha = - p / 2 + math.sqrt(p*p/4 - q)
        else:
            alpha = - p / 2 - math.sqrt(p*p/4 - q)
        return alpha*dx - cx, alpha*dy - cy

    def _linealignpointvector(self, a, dx, dy, px, py):
        cx, cy = self.x[0], self.y[0]
        beta = (a*dx+cx-px)*dy - (a*dy+cy-py)*dx
        return a*dx - beta*dy - px, a*dy + beta*dx - py

    def _alignvector(self, a, dx, dy, alignlinevector, alignpointvector):
        linevectors = map(lambda (i, j), self=self, a=a, dx=dx, dy=dy, x=self.x, y=self.y, alignlinevector=alignlinevector:
                                alignlinevector(a, dx, dy, x[i], y[i], x[j], y[j]), self.successivepoints())
        for linevector in linevectors:
            if type(linevector) is types.TupleType:
                return linevector
        for i, j in self.successivepoints():
            if ((linevectors[i-1] == 1 and linevectors[j-1] == 0) or
                (linevectors[i-1] == 1 and linevectors[j-1] is None) or
                (linevectors[i-1] is None and linevectors[j-1] == 0)):
                k = j == 1 and self.points or j - 1
                return alignpointvector(a, dx, dy, self.x[k], self.y[k])
        return a*dx, a*dy

    def _circlealignvector(self, a, dx, dy):
        return self._alignvector(a, dx, dy, self._circlealignlinevector, self._circlealignpointvector)

    def _linealignvector(self, a, dx, dy):
        return self._alignvector(a, dx, dy, self._linealignlinevector, self._linealignpointvector)

    def circlealignvector(self, a, dx, dy):
        return self._circlealignvector(unit.topt(a), dx, dy)

    def linealignvector(self, a, dx, dy):
        return self._linealignvector(unit.topt(a), dx, dy)

    def _circlealign(self, *args):
        self.transform(trafo._translate(*self._circlealignvector(*args)))
        return self

    def _linealign(self, *args):
        self.transform(trafo._translate(*self._linealignvector(*args)))
        return self

    def circlealign(self, *args):
        self.transform(trafo._translate(*self.circlealignvector(*args)))
        return self

    def linealign(self, *args):
        self.transform(trafo._translate(*self.linealignvector(*args)))
        return self

    def extent(self, dx, dy):
        x1, y1 = self._linealignvector(0, dx, dy)
        x2, y2 = self._linealignvector(0, -dx, -dy)
        return (x1-x2)*dx + (y1-y2)*dy


class alignbox(_alignbox):

    def __init__(self, *args):
        args = map(lambda x: x, map(lambda x, unit=unit: unit.topt(x), args))
        _alignbox.__init__(self, *args)


class _rectbox(_alignbox):

    def __init__(self, llx, lly, urx, ury, x0=0, y0=0):
        if llx > urx: llx, urx = urx, llx
        if lly > ury: lly, ury = ury, lly
        _alignbox.__init__(self, (x0, y0), (llx, lly), (urx, lly), (urx, ury), (llx, ury))


class rectbox(_rectbox):

    def __init__(self, *arglist, **argdict):
        arglist = map(lambda x, unit=unit: unit.topt(x), arglist)
        for key in argdict.keys():
            argdict[key] = unit.topt(argdict[key])
        _rectbox.__init__(self, *argslist, **argdict)


class textbox(_rectbox, attrlist.attrlist):

    def __init__(self, _tex, text, textstyles = (), vtext="0"):
        self.tex = _tex
        self.text = text
        self.textstyles = textstyles
        self.reldx, self.reldy = 1, 0
        self.halign = self.attrget(self.textstyles, tex.halign, None)
        self.textstyles = self.attrdel(self.textstyles, tex.halign)
        self.direction = self.attrget(self.textstyles, tex.direction, None)
        hwdtextstyles = self.attrdel(self.textstyles, tex.direction)
        self.ht = unit.topt(self.tex.textht(text, *hwdtextstyles))
        self.wd = unit.topt(self.tex.textwd(text, *hwdtextstyles))
        self.dp = unit.topt(self.tex.textdp(text, *hwdtextstyles))
        self.shiftht = 0.5 * unit.topt(self.tex.textht(vtext, *hwdtextstyles))
        self.manualextents()

    def manualextents(self, ht = None, wd = None, dp = None, shiftht = None):
        if ht is not None: self.ht = ht
        if wd is not None: self.wd = wd
        if dp is not None: self.dp = dp
        if shiftht is not None: self.shiftht = None
        self.xtext = 0
        self.ytext = 0
        xorigin = 0.5 * self.wd
        if self.halign is not None:
            if self.halign == tex.halign.left:
                xorigin = 0
            if self.halign == tex.halign.right:
                xorigin = self.wd
        _rectbox.__init__(self, 0, -self.dp, self.wd, self.ht, xorigin, self.shiftht)
        if self.direction is not None:
            self.transform(trafo._rotate(self.direction.value))

    def transform(self, trafo):
        _rectbox.transform(self, trafo)
        self.xtext, self.ytext = trafo._apply(self.xtext, self.ytext)

    def _printtext(self, x, y):
        self.tex._text(x + self.xtext, y + self.ytext, self.text, *self.textstyles)

    def printtext(self, x, y):
        self._printtext(unit.topt(x), unit.topt(y))


################################################################################
# axis painter
################################################################################

class axispainter(attrlist.attrlist):

    paralleltext = -90
    orthogonaltext = 0

    fractypeauto = 1
    fractypedec = 2
    fractypeexp = 3
    fractyperat = 4

    def __init__(self, innerticklength="0.2 cm",
                       outerticklength="0 cm",
                       tickstyles=(),
                       subticklengthfactor=1/goldenrule,
                       drawgrid=0,
                       gridstyles=canvas.linestyle.dotted,
                       labeldist="0.3 cm",
                       labelstyles=((), (tex.fontsize.footnotesize,)),
                       labeldirection=None,
                       labelhequalize=0,
                       labelvequalize=1,
                       titledist="0.3 cm",
                       fractype=fractypeauto,
                       decfracpoint=".",
                       expfractimes="\cdot",
                       expfracpre1=0,
                       expfracminexp=4,
                       presuf0=0,
                       presuf1=0):
        self.innerticklength_str = innerticklength
        self.outerticklength_str = outerticklength
        self.tickstyles = tickstyles
        self.subticklengthfactor = subticklengthfactor
        self.drawgrid = drawgrid
        self.gridstyles = gridstyles
        self.labeldist_str = labeldist
        self.labelstyles = list(labelstyles)
        self.labeldirection = labeldirection
        self.labelhequalize = labelhequalize
        self.labelvequalize = labelvequalize
        self.titledist_str = titledist
        self.fractype = fractype
        self.decfracpoint = decfracpoint
        self.expfractimes = expfractimes
        self.expfracpre1 = expfracpre1
        self.expfracminexp = expfracminexp
        self.presuf0 = presuf0
        self.presuf1 = presuf1

    def reldirection(self, direction, dx, dy, epsilon=1e-10):
        direction += math.atan2(dy, dx) * 180 / math.pi
        while (direction > 90 + epsilon):
            direction -= 180
        while (direction < -90 - epsilon):
            direction += 180
        return direction

    def gcd(self, m, n):
        # calculate greates common divisor
        if m < 0: m = -m
        if n < 0: n = -n
        if m < n:
            m, n = n, m
        while n > 0:
            m, (dummy, n) = n, divmod(m, n)
        return m

    def decfrac(self, m, n):
        gcd = self.gcd(m, n)
        (m, dummy1), (n, dummy2) = divmod(m, gcd), divmod(n, gcd)
        frac, rest = divmod(m, n)
        strfrac = str(frac)
        rest = m % n
        if rest:
            strfrac += self.decfracpoint
        oldrest = []
        while (rest):
            if rest in oldrest:
                periodstart = len(strfrac) - (len(oldrest) - oldrest.index(rest))
                strfrac = strfrac[:periodstart] + r"\overline{" + strfrac[periodstart:] + "}"
                break
            oldrest += [rest]
            rest *= 10
            frac, rest = divmod(rest, n)
            strfrac += str(frac)
        return strfrac

    def expfrac(self, m, n, minexp = None):
        exp = 0
        while divmod(m, n)[0] > 9:
            n *= 10
            exp += 1
        while divmod(m, n)[0] < 1:
            m *= 10
            exp -= 1
        if minexp is not None and ((exp < 0 and -exp < minexp) or (exp >= 0 and exp < minexp)):
            return None
        prefactor = self.decfrac(m, n)
        if prefactor == "1" and not self.expfracpre1:
            return r"10^{%i}" % exp
        else:
            return prefactor + r"%s10^{%i}" % (self.expfractimes, exp)

    def ratfrac(self, m, n):
        gcd = self.gcd(m, n)
        (m, dummy1), (n, dummy2) = divmod(m, gcd), divmod(n, gcd)
        if n != 1:
            frac = "{{%s}\over{%s}}" % (m, n)
        else:
            frac = str(m)
        return frac

    def selectstyle(self, number, styles):
        if type(styles) not in (types.TupleType, types.ListType):
            return [styles,]
        else:
            try:
                if type(styles[0]) not in (types.TupleType, types.ListType):
                    return list(styles)
            except IndexError:
                return list(styles)
            return list(styles[number])

    def paint(self, graph, axis):
        innerticklength = unit.topt(unit.length(self.innerticklength_str, default_type="v"))
        outerticklength = unit.topt(unit.length(self.outerticklength_str, default_type="v"))
        labeldist = unit.topt(unit.length(self.labeldist_str, default_type="v"))
        titledist = unit.topt(unit.length(self.titledist_str, default_type="v"))

        haslabel = 0
        for tick in axis.ticks:
            tick.virtual = axis.convert(float(tick) * axis.factor)
            tick.x, tick.y = axis.tickpoint(axis, tick.virtual)
            tick.dx, tick.dy = axis.tickdirection(axis, tick.virtual)
            if tick.labellevel is not None:
                if tick.labellevel + 1 > haslabel:
                    haslabel = tick.labellevel + 1

        if haslabel:
            for tick in axis.ticks:
                if tick.labellevel is not None:
                    tick.labelstyles = self.selectstyle(tick.labellevel, self.labelstyles)
                    if not hasattr(tick, "text"):
                        if self.fractype == axispainter.fractypeauto:
                            if axis.prefix is not None or axis.suffix is not None:
                                tick.text = self.ratfrac(tick.enum, tick.denom)
                            else:
                                tick.text = self.expfrac(tick.enum, tick.denom, self.expfracminexp)
                                if tick.text is None:
                                    tick.text = self.decfrac(tick.enum, tick.denom)
                        elif self.fractype == axispainter.fractypedec:
                            tick.text = self.decfrac(tick.enum, tick.denom)
                        elif self.fractype == axispainter.fractypeexp:
                            tick.text = self.expfrac(tick.enum, tick.denom)
                        elif self.fractype == axispainter.fractyperat:
                            tick.text = self.ratfrac(tick.enum, tick.denom)
                        else:
                            raise ValueError("fractype invalid")
                        if self.presuf0 or tick.enum:
                            if tick.enum == tick.denom and (axis.prefix is not None or
                                                            axis.suffix is not None) and not self.presuf1:
                                tick.text = ""
                            if axis.prefix is not None:
                                tick.text = axis.prefix + tick.text
                            if axis.suffix is not None:
                                tick.text = tick.text + axis.suffix
                        if not self.attrcount(tick.labelstyles, tex.direction):
                            tick.labelstyles += [tex.style.math]
                    if self.labeldirection is not None and not self.attrcount(axis.labelstyles, tex.direction):
                        tick.labelstyles += [tex.direction(self.reldirection(self.labeldirection, tick.dx, tick.dy))]
                    tick.textbox = textbox(graph.tex, tick.text, textstyles = tick.labelstyles)

            for tick in axis.ticks[1:]:
                if tick.dx != axis.ticks[0].dx or tick.dy != axis.ticks[0].dy:
                    equaldirection = 0
                    break
            else:
                equaldirection = 1

            if equaldirection:
                maxht, maxwd, maxdp = 0, 0, 0
                for tick in axis.ticks:
                    if tick.labellevel is not None:
                        if maxht < tick.textbox.ht: maxht = tick.textbox.ht
                        if maxwd < tick.textbox.wd: maxwd = tick.textbox.wd
                        if maxdp < tick.textbox.dp: maxdp = tick.textbox.dp
                for tick in axis.ticks:
                    if tick.labellevel is not None:
                        if self.labelhequalize:
                            tick.textbox.manualextents(wd = maxwd)
                        if self.labelvequalize:
                            tick.textbox.manualextents(ht = maxht, dp = maxdp)

            for tick in axis.ticks:
                if tick.labellevel is not None:
                    tick.textbox._linealign(labeldist, tick.dx, tick.dy)
                    tick.extent = tick.textbox.extent(tick.dx, tick.dy) + labeldist

        # we could now measure distances between textboxes -> TODO: rating

        axis.extent = 0
        for tick in axis.ticks:
            if tick.labellevel is None:
                tick.extent = outerticklength * math.pow(self.subticklengthfactor, tick.ticklevel)
            if axis.extent < tick.extent:
                axis.extent = tick.extent

        for tick in axis.ticks:
            if tick.ticklevel is not None:
                if self.drawgrid > tick.ticklevel:
                    gridpath = axis.gridpath(axis, tick.virtual)
                    graph.draw(gridpath, *self.selectstyle(tick.ticklevel, self.gridstyles))
                factor = math.pow(self.subticklengthfactor, tick.ticklevel)
                x1 = tick.x - tick.dx * innerticklength * factor
                y1 = tick.y - tick.dy * innerticklength * factor
                x2 = tick.x + tick.dx * outerticklength * factor
                y2 = tick.y + tick.dy * outerticklength * factor
                graph.draw(path._line(x1, y1, x2, y2), *self.selectstyle(tick.ticklevel, self.tickstyles))
            if tick.labellevel is not None:
                tick.textbox._printtext(tick.x, tick.y)

        if axis.title is not None:
            x, y = axis.tickpoint(axis, 0.5)
            dx, dy = axis.tickdirection(axis, 0.5)
            if axis.titledirection is not None and not self.attrcount(axis.titlestyles, tex.direction):
                axis.titlestyles += [tex.direction(self.reldirection(axis.titledirection, tick.dx, tick.dy))]
            axis.titlebox = textbox(graph.tex, axis.title, textstyles = axis.titlestyles)
            axis.extent += titledist
            axis.titlebox._linealign(axis.extent, dx, dy)
            axis.titlebox._printtext(x, y)
            axis.extent += axis.titlebox.extent(dx, dy)

class linkaxispainter(axispainter):

    def __init__(self, skipticklevel = None, skiplabellevel = 0, **args):
        self.skipticklevel = skipticklevel
        self.skiplabellevel = skiplabellevel
        axispainter.__init__(self, **args)

    def paint(self, graph, axis):
        axis.ticks = []
        for _tick in axis.linkedaxis.ticks:
            ticklevel = _tick.ticklevel
            labellevel = _tick.labellevel
            if self.skipticklevel is not None and ticklevel >= self.skipticklevel:
                ticklevel = None
            if self.skiplabellevel is not None and labellevel >= self.skiplabellevel:
                labellevel = None
            if ticklevel is not None or labellevel is not None:
                axis.ticks.append(tick(_tick.enum, _tick.denom, ticklevel, labellevel))
        axis.convert = axis.linkedaxis.convert

        # XXX: don't forget to calculate new text positions as soon as this is moved
        #      outside of the paint method (when rating is moved into the axispainter)

        axispainter.paint(self, graph, axis)


################################################################################
# axes
################################################################################

class _axis:

    def __init__(self, min=None, max=None, reverse=0,
                       title=None, titlestyles=(), titledirection=axispainter.paralleltext,
                       painter = axispainter(),
                       factor = 1, prefix = None, suffix = None):
        self.fixmin = min is not None
        self.fixmax = max is not None
        self.min = min
        self.max = max
        self.reverse = reverse
        self.title = title
        self.titlestyles = list(titlestyles)
        self.titledirection = titledirection
        self.painter = painter
        self.factor = factor
        self.prefix = prefix
        self.suffix = suffix
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

class linkaxis(_axis):

    def __init__(self, linkedaxis, **args):
        self.linkedaxis = linkedaxis
        if not args.has_key("painter"):
            args["painter"] = linkaxispainter()
        _axis.__init__(self, **args)


################################################################################
# graph
################################################################################

class defaultstyleiterator:

    def __init__(self):
        self.laststyles = {}

    def iteratestyle(self, defaultstyle):
        if self.laststyles.has_key(defaultstyle):
            self.laststyles[defaultstyle] = self.laststyles[defaultstyle].next
        else:
            self.laststyles[defaultstyle] = defaultstyle
        return self.laststyles[defaultstyle]()


_XPattern = re.compile(r"x([2-9]|[1-9][0-9]+)?$")
_YPattern = re.compile(r"y([2-9]|[1-9][0-9]+)?$")
_DXPattern = re.compile(r"dx([2-9]|[1-9][0-9]+)?$")
_DYPattern = re.compile(r"dy([2-9]|[1-9][0-9]+)?$")


class graphxy(canvas.canvas):

    def __init__(self, tex, xpos=0, ypos=0, width=None, height=None, ratio=goldenrule, axesdist="0.8 cm", styleiterator=defaultstyleiterator(), **axes):
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
        if not axes.has_key("x"):
            axes["x"] = linaxis()
        if not axes.has_key("x2"):
            axes["x2"] = linkaxis(axes["x"])
        if not axes.has_key("y"):
            axes["y"] = linaxis()
        if not axes.has_key("y2"):
            axes["y2"] = linkaxis(axes["y"])
        self.axes = axes
        self.axesdist_str = axesdist
        self.styleiterator = styleiterator
        self.data = [ ]
        self._drawstate = self.drawlayout

    def plot(self, data, style = None):
        if self._drawstate != self.drawlayout:
            raise PyxGraphDrawstateError
        if not style:
            style = self.styleiterator.iteratestyle(data.defaultstyle)
        data.setstyle(style)
        self.data.append(data)

    def xtickpoint(self, axis, virtual):
        return (self.xmap.convert(virtual), axis.yaxispos)

    def ytickpoint(self, axis, virtual):
        return (axis.xaxispos, self.ymap.convert(virtual))

    def tickdirection(self, axis, virtual):
        return axis.fixtickdirection

    def xgridpath(self, axis, virtual):
        return path._line(self.xmap.convert(virtual), self.ymap.convert(0),
                          self.xmap.convert(virtual), self.ymap.convert(1))

    def ygridpath(self, axis, virtual):
        return path._line(self.xmap.convert(0), self.ymap.convert(virtual),
                          self.xmap.convert(1), self.ymap.convert(virtual))

    def keynum(self, key):
        try:
            while key[0] in string.letters:
                key = key[1:]
            return int(key)
        except IndexError:
            return 1

    def gatherranges(self):
        ranges = {}
        for data in self.data:
            pdranges = data.ranges()
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
        for data in self.data:
            data.newranges(ranges)
        # 3. gather ranges again
        ranges = self.gatherranges()

        # set axes ranges
        for key, axis in self.axes.items():
            if ranges.has_key(key):
                axis.setrange(min=ranges[key][0], max=ranges[key][1])
            else:
                # TODO: appropriate linkaxis handling
                pass

        # TODO: move rating into the painter
        # move parting into the painter too???
        for key, axis in self.axes.items():
            # TODO: appropriate linkaxis handling
            try:
                axis.part
            except AttributeError:
                continue
            axis.parts = axis.part.getparts(axis.min / axis.factor, axis.max / axis.factor) # TODO: make use of pinch
            if len(axis.parts) > 1:
                axis.partnum = 0
                axis.rates = []
                bestrate = None
                for i in range(len(axis.parts)):
                    rate = axis.rate.getrate(axis.parts[i], 1) # TODO: make use of pinch
                    axis.rates.append(rate)
                    if (bestrate is None) or ((rate is not None) and (bestrate > rate)):
                        axis.partnum = i
                        bestrate = rate
            else:
                axis.rates = [0, ]
                axis.partnum = 0

            # TODO: Additional ratings (spacing of text etc.)
            axis.ticks = axis.parts[axis.partnum]
            axis.setrange(min=float(axis.ticks[0])*axis.factor,
                          max=float(axis.ticks[-1])*axis.factor)

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
        axesdist = unit.topt(unit.length(self.axesdist_str, default_type="v"))
        if self._drawstate != self.drawaxes:
            raise PyxGraphDrawstateError
        self.xaxisextents = [0, 0]
        self.yaxisextents = [0, 0]
        needxaxisdist = [0, 0]
        needyaxisdist = [0, 0]
        items = list(self.axes.items())
        items.sort() #TODO: alphabetical sorting breaks for axis numbers bigger than 9
        for key, axis in items:
            num = self.keynum(key)
            num2 = 1 - num % 2 # x1 -> 0, x2 -> 1, x3 -> 0, x4 -> 1, ...
            num3 = 1 - 2 * (num % 2) # x1 -> -1, x2 -> 1, x3 -> -1, x4 -> 1, ...
            if _XPattern.match(key):
                 if needxaxisdist[num2]:
                     self.xaxisextents[num2] += axesdist
                 axis.yaxispos = self.ymap.convert(num2) + num3*self.xaxisextents[num2]
                 axis.tickpoint = self.xtickpoint
                 axis.fixtickdirection = (0, num3)
                 axis.gridpath = self.xgridpath
                 if needxaxisdist[num2]:
                     x1, y1 = self.xtickpoint(axis, 0)
                     x2, y2 = self.xtickpoint(axis, 1)
                     self.draw(path._line(x1, y1, x2, y2))
            elif _YPattern.match(key):
                 if needyaxisdist[num2]:
                     self.yaxisextents[num2] += axesdist
                 axis.xaxispos = self.xmap.convert(num2) + num3*self.yaxisextents[num2]
                 axis.tickpoint = self.ytickpoint
                 axis.fixtickdirection = (num3, 0)
                 axis.gridpath = self.ygridpath
                 if needyaxisdist[num2]:
                     x1, y1 = self.ytickpoint(axis, 0)
                     x2, y2 = self.ytickpoint(axis, 1)
                     self.draw(path._line(x1, y1, x2, y2))
            else:
                assert 0, "Axis key %s not allowed" % key
            axis.tickdirection = self.tickdirection
            axis.painter.paint(self, axis)
            if _XPattern.match(key):
                 self.xaxisextents[num2] += axis.extent
                 needxaxisdist[num2] = 1
            if _YPattern.match(key):
                 self.yaxisextents[num2] += axis.extent
                 needyaxisdist[num2] = 1
        self._drawstate = self.drawdata

    def drawdata(self):
        if self._drawstate != self.drawdata:
            raise PyxGraphDrawstateError
        for data in self.data:
            data.draw(self)
        self._drawstate = None

    def drawall(self):
        while self._drawstate is not None:
            self._drawstate()

    def bbox(self):
        self.drawall()
        return bbox.bbox(self.xpos - self.yaxisextents[0],
                         self.ypos - self.xaxisextents[0],
                         self.xpos + self.width + self.yaxisextents[1],
                         self.ypos + self.height + self.xaxisextents[1])

    def write(self, file):
        self.drawall()
        canvas.canvas.write(self, file)


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

class plotstyle:

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


class mark(plotstyle):

    def __init__(self, size = "0.1 cm"):
        self.size_str = size

    def draw(self, graph, keys, data):
        size = unit.topt(unit.length(self.size_str, default_type="v"))
        if _XPattern.match(keys[0]): xindex, yindex = 0, 1
        if _XPattern.match(keys[1]): xindex, yindex = 1, 0
        xaxis = graph.axes[keys[xindex]]
        yaxis = graph.axes[keys[yindex]]
        for pt in data:
            graph.draw(self.drawsymbol(size, graph.xmap.convert(xaxis.convert(pt[xindex])),
                                             graph.ymap.convert(yaxis.convert(pt[yindex]))))


class markcross(mark):

    def drawsymbol(self, size, x, y):
        return path.path(path._moveto(x - 0.5 * size, y - 0.5 * size),
                         path._lineto(x + 0.5 * size, y + 0.5 * size),
                         path._moveto(x - 0.5 * size, y + 0.5 * size),
                         path._lineto(x + 0.5 * size, y - 0.5 * size))


class markplus(mark):

    def drawsymbol(self, size, x, y):
        return path.path(path._moveto(x - 0.707106781 * size, y),
                         path._lineto(x + 0.707106781 * size, y),
                         path._moveto(x, y - 0.707106781 * size),
                         path._lineto(x, y + 0.707106781 * size))


class marksquare(mark):

    def drawsymbol(self, size, x, y):
        return path.path(path._moveto(x - 0.5 * size, y - 0.5 * size),
                         path._lineto(x + 0.5 * size, y - 0.5 * size),
                         path._lineto(x + 0.5 * size, y + 0.5 * size),
                         path._lineto(x - 0.5 * size, y + 0.5 * size),
                         path.closepath())


class marktriangle(mark):

    def drawsymbol(self, size, x, y):
        return path.path(path._moveto(x - 0.759835685 * size, y - 0.438691337 * size),
                         path._lineto(x + 0.759835685 * size, y - 0.438691337 * size),
                         path._lineto(x, y + 0.877382675 * size),
                         path.closepath())


class markcircle(mark):

    def drawsymbol(self, size, x, y):
        return path.path(path._moveto(x + 0.564189583 * size, y),
                         path._arc(x, y, 0.564189583 * size, 0, 360),
                         path.closepath())


class markdiamond(mark):

    def drawsymbol(self, size, x, y):
        return path.path(path._moveto(x - 0.537284965 * size, y),
                         path._lineto(x, y - 0.930604859 * size),
                         path._lineto(x + 0.537284965 * size, y),
                         path._lineto(x, y + 0.930604859 * size),
                         path.closepath())


markcross.next = markplus
markplus.next = marksquare
marksquare.next = marktriangle
marktriangle.next = markcircle
markcircle.next = markdiamond
markdiamond.next = markcross


################################################################################
# data
################################################################################


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

    defaultstyle = markcross

    def __init__(self, datafile, **columns):
        self.datafile = datafile
        self.columns = columns

    def setstyle(self, style):
        self.style = style

    def ranges(self):
        result = {}
        for kind, key in self.columns.items():
            result[kind] = (min(self.datafile.data[key - 1]), max(self.datafile.data[key - 1]))
        return result

    def newranges(self, ranges):
        pass

    def draw(self, graph):
        columns = {}
        for kind in self.columns.keys():
            columns[kind] = self.datafile.GetColumn(self.columns[kind] - 1)
        self.style.draw(graph, columns.keys(), zip(*columns.values()))


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
