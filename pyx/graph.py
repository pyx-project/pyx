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

# TODO for 0.1: - documentation (some interfaces, user manual)


import types, re, math, string, sys
import bbox, canvas, path, tex, unit, mathtree, trafo, attrlist, color, datafile


goldenrule = 0.5 * (math.sqrt(5) + 1)

class _nodefault: pass


################################################################################
# some general helper routines
################################################################################


def _isstring(arg):
    "arg is string-like (cf. python cookbook 3.2)"
    try: arg + ''
    except: return None
    return 1


def _isnumber(arg):
    "arg is number-like"
    try: arg + 0
    except: return None
    return 1


def _isinteger(arg):
    "arg is integer-like"
    try:
        if type(arg + 0.0) is type(arg):
            return None
        return 1
    except: return None


def _issequence(arg):
    """arg is sequence-like (e.g. has a len)
       a string is *not* considered to be a sequence"""
    if _isstring(arg): return None
    try: len(arg)
    except: return None
    return 1


def _ensuresequence(arg):
    """return arg or (arg,) depending on the result of _issequence,
       None is converted to ()"""
    if _isstring(arg): return (arg,)
    if arg is None: return ()
    if _issequence(arg): return arg
    return (arg,)


def _getitemno(arg, n):
    if _issequence(arg):
        try: return arg[n]
        except: return None
    else:
        return arg


def _issequenceofsequences(arg):
    """check if arg has a sequence or None as it's first entry"""
    return _issequence(arg) and len(arg) and (_issequence(arg[0]) or arg[0] is None)


def _getsequenceno(arg, n):
    """get sequence number n if arg is a sequence of sequences,
       otherwise it gets just arg"""
    if _issequenceofsequences(arg):
        try: return arg[n]
        except: return None
    else:
        return arg



################################################################################
# maps
################################################################################

class _Imap:
    "maps convert a value into another value by bijective transformation f"

    def convert(self, x):
        "returns f(x)"

    def invert(self, y):
        "returns f^-1(y) where f^-1 is the inverse transformation (x=f^-1(f(x)) for all x)"

    def setbasepoint(self, basepoints):
        """set basepoints for the convertions
           basepoints are tuples (x, y) with y == f(x) and x == f^-1(y)
           the number of basepoints needed might depend on the transformation
           usually two pairs are needed like for linear maps, logarithmic maps, etc."""


class _linmap:
    "linear mapping"
    __implements__ = _Imap

    def setbasepoints(self, basepoints):
        self.dydx = (basepoints[1][1] - basepoints[0][1]) / float(basepoints[1][0] - basepoints[0][0])
        self.dxdy = (basepoints[1][0] - basepoints[0][0]) / float(basepoints[1][1] - basepoints[0][1])
        self.x1 = basepoints[0][0]
        self.y1 = basepoints[0][1]
        return self

    def convert(self, value):
        return self.y1 + self.dydx * (value - self.x1)

    def invert(self, value):
        return self.x1 + self.dxdy * (value - self.y1)


class _logmap:
    "logarithmic mapping"
    __implements__ = _Imap

    def setbasepoints(self, basepoints):
        self.dydx = ((basepoints[1][1] - basepoints[0][1]) /
                     float(math.log(basepoints[1][0]) - math.log(basepoints[0][0])))
        self.dxdy = ((math.log(basepoints[1][0]) - math.log(basepoints[0][0])) /
                     float(basepoints[1][1] - basepoints[0][1]))
        self.x1 = math.log(basepoints[0][0])
        self.y1 = basepoints[0][1]
        return self

    def convert(self, value):
        return self.y1 + self.dydx * (math.log(value) - self.x1)

    def invert(self, value):
        return math.exp(self.x1 + self.dxdy * (value - self.y1))



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
        if other is None:
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
            return frac(long(commaparts[0]), 1)
        elif len(commaparts) == 2:
            result = frac(1, 10l, power=len(commaparts[1]))
            result.enum = long(commaparts[0])*result.denom + long(commaparts[1])
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
    if not isinstance(arg, frac): raise ValueError("can't convert argument to frac")
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
    # TODO: improve this using bisect
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

    def __init__(self, ticks=None, labels=None, texts=None, mix=()):
        self.multipart = 0
        if ticks is None and labels is not None:
            self.ticks = _ensuresequence(_getsequenceno(labels, 0))
        else:
            self.ticks = ticks

        if labels is None and ticks is not None:
            self.labels = _ensuresequence(_getsequenceno(ticks, 0))
        else:
            self.labels = labels
        self.texts = texts
        self.mix = mix


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

    def part(self):
        ticks = list(self.mix)
        if _issequenceofsequences(self.ticks):
            for fracs, level in zip(self.ticks, xrange(sys.maxint)):
                ticks = _mergeticklists(ticks, [tick(frac.enum, frac.denom, ticklevel = level)
                                                for frac in self.checkfraclist(*map(_ensurefrac, _ensuresequence(fracs)))])
        else:
            ticks = _mergeticklists(ticks, [tick(frac.enum, frac.denom, ticklevel = 0)
                                            for frac in self.checkfraclist(*map(_ensurefrac, _ensuresequence(self.ticks)))])

        if _issequenceofsequences(self.labels):
            for fracs, level in zip(self.labels, xrange(sys.maxint)):
                ticks = _mergeticklists(ticks, [tick(frac.enum, frac.denom, labellevel = level)
                                                for frac in self.checkfraclist(*map(_ensurefrac, _ensuresequence(fracs)))])
        else:
            ticks = _mergeticklists(ticks, [tick(frac.enum, frac.denom, labellevel = 0)
                                            for frac in self.checkfraclist(*map(_ensurefrac, _ensuresequence(self.labels)))])

        _mergetexts(ticks, self.texts)

        return ticks

    def defaultpart(self, min, max, extendmin, extendmax):
        return self.part()


class linpart:

    def __init__(self, ticks=None, labels=None, texts=None, extendtick=0, extendlabel=None, epsilon=1e-10, mix=()):
        self.multipart = 0
        if ticks is None and labels is not None:
            self.ticks = (_ensurefrac(_ensuresequence(labels)[0]),)
        else:
            self.ticks = map(_ensurefrac, _ensuresequence(ticks))
        if labels is None and ticks is not None:
            self.labels = (_ensurefrac(_ensuresequence(ticks)[0]),)
        else:
            self.labels = map(_ensurefrac, _ensuresequence(labels))
        self.texts = texts
        self.extendtick = extendtick
        self.extendlabel = extendlabel
        self.epsilon = epsilon
        self.mix = mix

    def extendminmax(self, min, max, frac, extendmin, extendmax):
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

    def defaultpart(self, min, max, extendmin, extendmax):
        if self.extendtick is not None and len(self.ticks) > self.extendtick:
            min, max = self.extendminmax(min, max, self.ticks[self.extendtick], extendmin, extendmax)
        if self.extendlabel is not None and len(self.labels) > self.extendlabel:
            min, max = self.extendminmax(min, max, self.labels[self.extendlabel], extendmin, extendmax)

        ticks = list(self.mix)
        for i in range(len(self.ticks)):
            ticks = _mergeticklists(ticks, self.getticks(min, max, self.ticks[i], ticklevel = i))
        for i in range(len(self.labels)):
            ticks = _mergeticklists(ticks, self.getticks(min, max, self.labels[i], labellevel = i))

        _mergetexts(ticks, self.texts)

        return ticks


class autolinpart:

    defaultlist = ((frac(1, 1), frac(1, 2)),
                   (frac(2, 1), frac(1, 1)),
                   (frac(5, 2), frac(5, 4)),
                   (frac(5, 1), frac(5, 2)))

    def __init__(self, list=defaultlist, extendtick=0, epsilon=1e-10, mix=()):
        self.multipart = 1
        self.list = list
        self.extendtick = extendtick
        self.epsilon = epsilon
        self.mix = mix

    def defaultpart(self, min, max, extendmin, extendmax):
        base = frac(10L, 1, int(math.log(max - min) / math.log(10)))
        ticks = self.list[0]
        useticks = [tick * base for tick in ticks]
        self.lesstickindex = self.moretickindex = 0
        self.lessbase = self.morebase = base
        self.min, self.max, self.extendmin, self.extendmax = min, max, extendmin, extendmax
        part = linpart(ticks=useticks, extendtick=self.extendtick, epsilon=self.epsilon, mix=self.mix)
        return part.defaultpart(self.min, self.max, self.extendmin, self.extendmax)

    def lesspart(self):
        if self.lesstickindex < len(self.list) - 1:
            self.lesstickindex += 1
        else:
            self.lesstickindex = 0
            self.lessbase.enum *= 10
        ticks = self.list[self.lesstickindex]
        useticks = [tick * self.lessbase for tick in ticks]
        part = linpart(ticks=useticks, extendtick=self.extendtick, epsilon=self.epsilon, mix=self.mix)
        return part.defaultpart(self.min, self.max, self.extendmin, self.extendmax)

    def morepart(self):
        if self.moretickindex:
            self.moretickindex -= 1
        else:
            self.moretickindex = len(self.list) - 1
            self.morebase.denom *= 10
        ticks = self.list[self.moretickindex]
        useticks = [tick * self.morebase for tick in ticks]
        part = linpart(ticks=useticks, extendtick=self.extendtick, epsilon=self.epsilon, mix=self.mix)
        return part.defaultpart(self.min, self.max, self.extendmin, self.extendmax)


class shiftfracs:

    def __init__(self, shift, *fracs):
         self.shift = shift
         self.fracs = fracs


class logpart(linpart):

    shift5fracs1   = shiftfracs(100000, frac(1, 1))
    shift4fracs1   = shiftfracs(10000, frac(1, 1))
    shift3fracs1   = shiftfracs(1000, frac(1, 1))
    shift2fracs1   = shiftfracs(100, frac(1, 1))
    shiftfracs1    = shiftfracs(10, frac(1, 1))
    shiftfracs125  = shiftfracs(10, frac(1, 1), frac(2, 1), frac(5, 1))
    shiftfracs1to9 = shiftfracs(10, *list(map(lambda x: frac(x, 1), range(1, 10))))
    #         ^- we always include 1 in order to get extendto(tick|label)level to work as expected

    def __init__(self, ticks=None, labels=None, texts=None, extendtick=0, extendlabel=None, epsilon=1e-10, mix=()):
        self.multipart = 0
        if ticks is None and labels is not None:
            self.ticks = (_ensuresequence(labels)[0],)
        else:
            self.ticks = _ensuresequence(ticks)

        if labels is None and ticks is not None:
            self.labels = (_ensuresequence(ticks)[0],)
        else:
            self.labels = _ensuresequence(labels)
        self.texts = texts
        self.extendtick = extendtick
        self.extendlabel = extendlabel
        self.epsilon = epsilon
        self.mix = mix

    def extendminmax(self, min, max, shiftfracs, extendmin, extendmax):
        minpower = None
        maxpower = None
        for i in xrange(len(shiftfracs.fracs)):
            imin = int(math.floor(math.log(min / float(shiftfracs.fracs[i])) /
                                  math.log(shiftfracs.shift) + self.epsilon)) + 1
            imax = int(math.ceil(math.log(max / float(shiftfracs.fracs[i])) /
                                 math.log(shiftfracs.shift) - self.epsilon)) - 1
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
            min = float(minfrac) * float(shiftfracs.shift) ** minpower
        if extendmax:
            max = float(maxfrac) * float(shiftfracs.shift) ** maxpower
        return min, max

    def getticks(self, min, max, shiftfracs, ticklevel=None, labellevel=None):
        ticks = list(self.mix)
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


class autologpart(logpart):

    defaultlist = (((logpart.shiftfracs1,      # ticks
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

    def __init__(self, list=defaultlist, listindex=None, extendtick=0, extendlabel=None, epsilon=1e-10, mix=()):
        self.multipart = 1
        self.list = list
        if listindex is None:
            listindex = divmod(len(list), 2)[0]
        self.listindex = listindex
        self.extendtick = extendtick
        self.extendlabel = extendlabel
        self.epsilon = epsilon
        self.mix = mix

    def defaultpart(self, min, max, extendmin, extendmax):
        self.min, self.max, self.extendmin, self.extendmax = min, max, extendmin, extendmax
        self.morelistindex = self.listindex
        self.lesslistindex = self.listindex
        part = logpart(ticks=self.list[self.listindex][0], labels=self.list[self.listindex][1],
                       extendtick=self.extendtick, extendlabel=self.extendlabel, epsilon=self.epsilon, mix=self.mix)
        return part.defaultpart(self.min, self.max, self.extendmin, self.extendmax)

    def lesspart(self):
        self.lesslistindex += 1
        if self.lesslistindex < len(self.list):
            part = logpart(ticks=self.list[self.lesslistindex][0], labels=self.list[self.lesslistindex][1],
                           extendtick=self.extendtick, extendlabel=self.extendlabel, epsilon=self.epsilon, mix=self.mix)
            return part.defaultpart(self.min, self.max, self.extendmin, self.extendmax)
        return None

    def morepart(self):
        self.morelistindex -= 1
        if self.morelistindex >= 0:
            part = logpart(ticks=self.list[self.morelistindex][0], labels=self.list[self.morelistindex][1],
                           extendtick=self.extendtick, extendlabel=self.extendlabel, epsilon=self.epsilon, mix=self.mix)
            return part.defaultpart(self.min, self.max, self.extendmin, self.extendmax)
        return None



################################################################################
# rate partitions
################################################################################


class _cuberate:

        def __init__(self, opt, left=None, right=None, weight=1):
            if left is None:
                left = 0
            if right is None:
                right = 3*opt
            self.opt = opt
            self.left = left
            self.right = right
            self.weight = weight

        def rate(self, value, stretch = 1):
            opt = stretch * self.opt
            if value < opt:
                other = stretch * self.left
            elif value > opt:
                other = stretch * self.right
            else:
                return 0
            factor = (value - opt) / float(other - opt)
            return self.weight * (factor ** 3)


class cuberate:

    linticks = (_cuberate(4), _cuberate(10, weight=0.5), )
    linlabels = (_cuberate(4), )
    logticks = (_cuberate(5, right=20), _cuberate(20, right=100, weight=0.5), )
    loglabels = (_cuberate(5, right=20), _cuberate(5, left=-20, right=20, weight=0.5), )
    stdtickrange = (_cuberate(1, weight=2))

    def __init__(self, ticks=linticks, labels=linlabels, tickrange=stdtickrange):
        self.ticks = ticks
        self.labels = labels
        self.tickrange = tickrange

    def ratepart(self, axis, part, stretch):
        tickslen = len(self.ticks)
        labelslen = len(self.labels)
        ticks = [0]*tickslen
        labels = [0]*labelslen
        if part is not None:
            for tick in part:
                if tick.ticklevel is not None:
                    for level in xrange(tick.ticklevel, tickslen):
                        ticks[level] += 1
                if tick.labellevel is not None:
                    for level in xrange(tick.labellevel, labelslen):
                        labels[level] += 1
        rate = 0
        weight = 0
        for tick, rater in zip(ticks, self.ticks):
            rate += rater.rate(tick, stretch=stretch)
            weight += rater.weight
        for label, rater in zip(labels, self.labels):
            rate += rater.rate(label, stretch=stretch)
            weight += rater.weight
        if part is not None and len(part):
            tickmin, tickmax = axis.gettickrange()
            rate += self.tickrange.rate((float(part[-1]) - float(part[0])) * axis.divisor / (tickmax - tickmin))
        else:
            rate += self.tickrange.rate(0)
        weight += self.tickrange.weight
        return rate/weight



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
        return unit.t_pt(self._circlealignvector(unit.topt(a), dx, dy))

    def linealignvector(self, a, dx, dy):
        return unit.t_pt(self._linealignvector(unit.topt(a), dx, dy))

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

    def _extent(self, dx, dy):
        x1, y1 = self._linealignvector(0, dx, dy)
        x2, y2 = self._linealignvector(0, -dx, -dy)
        return (x1-x2)*dx + (y1-y2)*dy

    def extent(self, dx, dy):
        return unit.t_pt(self._extent(dx, dy))


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

    def __init__(self, _tex, text, textattrs = (), vtext="0"):
        self.tex = _tex
        self.text = text
        self.textattrs = textattrs
        self.reldx, self.reldy = 1, 0
        self.halign = self.attrget(self.textattrs, tex.halign, None)
        self.textattrs = self.attrdel(self.textattrs, tex.halign)
        self.direction = self.attrget(self.textattrs, tex.direction, None)
        hwdtextattrs = self.attrdel(self.textattrs, tex.direction)
        self.ht = unit.topt(self.tex.textht(text, *hwdtextattrs))
        self.wd = unit.topt(self.tex.textwd(text, *hwdtextattrs))
        self.dp = unit.topt(self.tex.textdp(text, *hwdtextattrs))
        self.shiftht = 0.5 * unit.topt(self.tex.textht(vtext, *hwdtextattrs))
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
            if self.halign is tex.halign.left:
                xorigin = 0
            if self.halign is tex.halign.right:
                xorigin = self.wd
        _rectbox.__init__(self, 0, -self.dp, self.wd, self.ht, xorigin, self.shiftht)
        if self.direction is not None:
            self.transform(trafo._rotation(self.direction.value))

    def transform(self, trafo):
        _rectbox.transform(self, trafo)
        self.xtext, self.ytext = trafo._apply(self.xtext, self.ytext)

    def _printtext(self, x, y):
        self.tex._text(x + self.xtext, y + self.ytext, self.text, *self.textattrs)

    def printtext(self, *args):
        self._printtext(*map(unit.topt, args))



################################################################################
# axis painter
################################################################################


class axispainter(attrlist.attrlist):

    defaultticklengths = ["%0.5f cm" % (0.2*goldenrule**(-i)) for i in range(10)]

    paralleltext = -90
    orthogonaltext = 0

    fractypeauto = 1
    fractyperat = 2
    fractypedec = 3
    fractypeexp = 4

    def __init__(self, innerticklengths=defaultticklengths,
                       outerticklengths=None,
                       tickattrs=(),
                       gridattrs=None,
                       zerolineattrs=(),
                       baselineattrs=canvas.linecap.square,
                       labeldist="0.3 cm",
                       labelattrs=((), tex.fontsize.footnotesize),
                       labeldirection=None,
                       labelhequalize=0,
                       labelvequalize=1,
                       titledist="0.3 cm",
                       titleattrs=(),
                       titledirection=-90,
                       titlepos=0.5,
                       fractype=fractypeauto,
                       ratfracsuffixenum=1,
                       ratfracover=r"\over",
                       decfracpoint=".",
                       expfractimes=r"\cdot",
                       expfracpre1=0,
                       expfracminexp=4,
                       suffix0=0,
                       suffix1=0):
        self.innerticklengths_str = innerticklengths
        self.outerticklengths_str = outerticklengths
        self.tickattrs = tickattrs
        self.gridattrs = gridattrs
        self.zerolineattrs = zerolineattrs
        self.baselineattrs = baselineattrs
        self.labeldist_str = labeldist
        self.labelattrs = labelattrs
        self.labeldirection = labeldirection
        self.labelhequalize = labelhequalize
        self.labelvequalize = labelvequalize
        self.titledist_str = titledist
        self.titleattrs = titleattrs
        self.titledirection = titledirection
        self.titlepos = titlepos
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
        if not self.attrcount(tick.labelattrs, tex.style):
            tick.labelattrs += [tex.style.math]

    def paint(self, graph, axis):

        def topt_v_recursive(arg):
            if _issequence(arg):
                # return map(topt_v_recursive, arg) needs python2.2
                return [unit.topt(unit.length(a, default_type="v")) for a in arg]
            else:
                if arg is not None:
                    return unit.topt(unit.length(arg, default_type="v"))

        innerticklengths = topt_v_recursive(self.innerticklengths_str)
        outerticklengths = topt_v_recursive(self.outerticklengths_str)
        labeldist = unit.topt(unit.length(self.labeldist_str, default_type="v"))
        titledist = unit.topt(unit.length(self.titledist_str, default_type="v"))

        for tick in axis.ticks:
            tick.virtual = axis.convert(float(tick) * axis.divisor)
            tick.x, tick.y = axis.tickpoint(axis, tick.virtual)
            tick.dx, tick.dy = axis.tickdirection(axis, tick.virtual)

        for tick in axis.ticks:
            if tick.labellevel is not None:
                tick.labelattrs = _getsequenceno(self.labelattrs, tick.labellevel)
                if tick.labelattrs is not None:
                    tick.labelattrs = list(_ensuresequence(tick.labelattrs))
                    if tick.text is None:
                        tick.suffix = axis.suffix
                        self.createtext(tick)
                    if self.labeldirection is not None and not self.attrcount(tick.labelattrs, tex.direction):
                        tick.labelattrs += [tex.direction(self.reldirection(self.labeldirection, tick.dx, tick.dy))]
                    tick.textbox = textbox(graph.tex, tick.text, textattrs=tick.labelattrs)
                else:
                    tick.textbox = None
            else:
                tick.textbox = None

        for tick in axis.ticks[1:]:
            if tick.dx != axis.ticks[0].dx or tick.dy != axis.ticks[0].dy:
                equaldirection = 0
                break
        else:
            equaldirection = 1

        if equaldirection:
            maxht, maxwd, maxdp = 0, 0, 0
            for tick in axis.ticks:
                if tick.textbox is not None:
                    if maxht < tick.textbox.ht: maxht = tick.textbox.ht
                    if maxwd < tick.textbox.wd: maxwd = tick.textbox.wd
                    if maxdp < tick.textbox.dp: maxdp = tick.textbox.dp
            for tick in axis.ticks:
                if tick.textbox is not None:
                    if self.labelhequalize:
                        tick.textbox.manualextents(wd = maxwd)
                    if self.labelvequalize:
                        tick.textbox.manualextents(ht = maxht, dp = maxdp)

        for tick in axis.ticks:
            if tick.textbox is not None:
                tick.textbox._linealign(labeldist, tick.dx, tick.dy)
                tick._extent = tick.textbox._extent(tick.dx, tick.dy) + labeldist

        # we could now measure distances between textboxes -> TODO: rating

        axis._extent = 0
        for tick in axis.ticks:
            if tick.ticklevel is not None:
                tick.innerticklength = _getitemno(innerticklengths, tick.ticklevel)
                tick.outerticklength = _getitemno(outerticklengths, tick.ticklevel)
                if tick.innerticklength is not None and tick.outerticklength is None:
                    tick.outerticklength = 0
                if tick.outerticklength is not None and tick.innerticklength is None:
                    tick.innerticklength = 0
            if tick.textbox is None:
                if tick.outerticklength is not None and tick.outerticklength > 0:
                    tick._extent = tick.outerticklength
                else:
                    tick._extent = 0
            if axis._extent < tick._extent:
                axis._extent = tick._extent

        for tick in axis.ticks:
            if tick.ticklevel is not None:
                if tick != frac(0, 1) or self.zerolineattrs is None:
                    gridattrs = _getsequenceno(self.gridattrs, tick.ticklevel)
                    if gridattrs is not None:
                        graph.stroke(axis.vgridpath(tick.virtual), *_ensuresequence(gridattrs))
                tickattrs = _getsequenceno(self.tickattrs, tick.ticklevel)
                if None not in (tick.innerticklength, tick.outerticklength, tickattrs):
                    x1 = tick.x - tick.dx * tick.innerticklength
                    y1 = tick.y - tick.dy * tick.innerticklength
                    x2 = tick.x + tick.dx * tick.outerticklength
                    y2 = tick.y + tick.dy * tick.outerticklength
                    graph.stroke(path._line(x1, y1, x2, y2), *_ensuresequence(tickattrs))
            if tick.textbox is not None:
                tick.textbox._printtext(tick.x, tick.y)
        if self.baselineattrs is not None:
            graph.stroke(axis.vbaseline(axis, 0, 1), *_ensuresequence(self.baselineattrs))
        if self.zerolineattrs is not None:
            if len(axis.ticks) and axis.ticks[0] * axis.ticks[-1] < frac(0, 1):
                graph.stroke(axis.vgridpath(axis.convert(0)), *_ensuresequence(self.zerolineattrs))


        if axis.title is not None and self.titleattrs is not None:
            x, y = axis.tickpoint(axis, self.titlepos)
            dx, dy = axis.tickdirection(axis, self.titlepos)
            # no not modify self.titleattrs ... the painter might be used by several axes!!!
            titleattrs = list(_ensuresequence(self.titleattrs))
            if self.titledirection is not None and not self.attrcount(titleattrs, tex.direction):
                titleattrs = titleattrs + [tex.direction(self.reldirection(self.titledirection, dx, dy))]
            axis.titlebox = textbox(graph.tex, axis.title, textattrs=titleattrs)
            axis._extent += titledist
            axis.titlebox._linealign(axis._extent, dx, dy)
            axis.titlebox._printtext(x, y)
            axis._extent += axis.titlebox._extent(dx, dy)


class linkaxispainter(axispainter):

    def __init__(self, skipticklevel=None, skiplabellevel=0, zerolineattrs=None, **args):
        self.skipticklevel = skipticklevel
        self.skiplabellevel = skiplabellevel
        args["zerolineattrs"] = zerolineattrs
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
        # XXX: don't forget to calculate new text positions as soon as this is moved
        #      outside of the paint method (when rating is moved into the axispainter)

        axis.convert = axis.linkedaxis.convert
        axis.divisor = axis.linkedaxis.divisor
        axis.suffix = axis.linkedaxis.suffix
        axispainter.paint(self, graph, axis)



################################################################################
# axes
################################################################################


class _axis:

    def __init__(self, min=None, max=None, reverse=0, divisor=1,
                       datavmin=None, datavmax=None, tickvmin=None, tickvmax=None,
                       title=None, suffix=None, painter=axispainter()):
        if None not in (min, max) and min > max:
            min, max = max, min
            if reverse:
                reverse = 0
            else:
                reverse = 1
        self.fixmin = min is not None
        self.fixmax = max is not None
        self.min, self.max = min, max
        self.reverse = reverse

        self.datamin = self.datamax = self.tickmin = self.tickmax = None
        if datavmin is None:
            if self.fixmin:
                self.datavmin = 0
            else:
                self.datavmin = 0.05
        else:
            self.datavmin = datavmin
        if datavmax is None:
            if self.fixmax:
                self.datavmax = 1
            else:
                self.datavmax = 0.95
        else:
            self.datavmax = datavmax
        if tickvmin is None:
            self.tickvmin = 0
        else:
            self.tickvmin = tickvmin
        if tickvmax is None:
            self.tickvmax = 1
        else:
            self.tickvmax = tickvmax

        self.title = title
        self.painter = painter
        self.divisor = divisor
        self.suffix = suffix
        self.canconvert = 0
        self._setrange()

    def _setrange(self, min=None, max=None):
        if not self.fixmin and min is not None and (self.min is None or min < self.min):
            self.min = min
        if not self.fixmax and max is not None and (self.max is None or max > self.max):
            self.max = max
        if None not in (self.min, self.max):
            min, max, vmin, vmax = self.min, self.max, 0, 1
            self.canconvert = 1
            self.setbasepoints(((min, vmin), (max, vmax)))
            if not self.fixmin:
                if self.datamin is not None and self.convert(self.datamin) < self.datavmin:
                    min, vmin = self.datamin, self.datavmin
                    self.setbasepoints(((min, vmin), (max, vmax)))
                if self.tickmin is not None and self.convert(self.tickmin) < self.tickvmin:
                    min, vmin = self.tickmin, self.tickvmin
                    self.setbasepoints(((min, vmin), (max, vmax)))
            if not self.fixmax:
                if self.datamax is not None and self.convert(self.datamax) > self.datavmax:
                    max, vmax = self.datamax, self.datavmax
                    self.setbasepoints(((min, vmin), (max, vmax)))
                if self.tickmax is not None and self.convert(self.tickmax) > self.tickvmax:
                    max, vmax = self.tickmax, self.tickvmax
                    self.setbasepoints(((min, vmin), (max, vmax)))
            if self.reverse:
                self.setbasepoints(((min, vmax), (max, vmin)))

    def gridpath(self, x):
        return self.vgridpath(self.convert(x))

    def setdatarange(self, min, max):
        self.datamin, self.datamax = min, max
        self._setrange(min, max)

    def settickrange(self, min, max):
        self.tickmin, self.tickmax = min, max
        self._setrange(min, max)

    def getdatarange(self):
        if self.canconvert:
            if self.reverse:
                return self.invert(1-self.datavmin), self.invert(1-self.datavmax)
            else:
                return self.invert(self.datavmin), self.invert(self.datavmax)

    def gettickrange(self):
        if self.canconvert:
            if self.reverse:
                return self.invert(1-self.tickvmin), self.invert(1-self.tickvmax)
            else:
                return self.invert(self.tickvmin), self.invert(self.tickvmax)


class linaxis(_axis, _linmap):

    def __init__(self, part=autolinpart(), rate=cuberate(), **args):
        _axis.__init__(self, **args)
        self.part = part
        self.rate = rate


class logaxis(_axis, _logmap):

    def __init__(self, part=autologpart(), rate=cuberate(ticks=cuberate.logticks, labels=cuberate.loglabels), **args):
        _axis.__init__(self, **args)
        self.part = part
        self.rate = rate


class linkaxis:

    def __init__(self, linkedaxis, title=None, painter=linkaxispainter()):
        self.linkedaxis = linkedaxis
        while isinstance(self.linkedaxis, linkaxis):
            self.linkedaxis = self.linkedaxis.linkedaxis
        self.title = title
        self.painter = painter

    def getdatarange(self):
        return self.linkedaxis.getdatarange()

    def setdatarange(self, min, max):
        prevrange = self.linkedaxis.getdatarange()
        self.linkedaxis.setdatarange(min, max)
        if hasattr(self.linkedaxis, "ticks") and prevrange != self.linkedaxis.getdatarange():
            raise RuntimeError("linkaxis datarange setting performed while linked axis layout already fixed")



################################################################################
# graph
################################################################################


class graphxy(canvas.canvas):

    Names = "x", "y"

    def clipcanvas(self):
        return self.insert(canvas.canvas(canvas.clip(path._rect(self._xpos, self._ypos, self._width, self._height))))

    def plot(self, data, style=None):
        if self.haslayout:
            raise RuntimeError("layout setup was already performed")
        if style is None:
            if self.defaultstyle.has_key(data.defaultstyle):
                style = self.defaultstyle[data.defaultstyle].iterate()
            else:
                style = data.defaultstyle()
                self.defaultstyle[data.defaultstyle] = style
        styles = []
        first = 1
        for d in _ensuresequence(data):
            if first:
                styles.append(style)
            else:
                styles.append(style.iterate())
            first = 0
            d.setstyle(self, styles[-1])
            self.data.append(d)
        if _issequence(data):
            return styles
        return styles[0]

    def _xtickpoint(self, axis, v):
        return (self._xpos+v*self._width, axis.axispos)

    def _ytickpoint(self, axis, v):
        return (axis.axispos, self._ypos+v*self._height)

    def tickdirection(self, axis, virtual):
        return axis.fixtickdirection

    def _pos(self, x, y, xaxis=None, yaxis=None):
        if xaxis is None: xaxis = self.axes["x"]
        if yaxis is None: yaxis = self.axes["y"]
        return self._xpos+xaxis.convert(x)*self._width, self._ypos+yaxis.convert(y)*self._height

    def pos(self, x, y, xaxis=None, yaxis=None):
        if xaxis is None: xaxis = self.axes["x"]
        if yaxis is None: yaxis = self.axes["y"]
        return self.xpos+xaxis.convert(x)*self.width, self.ypos+yaxis.convert(y)*self.height

    def _vpos(self, vx, vy):
        return self._xpos+vx*self._width, self._ypos+vy*self._height

    def vpos(self, vx, vy):
        return self.xpos+vx*self.width, self.ypos+vy*self.height

    def xbaseline(self, axis, x1, x2, shift=0, xaxis=None):
        if xaxis is None: xaxis = self.axes["x"]
        v1, v2 = xaxis.convert(x1), xaxis.convert(x2)
        return path._line(self._xpos+v1*self._width, axis.axispos+shift,
                          self._xpos+v2*self._width, axis.axispos+shift)

    def ybaseline(self, axis, y1, y2, shift=0, yaxis=None):
        if yaxis is None: yaxis = self.axes["y"]
        v1, v2 = yaxis.convert(y1), yaxis.convert(y2)
        return path._line(axis.axispos+shift, self._ypos+v1*self._height,
                          axis.axispos+shift, self._ypos+v2*self._height)

    def vxbaseline(self, axis, v1, v2, shift=0):
        return path._line(self._xpos+v1*self._width, axis.axispos+shift,
                          self._xpos+v2*self._width, axis.axispos+shift)

    def vybaseline(self, axis, v1, v2, shift=0):
        return path._line(axis.axispos+shift, self._ypos+v1*self._height,
                          axis.axispos+shift, self._ypos+v2*self._height)

    def xgridpath(self, x, xaxis=None):
        if xaxis is None: xaxis = self.axes["x"]
        v = xaxis.convert(x)
        return path._line(self._xpos+v*self._width, self._ypos,
                          self._xpos+v*self._width, self._ypos+self._height)

    def ygridpath(self, y, yaxis=None):
        if yaxis is None: yaxis = self.axes["y"]
        v = yaxis.convert(y)
        return path._line(self._xpos, self._ypos+v*self._height,
                          self._xpos+self._width, self._ypos+v*self._height)

    def vxgridpath(self, v):
        return path._line(self._xpos+v*self._width, self._ypos,
                          self._xpos+v*self._width, self._ypos+self._height)

    def vygridpath(self, v):
        return path._line(self._xpos, self._ypos+v*self._height,
                          self._xpos+self._width, self._ypos+v*self._height)

    def _addpos(self, x, y, dx, dy):
        return x+dx, y+dy

    def _connect(self, x1, y1, x2, y2):
        return path._lineto(x2, y2)

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
                axis.setdatarange(*ranges[key])
            ranges[key] = axis.getdatarange()
            if ranges[key] is None:
                del ranges[key]
        return ranges

    def removedomethod(self, method):
        hadmethod = 0
        while 1:
            try:
                self.domethods.remove(method)
                hadmethod = 1
            except ValueError:
                return hadmethod

    def dolayout(self):
        if not self.removedomethod(self.dolayout): return
        self.haslayout = 1
        # create list of ranges
        # 1. gather ranges
        ranges = self.gatherranges()
        # 2. calculate additional ranges out of known ranges
        for data in self.data:
            data.setranges(ranges)
        # 3. gather ranges again
        ranges = self.gatherranges()

        # TODO: move rating into the painter
        for key, axis in self.axes.items():
            if isinstance(axis, linkaxis):
                continue

            # TODO: make use of stretch
            min, max = axis.gettickrange()
            axis.ticks = axis.part.defaultpart(min/axis.divisor, max/axis.divisor, not axis.fixmin, not axis.fixmax)
            if axis.part.multipart:
                # lesspart and morepart can be called after defaultpart,
                # although some axes may share their autoparting ---
                # it works, because the axes are processed sequentially
                rate = axis.rate.ratepart(axis, axis.ticks, 1)
                maxworse = 2
                worse = 0
                while worse < maxworse:
                    newticks = axis.part.lesspart()
                    newrate = axis.rate.ratepart(axis, newticks, 1)
                    if newticks is not None and newrate < rate:
                        axis.ticks = newticks
                        rate = newrate
                        worse = 0
                    else:
                        worse += 1
                worse = 0
                while worse < maxworse:
                    newticks = axis.part.morepart()
                    newrate = axis.rate.ratepart(axis, newticks, 1)
                    if newticks is not None and newrate < rate:
                        axis.ticks = newticks
                        rate = newrate
                        worse = 0
                    else:
                        worse += 1
            if len(axis.ticks):
                axis.settickrange(float(axis.ticks[0])*axis.divisor, float(axis.ticks[-1])*axis.divisor)

    def dobackground(self):
        self.dolayout()
        if not self.removedomethod(self.dobackground): return
        if self.backgroundattrs is not None:
            self.draw(path._rect(self._xpos, self._ypos, self._width, self._height),
                      *_ensuresequence(self.backgroundattrs))

    def doaxes(self):
        self.dolayout()
        if not self.removedomethod(self.doaxes): return
        axesdist = unit.topt(unit.length(self.axesdist_str, default_type="v"))
        XPattern = re.compile(r"%s([2-9]|[1-9][0-9]+)?$" % self.Names[0])
        YPattern = re.compile(r"%s([2-9]|[1-9][0-9]+)?$" % self.Names[1])
        self._xaxisextents = [0, 0]
        self._yaxisextents = [0, 0]
        needxaxisdist = [0, 0]
        needyaxisdist = [0, 0]
        items = list(self.axes.items())
        items.sort() #TODO: alphabetical sorting breaks for axis numbers bigger than 9
        for key, axis in items:
            num = self.keynum(key)
            num2 = 1 - num % 2 # x1 -> 0, x2 -> 1, x3 -> 0, x4 -> 1, ...
            num3 = 1 - 2 * (num % 2) # x1 -> -1, x2 -> 1, x3 -> -1, x4 -> 1, ...
            if XPattern.match(key):
                if needxaxisdist[num2]:
                    self._xaxisextents[num2] += axesdist
                axis.axispos = self._ypos+num2*self._height + num3*self._xaxisextents[num2]
                axis.tickpoint = self._xtickpoint
                axis.fixtickdirection = (0, num3)
                axis.vgridpath = self.vxgridpath
                axis.vbaseline = self.vxbaseline
            elif YPattern.match(key):
                if needyaxisdist[num2]:
                    self._yaxisextents[num2] += axesdist
                axis.axispos = self._xpos+num2*self._width + num3*self._yaxisextents[num2]
                axis.tickpoint = self._ytickpoint
                axis.fixtickdirection = (num3, 0)
                axis.vgridpath = self.vygridpath
                axis.vbaseline = self.vybaseline
            else:
                raise ValueError("Axis key '%s' not allowed" % key)
            axis.tickdirection = self.tickdirection
            if axis.painter is not None:
                axis.painter.paint(self, axis)
            if XPattern.match(key):
                self._xaxisextents[num2] += axis._extent
                needxaxisdist[num2] = 1
            if YPattern.match(key):
                self._yaxisextents[num2] += axis._extent
                needyaxisdist[num2] = 1

    def dodata(self):
        self.dolayout()
        if not self.removedomethod(self.dodata): return
        for data in self.data:
            data.draw(self)

    def finish(self):
        while len(self.domethods):
            self.domethods[0]()

    def __init__(self, tex, xpos=0, ypos=0, width=None, height=None, ratio=goldenrule,
                 backgroundattrs=None, axesdist="0.8 cm", **axes):
        canvas.canvas.__init__(self)
        self.tex = tex
        self.xpos = xpos
        self.ypos = ypos
        self._xpos = unit.topt(xpos)
        self._ypos = unit.topt(ypos)
        if (width is not None) and (height is None):
             height = (1/ratio) * width
        if (height is not None) and (width is None):
             width = ratio * height
        self._width = unit.topt(width)
        self._height = unit.topt(height)
        self.width = width
        self.height = height
        if self._width <= 0: raise ValueError("width < 0")
        if self._height <= 0: raise ValueError("height < 0")
        if not axes.has_key("x"):
            axes["x"] = linaxis()
        elif axes["x"] is None:
            del axes["x"]
        if not axes.has_key("x2") and axes.has_key("x"):
            axes["x2"] = linkaxis(axes["x"])
        elif axes["x2"] is None:
            del axes["x2"]
        if not axes.has_key("y"):
            axes["y"] = linaxis()
        elif axes["y"] is None:
            del axes["y"]
        if not axes.has_key("y2") and axes.has_key("y"):
            axes["y2"] = linkaxis(axes["y"])
        elif axes["y2"] is None:
            del axes["y2"]
        self.axes = axes
        self.axesdist_str = axesdist
        self.backgroundattrs = backgroundattrs
        self.data = []
        self.domethods = [self.dolayout, self.dobackground, self.doaxes, self.dodata]
        self.haslayout = 0
        self.defaultstyle = {}

    def bbox(self):
        self.finish()
        return bbox.bbox(self._xpos - self._yaxisextents[0],
                         self._ypos - self._xaxisextents[0],
                         self._xpos + self._width + self._yaxisextents[1],
                         self._ypos + self._height + self._xaxisextents[1])

    def write(self, file):
        self.finish()
        canvas.canvas.write(self, file)



################################################################################
# attr changers
################################################################################


#class _Ichangeattr:
#    """attribute changer
#       is an iterator for attributes where an attribute
#       is not refered by just a number (like for a sequence),
#       but also by the number of attributes requested
#       by calls of the next method (like for an color gradient)
#       (you should ensure to call all needed next before the attr)
#
#       the attribute itself is implemented by overloading the _attr method"""
#
#    def attr(self):
#        "get an attribute"
#
#    def next(self):
#        "get an attribute changer for the next attribute"


class _changeattr: pass


class changeattr(_changeattr):

    def __init__(self):
        self.counter = 1

    def getattr(self):
        return self.attr(0)

    def iterate(self):
        newindex = self.counter
        self.counter += 1
        return refattr(self, newindex)


class refattr(_changeattr):

    def __init__(self, ref, index):
        self.ref = ref
        self.index = index

    def getattr(self):
        return self.ref.attr(self.index)

    def iterate(self):
        return self.ref.iterate()


# helper routines for a using attrs

def _getattr(attr):
    """get attr out of a attr/changeattr"""
    if isinstance(attr, _changeattr):
        return attr.getattr()
    return attr


def _getattrs(attrs):
    """get attrs out of a sequence of attr/changeattr"""
    if attrs is not None:
        result = []
        for attr in _ensuresequence(attrs):
            if isinstance(attr, _changeattr):
                result.append(attr.getattr())
            else:
                result.append(attr)
        return result


def _iterateattr(attr):
    """perform next to a attr/changeattr"""
    if isinstance(attr, _changeattr):
        return attr.iterate()
    return attr


def _iterateattrs(attrs):
    """perform next to a sequence of attr/changeattr"""
    if attrs is not None:
        result = []
        for attr in _ensuresequence(attrs):
            if isinstance(attr, _changeattr):
                result.append(attr.iterate())
            else:
                result.append(attr)
        return result


class changecolor(changeattr):

    def __init__(self, gradient):
        changeattr.__init__(self)
        self.gradient = gradient

    def attr(self, index):
        if self.counter != 1:
            return self.gradient.getcolor(index/float(self.counter-1))
        else:
            return self.gradient.getcolor(0)


class _changecolorgray(changecolor):

    def __init__(self, gradient=color.gradient.Gray):
        changecolor.__init__(self, gradient)


class _changecolorreversegray(changecolor):

    def __init__(self, gradient=color.gradient.ReverseGray):
        changecolor.__init__(self, gradient)


class _changecolorredblack(changecolor):

    def __init__(self, gradient=color.gradient.RedBlack):
        changecolor.__init__(self, gradient)


class _changecolorblackred(changecolor):

    def __init__(self, gradient=color.gradient.BlackRed):
        changecolor.__init__(self, gradient)


class _changecolorredwhite(changecolor):

    def __init__(self, gradient=color.gradient.RedWhite):
        changecolor.__init__(self, gradient)


class _changecolorwhitered(changecolor):

    def __init__(self, gradient=color.gradient.WhiteRed):
        changecolor.__init__(self, gradient)


class _changecolorgreenblack(changecolor):

    def __init__(self, gradient=color.gradient.GreenBlack):
        changecolor.__init__(self, gradient)


class _changecolorblackgreen(changecolor):

    def __init__(self, gradient=color.gradient.BlackGreen):
        changecolor.__init__(self, gradient)


class _changecolorgreenwhite(changecolor):

    def __init__(self, gradient=color.gradient.GreenWhite):
        changecolor.__init__(self, gradient)


class _changecolorwhitegreen(changecolor):

    def __init__(self, gradient=color.gradient.WhiteGreen):
        changecolor.__init__(self, gradient)


class _changecolorblueblack(changecolor):

    def __init__(self, gradient=color.gradient.BlueBlack):
        changecolor.__init__(self, gradient)


class _changecolorblackblue(changecolor):

    def __init__(self, gradient=color.gradient.BlackBlue):
        changecolor.__init__(self, gradient)


class _changecolorbluewhite(changecolor):

    def __init__(self, gradient=color.gradient.BlueWhite):
        changecolor.__init__(self, gradient)


class _changecolorwhiteblue(changecolor):

    def __init__(self, gradient=color.gradient.WhiteBlue):
        changecolor.__init__(self, gradient)


class _changecolorredgreen(changecolor):

    def __init__(self, gradient=color.gradient.RedGreen):
        changecolor.__init__(self, gradient)


class _changecolorredblue(changecolor):

    def __init__(self, gradient=color.gradient.RedBlue):
        changecolor.__init__(self, gradient)


class _changecolorgreenred(changecolor):

    def __init__(self, gradient=color.gradient.GreenRed):
        changecolor.__init__(self, gradient)


class _changecolorgreenblue(changecolor):

    def __init__(self, gradient=color.gradient.GreenBlue):
        changecolor.__init__(self, gradient)


class _changecolorbluered(changecolor):

    def __init__(self, gradient=color.gradient.BlueRed):
        changecolor.__init__(self, gradient)


class _changecolorbluegreen(changecolor):

    def __init__(self, gradient=color.gradient.BlueGreen):
        changecolor.__init__(self, gradient)


class _changecolorrainbow(changecolor):

    def __init__(self, gradient=color.gradient.Rainbow):
        changecolor.__init__(self, gradient)


class _changecolorreverserainbow(changecolor):

    def __init__(self, gradient=color.gradient.ReverseRainbow):
        changecolor.__init__(self, gradient)


class _changecolorhue(changecolor):

    def __init__(self, gradient=color.gradient.Hue):
        changecolor.__init__(self, gradient)


class _changecolorreversehue(changecolor):

    def __init__(self, gradient=color.gradient.ReverseHue):
        changecolor.__init__(self, gradient)


changecolor.Gray           = _changecolorgray
changecolor.Reversegray    = _changecolorreversegray
changecolor.Redblack       = _changecolorredblack
changecolor.Blackred       = _changecolorblackred
changecolor.Redwhite       = _changecolorredwhite
changecolor.WhiteRed       = _changecolorwhitered
changecolor.GreenBlack     = _changecolorgreenblack
changecolor.BlackGreen     = _changecolorblackgreen
changecolor.GreenWhite     = _changecolorgreenwhite
changecolor.WhiteGreen     = _changecolorwhitegreen
changecolor.BlueBlack      = _changecolorblueblack
changecolor.BlackBlue      = _changecolorblackblue
changecolor.BlueWhite      = _changecolorbluewhite
changecolor.WhiteBlue      = _changecolorwhiteblue
changecolor.RedGreen       = _changecolorredgreen
changecolor.RedBlue        = _changecolorredblue
changecolor.GreenRed       = _changecolorgreenred
changecolor.GreenBlue      = _changecolorgreenblue
changecolor.BlueRed        = _changecolorbluered
changecolor.BlueGreen      = _changecolorbluegreen
changecolor.Rainbow        = _changecolorrainbow
changecolor.ReverseRainbow = _changecolorreverserainbow
changecolor.Hue            = _changecolorhue
changecolor.ReverseHue     = _changecolorreversehue


class changesequence(changeattr):
    """cycles through a sequence"""

    def __init__(self, *sequence):
        changeattr.__init__(self)
        if not len(sequence):
            sequence = self.defaultsequence
        self.sequence = sequence

    def attr(self, index):
        return self.sequence[index % len(self.sequence)]


class changelinestyle(changesequence):
    defaultsequence = (canvas.linestyle.solid,
                       canvas.linestyle.dashed,
                       canvas.linestyle.dotted,
                       canvas.linestyle.dashdotted)


class changestrokedfilled(changesequence):
    defaultsequence = (canvas.stroked(), canvas.filled())


class changefilledstroked(changesequence):
    defaultsequence = (canvas.filled(), canvas.stroked())



################################################################################
# styles
################################################################################


class mark:

    def cross(self, x, y):
        return (path._moveto(x-0.5*self._size, y-0.5*self._size),
                path._lineto(x+0.5*self._size, y+0.5*self._size),
                path._moveto(x-0.5*self._size, y+0.5*self._size),
                path._lineto(x+0.5*self._size, y-0.5*self._size))

    def plus(self, x, y):
        return (path._moveto(x-0.707106781*self._size, y),
                path._lineto(x+0.707106781*self._size, y),
                path._moveto(x, y-0.707106781*self._size),
                path._lineto(x, y+0.707106781*self._size))

    def square(self, x, y):
        return (path._moveto(x-0.5*self._size, y-0.5 * self._size),
                path._lineto(x+0.5*self._size, y-0.5 * self._size),
                path._lineto(x+0.5*self._size, y+0.5 * self._size),
                path._lineto(x-0.5*self._size, y+0.5 * self._size),
                path.closepath())

    def triangle(self, x, y):
        return (path._moveto(x-0.759835685*self._size, y-0.438691337*self._size),
                path._lineto(x+0.759835685*self._size, y-0.438691337*self._size),
                path._lineto(x, y+0.877382675*self._size),
                path.closepath())

    def circle(self, x, y):
        return (path._arc(x, y, 0.564189583*self._size, 0, 360),
                path.closepath())

    def diamond(self, x, y):
        return (path._moveto(x-0.537284965*self._size, y),
                path._lineto(x, y-0.930604859*self._size),
                path._lineto(x+0.537284965*self._size, y),
                path._lineto(x, y+0.930604859*self._size),
                path.closepath())

    def __init__(self, mark=_nodefault,
                       size="0.2 cm", markattrs=canvas.stroked(),
                       errorscale=0.5, errorbarattrs=(),
                       lineattrs=None):
        self.size_str = size
        if mark is _nodefault:
            self._mark = changemark.cross()
        else:
            self._mark = mark
        self._markattrs = markattrs
        self.errorscale = errorscale
        self._errorbarattrs = errorbarattrs
        self._lineattrs = lineattrs

    def iteratedict(self):
        result = {}
        result["mark"] = _iterateattr(self._mark)
        result["size"] = _iterateattr(self.size_str)
        result["markattrs"] = _iterateattrs(self._markattrs)
        result["errorscale"] = _iterateattr(self.errorscale)
        result["errorbarattrs"] = _iterateattrs(self._errorbarattrs)
        result["lineattrs"] = _iterateattrs(self._lineattrs)
        return result

    def iterate(self):
        return mark(**self.iteratedict())

    def othercolumnkey(self, key, index):
        raise ValueError("unsuitable key '%s'" % key)

    def setcolumns(self, graph, columns):
        def checkpattern(key, index, pattern, iskey, isindex):
             if key is not None:
                 match = pattern.match(key)
                 if match:
                     if isindex is not None: raise ValueError("multiple key specification")
                     if iskey is not None and iskey != match.groups()[0]: raise ValueError("inconsistent key names")
                     key = None
                     iskey = match.groups()[0]
                     isindex = index
             return key, iskey, isindex

        self.xi = self.xmini = self.xmaxi = None
        self.dxi = self.dxmini = self.dxmaxi = None
        self.yi = self.ymini = self.ymaxi = None
        self.dyi = self.dymini = self.dymaxi = None
        self.xkey = self.ykey = None
        if len(graph.Names) != 2: raise TypeError("style not applicable in graph")
        XPattern = re.compile(r"(%s([2-9]|[1-9][0-9]+)?)$" % graph.Names[0])
        YPattern = re.compile(r"(%s([2-9]|[1-9][0-9]+)?)$" % graph.Names[1])
        XMinPattern = re.compile(r"(%s([2-9]|[1-9][0-9]+)?)min$" % graph.Names[0])
        YMinPattern = re.compile(r"(%s([2-9]|[1-9][0-9]+)?)min$" % graph.Names[1])
        XMaxPattern = re.compile(r"(%s([2-9]|[1-9][0-9]+)?)max$" % graph.Names[0])
        YMaxPattern = re.compile(r"(%s([2-9]|[1-9][0-9]+)?)max$" % graph.Names[1])
        DXPattern = re.compile(r"d(%s([2-9]|[1-9][0-9]+)?)$" % graph.Names[0])
        DYPattern = re.compile(r"d(%s([2-9]|[1-9][0-9]+)?)$" % graph.Names[1])
        DXMinPattern = re.compile(r"d(%s([2-9]|[1-9][0-9]+)?)min$" % graph.Names[0])
        DYMinPattern = re.compile(r"d(%s([2-9]|[1-9][0-9]+)?)min$" % graph.Names[1])
        DXMaxPattern = re.compile(r"d(%s([2-9]|[1-9][0-9]+)?)max$" % graph.Names[0])
        DYMaxPattern = re.compile(r"d(%s([2-9]|[1-9][0-9]+)?)max$" % graph.Names[1])
        for key, index in columns.items():
            key, self.xkey, self.xi = checkpattern(key, index, XPattern, self.xkey, self.xi)
            key, self.ykey, self.yi = checkpattern(key, index, YPattern, self.ykey, self.yi)
            key, self.xkey, self.xmini = checkpattern(key, index, XMinPattern, self.xkey, self.xmini)
            key, self.ykey, self.ymini = checkpattern(key, index, YMinPattern, self.ykey, self.ymini)
            key, self.xkey, self.xmaxi = checkpattern(key, index, XMaxPattern, self.xkey, self.xmaxi)
            key, self.ykey, self.ymaxi = checkpattern(key, index, YMaxPattern, self.ykey, self.ymaxi)
            key, self.xkey, self.dxi = checkpattern(key, index, DXPattern, self.xkey, self.dxi)
            key, self.ykey, self.dyi = checkpattern(key, index, DYPattern, self.ykey, self.dyi)
            key, self.xkey, self.dxmini = checkpattern(key, index, DXMinPattern, self.xkey, self.dxmini)
            key, self.ykey, self.dymini = checkpattern(key, index, DYMinPattern, self.ykey, self.dymini)
            key, self.xkey, self.dxmaxi = checkpattern(key, index, DXMaxPattern, self.xkey, self.dxmaxi)
            key, self.ykey, self.dymaxi = checkpattern(key, index, DYMaxPattern, self.ykey, self.dymaxi)
            if key is not None:
                self.othercolumnkey(key, index)
        if None in (self.xkey, self.ykey): raise ValueError("incomplete axis specification")
        if (len(filter(None, (self.xmini, self.dxmini, self.dxi))) > 1 or
            len(filter(None, (self.ymini, self.dymini, self.dyi))) > 1 or
            len(filter(None, (self.xmaxi, self.dxmaxi, self.dxi))) > 1 or
            len(filter(None, (self.ymaxi, self.dymaxi, self.dyi))) > 1):
            raise ValueError("multiple errorbar definition")
        if ((self.xi is None and self.dxi is not None) or
            (self.yi is None and self.dyi is not None) or
            (self.xi is None and self.dxmini is not None) or
            (self.yi is None and self.dymini is not None) or
            (self.xi is None and self.dxmaxi is not None) or
            (self.yi is None and self.dymaxi is not None)):
            raise ValueError("errorbar definition start value missing")

    def minmidmax(self, point, i, mini, maxi, di, dmini, dmaxi):
        min = max = mid = None
        try:
            mid = point[i] + 0.0
        except (TypeError, ValueError):
            pass
        try:
            if di is not None: min = point[i] - point[di]
            elif dmini is not None: min = point[i] - point[dmini]
            elif mini is not None: min = point[mini] + 0.0
        except (TypeError, ValueError):
            pass
        try:
            if di is not None: max = point[i] + point[di]
            elif dmaxi is not None: max = point[i] + point[dmaxi]
            elif maxi is not None: max = point[maxi] + 0.0
        except (TypeError, ValueError):
            pass
        if mid is not None:
            if min is not None and min > mid: raise ValueError("minimum error in errorbar")
            if max is not None and max < mid: raise ValueError("maximum error in errorbar")
        else:
            if min is not None and max is not None and min > max: raise ValueError("minimum/maximum error in errorbar")
        return min, mid, max

    def keyrange(self, points, i, mini, maxi, di, dmini, dmaxi):
        allmin = allmax = None
        if filter(None, (mini, maxi, di, dmini, dmaxi)) is not None:
            for point in points:
                min, mid, max = self.minmidmax(point, i, mini, maxi, di, dmini, dmaxi)
                if min is not None and (allmin is None or min < allmin): allmin = min
                if mid is not None and (allmin is None or mid < allmin): allmin = mid
                if mid is not None and (allmax is None or mid > allmax): allmax = mid
                if max is not None and (allmax is None or max > allmax): allmax = max
        else:
            for point in points:
                try:
                    value = point[i] + 0.0
                    if allmin is None or point[i] < allmin: allmin = point[i]
                    if allmax is None or point[i] > allmax: allmax = point[i]
                except (TypeError, ValueError):
                    pass
        return allmin, allmax

    def getranges(self, points):
        xmin, xmax = self.keyrange(points, self.xi, self.xmini, self.xmaxi, self.dxi, self.dxmini, self.dxmaxi)
        ymin, ymax = self.keyrange(points, self.yi, self.ymini, self.ymaxi, self.dyi, self.dymini, self.dymaxi)
        return {self.xkey: (xmin, xmax), self.ykey: (ymin, ymax)}

    def _drawerrorbar(self, graph, topleft, top, topright,
                                   left, center, right,
                                   bottomleft, bottom, bottomright, point=None):
        if left is not None:
            if right is not None:
                left1 = graph._addpos(*(left+(0, -self._errorsize)))
                left2 = graph._addpos(*(left+(0, self._errorsize)))
                right1 = graph._addpos(*(right+(0, -self._errorsize)))
                right2 = graph._addpos(*(right+(0, self._errorsize)))
                graph.stroke(path.path(path._moveto(*left1),
                                       graph._connect(*(left1+left2)),
                                       path._moveto(*left),
                                       graph._connect(*(left+right)),
                                       path._moveto(*right1),
                                       graph._connect(*(right1+right2))),
                             *self.errorbarattrs)
            elif center is not None:
                left1 = graph._addpos(*(left+(0, -self._errorsize)))
                left2 = graph._addpos(*(left+(0, self._errorsize)))
                graph.stroke(path.path(path._moveto(*left1),
                                       graph._connect(*(left1+left2)),
                                       path._moveto(*left),
                                       graph._connect(*(left+center))),
                             *self.errorbarattrs)
            else:
                left1 = graph._addpos(*(left+(0, -self._errorsize)))
                left2 = graph._addpos(*(left+(0, self._errorsize)))
                left3 = graph._addpos(*(left+(self._errorsize, 0)))
                graph.stroke(path.path(path._moveto(*left1),
                                       graph._connect(*(left1+left2)),
                                       path._moveto(*left),
                                       graph._connect(*(left+left3))),
                             *self.errorbarattrs)
        if right is not None and left is None:
            if center is not None:
                right1 = graph._addpos(*(right+(0, -self._errorsize)))
                right2 = graph._addpos(*(right+(0, self._errorsize)))
                graph.stroke(path.path(path._moveto(*right1),
                                       graph._connect(*(right1+right2)),
                                       path._moveto(*right),
                                       graph._connect(*(right+center))),
                             *self.errorbarattrs)
            else:
                right1 = graph._addpos(*(right+(0, -self._errorsize)))
                right2 = graph._addpos(*(right+(0, self._errorsize)))
                right3 = graph._addpos(*(right+(-self._errorsize, 0)))
                graph.stroke(path.path(path._moveto(*right1),
                                       graph._connect(*(right1+right2)),
                                       path._moveto(*right),
                                       graph._connect(*(right+right3))),
                             *self.errorbarattrs)

        if bottom is not None:
            if top is not None:
                bottom1 = graph._addpos(*(bottom+(-self._errorsize, 0)))
                bottom2 = graph._addpos(*(bottom+(self._errorsize, 0)))
                top1 = graph._addpos(*(top+(-self._errorsize, 0)))
                top2 = graph._addpos(*(top+(self._errorsize, 0)))
                graph.stroke(path.path(path._moveto(*bottom1),
                                       graph._connect(*(bottom1+bottom2)),
                                       path._moveto(*bottom),
                                       graph._connect(*(bottom+top)),
                                       path._moveto(*top1),
                                       graph._connect(*(top1+top2))),
                             *self.errorbarattrs)
            elif center is not None:
                bottom1 = graph._addpos(*(bottom+(-self._errorsize, 0)))
                bottom2 = graph._addpos(*(bottom+(self._errorsize, 0)))
                graph.stroke(path.path(path._moveto(*bottom1),
                                       graph._connect(*(bottom1+bottom2)),
                                       path._moveto(*bottom),
                                       graph._connect(*(bottom+center))),
                             *self.errorbarattrs)
            else:
                bottom1 = graph._addpos(*(bottom+(-self._errorsize, 0)))
                bottom2 = graph._addpos(*(bottom+(self._errorsize, 0)))
                bottom3 = graph._addpos(*(bottom+(0, self._errorsize)))
                graph.stroke(path.path(path._moveto(*bottom1),
                                       graph._connect(*(bottom1+bottom2)),
                                       path._moveto(*bottom),
                                       graph._connect(*(bottom+bottom3))),
                             *self.errorbarattrs)
        if top is not None and bottom is None:
            if center is not None:
                top1 = graph._addpos(*(top+(-self._errorsize, 0)))
                top2 = graph._addpos(*(top+(self._errorsize, 0)))
                graph.stroke(path.path(path._moveto(*top1),
                                       graph._connect(*(top1+top2)),
                                       path._moveto(*top),
                                       graph._connect(*(top+center))),
                             *self.errorbarattrs)
            else:
                top1 = graph._addpos(*(top+(-self._errorsize, 0)))
                top2 = graph._addpos(*(top+(self._errorsize, 0)))
                top3 = graph._addpos(*(top+(0, -self._errorsize)))
                graph.stroke(path.path(path._moveto(*top1),
                                       graph._connect(*(top1+top2)),
                                       path._moveto(*top),
                                       graph._connect(*(top+top3))),
                             *self.errorbarattrs)
        if bottomleft is not None:
            if topleft is not None and bottomright is None:
                bottomleft1 = graph._addpos(*(bottomleft+(self._errorsize, 0)))
                topleft1 = graph._addpos(*(topleft+(self._errorsize, 0)))
                graph.stroke(path.path(path._moveto(*bottomleft1),
                                       graph._connect(*(bottomleft1+bottomleft)),
                                       graph._connect(*(bottomleft+topleft)),
                                       graph._connect(*(topleft+topleft1))),
                             *self.errorbarattrs)
            elif bottomright is not None and topleft is None:
                bottomleft1 = graph._addpos(*(bottomleft+(0, self._errorsize)))
                bottomright1 = graph._addpos(*(bottomright+(0, self._errorsize)))
                graph.stroke(path.path(path._moveto(*bottomleft1),
                                       graph._connect(*(bottomleft1+bottomleft)),
                                       graph._connect(*(bottomleft+bottomright)),
                                       graph._connect(*(bottomright+bottomright1))),
                             *self.errorbarattrs)
            elif bottomright is None and topleft is None:
                bottomleft1 = graph._addpos(*(bottomleft+(self._errorsize, 0)))
                bottomleft2 = graph._addpos(*(bottomleft+(0, self._errorsize)))
                graph.stroke(path.path(path._moveto(*bottomleft1),
                                       graph._connect(*(bottomleft1+bottomleft)),
                                       graph._connect(*(bottomleft+bottomleft2))),
                             *self.errorbarattrs)
        if topright is not None:
            if bottomright is not None and topleft is None:
                topright1 = graph._addpos(*(topright+(-self._errorsize, 0)))
                bottomright1 = graph._addpos(*(bottomright+(-self._errorsize, 0)))
                graph.stroke(path.path(path._moveto(*topright1),
                                       graph._connect(*(topright1+topright)),
                                       graph._connect(*(topright+bottomright)),
                                       graph._connect(*(bottomright+bottomright1))),
                             *self.errorbarattrs)
            elif topleft is not None and bottomright is None:
                topright1 = graph._addpos(*(topright+(0, -self._errorsize)))
                topleft1 = graph._addpos(*(topleft+(0, -self._errorsize)))
                graph.stroke(path.path(path._moveto(*topright1),
                                       graph._connect(*(topright1+topright)),
                                       graph._connect(*(topright+topleft)),
                                       graph._connect(*(topleft+topleft1))),
                             *self.errorbarattrs)
            elif topleft is None and bottomright is None:
                topright1 = graph._addpos(*(topright+(-self._errorsize, 0)))
                topright2 = graph._addpos(*(topright+(0, -self._errorsize)))
                graph.stroke(path.path(path._moveto(*topright1),
                                       graph._connect(*(topright1+topright)),
                                       graph._connect(*(topright+topright2))),
                             *self.errorbarattrs)
        if bottomright is not None and bottomleft is None and topright is None:
            bottomright1 = graph._addpos(*(bottomright+(-self._errorsize, 0)))
            bottomright2 = graph._addpos(*(bottomright+(0, self._errorsize)))
            graph.stroke(path.path(path._moveto(*bottomright1),
                                   graph._connect(*(bottomright1+bottomright)),
                                   graph._connect(*(bottomright+bottomright2))),
                         *self.errorbarattrs)
        if topleft is not None and bottomleft is None and topright is None:
            topleft1 = graph._addpos(*(topleft+(self._errorsize, 0)))
            topleft2 = graph._addpos(*(topleft+(0, -self._errorsize)))
            graph.stroke(path.path(path._moveto(*topleft1),
                                   graph._connect(*(topleft1+topleft)),
                                   graph._connect(*(topleft+topleft2))),
                         *self.errorbarattrs)
        if bottomleft is not None and bottomright is not None and topright is not None and topleft is not None:
            graph.stroke(path.path(path._moveto(*bottomleft),
                                   graph._connect(*(bottomleft+bottomright)),
                                   graph._connect(*(bottomright+topright)),
                                   graph._connect(*(topright+topleft)),
                                   path.closepath()),
                         *self.errorbarattrs)

    def _drawmark(self, graph, x, y, point=None):
        if x is not None and y is not None:
            graph.draw(path.path(*self.mark(self, x, y)), *self.markattrs)

    def drawmark(self, graph, x, y, point=None):
        self._drawmark(graph, unit.topt(x), unit.topt(y), point)

    def drawpoints(self, graph, points):
        xaxis = graph.axes[self.xkey]
        yaxis = graph.axes[self.ykey]
        xaxismin, xaxismax = xaxis.getdatarange()
        yaxismin, yaxismax = yaxis.getdatarange()
        self.size = unit.length(_getattr(self.size_str), default_type="v")
        self._size = unit.topt(self.size)
        self.mark = _getattr(self._mark)
        self.markattrs = _getattrs(_ensuresequence(self._markattrs))
        self.errorbarattrs = _getattrs(_ensuresequence(self._errorbarattrs))
        self._errorsize = self.errorscale * self._size
        self.errorsize = self.errorscale * self.size
        self.lineattrs = _getattrs(_ensuresequence(self._lineattrs))
        if self._lineattrs is not None:
            clipcanvas = graph.clipcanvas()
        lineels = []
        haserror = filter(None, (self.xmini, self.ymini, self.xmaxi, self.ymaxi,
                                 self.dxi, self.dyi, self.dxmini, self.dymini, self.dxmaxi, self.dymaxi)) is not None
        moveto = 1
        for point in points:
            drawmark = 1
            xmin, x, xmax = self.minmidmax(point, self.xi, self.xmini, self.xmaxi, self.dxi, self.dxmini, self.dxmaxi)
            ymin, y, ymax = self.minmidmax(point, self.yi, self.ymini, self.ymaxi, self.dyi, self.dymini, self.dymaxi)
            if x is not None and x < xaxismin: drawmark = 0
            elif x is not None and x > xaxismax: drawmark = 0
            elif y is not None and y < yaxismin: drawmark = 0
            elif y is not None and y > yaxismax: drawmark = 0
            elif haserror:
                if xmin is not None and xmin < xaxismin: drawmark = 0
                elif xmax is not None and xmax < xaxismin: drawmark = 0
                elif xmax is not None and xmax > xaxismax: drawmark = 0
                elif xmin is not None and xmin > xaxismax: drawmark = 0
                elif ymin is not None and ymin < yaxismin: drawmark = 0
                elif ymax is not None and ymax < yaxismin: drawmark = 0
                elif ymax is not None and ymax > yaxismax: drawmark = 0
                elif ymin is not None and ymin > yaxismax: drawmark = 0
            xpos=ypos=topleft=top=topright=left=center=right=bottomleft=bottom=bottomright=None
            if x is not None and y is not None:
                center = xpos, ypos = graph._pos(x, y, xaxis=xaxis, yaxis=yaxis)
            if haserror:
                if y is not None:
                    if xmin is not None: left = graph._pos(xmin, y, xaxis=xaxis, yaxis=yaxis)
                    if xmax is not None: right = graph._pos(xmax, y, xaxis=xaxis, yaxis=yaxis)
                if x is not None:
                    if ymax is not None: top = graph._pos(x, ymax, xaxis=xaxis, yaxis=yaxis)
                    if ymin is not None: bottom = graph._pos(x, ymin, xaxis=xaxis, yaxis=yaxis)
                if x is None or y is None:
                    if ymax is not None:
                        if xmin is not None: topleft = graph._pos(xmin, ymax, xaxis=xaxis, yaxis=yaxis)
                        if xmax is not None: topright = graph._pos(xmax, ymax, xaxis=xaxis, yaxis=yaxis)
                    if ymin is not None:
                        if xmin is not None: bottomleft = graph._pos(xmin, ymin, xaxis=xaxis, yaxis=yaxis)
                        if xmax is not None: bottomright = graph._pos(xmax, ymin, xaxis=xaxis, yaxis=yaxis)
            if drawmark:
                if self._errorbarattrs is not None and haserror:
                    self._drawerrorbar(graph, topleft, top, topright,
                                              left, center, right,
                                              bottomleft, bottom, bottomright, point)
                if self._markattrs is not None:
                    self._drawmark(graph, xpos, ypos, point)
            if xpos is not None and ypos is not None:
                if moveto:
                    lineels.append(path._moveto(xpos, ypos))
                    moveto = 0
                else:
                    lineels.append(path._lineto(xpos, ypos))
            else:
                moveto = 1
        self.path = path.path(*lineels)
        if self._lineattrs is not None:
            clipcanvas.stroke(self.path, *self.lineattrs)


class changemark(changesequence): pass


class _changemarkcross(changemark):
    defaultsequence = (mark.cross, mark.plus, mark.square, mark.triangle, mark.circle, mark.diamond)


class _changemarkplus(changemark):
    defaultsequence = (mark.plus, mark.square, mark.triangle, mark.circle, mark.diamond, mark.cross)


class _changemarksquare(changemark):
    defaultsequence = (mark.square, mark.triangle, mark.circle, mark.diamond, mark.cross, mark.plus)


class _changemarktriangle(changemark):
    defaultsequence = (mark.triangle, mark.circle, mark.diamond, mark.cross, mark.plus, mark.square)


class _changemarkcircle(changemark):
    defaultsequence = (mark.circle, mark.diamond, mark.cross, mark.plus, mark.square, mark.triangle)


class _changemarkdiamond(changemark):
    defaultsequence = (mark.diamond, mark.cross, mark.plus, mark.square, mark.triangle, mark.circle)


class _changemarksquaretwice(changemark):
    defaultsequence = (mark.square, mark.square, mark.triangle, mark.triangle,
                       mark.circle, mark.circle, mark.diamond, mark.diamond)


class _changemarktriangletwice(changemark):
    defaultsequence = (mark.triangle, mark.triangle, mark.circle, mark.circle,
                       mark.diamond, mark.diamond, mark.square, mark.square)


class _changemarkcircletwice(changemark):
    defaultsequence = (mark.circle, mark.circle, mark.diamond, mark.diamond,
                       mark.square, mark.square, mark.triangle, mark.triangle)


class _changemarkdiamondtwice(changemark):
    defaultsequence = (mark.diamond, mark.diamond, mark.square, mark.square,
                       mark.triangle, mark.triangle, mark.circle, mark.circle)


changemark.cross         = _changemarkcross
changemark.plus          = _changemarkplus
changemark.square        = _changemarksquare
changemark.triangle      = _changemarktriangle
changemark.circle        = _changemarkcircle
changemark.diamond       = _changemarkdiamond
changemark.squaretwice   = _changemarksquaretwice
changemark.triangletwice = _changemarktriangletwice
changemark.circletwice   = _changemarkcircletwice
changemark.diamondtwice  = _changemarkdiamondtwice


class line(mark):

    def __init__(self, lineattrs=_nodefault):
        if lineattrs is _nodefault:
            lineattrs = changelinestyle()
        mark.__init__(self, markattrs=None, errorbarattrs=None, lineattrs=lineattrs)


class rect(mark):

    def __init__(self, gradient=color.gradient.Gray):
        self.gradient = gradient
        self.colorindex = None
        mark.__init__(self, markattrs=None, errorbarattrs=(), lineattrs=None)

    def iterate(self):
        raise RuntimeError("style is not iterateable")

    def othercolumnkey(self, key, index):
        if key == "color":
            self.colorindex = index
        else:
            mark.othercolumnkey(self, key, index)

    def _drawerrorbar(self, graph, topleft, top, topright,
                                   left, center, right,
                                   bottomleft, bottom, bottomright, point=None):
        color = point[self.colorindex]
        if color is not None:
            if color != self.lastcolor:
                self.rectclipcanvas.set(self.gradient.getcolor(color))
            if bottom is not None and left is not None:
                bottomleft = left[0], bottom[1]
            if bottom is not None and right is not None:
                bottomright = right[0], bottom[1]
            if top is not None and right is not None:
                topright = right[0], top[1]
            if top is not None and left is not None:
                topleft = left[0], top[1]
            if bottomleft is not None and bottomright is not None and topright is not None and topleft is not None:
                self.rectclipcanvas.fill(path.path(path._moveto(*bottomleft),
                                         graph._connect(*(bottomleft+bottomright)),
                                         graph._connect(*(bottomright+topright)),
                                         graph._connect(*(topright+topleft)),
                                         path.closepath()))

    def drawpoints(self, graph, points):
        if self.colorindex is None:
            raise RuntimeError("column 'color' not set")
        self.lastcolor = None
        self.rectclipcanvas = graph.clipcanvas()
        mark.drawpoints(self, graph, points)



class text(mark):

    def __init__(self, textdx="0", textdy="0.3 cm", textattrs=tex.halign.center, **args):
        self.textindex = None
        self.textdx_str = textdx
        self.textdy_str = textdy
        self._textattrs = textattrs
        mark.__init__(self, **args)

    def iteratedict(self):
        result = mark.iteratedict()
        result["textattrs"] = _iterateattr(self._textattrs)
        return result

    def iterate(self):
        return textmark(**self.iteratedict())

    def othercolumnkey(self, key, index):
        if key == "text":
            self.textindex = index
        else:
            mark.othercolumnkey(self, key, index)

    def _drawmark(self, graph, x, y, point=None):
        mark._drawmark(self, graph, x, y, point)
        if None not in (x, y, point[self.textindex], self._textattrs):
            graph.tex._text(x + self._textdx, y + self._textdy, str(point[self.textindex]), *_ensuresequence(self.textattrs))

    def drawpoints(self, graph, points):
        self.textdx = unit.length(_getattr(self.textdx_str), default_type="v")
        self.textdy = unit.length(_getattr(self.textdy_str), default_type="v")
        self._textdx = unit.topt(self.textdx)
        self._textdy = unit.topt(self.textdy)
        if self._textattrs is not None:
            self.textattrs = _getattr(self._textattrs)
        if self.textindex is None:
            raise RuntimeError("column 'text' not set")
        mark.drawpoints(self, graph, points)


class arrow(mark):

    def __init__(self, linelength="0.2 cm", arrowattrs=(), arrowsize="0.1 cm", arrowdict={}, epsilon=1e-10):
        self.linelength_str = linelength
        self.arrowsize_str = arrowsize
        self.arrowattrs = arrowattrs
        self.arrowdict = arrowdict
        self.epsilon = epsilon
        self.sizeindex = self.angleindex = None
        mark.__init__(self, markattrs=(), errorbarattrs=None, lineattrs=None)

    def iterate(self):
        raise RuntimeError("style is not iterateable")

    def othercolumnkey(self, key, index):
        if key == "size":
            self.sizeindex = index
        elif key == "angle":
            self.angleindex = index
        else:
            mark.othercolumnkey(self, key, index)

    def _drawmark(self, graph, x, y, point=None):
        if None not in (x, y, point[self.angleindex], point[self.sizeindex], self.arrowattrs, self.arrowdict):
            if point[self.sizeindex] > self.epsilon:
                dx, dy = math.cos(point[self.angleindex]*math.pi/180.0), math.sin(point[self.angleindex]*math.pi/180)
                x1 = unit.t_pt(x)-0.5*dx*self.linelength*point[self.sizeindex]
                y1 = unit.t_pt(y)-0.5*dy*self.linelength*point[self.sizeindex]
                x2 = unit.t_pt(x)+0.5*dx*self.linelength*point[self.sizeindex]
                y2 = unit.t_pt(y)+0.5*dy*self.linelength*point[self.sizeindex]
                graph.stroke(path.line(x1, y1, x2, y2),
                             canvas.earrow(self.arrowsize*point[self.sizeindex],
                                           **self.arrowdict),
                             *_ensuresequence(self.arrowattrs))

    def drawpoints(self, graph, points):
        self.arrowsize = unit.length(_getattr(self.arrowsize_str), default_type="v")
        self.linelength = unit.length(_getattr(self.linelength_str), default_type="v")
        self._arrowsize = unit.topt(self.arrowsize)
        self._linelength = unit.topt(self.linelength)
        if self.sizeindex is None:
            raise RuntimeError("column 'size' not set")
        if self.angleindex is None:
            raise RuntimeError("column 'angle' not set")
        mark.drawpoints(self, graph, points)



################################################################################
# data
################################################################################


class data:

    defaultstyle = mark

    def __init__(self, file, **columns):
        if not isinstance(file, datafile._datafile):
            self.datafile = datafile.datafile(file)
        else:
            self.datafile = file
        self.columns = {}
        usedkeys = []
        for key, column in columns.items():
            try:
                self.columns[key] = self.datafile.getcolumnno(column)
            except datafile.ColumnError:
                self.columns[key] = len(self.datafile.titles)
                usedkeys.extend(self.datafile._addcolumn(column, **columns))
        for usedkey in usedkeys:
            if usedkey in self.columns.keys():
                del self.columns[usedkey]

    def setstyle(self, graph, style):
        self.style = style
        self.style.setcolumns(graph, self.columns)

    def getranges(self):
        return self.style.getranges(self.datafile.data)

    def setranges(self, ranges):
        pass

    def draw(self, graph):
        self.style.drawpoints(graph, self.datafile.data)


class function:

    defaultstyle = line

    def __init__(self, expression, min=None, max=None, points=100, parser=mathtree.parser()):
        self.min = min
        self.max = max
        self.points = points
        self.result, expression = expression.split("=")
        self.mathtree = parser.parse(expression)
        self.variable, = self.mathtree.VarList()
        self.evalranges = 0

    def setstyle(self, graph, style):
        self.xaxis = graph.axes[self.variable]
        self.style = style
        self.style.setcolumns(graph, {self.variable: 0, self.result: 1})

    def getranges(self):
        if self.evalranges:
            return self.style.getranges(self.data)

    def setranges(self, ranges):
        if ranges.has_key(self.variable):
            min, max = ranges[self.variable]
        if self.min is not None: min = self.min
        if self.max is not None: max = self.max
        vmin = self.xaxis.convert(min)
        vmax = self.xaxis.convert(max)
        self.data = []
        for i in range(self.points):
            x = self.xaxis.invert(vmin + (vmax-vmin)*i / (self.points-1.0))
            try:
                y = self.mathtree.Calc({self.variable: x})
            except (ArithmeticError, ValueError):
                y = None
            self.data.append((x, y))
        self.evalranges = 1

    def draw(self, graph):
        self.style.drawpoints(graph, self.data)


class paramfunction:

    defaultstyle = line

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
        self.style.drawpoints(graph, self.data)

