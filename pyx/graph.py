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
        if type(enum) not in (types.IntType, types.LongType, ): raise ValueError
        if type(denom) not in (types.IntType, types.LongType, ): raise ValueError
        if denom == 0: raise ValueError
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
        if type(y) != types.IntType: raise ValueError
        if y < 0: raise ValueError
        if y:
            y2, yr = divmod(y, 2)
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
        if self != other: raise ValueError
        if (self.ticklevel == None) or ((other.ticklevel != None) and (other.ticklevel < self.ticklevel)):
            self.ticklevel = other.ticklevel
        if (self.labellevel == None) or ((other.labellevel != None) and (other.labellevel < self.labellevel)):
            self.labellevel = other.labellevel


class anypart:

    def __init__(self, labels=None, sublabels=None):
        self.labels = labels
        self.sublabels = sublabels

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

    def setlabels(self, part):
        if self.labels is not None:
            for tick, label in zip([tick for tick in part if tick.labellevel == 0], self.labels):
                tick.text = label
        if self.sublabels is not None:
            for tick, sublabel in zip([tick for tick in part if tick.labellevel == 1], self.sublabels):
                tick.text = sublabel


def _ensuresequence(arg):
    "return arg or (arg,) if it wasn't a sequence before"
    if arg is not None:
        try:
            arg[0]
            try:
                arg + ''
                return (arg,)
            except:
                pass
        except AttributeError:
            return (arg,)
        except IndexError:
            return ()
    return arg


def _ensurefrac(arg):
    "convert string to frac when appropriate"

    def createfrac(str):
        commaparts = str.split(".")
        for part in commaparts:
            if not part.isdigit(): raise ValueError
        if len(commaparts) == 1:
            return frac(int(commaparts[0]), 1)
        elif len(commaparts) == 2:
            result = frac(1, 10l, power=len(commaparts[1]))
            result.enum = int(commaparts[0])*result.denom + int(commaparts[1])
            return result
        else: raise ValueError

    if not isinstance(arg, frac):
        fraction = arg.split("/")
        if len(fraction) > 2: raise ValueError
        value = createfrac(fraction[0])
        if len(fraction) == 2:
            value2 = createfrac(fraction[1])
            value = frac(value.enum * value2.denom, value.denom * value2.enum)
        return value
    return arg

def _nonemap(method, list):
    "like map, but allows for list is None"
    if list is None:
        return None
    return map(method, list)


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
        self.multipart = 0
        self.tickfracs = _nonemap(_ensurefrac, _ensuresequence(tickfracs))
        self.labelfracs = _nonemap(_ensurefrac, _ensuresequence(labelfracs))
        self.extendtoticklevel = extendtoticklevel
        self.extendtolabellevel = extendtolabellevel
        self.epsilon = epsilon
        anypart.__init__(self, **args)

    def extendminmax(self, min, max, extendmin, extendmax, frac):
        if extendmin:
            min = float(frac) * math.floor(min / float(frac) + self.epsilon)
        if extendmax:
            max = float(frac) * math.ceil(max / float(frac) - self.epsilon)
        return min, max

    def getticks(self, min, max, frac, ticklevel=None, labellevel=None):
        imin = int(math.ceil(min / float(frac) - 0.5 * self.epsilon))
        imax = int(math.floor(max / float(frac) + 0.5 * self.epsilon))
        ticks = []
        for i in range(imin, imax + 1):
            ticks.append(tick(long(i) * frac.enum, frac.denom, ticklevel = ticklevel, labellevel = labellevel))
        return ticks

    def getpart(self, min, max, extendmin=0, extendmax=0, tickfracs=None, labelfracs=None):
        """
        When tickfracs or labelfracs are set, they will be taken instead of the
        values provided to the constructor. It is not allowed to provide something
        to tickfracs and labelfracs here and at the constructor at the same time.
        """
        if tickfracs is None and tickfracs is None:
            tickfracs = self.tickfracs
            labelfracs = self.labelfracs
        else:
            if self.tickfracs is not None: raise ValueError
            if self.labelfracs is not None: raise ValueError
        if tickfracs is None:
            if labelfracs is None:
                tickfracs = ()
            else:
                tickfracs = labelfracs
        if labelfracs is None:
            if len(tickfracs):
                labelfracs = (tickfracs[0], )
            else:
                labelfracs = ()

        if self.extendtoticklevel is not None:
            min, max = self.extendminmax(min, max, extendmin, extendmax, tickfracs[self.extendtoticklevel])
        if self.extendtolabellevel is not None:
            min, max = self.extendminmax(min, max, extendmin, extendmax, labelfracs[self.extendtolabellevel])

        ticks = []
        for i in range(len(tickfracs)):
            ticks = self.mergeticklists(ticks, self.getticks(min, max, tickfracs[i], ticklevel = i))
        for i in range(len(labelfracs)):
            ticks = self.mergeticklists(ticks, self.getticks(min, max, labelfracs[i], labellevel = i))

        self.setlabels(ticks)
        return ticks

    defaultpart = getpart


class autolinpart(linpart):
    defaulttickfracslist = ((frac(1, 1), frac(1, 2)),
                            (frac(2, 1), frac(1, 1)),
                            (frac(5, 2), frac(5, 4)),
                            (frac(5, 1), frac(5, 2)))

    def __init__(self, tickfracslist=defaulttickfracslist,
                 extendtoticklevel=0, extendtolabellevel=None, epsilon=1e-10):
        linpart.__init__(self, extendtoticklevel=0, extendtolabellevel=None, epsilon=1e-10)
        self.multipart = 1
        self.tickfracslist = tickfracslist

    def defaultpart(self, min, max, extendmin=0, extendmax=0):
        basefrac = frac(10L, 1, int(math.log(max - min) / math.log(10)))
        tickfracs = self.tickfracslist[0]
        usefracs = [tickfrac*basefrac for tickfrac in tickfracs]
        self.lesstickfracindex = self.moretickfracindex = 0
        self.lessbasefrac = self.morebasefrac = basefrac
        self.usemin, self.usemax, self.useextendmin, self.useextendmax = min, max, extendmin, extendmax
        return self.getpart(self.usemin, self.usemax, self.useextendmin, self.useextendmax, usefracs)

    def lesspart(self):
        if self.lesstickfracindex < len(self.tickfracslist) - 1:
            self.lesstickfracindex += 1
        else:
            self.lesstickfracindex = 0
            self.lessbasefrac.enum *= 10
        tickfracs = self.tickfracslist[self.lesstickfracindex]
        usefracs = [tickfrac*self.lessbasefrac for tickfrac in tickfracs]
        return self.getpart(self.usemin, self.usemax, self.useextendmin, self.useextendmax, usefracs)

    def morepart(self):
        if self.moretickfracindex:
            self.moretickfracindex -= 1
        else:
            self.moretickfracindex = len(self.tickfracslist) - 1
            self.morebasefrac.denom *= 10
        tickfracs = self.tickfracslist[self.moretickfracindex]
        usefracs = [tickfrac*self.morebasefrac for tickfrac in tickfracs]
        return self.getpart(self.usemin, self.usemax, self.useextendmin, self.useextendmax, usefracs)


class shiftfracs:
    def __init__(self, shift, *fracs):
         self.shift = shift
         self.fracs = fracs


class logpart(anypart):

    """
    This class looks like code duplication of linpart. However, it is not,
    because logaxis use shiftfracs instead of fracs all the time.
    """

    shift5fracs1   = shiftfracs(100000, frac(1, 10))
    shift4fracs1   = shiftfracs(10000, frac(1, 10))
    shift3fracs1   = shiftfracs(1000, frac(1, 10))
    shift2fracs1   = shiftfracs(100, frac(1, 10))
    shiftfracs1    = shiftfracs(10, frac(1, 10))
    shiftfracs125  = shiftfracs(10, frac(1, 10), frac(2, 10), frac(5, 10))
    shiftfracs1to9 = shiftfracs(10, *list(map(lambda x: frac(x, 10), range(1, 10))))
    #         ^- we always include 1 in order to get extendto(tick|label)level to work as expected

    def __init__(self, tickshiftfracslist=None, labelshiftfracslist=None,
                 extendtoticklevel=0, extendtolabellevel=None, epsilon=1e-10, **args):
        """
        For the parameters tickshiftfracslist and labelshiftfracslist apply
        rules like for tickfracs and labelfracs in linpart.
        """
        self.multipart = 0
        self.tickshiftfracslist = _ensuresequence(tickshiftfracslist)
        self.labelshiftfracslist = _ensuresequence(labelshiftfracslist)
        self.extendtoticklevel = extendtoticklevel
        self.extendtolabellevel = extendtolabellevel
        self.epsilon = epsilon
        anypart.__init__(self, **args)

    def extendminmax(self, min, max, extendmin, extendmax, shiftfracs):
        minpower = None
        maxpower = None
        for i in xrange(len(shiftfracs.fracs)):
            imin = int(math.floor(math.log(min / float(shiftfracs.fracs[i])) /
                                  math.log(shiftfracs.shift) + 0.5 * self.epsilon)) + 1
            imax = int(math.ceil(math.log(max / float(shiftfracs.fracs[i])) /
                                 math.log(shiftfracs.shift) - 0.5 * self.epsilon)) - 1
            if minpower is None or imin < minpower:
                minpower, minindex = imin, i
            if maxpower is None or imax >= maxpower:
                maxpower, maxindex = imax, i
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
        if extendmin:
            min = float(minfrac) * math.pow(10, minpower)
        if extendmax:
            max = float(maxfrac) * math.pow(10, maxpower)
        return min, max

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

    def getpart(self, min, max, extendmin=0, extendmax=0, tickshiftfracslist=None, labelshiftfracslist=None):
        """
        For the parameters tickshiftfracslist and labelshiftfracslist apply
        rules like for tickfracs and labelfracs in linpart.
        """
        if tickshiftfracslist is None and labelshiftfracslist is None:
            tickshiftfracslist = self.tickshiftfracslist
            labelshiftfracslist = self.labelshiftfracslist
        else:
            if self.tickshiftfracslist is not None: raise ValueError
            if self.labelshiftfracslist is not None: raise ValueError
        if tickshiftfracslist is None:
            if labelshiftfracslist is None:
                tickshiftfracslist = (shiftfracs(10), )
            else:
                tickshiftfracslist = labelshiftfracslist
        if labelshiftfracslist is None:
            if len(tickshiftfracslist):
                labelshiftfracslist = (tickshiftfracslist[0], )
            else:
                labelshiftfracslist = ()

        if self.extendtoticklevel is not None:
            min, max = self.extendminmax(min, max, extendmin, extendmax, tickshiftfracslist[self.extendtoticklevel])
        if self.extendtolabellevel is not None:
            min, max = self.extendminmax(min, max, extendmin, extendmax, labelshiftfracslist[self.extendtolabellevel])

        ticks = []
        for i in range(len(tickshiftfracslist)):
            ticks = self.mergeticklists(ticks, self.getticklist(min, max, tickshiftfracslist[i], ticklevel = i))
        for i in range(len(labelshiftfracslist)):
            ticks = self.mergeticklists(ticks, self.getticklist(min, max, labelshiftfracslist[i], labellevel = i))

        self.setlabels(ticks)
        return ticks

    defaultpart = getpart


class autologpart(logpart):

    defaultshiftfracslists = (((logpart.shiftfracs1,      # ticks
                                logpart.shiftfracs1to9),  # subticks
                               (logpart.shiftfracs1,      # labels
                                logpart.shiftfracs125)),  # sublevels

                              ((logpart.shiftfracs1,      # ticks
                                logpart.shiftfracs1to9),  # subticks
                               None),                     # labels like ticks

                              ((logpart.shift2fracs1,     # ticks
                                logpart.shiftfracs1),     # subticks
                               None),                     # labels like ticks

                              ((logpart.shift3fracs1,     # ticks
                                logpart.shiftfracs1),     # subticks
                               None),                     # labels like ticks

                              ((logpart.shift4fracs1,     # ticks
                                logpart.shiftfracs1),     # subticks
                               None),                     # labels like ticks

                              ((logpart.shift5fracs1,     # ticks
                                logpart.shiftfracs1),     # subticks
                               None))                     # labels like ticks

    def __init__(self, shiftfracslists=defaultshiftfracslists, shiftfracslistsindex=None,
                 extendtoticklevel=0, extendtolabellevel=None, epsilon=1e-10):
        logpart.__init__(self, extendtoticklevel=0, extendtolabellevel=None, epsilon=1e-10)
        self.multipart = 1
        self.shiftfracslists = shiftfracslists
        if shiftfracslistsindex is None:
            shiftfracslistsindex, dummy = divmod(len(shiftfracslists), 2)
        self.shiftfracslistsindex = shiftfracslistsindex

    def defaultpart(self, min, max, extendmin=0, extendmax=0):
        self.usemin, self.usemax, self.useextendmin, self.useextendmax = min, max, extendmin, extendmax
        self.moreshiftfracslistsindex = self.shiftfracslistsindex
        self.lessshiftfracslistsindex = self.shiftfracslistsindex
        return self.getpart(self.usemin, self.usemax, self.useextendmin, self.useextendmax,
                            self.shiftfracslists[self.shiftfracslistsindex][0],
                            self.shiftfracslists[self.shiftfracslistsindex][1])

    def lesspart(self):
        self.moreshiftfracslistsindex += 1
        if self.moreshiftfracslistsindex < len(self.shiftfracslists):
            return self.getpart(self.usemin, self.usemax, self.useextendmin, self.useextendmax,
                                self.shiftfracslists[self.moreshiftfracslistsindex][0],
                                self.shiftfracslists[self.moreshiftfracslistsindex][1])
        return None

    def morepart(self):
        self.lessshiftfracslistsindex -= 1
        if self.lessshiftfracslistsindex >= 0:
            return self.getpart(self.usemin, self.usemax, self.useextendmin, self.useextendmax,
                                self.shiftfracslists[self.lessshiftfracslistsindex][0],
                                self.shiftfracslists[self.lessshiftfracslistsindex][1])
        return None

#print linpart("1/2").getpart(0, 1.9)
#print linpart(("1/2", "0.25")).getpart(0, 1.9)
#print logpart((autologpart.shiftfracs1, autologpart.shiftfracs1to9)).getpart(0.673, 2.4623)
#print autologpart().getparts(0.0432, 24.623)


#class favorautolinpart(autolinpart):
#    """favorfixfrac - shift - frac - partitioning"""
#    # TODO: just to be done ... throw out parts within the favor region -- or what else to do?
#    degreefracs = ((frac( 15, 1), frac(  5, 1)),
#                   (frac( 30, 1), frac( 15, 1)),
#                   (frac( 45, 1), frac( 15, 1)),
#                   (frac( 60, 1), frac( 30, 1)),
#                   (frac( 90, 1), frac( 30, 1)),
#                   (frac( 90, 1), frac( 45, 1)),
#                   (frac(180, 1), frac( 45, 1)),
#                   (frac(180, 1), frac( 90, 1)),
#                   (frac(360, 1), frac( 90, 1)),
#                   (frac(360, 1), frac(180, 1)))
#    # favouring some fixed fracs, e.g. partitioning of an axis in degree
#    def __init__(self, fixfracs, **args):
#        sfpart.__init__(self, **args)
#        self.fixfracs = fixfracs
#
#
#class timepart:
#    """partitioning of times and dates"""
#    # TODO: this will be a difficult subject ...
#    pass



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
        rate = ((opt - min) * math.log((opt - min) / (val - min)) +
                (max - opt) * math.log((max - opt) / (max - val))) / (max - min)
        return rate

    def getrate(self, ticks, stretch):
        if ticks is None:
            return None
        rate = 0
        weight = 0
        tickcounts, labelcounts = self.getcounts(ticks)
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
        pathels = [path._arc(self.x[0], self.y[0], r, 0, 360), path.closepath(), path._moveto(self.x[1], self.y[1])]
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
        self.transform(trafo._translation(*self._circlealignvector(*args)))
        return self

    def _linealign(self, *args):
        self.transform(trafo._translation(*self._linealignvector(*args)))
        return self

    def circlealign(self, *args):
        self.transform(trafo._translation(*self.circlealignvector(*args)))
        return self

    def linealign(self, *args):
        self.transform(trafo._translation(*self.linealignvector(*args)))
        return self

    def extent(self, dx, dy):
        x1, y1 = self._linealignvector(0, dx, dy)
        x2, y2 = self._linealignvector(0, -dx, -dy)
        return (x1-x2)*dx + (y1-y2)*dy


class alignbox(_alignbox):

    def __init__(self, *args):
        args = map(unit.topt, args)
        _alignbox.__init__(self, *args)


class _rectbox(_alignbox):

    def __init__(self, llx, lly, urx, ury, x0=0, y0=0):
        if llx > urx: llx, urx = urx, llx
        if lly > ury: lly, ury = ury, lly
        _alignbox.__init__(self, (x0, y0), (llx, lly), (urx, lly), (urx, ury), (llx, ury))


class rectbox(_rectbox):

    def __init__(self, *arglist, **argdict):
        arglist = map(unit.topt, arglist)
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
            self.transform(trafo._rotation(self.direction.value))

    def transform(self, trafo):
        _rectbox.transform(self, trafo)
        self.xtext, self.ytext = trafo._apply(self.xtext, self.ytext)

    def _printtext(self, x, y):
        self.tex._text(x + self.xtext, y + self.ytext, self.text, *self.textstyles)

    def printtext(self, *args):
        self._printtext(*map(unit.topt, args))


################################################################################
# axis painter
################################################################################

class axispainter(attrlist.attrlist):

    paralleltext = -90
    orthogonaltext = 0

    fractypeauto = 1
    fractyperat = 2
    fractypedec = 3
    fractypeexp = 4

    def __init__(self, innerticklength="0.2 cm",
                       outerticklength="0 cm",
                       tickstyles=None,
                       subticklengthfactor=1/goldenrule,
                       drawgrid=0,
                       gridstyles=canvas.linestyle.dotted,
                       zerolinestyles=(),
                       labeldist="0.3 cm",
                       labelstyles=((), tex.fontsize.footnotesize),
                       labeldirection=None,
                       labelhequalize=0,
                       labelvequalize=1,
                       titledist="0.3 cm",
                       titlestyles=None,
                       titledirection=-90,
                       fractype=fractypeauto,
                       ratfracsuffixenum=1,
                       ratfracover=r"\over",
                       decfracpoint=".",
                       expfractimes=r"\cdot",
                       expfracpre1=0,
                       expfracminexp=4,
                       suffix0=0,
                       suffix1=0):
        self.innerticklength_str = innerticklength
        self.outerticklength_str = outerticklength
        self.tickstyles = tickstyles
        self.subticklengthfactor = subticklengthfactor
        self.drawgrid = drawgrid
        self.gridstyles = gridstyles
        self.zerolinestyles = zerolinestyles
        self.labeldist_str = labeldist
        self.labelstyles = labelstyles
        self.labeldirection = labeldirection
        self.labelhequalize = labelhequalize
        self.labelvequalize = labelvequalize
        self.titledist_str = titledist
        self.titlestyles = titlestyles
        self.titledirection = titledirection
        self.fractype = fractype
        self.ratfracsuffixenum = ratfracsuffixenum
        self.ratfracover = ratfracover
        self.decfracpoint = decfracpoint
        self.expfractimes = expfractimes
        self.expfracpre1 = expfracpre1
        self.expfracminexp = expfracminexp
        self.suffix0 = suffix0
        self.suffix1 = suffix1

    def reldirection(self, direction, dx, dy, epsilon=1e-10):
        direction += math.atan2(dy, dx) * 180 / math.pi
        while (direction > 90 + epsilon):
            direction -= 180
        while (direction < -90 - epsilon):
            direction += 180
        return direction

    def gcd(self, m, n):
        # greates common divisor, m & n must be non-negative
        if m < n:
            m, n = n, m
        while n > 0:
            m, (dummy, n) = n, divmod(m, n)
        return m

    def attachsuffix(self, tick, str):
        if self.suffix0 or tick.enum:
            if tick.suffix is not None and not self.suffix1:
                if str == "1":
                    str = ""
                elif str == "-1":
                    str = "-"
            if tick.suffix is not None:
                str = str + tick.suffix
        return str

    def ratfrac(self, tick):
        m, n = tick.enum, tick.denom
        sign = 1
        if m < 0: m, sign = -m, -sign
        if n < 0: n, sign = -n, -sign
        gcd = self.gcd(m, n)
        (m, dummy1), (n, dummy2) = divmod(m, gcd), divmod(n, gcd)
        if n != 1:
            if self.ratfracsuffixenum:
                if sign == -1:
                    return "-{{%s}%s{%s}}" % (self.attachsuffix(tick, str(m)), self.ratfracover, n)
                else:
                    return "{{%s}%s{%s}}" % (self.attachsuffix(tick, str(m)), self.ratfracover, n)
            else:
                if sign == -1:
                    return self.attachsuffix(tick, "-{{%s}%s{%s}}" % (m, self.ratfracover, n))
                else:
                    return self.attachsuffix(tick, "{{%s}%s{%s}}" % (m, self.ratfracover, n))
        else:
            if sign == -1:
                return self.attachsuffix(tick, "-%s" % m)
            else:
                return self.attachsuffix(tick, "%s" % m)

    def decfrac(self, tick):
        m, n = tick.enum, tick.denom
        sign = 1
        if m < 0: m, sign = -m, -sign
        if n < 0: n, sign = -n, -sign
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
        if sign == -1:
            return self.attachsuffix(tick, "-%s" % strfrac)
        else:
            return self.attachsuffix(tick, strfrac)

    def expfrac(self, tick, minexp = None):
        m, n = tick.enum, tick.denom
        sign = 1
        if m < 0: m, sign = -m, -sign
        if n < 0: n, sign = -n, -sign
        exp = 0
        if m:
            while divmod(m, n)[0] > 9:
                n *= 10
                exp += 1
            while divmod(m, n)[0] < 1:
                m *= 10
                exp -= 1
        if minexp is not None and ((exp < 0 and -exp < minexp) or (exp >= 0 and exp < minexp)):
            return None
        dummy = frac(m, n)
        dummy.suffix = None
        prefactor = self.decfrac(dummy)
        if prefactor == "1" and not self.expfracpre1:
            if sign == -1:
                return self.attachsuffix(tick, "-10^{%i}" % exp)
            else:
                return self.attachsuffix(tick, "10^{%i}" % exp)
        else:
            if sign == -1:
                return self.attachsuffix(tick, "-%s%s10^{%i}" % (prefactor, self.expfractimes, exp))
            else:
                return self.attachsuffix(tick, "%s%s10^{%i}" % (prefactor, self.expfractimes, exp))

    def createtext(self, tick):
        if self.fractype == axispainter.fractypeauto:
            if tick.suffix is not None:
                tick.text = self.ratfrac(tick)
            else:
                tick.text = self.expfrac(tick, self.expfracminexp)
                if tick.text is None:
                    tick.text = self.decfrac(tick)
        elif self.fractype == axispainter.fractypedec:
            tick.text = self.decfrac(tick)
        elif self.fractype == axispainter.fractypeexp:
            tick.text = self.expfrac(tick)
        elif self.fractype == axispainter.fractyperat:
            tick.text = self.ratfrac(tick)
        else:
            raise ValueError("fractype invalid")
        if not self.attrcount(tick.labelstyles, tex.style):
            tick.labelstyles += [tex.style.math]

    def selectstyle(self, number, styles):
        if styles is None:
            return ()
        sequence = _ensuresequence(styles)
        if sequence != styles:
            return sequence
        else:
            sequence = _ensuresequence(styles[number])
            if sequence != styles[number]:
                return styles
            else:
                return _ensuresequence(styles[number])

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
                    tick.labelstyles = list(self.selectstyle(tick.labellevel, self.labelstyles))
                    if not hasattr(tick, "text"):
                        tick.suffix = axis.suffix
                        self.createtext(tick)
                    if self.labeldirection is not None and not self.attrcount(tick.labelstyles, tex.direction):
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
                if self.drawgrid > tick.ticklevel and (tick != frac(0, 1) or self.zerolinestyles is None):
                    gridpath = axis.gridpath(tick.virtual)
                    graph.draw(gridpath, *self.selectstyle(tick.ticklevel, self.gridstyles))
                factor = math.pow(self.subticklengthfactor, tick.ticklevel)
                x1 = tick.x - tick.dx * innerticklength * factor
                y1 = tick.y - tick.dy * innerticklength * factor
                x2 = tick.x + tick.dx * outerticklength * factor
                y2 = tick.y + tick.dy * outerticklength * factor
                graph.draw(path._line(x1, y1, x2, y2), *self.selectstyle(tick.ticklevel, self.tickstyles))
            if tick.labellevel is not None:
                tick.textbox._printtext(tick.x, tick.y)
        if self.zerolinestyles is not None:
            if axis.ticks[0] * axis.ticks[-1] < frac(0, 1):
                graph.draw(axis.gridpath(axis.convert(0)), *_ensuresequence(self.zerolinestyles))


        if axis.title is not None:
            x, y = axis.tickpoint(axis, 0.5)
            dx, dy = axis.tickdirection(axis, 0.5)
            # no not modify self.titlestyles ... the painter might be used by several axes!!!
            if self.titlestyles is None:
                titlestyles = []
            else:
                titlestyles = list(_ensuresequence(self.titlestyles))
            if self.titledirection is not None and not self.attrcount(titlestyles, tex.direction):
                titlestyles = titlestyles + [tex.direction(self.reldirection(self.titledirection, tick.dx, tick.dy))]
            axis.titlebox = textbox(graph.tex, axis.title, textstyles=titlestyles)
            axis.extent += titledist
            axis.titlebox._linealign(axis.extent, dx, dy)
            axis.titlebox._printtext(x, y)
            axis.extent += axis.titlebox.extent(dx, dy)


class linkaxispainter(axispainter):

    def __init__(self, skipticklevel = None, skiplabellevel = 0, zerolinestyles=None, **args):
        self.skipticklevel = skipticklevel
        self.skiplabellevel = skiplabellevel
        self.zerolinestyles = zerolinestyles
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

    def __init__(self, min=None, max=None, reverse=0, title=None, painter = axispainter(),
                       factor = 1, suffix = None):
        if min is not None and max is not None and min > max:
            min, max = max, min
            if reverse:
                reverse = 0
            else:
                reverse = 1
        self.fixmin = min is not None
        self.fixmax = max is not None
        self.min = min
        self.max = max
        self.reverse = reverse
        self.title = title
        self.painter = painter
        self.factor = factor
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

    def __init__(self, linkedaxis, title=None, painter=linkaxispainter()):
        self.linkedaxis = linkedaxis
        _axis.__init__(self, title=title, painter=painter)
        self.factor = linkedaxis.factor # XXX: not nice ...


################################################################################
# graph
################################################################################


class graphxy(canvas.canvas):

    XPattern = re.compile(r"x([2-9]|[1-9][0-9]+)?$")
    YPattern = re.compile(r"y([2-9]|[1-9][0-9]+)?$")
    DXPattern = re.compile(r"dx$")
    DYPattern = re.compile(r"dy$")
    DXMinPattern = re.compile(r"dxmin$")
    DYMinPattern = re.compile(r"dymin$")
    DXMaxPattern = re.compile(r"dxmax$")
    DYMaxPattern = re.compile(r"dymax$")

    def __init__(self, tex, xpos=0, ypos=0, width=None, height=None, ratio=goldenrule, axesdist="0.8 cm", **axes):
        canvas.canvas.__init__(self)
        self.tex = tex
        self.xpos = unit.topt(xpos)
        self.ypos = unit.topt(ypos)
        if (width is not None) and (height is None):
             height = width / ratio
        if (height is not None) and (width is None):
             width = height * ratio
        if width <= 0: raise ValueError
        if height <= 0: raise ValueError
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
        self.data = [ ]
        self._drawstate = self.drawlayout
        self.previousstyle = {}
        self.previouscolorchange = {}

    def plot(self, data, style = None):
        if self._drawstate != self.drawlayout:
            raise PyxGraphDrawstateError
        if style is None:
            if self.previousstyle.has_key(data.defaultstyle.styleid):
                style = self.previousstyle[data.defaultstyle.styleid].next()
            else:
                style = data.defaultstyle
        if hasattr(style, "styleid"):
            self.previousstyle[style.styleid] = style
        data.setstyle(self, style)
        self.data.append(data)

    def xtickpoint(self, axis, virtual):
        return (self.xmap.convert(virtual), axis.yaxispos)

    def ytickpoint(self, axis, virtual):
        return (axis.xaxispos, self.ymap.convert(virtual))

    def tickdirection(self, axis, virtual):
        return axis.fixtickdirection

    def xgridpath(self, virtual):
        return path._line(self.xmap.convert(virtual), self.ymap.convert(0),
                          self.xmap.convert(virtual), self.ymap.convert(1))

    def ygridpath(self, virtual):
        return path._line(self.xmap.convert(0), self.ymap.convert(virtual),
                          self.xmap.convert(1), self.ymap.convert(virtual))

    def xconvert(self, x):
        return self.xmap.convert(x)

    def yconvert(self, y):
        return self.ymap.convert(y)

    def lineto(self, x, y):
        return path._lineto(self.xmap.convert(x), self.ymap.convert(y))

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
            pdranges = data.getranges()
            if pdranges is not None:
                for key in pdranges.keys():
                    if key not in ranges.keys():
                        ranges[key] = pdranges[key]
                    else:
                        ranges[key] = (min(ranges[key][0], pdranges[key][0]),
                                       max(ranges[key][1], pdranges[key][1]))
        for key, axis in self.axes.items():
            if key in ranges.keys():
                if axis.min is not None:
                    ranges[key] = axis.min, ranges[key][1]
                if axis.max is not None:
                    ranges[key] = ranges[key][0], axis.max
            elif axis.min is not None and axis.max is not None:
                ranges[key] = axis.min, axis.max
        return ranges

    def drawlayout(self):
        if self._drawstate != self.drawlayout:
            raise PyxGraphDrawstateError

        # create list of ranges
        # 1. gather ranges
        ranges = self.gatherranges()
        # 2. calculate additional ranges out of known ranges
        for data in self.data:
            data.setranges(ranges)
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
        for key, axis in self.axes.items():
            # TODO: appropriate linkaxis handling
            try:
                axis.part
            except AttributeError:
                continue

            # TODO: make use of stretch
            axis.ticks = axis.part.defaultpart(axis.min / axis.factor,
                                               axis.max / axis.factor,
                                               not axis.fixmin,
                                               not axis.fixmax)
            if axis.part.multipart:
                # TODO: Additional ratings (spacing of text etc.) -> move rating into painter
                # XXX: lesspart and morepart can be called after defaultpart, although some
                #      axes may share their autoparting, because the axes are processed sequentially
                rate = axis.rate.getrate(axis.ticks, 1)
                #print rate, axis.ticks
                maxworse = 4 #TODO !!! (THIS JUST DOESN'T WORK WELL!!!)
                worse = 0
                while worse < maxworse:
                    newticks = axis.part.lesspart()
                    newrate = axis.rate.getrate(newticks, 1)
                    #print newrate, newticks
                    if newrate is not None and (rate is None or newrate < rate):
                        axis.ticks = newticks
                        rate = newrate
                        worse = 0
                    else:
                        worse += 1
                worse = 0
                while worse < maxworse:
                    newticks = axis.part.morepart()
                    newrate = axis.rate.getrate(newticks, 1)
                    #print newrate, newticks
                    if newrate is not None and (rate is None or newrate < rate):
                        axis.ticks = newticks
                        rate = newrate
                        worse = 0
                    else:
                        worse += 1

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
            if self.XPattern.match(key):
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
            elif self.YPattern.match(key):
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
                raise ValueError("Axis key %s not allowed" % key)
            axis.tickdirection = self.tickdirection
            axis.painter.paint(self, axis)
            if self.XPattern.match(key):
                 self.xaxisextents[num2] += axis.extent
                 needxaxisdist[num2] = 1
            if self.YPattern.match(key):
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
# styles
################################################################################


class colorchange:

    def __init__(self, lowcolor, highcolor):
        if lowcolor.__class__ != highcolor.__class__: raise ValueError
        self.colorclass = lowcolor.__class__
        self.lowcolor = lowcolor
        self.highcolor = highcolor
        self.max = 0

    def getcolor(self, style):
        if hasattr(style, "colorchangeindex"):
            index = style.colorchangeindex
        else:
            index = self.max
        if index < 0 or index > self.max: raise ValueError
        color = {}
        for key in self.lowcolor.color.keys():
            color[key] = (index * self.highcolor.color[key] +
                          (self.max - index) * self.lowcolor.color[key])/float(self.max)
        return self.colorclass(**color)

    def next(self, style):
        style.colorchangeindex = self.max
        self.max += 1
        return self


class plotstyle:

    pass


class mark(plotstyle):

    styleid = "mark"

    def __init__(self, size="0.12 cm", colorchange=None, errorscale=1/goldenrule, symbolstyles=(), dodrawsymbol=1):
        self.size_str = size
        self.errorscale = errorscale
        self.dodrawsymbol = dodrawsymbol
        self.symbolstyles = symbolstyles
        self.colorchange = colorchange

    def next(self):
        if self.colorchange is None:
            return self.nextclass(size=self.size_str,
                                  errorscale=self.errorscale,
                                  symbolstyles=self.symbolstyles)
        else:
            return self.nextclass(size=self.size_str,
                                  colorchange=self.colorchange.next(self),
                                  errorscale=self.errorscale,
                                  symbolstyles=self.symbolstyles)

    def setcolumns(self, graph, columns):
        self.xindex = self.dxindex = self.dxminindex = self.dxmaxindex = None
        self.yindex = self.dyindex = self.dyminindex = self.dymaxindex = None
        for key, index in columns.items():
            if graph.XPattern.match(key) and self.xindex is None:
                self.xkey = key
                self.xindex = index
            elif graph.YPattern.match(key) and self.yindex is None:
                self.ykey = key
                self.yindex = index
            elif graph.DXPattern.match(key) and self.dxindex is None:
                self.dxindex = index
            elif graph.DXMinPattern.match(key) and self.dxminindex is None:
                self.dxminindex = index
            elif graph.DXMaxPattern.match(key) and self.dxmaxindex is None:
                self.dxmaxindex = index
            elif graph.DYPattern.match(key) and self.dyindex is None:
                self.dyindex = index
            elif graph.DYMinPattern.match(key) and self.dyminindex is None:
                self.dyminindex = index
            elif graph.DYMaxPattern.match(key) and self.dymaxindex is None:
                self.dymaxindex = index
            else:
                raise ValueError

        if None in (self.xindex, self.yindex): raise ValueError
        if self.dxindex is not None and (self.dxminindex is not None or
                                         self.dxmaxindex is not None): raise ValueError
        if self.dyindex is not None and (self.dyminindex is not None or 
                                         self.dymaxindex is not None): raise ValueError

    def keyrange(self, points, index, dindex, dminindex, dmaxindex):
        min = max = None
        for point in points:
            try:
                if dindex is not None:
                    pointmin = point[index] - point[dindex]
                    pointmax = point[index] + point[dindex]
                elif dminindex is not None:
                    pointmin = point[dminindex]
                    pointmax = point[dmaxindex]
                else:
                    pointmin = pointmax = point[index]
                if pointmin is None: raise TypeError
                if pointmax is None: raise TypeError
                if min is None or pointmin < min: min = pointmin
                if max is None or pointmax > max: max = pointmax
            except (TypeError, ValueError):
                pass
        return min, max

    def getranges(self, points):
        return {self.xkey: self.keyrange(points, self.xindex, self.dxindex, self.dxminindex, self.dxmaxindex),
                self.ykey: self.keyrange(points, self.yindex, self.dyindex, self.dyminindex, self.dymaxindex)}

    def drawpointlist(self, graph, points):
        xaxis = graph.axes[self.xkey]
        yaxis = graph.axes[self.ykey]
        self.size = unit.topt(unit.length(self.size_str, default_type="v"))
        if self.colorchange: self.symbolstyles = [self.colorchange.getcolor(self)] + list(self.symbolstyles)

        for point in points:
            try:
                x = graph.xconvert(xaxis.convert(point[self.xindex]))
                y = graph.yconvert(yaxis.convert(point[self.yindex]))
            except (TypeError, ValueError):
                continue
            try:
                if self.dxindex is not None or (self.dxminindex is not None and self.dxmaxindex is not None):
                    if self.dxindex is not None:
                        xmin = graph.xconvert(xaxis.convert(point[self.xindex] - point[self.dxindex]))
                        xmax = graph.xconvert(xaxis.convert(point[self.xindex] + point[self.dxindex]))
                    else:
                        xmin = graph.xconvert(xaxis.convert(point[self.dxminindex]))
                        xmax = graph.xconvert(xaxis.convert(point[self.dxmaxindex]))
                    graph.draw(path.path(path._moveto(xmin, y-self.errorscale*self.size),
                                         path._lineto(xmin, y+self.errorscale*self.size),
                                         path._moveto(xmin, y),
                                         path._lineto(xmax, y),
                                         path._moveto(xmax, y-self.errorscale*self.size),
                                         path._lineto(xmax, y+self.errorscale*self.size)))
            except (TypeError, ValueError):
                pass
            try:
                if self.dyindex is not None or (self.dyminindex is not None and self.dymaxindex is not None):
                    if self.dyindex is not None:
                        ymin = graph.yconvert(yaxis.convert(point[self.yindex] - point[self.dyindex]))
                        ymax = graph.yconvert(yaxis.convert(point[self.yindex] + point[self.dyindex]))
                    else:
                        ymin = graph.yconvert(yaxis.convert(point[self.dyminindex]))
                        ymax = graph.yconvert(yaxis.convert(point[self.dymaxindex]))
                    graph.draw(path.path(path._moveto(x-self.errorscale*self.size, ymin),
                                         path._lineto(x+self.errorscale*self.size, ymin),
                                         path._moveto(x, ymin),
                                         path._lineto(x, ymax),
                                         path._moveto(x-self.errorscale*self.size, ymax),
                                         path._lineto(x+self.errorscale*self.size, ymax)))
            except (TypeError, ValueError):
                pass
            if self.dodrawsymbol:
                self._drawsymbol(graph, x, y)

    def _drawsymbol(self, canvas, x, y):
        canvas.draw(path.path(*self._symbol(x, y)), *self.symbolstyles)

    def drawsymbol(self, canvas, *args):
        return self._drawsymbol(canvas, *map(unit.topt, args))

    def symbol(self, *args):
        return self._symbol(*map(unit.topt, args))


class _markcross(mark):

    def _symbol(self, x, y):
        return (path._moveto(x-0.5*self.size, y-0.5*self.size),
                path._lineto(x+0.5*self.size, y+0.5*self.size),
                path._moveto(x-0.5*self.size, y+0.5*self.size),
                path._lineto(x+0.5*self.size, y-0.5*self.size))


class _markplus(mark):

    def _symbol(self, x, y):
        return (path._moveto(x-0.707106781*self.size, y),
                path._lineto(x+0.707106781*self.size, y),
                path._moveto(x, y-0.707106781*self.size),
                path._lineto(x, y+0.707106781*self.size))


class _marksquare(mark):

    def _symbol(self, x, y):
        return (path._moveto(x-0.5*self.size, y-0.5 * self.size),
                path._lineto(x+0.5*self.size, y-0.5 * self.size),
                path._lineto(x+0.5*self.size, y+0.5 * self.size),
                path._lineto(x-0.5*self.size, y+0.5 * self.size),
                path.closepath())


class _marktriangle(mark):

    def _symbol(self, x, y):
        return (path._moveto(x-0.759835685*self.size, y-0.438691337*self.size),
                path._lineto(x+0.759835685*self.size, y-0.438691337*self.size),
                path._lineto(x, y+0.877382675*self.size),
                path.closepath())


class _markcircle(mark):

    def _symbol(self, x, y):
        return (path._arc(x, y, 0.564189583*self.size, 0, 360),
                path.closepath())


class _markdiamond(mark):

    def _symbol(self, x, y):
        return (path._moveto(x-0.537284965*self.size, y),
                path._lineto(x, y-0.930604859*self.size),
                path._lineto(x+0.537284965*self.size, y),
                path._lineto(x, y+0.930604859*self.size),
                path.closepath())


class _fmark:

    def _drawsymbol(self, canvas, x, y):
        canvas.fill(path.path(*self._symbol(x, y)), *self.symbolstyles)


class _markfsquare(_fmark, _marksquare): pass
class _markftriangle(_fmark, _marktriangle): pass
class _markfcircle(_fmark, _markcircle): pass
class _markfdiamond(_fmark, _markdiamond): pass


_markcross.nextclass = _markplus
_markplus.nextclass = _marksquare
_marksquare.nextclass = _marktriangle
_marktriangle.nextclass = _markcircle
_markcircle.nextclass = _markdiamond
_markdiamond.nextclass = _markfsquare
_markfsquare.nextclass = _markftriangle
_markftriangle.nextclass = _markfcircle
_markfcircle.nextclass = _markfdiamond
_markfdiamond.nextclass = _markcross

mark.cross = _markcross
mark.plus = _markplus
mark.square = _marksquare
mark.triangle = _marktriangle
mark.circle = _markcircle
mark.diamond = _markdiamond
mark.fsquare = _markfsquare
mark.ftriangle = _markftriangle
mark.fcircle = _markfcircle
mark.fdiamond = _markfdiamond


class line(plotstyle):

    styleid = "line"

    def __init__(self, colorchange=None, linestyles=(), dodrawline=1):
        self.colorchange = colorchange
        self.linestyles = linestyles
        self.dodrawline = dodrawline

    def next(self):
        if self.colorchange is None:
            return self.nextclass(linestyles=self.linestyles)
        else:
            return self.nextclass(colorchange=self.colorchange.next(self),
                                  linestyles=self.linestyles)

    def setcolumns(self, graph, columns):
        self.xindex = self.yindex = None
        for key, index in columns.items():
            if graph.XPattern.match(key) and self.xindex is None:
                self.xkey = key
                self.xindex = index
            elif graph.YPattern.match(key) and self.yindex is None:
                self.ykey = key
                self.yindex = index
            else:
                raise ValueError
        if None in (self.xindex, self.yindex): raise ValueError

    def keyrange(self, points, index):
        min = max = None
        for point in points:
            try:
                if point[index] is None: raise TypeError
                if min is None or point[index] < min: min = point[index]
                if max is None or point[index] > max: max = point[index]
            except (TypeError, ValueError):
                pass
        return min, max

    def getranges(self, points):
        return {self.xkey: self.keyrange(points, self.xindex),
                self.ykey: self.keyrange(points, self.yindex)}

    def drawpointlist(self, graph, points):
        if self.colorchange: self.linestyles = [self.colorchange.getcolor(self)] + list(self.linestyles)

        xaxis = graph.axes[self.xkey]
        yaxis = graph.axes[self.ykey]

        moveto = 1
        line = []
        for point in points:
            try:
                x = graph.xconvert(xaxis.convert(point[self.xindex]))
                y = graph.yconvert(yaxis.convert(point[self.yindex]))
                if moveto:
                    line.append(path._moveto(x, y))
                    moveto = 0
                else:
                    line.append(path._lineto(x, y))
            except (TypeError, ValueError):
                moveto = 1
        self.path = path.path(*line)
        if self.dodrawline:
            graph.draw(self.path, *self.linestyles)


class _solidline(line, attrlist.attrlist):

    def __init__(self, **args):
        args["linestyles"] = [canvas.linestyle.solid, ] + self.attrdel(args["linestyles"], canvas.linestyle)
        line.__init__(self, **args)


class _dashedline(line, attrlist.attrlist):

    def __init__(self, **args):
        args["linestyles"] = [canvas.linestyle.dashed, ] + self.attrdel(args["linestyles"], canvas.linestyle)
        line.__init__(self, **args)


class _dottedline(line, attrlist.attrlist):

    def __init__(self, **args):
        args["linestyles"] = [canvas.linestyle.dotted, ] + self.attrdel(args["linestyles"], canvas.linestyle)
        line.__init__(self, **args)


line.nextclass = _dashedline
_dashedline.nextclass = _dottedline
_dottedline.nextclass = _solidline
_solidline.nextclass = _dashedline

line.solid = _solidline
line.dashed = _dashedline
line.dotted = _dottedline


################################################################################
# data
################################################################################


class data:

    defaultstyle = mark.cross()

    def __init__(self, datafile, **columns):
        self.datafile = datafile
        self.columns = {}
        for key, column in columns.items():
            self.columns[key] = datafile.getcolumnno(column)

    def setstyle(self, graph, style):
        self.style = style
        self.style.setcolumns(graph, self.columns)

    def getranges(self):
        return self.style.getranges(self.datafile.data)

    def setranges(self, ranges):
        pass

    def draw(self, graph):
        self.style.drawpointlist(graph, self.datafile.data)


class function:

    defaultstyle = line()

    def __init__(self, expression, xmin=None, xmax=None, ymin=None, ymax=None, points = 100, parser=mathtree.parser()):
        self.xmin, self.xmax, self.ymin, self.ymax = xmin, xmax, ymin, ymax
        self.points = points
        self.result, expression = expression.split("=")
        self.mathtree = parser.parse(expression)
        self.variable, = self.mathtree.VarList()
        self.evalranges = 0

    def setstyle(self, graph, style):
        self.style = style
        self.style.setcolumns(graph, {self.variable: 0, self.result: 1})

    def getranges(self):
        if self.evalranges:
            return self.style.getranges(self.data)

    def setranges(self, ranges):
        if None in (self.xmin, self.xmax):
            min, max = ranges[self.variable]
            if self.xmin is not None and min < self.xmin: min = self.xmin
            if self.xmax is not None and max > self.xmax: max = self.xmax
        else:
            min, max = self.xmin, self.xmax
        self.data = []
        for i in range(self.points):
            x = min + (max-min)*i / (self.points-1.0)
            y = self.mathtree.Calc({self.variable: x})
            if ((self.ymin is not None and y < self.ymin) or
                (self.ymax is not None and y > self.ymax)):
                y = None
            self.data.append((x, y))
        self.evalranges = 1

    def draw(self, graph):
        self.style.drawpointlist(graph, self.data)


class paramfunction:

    defaultstyle = line()

    def __init__(self, varname, min, max, expression, points = 100, parser=mathtree.parser()):
        self.varname = varname
        self.min = min
        self.max = max
        self.points = points
        self.expression = {}
        self.mathtrees = {}
        varlist, expressionlist = expression.split("=") 
        for key in varlist.split(","):
            key = key.strip()
            if self.mathtrees.has_key(key):
                raise ValueError("multiple assignment in tuple")
            try:
                self.mathtrees[key] = parser.parse(expressionlist)
                break
            except mathtree.CommaFoundMathTreeParseError, exception:
                self.mathtrees[key] = parser.parse(expressionlist[:exception.ParseStr.Pos-1])
                expressionlist = expressionlist[exception.ParseStr.Pos:]
        else:
            raise ValueError("unpack tuple of wrong size")
        if len(varlist.split(",")) != len(self.mathtrees.keys()):
            raise ValueError("unpack tuple of wrong size")
        self.data = []
        for i in range(self.points):
            value = self.min + (self.max-self.min)*i / (self.points-1.0)
            line = []
            for key, tree in self.mathtrees.items():
                line.append(tree.Calc({self.varname: value}))
            self.data.append(line)

    def setstyle(self, graph, style):
        self.style = style
        columns = {}
        for key, index in zip(self.mathtrees.keys(), xrange(sys.maxint)):
            columns[key] = index
        self.style.setcolumns(graph, columns)

    def getranges(self):
        return self.style.getranges(self.data)

    def setranges(self, ranges):
        pass

    def draw(self, graph):
        self.style.drawpointlist(graph, self.data)


################################################################################
# key
################################################################################

# to be written
