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
import bbox, canvas, path, tex, unit, mathtree, trafo, attrlist, color


goldenrule = 0.5 * (math.sqrt(5) + 1)



################################################################################
# some general helper routines
################################################################################


def _isstring(arg):
    "arg is string-like (cf. python cookbook 3.2)"
    try: arg + ''
    except: return 0
    return 1


def _isnumber(arg):
    "arg is number-like"
    try: arg + 0
    except: return 0
    return 1


def _isinteger(arg):
    "arg is integer-like"
    try:
        if type(arg + 0.0) == type(arg):
            return 0
        return 1
    except: return 0


def _issequence(arg):
    """arg is sequence-like (e.g. has a len)
       a string is *not* considered to be a sequence"""
    if _isstring(arg): return 0
    try: len(arg)
    except: return 0
    return 1


def _ensuresequence(arg):
    """return arg or (arg,) depending on the result of _issequence,
       None is converted to ()"""
    if _isstring(arg): return (arg,)
    if arg is None: return ()
    if _issequence(arg): return arg
    return (arg,)


def _issequenceofsequences(arg):
    """check if arg has a sequence as it's first entry"""
    return _issequence(arg) and len(arg) and _issequence(arg[0])


def _getsequenceno(arg, n):
    """get sequence number n if arg is a sequence of sequences,
       otherwise it gets just arg
       the return value is always a sequence"""
    if _issequenceofsequences(arg):
        return _ensuresequence(arg[n])
    else:
        return _ensuresequence(arg)


 
################################################################################
# maps
################################################################################


class _map:
    "maps convert a value into another value and vice verse (via invert)"

    def setbasepts(self, basepts):
        """set basepoints for convertion; basepoints are are tuples (x,y) where
           y = convert(x) and x = invert(y) has to be valid"""
        self.basepts = basepts
        return self

    def converts(self, sequence):
        "convert a sequence -> returns a number or a sequence"
        return map(self.convert, values)

    def inverts(self, sequence):
        "convert a sequence -> returns a number or a sequence, inverse mapping"
        return map(self.invert, values)


class _linmap(_map):
    "linear mapping"

    def convert(self, value):
        return self.basepts[0][1] + ((self.basepts[1][1] - self.basepts[0][1]) /
               float(self.basepts[1][0] - self.basepts[0][0])) * (value - self.basepts[0][0])

    def invert(self, value):
        return self.basepts[0][0] + ((self.basepts[1][0] - self.basepts[0][0]) /
               float(self.basepts[1][1] - self.basepts[0][1])) * (value - self.basepts[0][1])


class _logmap(_linmap):
    "logarithmic mapping"

    def setbasepts(self, basepts):
        self.basepts = ((math.log(basepts[0][0]), basepts[0][1], ),
                        (math.log(basepts[1][0]), basepts[1][1], ), )
        return self

    def convert(self, value):
        return _linmap.convert(self, math.log(value))

    def invert(self, value):
        return math.exp(_linmap.invert(self, value))



################################################################################
# tick lists = partitions
################################################################################


class frac:
    "fraction type for rational arithmetics"

    def __init__(self, enum, denom, power=None):
        "for power!=None: frac=(enum/denom)**power"
        if not _isinteger(enum) or not _isinteger(denom): raise TypeError("integer type expected")
        if not denom: raise ZeroDivisionError("zero denominator")
        if power != None:
            if not _isinteger(power): raise TypeError("integer type expected")
            if power >= 0:
                self.enum = long(enum) ** power
                self.denom = long(denom) ** power
            else:
                self.enum = long(denom) ** (-power)
                self.denom = long(enum) ** (-power)
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
        return "frac(%r, %r)" % (self.enum, self.denom) # I want to see the "L"


def _ensurefrac(arg):
    "ensure frac by converting a string to frac"

    def createfrac(str):
        commaparts = str.split(".")
        for part in commaparts:
            if not part.isdigit(): raise ValueError("non-digits found in '%s'" % part)
        if len(commaparts) == 1:
            return frac(int(commaparts[0]), 1)
        elif len(commaparts) == 2:
            result = frac(1, 10l, power=len(commaparts[1]))
            result.enum = int(commaparts[0])*result.denom + int(commaparts[1])
            return result
        else: raise ValueError("multiple '.' found in '%s'" % str)

    if _isstring(arg):
        fraction = arg.split("/")
        if len(fraction) > 2: raise ValueError("multiple '/' found in '%s'" % arg)
        value = createfrac(fraction[0])
        if len(fraction) == 2:
            value2 = createfrac(fraction[1])
            value = frac(value.enum * value2.denom, value.denom * value2.enum)
        return value
    return arg


class tick(frac):
    "a tick is a frac enhanced by a ticklevel, a labellevel and a text (they all might be None)"

    def __init__(self, enum, denom, ticklevel=None, labellevel=None, text=None):
        frac.__init__(self, enum, denom)
        self.ticklevel = ticklevel
        self.labellevel = labellevel
        self.text = text

    def merge(self, other):
        if self.ticklevel is None or (other.ticklevel is not None and other.ticklevel < self.ticklevel):
            self.ticklevel = other.ticklevel
        if self.labellevel is None or (other.labellevel is not None and other.labellevel < self.labellevel):
            self.labellevel = other.labellevel
        if self.text is None:
            self.text = other.text

    def __repr__(self):
        return "tick(%r, %r, %s, %s, %s)" % (self.enum, self.denom, self.ticklevel, self.labellevel, self.text)


def _mergeticklists(list1, list2):
    """return a merged list of ticks out of list1 and list2
       lists have to be ordered (returned list is also ordered)
       caution: side effects (input lists might be altered)"""
    # TODO: improve this by bisect
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


def _mergetexts(ticks, texts):
    "merges texts into ticks"
    if _issequenceofsequences(texts):
        for text, level in zip(texts, xrange(sys.maxint)):
            usetext = _ensuresequence(text)
            i = 0
            for tick in ticks:
                if tick.labellevel == level:
                    tick.text = usetext[i]
                    i += 1
            if i != len(usetext):
                raise IndexError("wrong sequence length of texts at level %i" % level)
    elif texts is not None:
        usetext = _ensuresequence(texts)
        i = 0
        for tick in ticks:
            if tick.labellevel == 0:
                tick.text = usetext[i]
                i += 1
        if i != len(usetext):
            raise IndexError("wrong sequence length of texts")


class manualpart:

    def __init__(self, ticks=None, labels=None, texts=None):
        self.multipart = 0
        self.ticks = ticks
        self.labels = labels
        self.texts = texts

    def checkfraclist(self, *fracs):
        if not len(fracs): return ()
        sorted = list(fracs)
        sorted.sort()
        last = sorted[0]
        for item in sorted[1:]:
            if last == item:
                raise ValueError("duplicate entry found")
            last = item
        return sorted

    def defaultpart(self, min, max):
        if self.ticks is None and self.labels is not None:
            useticks = _getsequenceno(self.labels, 0)
        else:
            useticks = self.ticks

        if self.labels is None and self.ticks is not None:
            uselabels = _getsequenceno(self.ticks, 0)
        else:
            uselabels = self.labels

        ticks = []
        if _issequenceofsequences(useticks):
            for fracs, level in zip(useticks, xrange(sys.maxint)):
                ticks = _mergeticklists(ticks, [tick(frac.enum, frac.denom, ticklevel = level)
                                                for frac in self.checkfraclist(*map(_ensurefrac, _ensuresequence(fracs)))])
        else:
            ticks = _mergeticklists(ticks, [tick(frac.enum, frac.denom, ticklevel = 0)
                                            for frac in self.checkfraclist(*map(_ensurefrac, _ensuresequence(useticks)))])

        if _issequenceofsequences(uselabels):
            for fracs, level in zip(uselabels, xrange(sys.maxint)):
                ticks = _mergeticklists(ticks, [tick(frac.enum, frac.denom, labellevel = level)
                                                for frac in self.checkfraclist(*map(_ensurefrac, _ensuresequence(fracs)))])
        else:
            ticks = _mergeticklists(ticks, [tick(frac.enum, frac.denom, labellevel = 0)
                                            for frac in self.checkfraclist(*map(_ensurefrac, _ensuresequence(uselabels)))])
                
        _mergetexts(ticks, self.texts)

        return ticks


class linpart:

    def __init__(self, ticks=None, labels=None, texts=None, extendtoticklevel=0, extendtolabellevel=None, epsilon=1e-10):
        self.multipart = 0
        self.ticks = ticks
        self.labels = labels
        self.texts = texts
        self.extendtoticklevel = extendtoticklevel
        self.extendtolabellevel = extendtolabellevel
        self.epsilon = epsilon

    def extendminmax(self, min, max, frac):
        min = float(frac) * math.floor(min / float(frac) + self.epsilon)
        max = float(frac) * math.ceil(max / float(frac) - self.epsilon)
        return min, max

    def getticks(self, min, max, frac, ticklevel=None, labellevel=None):
        imin = int(math.ceil(min / float(frac) - 0.5 * self.epsilon))
        imax = int(math.floor(max / float(frac) + 0.5 * self.epsilon))
        ticks = []
        for i in range(imin, imax + 1):
            ticks.append(tick(long(i) * frac.enum, frac.denom, ticklevel = ticklevel, labellevel = labellevel))
        return ticks

    def defaultpart(self, min, max):
        if self.ticks is None and self.labels is not None:
            useticks = (_ensurefrac(_ensuresequence(self.labels)[0]),)
        else:
            useticks = map(_ensurefrac, _ensuresequence(self.ticks))

        if self.labels is None and self.ticks is not None:
            uselabels = (_ensurefrac(_ensuresequence(self.ticks)[0]),)
        else:
            uselabels = map(_ensurefrac, _ensuresequence(self.labels))

        if self.extendtoticklevel is not None and len(useticks) > self.extendtoticklevel:
            min, max = self.extendminmax(min, max, useticks[self.extendtoticklevel])
        if self.extendtolabellevel is not None and len(uselabels) > self.extendtolabellevel:
            min, max = self.extendminmax(min, max, uselabels[self.extendtolabellevel])

        ticks = []
        for i in range(len(useticks)):
            ticks = _mergeticklists(ticks, self.getticks(min, max, useticks[i], ticklevel = i))
        for i in range(len(uselabels)):
            ticks = _mergeticklists(ticks, self.getticks(min, max, uselabels[i], labellevel = i))

        _mergetexts(ticks, self.texts)

        return ticks


class autolinpart:
    defaulttickslist = ((frac(1, 1), frac(1, 2)),
                        (frac(2, 1), frac(1, 1)),
                        (frac(5, 2), frac(5, 4)),
                        (frac(5, 1), frac(5, 2)))

    def __init__(self, tickslist=defaulttickslist, extendtoticklevel=0, epsilon=1e-10):
        self.multipart = 1
        self.tickslist = tickslist
        self.extendtoticklevel = extendtoticklevel
        self.epsilon = epsilon

    def defaultpart(self, min, max):
        base = frac(10L, 1, int(math.log(max - min) / math.log(10)))
        ticks = self.tickslist[0]
        useticks = [tick * base for tick in ticks]
        self.lesstickindex = self.moretickindex = 0
        self.lessbase = self.morebase = base
        self.usemin, self.usemax = min, max
        part = linpart(ticks=useticks, extendtoticklevel=self.extendtoticklevel, epsilon=self.epsilon)
        return part.defaultpart(self.usemin, self.usemax)

    def lesspart(self):
        if self.lesstickindex < len(self.tickslist) - 1:
            self.lesstickindex += 1
        else:
            self.lesstickindex = 0
            self.lessbase.enum *= 10
        ticks = self.tickslist[self.lesstickindex]
        useticks = [tick * self.lessbase for tick in ticks]
        part = linpart(ticks=useticks, extendtoticklevel=self.extendtoticklevel, epsilon=self.epsilon)
        return part.defaultpart(self.usemin, self.usemax)

    def morepart(self):
        if self.moretickindex:
            self.moretickindex -= 1
        else:
            self.moretickindex = len(self.tickslist) - 1
            self.morebase.denom *= 10
        ticks = self.tickslist[self.moretickindex]
        useticks = [tick * self.morebase for tick in ticks]
        part = linpart(ticks=useticks, extendtoticklevel=self.extendtoticklevel, epsilon=self.epsilon)
        return part.defaultpart(self.usemin, self.usemax)


class shiftfracs:
    def __init__(self, shift, *fracs):
         self.shift = shift
         self.fracs = fracs


class logpart:

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

    def __init__(self, ticks=None, labels=None, texts=None, extendtoticklevel=0, extendtolabellevel=None, epsilon=1e-10):
        self.multipart = 0
        self.ticks = ticks
        self.labels = labels
        self.texts = texts
        self.extendtoticklevel = extendtoticklevel
        self.extendtolabellevel = extendtolabellevel
        self.epsilon = epsilon

    def extendminmax(self, min, max, shiftfracs):
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
        if minpower >= 0:
            min = float(minfrac) * (10 ** minpower)
        else:
            min = float(minfrac) / (10 ** (-minpower))
        if maxpower >= 0:
            max = float(maxfrac) * (10 ** maxpower)
        else:
            max = float(maxfrac) / (10 ** (-maxpower))
        return min, max

    def getticks(self, min, max, shiftfracs, ticklevel=None, labellevel=None):
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
            ticks = _mergeticklists(ticks, fracticks)
        return ticks

    def defaultpart(self, min, max):
        if self.ticks is None and self.labels is not None:
            useticks = (_ensuresequence(self.labels)[0],)
        else:
            useticks = _ensuresequence(self.ticks)

        if self.labels is None and self.ticks is not None:
            uselabels = (_ensuresequence(self.ticks)[0],)
        else:
            uselabels = _ensuresequence(self.labels)

        if self.extendtoticklevel is not None and len(useticks) > self.extendtoticklevel:
            min, max = self.extendminmax(min, max, useticks[self.extendtoticklevel])
        if self.extendtolabellevel is not None and len(uselabels) > self.extendtolabellevel:
            min, max = self.extendminmax(min, max, uselabels[self.extendtolabellevel])

        ticks = []
        for i in range(len(useticks)):
            ticks = _mergeticklists(ticks, self.getticks(min, max, useticks[i], ticklevel = i))
        for i in range(len(uselabels)):
            ticks = _mergeticklists(ticks, self.getticks(min, max, uselabels[i], labellevel = i))

        _mergetexts(ticks, self.texts)

        return ticks


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
        self.multipart = 1
        self.shiftfracslists = shiftfracslists
        if shiftfracslistsindex is None:
            shiftfracslistsindex, dummy = divmod(len(shiftfracslists), 2)
        self.shiftfracslistsindex = shiftfracslistsindex
        self.extendtoticklevel = extendtoticklevel
        self.extendtolabellevel = extendtolabellevel
        self.epsilon = epsilon

    def defaultpart(self, min, max):
        self.usemin, self.usemax = min, max
        self.moreshiftfracslistsindex = self.shiftfracslistsindex
        self.lessshiftfracslistsindex = self.shiftfracslistsindex
        part = logpart(ticks=self.shiftfracslists[self.shiftfracslistsindex][0],
                       labels=self.shiftfracslists[self.shiftfracslistsindex][1],
                       extendtoticklevel=self.extendtoticklevel,
                       extendtolabellevel=self.extendtolabellevel,
                       epsilon=self.epsilon)
        return part.defaultpart(self.usemin, self.usemax)

    def lesspart(self):
        self.moreshiftfracslistsindex += 1
        if self.moreshiftfracslistsindex < len(self.shiftfracslists):
            part = logpart(ticks=self.shiftfracslists[self.moreshiftfracslistsindex][0],
                           labels=self.shiftfracslists[self.moreshiftfracslistsindex][1],
                           extendtoticklevel=self.extendtoticklevel,
                           extendtolabellevel=self.extendtolabellevel,
                           epsilon=self.epsilon)
            return part.defaultpart(self.usemin, self.usemax)
        return None

    def morepart(self):
        self.lessshiftfracslistsindex -= 1
        if self.lessshiftfracslistsindex >= 0:
            part = logpart(ticks=self.shiftfracslists[self.lessshiftfracslistsindex][0],
                           labels=self.shiftfracslists[self.lessshiftfracslistsindex][1],
                           extendtoticklevel=self.extendtoticklevel,
                           extendtolabellevel=self.extendtolabellevel,
                           epsilon=self.epsilon)
            return part.defaultpart(self.usemin, self.usemax)
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
                    if tick.text is None:
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
                    graph.stroke(gridpath, *self.selectstyle(tick.ticklevel, self.gridstyles))
                factor = math.pow(self.subticklengthfactor, tick.ticklevel)
                x1 = tick.x - tick.dx * innerticklength * factor
                y1 = tick.y - tick.dy * innerticklength * factor
                x2 = tick.x + tick.dx * outerticklength * factor
                y2 = tick.y + tick.dy * outerticklength * factor
                graph.stroke(path._line(x1, y1, x2, y2), *self.selectstyle(tick.ticklevel, self.tickstyles))
            if tick.labellevel is not None:
                tick.textbox._printtext(tick.x, tick.y)
        if self.zerolinestyles is not None:
            if axis.ticks[0] * axis.ticks[-1] < frac(0, 1):
                graph.stroke(axis.gridpath(axis.convert(0)), *_ensuresequence(self.zerolinestyles))


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
        args["zerolinestyles"] = zerolinestyles
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
                       factor = 1, suffix = None, baselinestyles=()):
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
        self.baselinestyles = baselinestyles
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

    def __init__(self, tex, xpos=0, ypos=0, width=None, height=None, ratio=goldenrule,
                 backgroundstyles=None, axesdist="0.8 cm", **axes):
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
        for key in axes.keys():
            if not self.XPattern.match(key) and not self.YPattern.match(key):
                raise TypeError("got an unexpected keyword argument '%s'" % key)
        if not axes.has_key("x"):
            axes["x"] = linaxis()
        if not axes.has_key("x2"):
            axes["x2"] = linkaxis(axes["x"])
        elif axes["x2"] is None:
            del axes["x2"]
        if not axes.has_key("y"):
            axes["y"] = linaxis()
        if not axes.has_key("y2"):
            axes["y2"] = linkaxis(axes["y"])
        elif axes["y2"] is None:
            del axes["y2"]
        self.axes = axes
        self.axesdist_str = axesdist
        self.backgroundstyles = backgroundstyles
        self.data = []
        self._drawstate = self.drawlayout
        self.previousstyle = {}

    def plot(self, data, style = None):
        if self._drawstate != self.drawlayout:
            raise PyxGraphDrawstateError
        if style is None:
            if self.previousstyle.has_key(data.defaultstyle.__class__):
                style = self.previousstyle[data.defaultstyle.__class__].next()
            else:
                style = data.defaultstyle
        self.previousstyle[style.__class__] = style
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
            axis.ticks = axis.part.defaultpart(axis.min / axis.factor, axis.max / axis.factor)
            if axis.part.multipart:
                # TODO: Additional ratings (spacing of text etc.) -> move rating into painter
                # XXX: lesspart and morepart can be called after defaultpart, although some
                #      axes may share their autoparting, because the axes are processed sequentially
                rate = axis.rate.getrate(axis.ticks, 1)
                #print rate, axis.ticks
                maxworse = 6 #TODO !!! (THIS JUST DOESN'T WORK WELL!!!)
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
        self._drawstate = self.drawdata

    def drawdata(self):
        if self._drawstate != self.drawdata:
            raise PyxGraphDrawstateError
        for data in self.data:
            data.draw(self)
        self._drawstate = self.drawbackground

    def drawbackground(self):
        if self._drawstate != self.drawbackground:
            raise PyxGraphDrawstateError
        if self.backgroundstyles is not None:
            self.draw(path._rect(self.xmap.convert(0),
                                 self.ymap.convert(0),
                                 self.xmap.convert(1) - self.xmap.convert(0),
                                 self.ymap.convert(1) - self.ymap.convert(0)),
                      *_ensuresequence(self.backgroundstyles))
        self._drawstate = self.drawaxes

    def drawaxes(self):
        if self._drawstate != self.drawaxes:
            raise PyxGraphDrawstateError
        axesdist = unit.topt(unit.length(self.axesdist_str, default_type="v"))
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
            elif self.YPattern.match(key):
                 if needyaxisdist[num2]:
                     self.yaxisextents[num2] += axesdist
                 axis.xaxispos = self.xmap.convert(num2) + num3*self.yaxisextents[num2]
                 axis.tickpoint = self.ytickpoint
                 axis.fixtickdirection = (num3, 0)
                 axis.gridpath = self.ygridpath
            else:
                raise ValueError("Axis key %s not allowed" % key)
            x1, y1 = axis.tickpoint(axis, 0)
            x2, y2 = axis.tickpoint(axis, 1)
            if axis.baselinestyles is not None:
                self.stroke(path._line(x1, y1, x2, y2),
                            *_ensuresequence(axis.baselinestyles))
            axis.tickdirection = self.tickdirection
            if axis.painter is not None:
                axis.painter.paint(self, axis)
            if self.XPattern.match(key):
                self.xaxisextents[num2] += axis.extent
                needxaxisdist[num2] = 1
            if self.YPattern.match(key):
                self.yaxisextents[num2] += axis.extent
                needyaxisdist[num2] = 1
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
# attr changers
################################################################################


class _changeattr: pass

class changeattrref(_changeattr):

    def __init__(self, ref, index):
        self.ref = ref
        self.index = index

    def attrindex(self):
        return self.index

    def attr(self):
        return self.ref._attr(self.index)

    def next(self):
        return self.ref.next()


class changeattr(_changeattr):

    def __init__(self):
        self.len = 1

    def attrindex(self):
        return 0

    def attr(self):
        return self._attr(0)

    def next(self):
        index = self.len
        self.len += 1
        return changeattrref(self, index)

    # def _attr(self, index):
    # to be defined in derived classes


# helper routines for a using attrs

def _getattr(attr):
    """get attr out of a attr/changeattr"""
    if isinstance(attr, _changeattr):
        return attr.attr()
    return attr


def _nextattr(attr):
    """perform next to a attr/changeattr"""
    if isinstance(attr, _changeattr):
        return attr.next()
    return attr


def _getattrs(attrs):
    """get attrs out of a sequence of attr/changeattr"""
    if attrs is not None:
        result = []
        for attr in _ensuresequence(attrs):
            if isinstance(attr, _changeattr):
                result.append(attr.attr())
            else:
                result.append(attr)
        return result


def _nextattrs(attrs):
    """perform next to a sequence of attr/changeattr"""
    if attrs is not None:
        result = []
        for attr in _ensuresequence(attrs):
            if isinstance(attr, _changeattr):
                result.append(attr.next())
            else:
                result.append(attr)
        return result


class changecolor(changeattr):

    def __init__(self, gradient):
        changeattr.__init__(self)
        self.gradient = gradient

    def _attr(self, index):
        if self.len:
            return self.gradient.getcolor(index/float(self.len-1))
        else:
            return gradient.getcolor(0)

changecolor.gray           = changecolor(color.gradient.gray)
changecolor.reversegray    = changecolor(color.gradient.reversegray)
changecolor.redgreen       = changecolor(color.gradient.redgreen)
changecolor.redblue        = changecolor(color.gradient.redblue)
changecolor.greenred       = changecolor(color.gradient.greenred)
changecolor.greenblue      = changecolor(color.gradient.greenblue)
changecolor.bluered        = changecolor(color.gradient.bluered)
changecolor.bluegreen      = changecolor(color.gradient.bluegreen)
changecolor.rainbow        = changecolor(color.gradient.rainbow)
changecolor.reverserainbow = changecolor(color.gradient.reverserainbow)
changecolor.hue            = changecolor(color.gradient.hue)
changecolor.reversehue     = changecolor(color.gradient.reversehue)


class changesequence(changeattr):
    """cycles through a sequence"""

    def __init__(self, *sequence):
        changeattr.__init__(self)
        if not len(sequence): raise("no attributes given")
        self.sequence = sequence

    def _attr(self, index):
        return self.sequence[index % len(self.sequence)]


changelinestyle = changesequence(canvas.linestyle.solid,
                                 canvas.linestyle.dashed,
                                 canvas.linestyle.dotted,
                                 canvas.linestyle.dashdotted)


changestrokedfilled = changesequence(canvas.stroked(), canvas.filled())
changefilledstroked = changesequence(canvas.filled(), canvas.stroked())


################################################################################
# styles
################################################################################


class mark:

    def _cross(self, x, y):
        return (path._moveto(x-0.5*self.size, y-0.5*self.size),
                path._lineto(x+0.5*self.size, y+0.5*self.size),
                path._moveto(x-0.5*self.size, y+0.5*self.size),
                path._lineto(x+0.5*self.size, y-0.5*self.size))

    def _plus(self, x, y):
        return (path._moveto(x-0.707106781*self.size, y),
                path._lineto(x+0.707106781*self.size, y),
                path._moveto(x, y-0.707106781*self.size),
                path._lineto(x, y+0.707106781*self.size))

    def _square(self, x, y):
        return (path._moveto(x-0.5*self.size, y-0.5 * self.size),
                path._lineto(x+0.5*self.size, y-0.5 * self.size),
                path._lineto(x+0.5*self.size, y+0.5 * self.size),
                path._lineto(x-0.5*self.size, y+0.5 * self.size),
                path.closepath())

    def _triangle(self, x, y):
        return (path._moveto(x-0.759835685*self.size, y-0.438691337*self.size),
                path._lineto(x+0.759835685*self.size, y-0.438691337*self.size),
                path._lineto(x, y+0.877382675*self.size),
                path.closepath())

    def _circle(self, x, y):
        return (path._arc(x, y, 0.564189583*self.size, 0, 360),
                path.closepath())

    def _diamond(self, x, y):
        return (path._moveto(x-0.537284965*self.size, y),
                path._lineto(x, y-0.930604859*self.size),
                path._lineto(x+0.537284965*self.size, y),
                path._lineto(x, y+0.930604859*self.size),
                path.closepath())

    cross = changesequence(_cross, _plus, _square, _triangle, _circle, _diamond)
    plus = changesequence(_plus, _square, _triangle, _circle, _diamond, _cross)
    square = changesequence(_square, _triangle, _circle, _diamond, _cross, _plus)
    triangle = changesequence(_triangle, _circle, _diamond, _cross, _plus, _square)
    circle = changesequence(_circle, _diamond, _cross, _plus, _square, _triangle)
    diamond = changesequence(_diamond, _cross, _plus, _square, _triangle, _circle)
    square2 = changesequence(_square, _square, _triangle, _triangle, _circle, _circle, _diamond, _diamond)
    triangle2 = changesequence(_triangle, _triangle, _circle, _circle, _diamond, _diamond, _square, _square)
    circle2 = changesequence(_circle, _circle, _diamond, _diamond, _square, _square, _triangle, _triangle)
    diamond2 = changesequence(_diamond, _diamond, _square, _square, _triangle, _triangle, _circle, _circle)

    def __init__(self, size="0.12 cm", errorscale=1/goldenrule, symbolstyles=canvas.stroked(), marker=cross):
        self.marker = marker
        self.size_str = size
        self.errorscale = errorscale
        self.symbolstyles = symbolstyles

    def next(self):
        return mark(size=_nextattr(self.size_str),
                    errorscale=_nextattr(self.errorscale),
                    marker=_nextattr(self.marker),
                    symbolstyles=_nextattrs(self.symbolstyles))

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
        self.size = unit.topt(unit.length(_getattr(self.size_str), default_type="v"))
        if self.symbolstyles is not None:
            symbolstyles = _getattrs(self.symbolstyles)

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
                    graph.stroke(path.path(path._moveto(xmin, y-self.errorscale*self.size),
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
                    graph.stroke(path.path(path._moveto(x-self.errorscale*self.size, ymin),
                                           path._lineto(x+self.errorscale*self.size, ymin),
                                           path._moveto(x, ymin),
                                           path._lineto(x, ymax),
                                           path._moveto(x-self.errorscale*self.size, ymax),
                                         path._lineto(x+self.errorscale*self.size, ymax)))
            except (TypeError, ValueError):
                pass
            if self.symbolstyles is not None:
                graph.draw(path.path(*_getattr(self.marker)(self, x, y)), *symbolstyles)


class line:

    def __init__(self, linestyles=()):
        self.linestyles = linestyles

    def next(self):
        return line(linestyles=_nextattrs(self.linestyles))

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
        if self.linestyles is not None:
            graph.stroke(self.path, *_getattrs(self.linestyles))


################################################################################
# data
################################################################################


class data:

    defaultstyle = mark()

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
