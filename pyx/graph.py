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


import types, re, math, string, sys
import bbox, box, canvas, path, unit, mathtree, trafo, color, helper
import text as textmodule
import data as datamodule


goldenrule = 0.5 * (math.sqrt(5) + 1)


################################################################################
# maps
################################################################################

class _Imap:
    """interface definition of a map
    maps convert a value into another value by bijective transformation f"""

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
        "method is part of the implementation of _Imap"
        self.dydx = (basepoints[1][1] - basepoints[0][1]) / float(basepoints[1][0] - basepoints[0][0])
        self.dxdy = (basepoints[1][0] - basepoints[0][0]) / float(basepoints[1][1] - basepoints[0][1])
        self.x1 = basepoints[0][0]
        self.y1 = basepoints[0][1]
        return self

    def convert(self, value):
        "method is part of the implementation of _Imap"
        return self.y1 + self.dydx * (value - self.x1)

    def invert(self, value):
        "method is part of the implementation of _Imap"
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
# partition schemes
# please note the nomenclature:
# - a partition is a ordered sequence of tick instances
# - a partition scheme is a class creating a single or several partitions
################################################################################


class frac:
    """fraction class for rational arithmetics
    the axis partitioning uses rational arithmetics (with infinite accuracy)
    basically it contains self.enum and self.denom"""

    def __init__(self, enum, denom, power=None):
        "for power!=None: frac=(enum/denom)**power"
        if not helper.isinteger(enum) or not helper.isinteger(denom): raise TypeError("integer type expected")
        if not denom: raise ZeroDivisionError("zero denominator")
        if power != None:
            if not helper.isinteger(power): raise TypeError("integer type expected")
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
        "caution: avoid final precision of floats"
        return float(self.enum) / self.denom

    def __str__(self):
        return "%i/%i" % (self.enum, self.denom)


def _ensurefrac(arg):
    """helper function to convert arg into a frac
    strings like 0.123, 1/-2, 1.23/34.21 are converted to a frac"""
    # TODO: exponentials are not yet supported, e.g. 1e-10, etc.
    # XXX: we don't need to force long on newer python versions

    def createfrac(str):
        "converts a string 0.123 into a frac"
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

    if helper.isstring(arg):
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
    """tick class
    a tick is a frac enhanced by
    - self.ticklevel (0 = tick, 1 = subtick, etc.)
    - self.labellevel (0 = label, 1 = sublabel, etc.)
    - self.text
    When ticklevel or labellevel is None, no tick or label is present at that value.
    When text is None, it should be automatically created (and stored), once the
    an axis painter needs it."""

    def __init__(self, enum, denom, ticklevel=None, labellevel=None, text=None):
        frac.__init__(self, enum, denom)
        self.ticklevel = ticklevel
        self.labellevel = labellevel
        self.text = text

    def merge(self, other):
        """merges two ticks together:
          - the lower ticklevel/labellevel wins
          - when present, self.text is taken over; otherwise the others text is taken
          - the ticks should be at the same position (otherwise it doesn't make sense)
            -> this is NOT checked
        """
        if self.ticklevel is None or (other.ticklevel is not None and other.ticklevel < self.ticklevel):
            self.ticklevel = other.ticklevel
        if self.labellevel is None or (other.labellevel is not None and other.labellevel < self.labellevel):
            self.labellevel = other.labellevel
        if self.text is None:
            self.text = other.text

    def __repr__(self):
        return "tick(%r, %r, %s, %s, %s)" % (self.enum, self.denom, self.ticklevel, self.labellevel, self.text)


def _mergeticklists(list1, list2):
    """helper function to merge tick lists
    return a merged list of ticks out of list1 and list2
    caution: original lists have to be ordered
             (the returned list is also ordered)
    caution: original lists are modified and they share references to
             the result list!"""
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
    """helper function to merge texts into ticks
    - when texts is not None, the text of all ticks with
      labellevel
      different from None are set
    - texts need to be a sequence of sequences of strings,
      where the first sequence contain the strings to be
      used as texts for the ticks with labellevel 0,
      the second sequence for labellevel 1, etc.
    - when the maximum labellevel is 0, just a sequence of
      strings might be provided as the texts argument
    - IndexError is raised, when a sequence length doesn't match"""
    if helper.issequenceofsequences(texts):
        for text, level in zip(texts, xrange(sys.maxint)):
            usetext = helper.ensuresequence(text)
            i = 0
            for tick in ticks:
                if tick.labellevel == level:
                    tick.text = usetext[i]
                    i += 1
            if i != len(usetext):
                raise IndexError("wrong sequence length of texts at level %i" % level)
    elif texts is not None:
        usetext = helper.ensuresequence(texts)
        i = 0
        for tick in ticks:
            if tick.labellevel == 0:
                tick.text = usetext[i]
                i += 1
        if i != len(usetext):
            raise IndexError("wrong sequence length of texts")


class _Ipart:
    """interface definition of a partition scheme
    partition schemes are used to create a list of ticks"""

    def defaultpart(self, min, max, extendmin, extendmax):
        """create a partition
        - returns an ordered list of ticks for the interval min to max
        - the interval is given in float numbers, thus an appropriate
          conversion to rational numbers has to be performed
        - extendmin and extendmax are booleans (integers)
        - when extendmin or extendmax is set, the ticks might
          extend the min-max range towards lower and higher
          ranges, respectively"""

    def lesspart(self):
        """create another partition which contains less ticks
        - this method is called several times after a call of defaultpart
        - returns an ordered list of ticks with less ticks compared to
          the partition returned by defaultpart and by previous calls
          of lesspart
        - the creation of a partition with strictly *less* ticks
          is not to be taken serious
        - the method might return None, when no other appropriate
          partition can be created"""


    def morepart(self):
        """create another partition which contains more ticks
        see lesspart, but increase the number of ticks"""


class manualpart:
    """manual partition scheme
    ticks and labels at positions explicitly provided to the constructor"""

    __implements__ = _Ipart

    def __init__(self, ticks=None, labels=None, texts=None, mix=()):
        """configuration of the partition scheme
        - ticks and labels should be a sequence of sequences, where
          the first sequence contains the values to be used for
          ticks with ticklevel/labellevel 0, the second sequence for
          ticklevel/labellevel 1, etc.
        - tick and label values must be frac instances or
          strings convertable to fracs by the _ensurefrac function
        - when the maximum ticklevel/labellevel is 0, just a sequence
          might be provided in ticks and labels
        - when labels is None and ticks is not None, the tick entries
          for ticklevel 0 are used for labels and vice versa (ticks<->labels)
        - texts are applied to the resulting partition via the
          mergetexts function (additional information available there)
        - mix specifies another partition to be merged into the
          created partition"""
        if ticks is None and labels is not None:
            self.ticks = helper.ensuresequence(helper.getsequenceno(labels, 0))
        else:
            self.ticks = ticks
        if labels is None and ticks is not None:
            self.labels = helper.ensuresequence(helper.getsequenceno(ticks, 0))
        else:
            self.labels = labels
        self.texts = texts
        self.mix = mix

    def checkfraclist(self, *fracs):
        """orders a list of fracs, equal entries are not allowed"""
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
        "create the partition as described in the constructor"
        ticks = list(self.mix)
        if helper.issequenceofsequences(self.ticks):
            for fracs, level in zip(self.ticks, xrange(sys.maxint)):
                ticks = _mergeticklists(ticks, [tick(frac.enum, frac.denom, ticklevel = level)
                                                for frac in self.checkfraclist(*map(_ensurefrac, helper.ensuresequence(fracs)))])
        else:
            ticks = _mergeticklists(ticks, [tick(frac.enum, frac.denom, ticklevel = 0)
                                            for frac in self.checkfraclist(*map(_ensurefrac, helper.ensuresequence(self.ticks)))])

        if helper.issequenceofsequences(self.labels):
            for fracs, level in zip(self.labels, xrange(sys.maxint)):
                ticks = _mergeticklists(ticks, [tick(frac.enum, frac.denom, labellevel = level)
                                                for frac in self.checkfraclist(*map(_ensurefrac, helper.ensuresequence(fracs)))])
        else:
            ticks = _mergeticklists(ticks, [tick(frac.enum, frac.denom, labellevel = 0)
                                            for frac in self.checkfraclist(*map(_ensurefrac, helper.ensuresequence(self.labels)))])

        _mergetexts(ticks, self.texts)

        return ticks

    def defaultpart(self, min, max, extendmin, extendmax):
        """method is part of the implementation of _Ipart
        XXX: we do not take care of the parameters -> correct?"""
        return self.part()

    def lesspart(self):
        "method is part of the implementation of _Ipart"
        return None

    def morepart(self):
        "method is part of the implementation of _Ipart"
        return None


class linpart:
    """linear partition scheme
    ticks and label distances are explicitly provided to the constructor"""

    __implements__ = _Ipart

    def __init__(self, ticks=None, labels=None, texts=None, extendtick=0, extendlabel=None, epsilon=1e-10, mix=()):
        """configuration of the partition scheme
        - ticks and labels should be a sequence, where the first value
          is the distance between ticks with ticklevel/labellevel 0,
          the second sequence for ticklevel/labellevel 1, etc.
        - tick and label values must be frac instances or
          strings convertable to fracs by the _ensurefrac function
        - when the maximum ticklevel/labellevel is 0, just a single value
          might be provided in ticks and labels
        - when labels is None and ticks is not None, the tick entries
          for ticklevel 0 are used for labels and vice versa (ticks<->labels)
        - texts are applied to the resulting partition via the
          mergetexts function (additional information available there)
        - extendtick allows for the extension of the range given to the
          defaultpart method to include the next tick with the specified
          level (None turns off this feature); note, that this feature is
          also disabled, when an axis prohibits its range extension by
          the extendmin/extendmax variables given to the defaultpart method
        - extendlabel is analogous to extendtick, but for labels
        - epsilon allows for exceeding the axis range by this relative
          value (relative to the axis range given to the defaultpart method)
          without creating another tick specified by extendtick/extendlabel
        - mix specifies another partition to be merged into the
          created partition"""
        if ticks is None and labels is not None:
            self.ticks = (_ensurefrac(helper.ensuresequence(labels)[0]),)
        else:
            self.ticks = map(_ensurefrac, helper.ensuresequence(ticks))
        if labels is None and ticks is not None:
            self.labels = (_ensurefrac(helper.ensuresequence(ticks)[0]),)
        else:
            self.labels = map(_ensurefrac, helper.ensuresequence(labels))
        self.texts = texts
        self.extendtick = extendtick
        self.extendlabel = extendlabel
        self.epsilon = epsilon
        self.mix = mix

    def extendminmax(self, min, max, frac, extendmin, extendmax):
        """return new min, max tuple extending the range min, max
        frac is the tick distance to be used
        extendmin and extendmax are booleans to allow for the extension"""
        if extendmin:
            min = float(frac) * math.floor(min / float(frac) + self.epsilon)
        if extendmax:
            max = float(frac) * math.ceil(max / float(frac) - self.epsilon)
        return min, max

    def getticks(self, min, max, frac, ticklevel=None, labellevel=None):
        """return a list of equal spaced ticks
        - the tick distance is frac, the ticklevel is set to ticklevel and
          the labellevel is set to labellevel
        - min, max is the range where ticks should be placed"""
        imin = int(math.ceil(min / float(frac) - 0.5 * self.epsilon))
        imax = int(math.floor(max / float(frac) + 0.5 * self.epsilon))
        ticks = []
        for i in range(imin, imax + 1):
            ticks.append(tick(long(i) * frac.enum, frac.denom, ticklevel=ticklevel, labellevel=labellevel))
        return ticks

    def defaultpart(self, min, max, extendmin, extendmax):
        "method is part of the implementation of _Ipart"
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

    def lesspart(self):
        "method is part of the implementation of _Ipart"
        return None

    def morepart(self):
        "method is part of the implementation of _Ipart"
        return None


class autolinpart:
    """automatic linear partition scheme
    - possible tick distances are explicitly provided to the constructor
    - tick distances are adjusted to the axis range by multiplication or division by 10"""

    __implements__ = _Ipart

    defaultlist = ((frac(1, 1), frac(1, 2)),
                   (frac(2, 1), frac(1, 1)),
                   (frac(5, 2), frac(5, 4)),
                   (frac(5, 1), frac(5, 2)))

    def __init__(self, list=defaultlist, extendtick=0, epsilon=1e-10, mix=()):
        """configuration of the partition scheme
        - list should be a sequence of fracs
        - ticks should be a sequence, where the first value
          is the distance between ticks with ticklevel 0,
          the second for ticklevel 1, etc.
        - tick values must be frac instances or
          strings convertable to fracs by the _ensurefrac function
        - labellevel is set to None except for those ticks in the partitions,
          where ticklevel is zero. There labellevel is also set to zero.
        - extendtick allows for the extension of the range given to the
          defaultpart method to include the next tick with the specified
          level (None turns off this feature); note, that this feature is
          also disabled, when an axis prohibits its range extension by
          the extendmin/extendmax variables given to the defaultpart method
        - epsilon allows for exceeding the axis range by this relative
          value (relative to the axis range given to the defaultpart method)
          without creating another tick specified by extendtick
        - mix specifies another partition to be merged into the
          created partition"""
        self.list = list
        self.extendtick = extendtick
        self.epsilon = epsilon
        self.mix = mix

    def defaultpart(self, min, max, extendmin, extendmax):
        "method is part of the implementation of _Ipart"
        base = frac(10L, 1, int(math.log(max - min) / math.log(10)))
        ticks = self.list[0]
        useticks = [tick * base for tick in ticks]
        self.lesstickindex = self.moretickindex = 0
        self.lessbase = frac(base.enum, base.denom)
        self.morebase = frac(base.enum, base.denom)
        self.min, self.max, self.extendmin, self.extendmax = min, max, extendmin, extendmax
        part = linpart(ticks=useticks, extendtick=self.extendtick, epsilon=self.epsilon, mix=self.mix)
        return part.defaultpart(self.min, self.max, self.extendmin, self.extendmax)

    def lesspart(self):
        "method is part of the implementation of _Ipart"
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
        "method is part of the implementation of _Ipart"
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
    """storage class for the definition of logarithmic axes partitions
    instances of this class define tick positions suitable for
    logarithmic axes by the following instance variables:
    - shift: integer, which defines multiplicator
    - fracs: list of tick positions (rational numbers, e.g. instances of frac)
    possible positions are these tick positions and arbitrary divisions
    and multiplications by the shift value"""

    def __init__(self, shift, *fracs):
         "create a shiftfracs instance and store its shift and fracs information"
         self.shift = shift
         self.fracs = fracs


class logpart(linpart):
    """logarithmic partition scheme
    ticks and label positions are explicitly provided to the constructor"""

    __implements__ = _Ipart

    shift5fracs1   = shiftfracs(100000, frac(1, 1))
    shift4fracs1   = shiftfracs(10000, frac(1, 1))
    shift3fracs1   = shiftfracs(1000, frac(1, 1))
    shift2fracs1   = shiftfracs(100, frac(1, 1))
    shiftfracs1    = shiftfracs(10, frac(1, 1))
    shiftfracs125  = shiftfracs(10, frac(1, 1), frac(2, 1), frac(5, 1))
    shiftfracs1to9 = shiftfracs(10, *map(lambda x: frac(x, 1), range(1, 10)))
    #         ^- we always include 1 in order to get extendto(tick|label)level to work as expected

    def __init__(self, ticks=None, labels=None, texts=None, extendtick=0, extendlabel=None, epsilon=1e-10, mix=()):
        """configuration of the partition scheme
        - ticks and labels should be a sequence, where the first value
          is a shiftfracs instance describing ticks with ticklevel/labellevel 0,
          the second sequence for ticklevel/labellevel 1, etc.
        - when the maximum ticklevel/labellevel is 0, just a single
          shiftfracs instance might be provided in ticks and labels
        - when labels is None and ticks is not None, the tick entries
          for ticklevel 0 are used for labels and vice versa (ticks<->labels)
        - texts are applied to the resulting partition via the
          mergetexts function (additional information available there)
        - extendtick allows for the extension of the range given to the
          defaultpart method to include the next tick with the specified
          level (None turns off this feature); note, that this feature is
          also disabled, when an axis prohibits its range extension by
          the extendmin/extendmax variables given to the defaultpart method
        - extendlabel is analogous to extendtick, but for labels
        - epsilon allows for exceeding the axis range by this relative
          logarithm value (relative to the logarithm axis range given
          to the defaultpart method) without creating another tick
          specified by extendtick/extendlabel
        - mix specifies another partition to be merged into the
          created partition"""
        if ticks is None and labels is not None:
            self.ticks = (helper.ensuresequence(labels)[0],)
        else:
            self.ticks = helper.ensuresequence(ticks)

        if labels is None and ticks is not None:
            self.labels = (helper.ensuresequence(ticks)[0],)
        else:
            self.labels = helper.ensuresequence(labels)
        self.texts = texts
        self.extendtick = extendtick
        self.extendlabel = extendlabel
        self.epsilon = epsilon
        self.mix = mix

    def extendminmax(self, min, max, shiftfracs, extendmin, extendmax):
        """return new min, max tuple extending the range min, max
        shiftfracs describes the allowed tick positions
        extendmin and extendmax are booleans to allow for the extension"""
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
        """return a list of ticks
        - shiftfracs describes the allowed tick positions
        - the ticklevel of the ticks is set to ticklevel and
          the labellevel is set to labellevel
        -  min, max is the range where ticks should be placed"""
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
    """automatic logarithmic partition scheme
    possible tick positions are explicitly provided to the constructor"""

    __implements__ = _Ipart

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

    def __init__(self, list=defaultlist, extendtick=0, extendlabel=None, epsilon=1e-10, mix=()):
        """configuration of the partition scheme
        - list should be a sequence of pairs of sequences of shiftfracs
          instances
        - within each pair the first sequence contains shiftfracs, where
          the first shiftfracs instance describes ticks positions with
          ticklevel 0, the second shiftfracs for ticklevel 1, etc.
        - the second sequence within each pair describes the same as
          before, but for labels
        - within each pair: when the second entry (for the labels) is None
          and the first entry (for the ticks) ticks is not None, the tick
          entries for ticklevel 0 are used for labels and vice versa
          (ticks<->labels)
        - extendtick allows for the extension of the range given to the
          defaultpart method to include the next tick with the specified
          level (None turns off this feature); note, that this feature is
          also disabled, when an axis prohibits its range extension by
          the extendmin/extendmax variables given to the defaultpart method
        - extendlabel is analogous to extendtick, but for labels
        - epsilon allows for exceeding the axis range by this relative
          logarithm value (relative to the logarithm axis range given
          to the defaultpart method) without creating another tick
          specified by extendtick/extendlabel
        - mix specifies another partition to be merged into the
          created partition"""
        self.list = list
        if len(list) > 2:
            self.listindex = divmod(len(list), 2)[0]
        else:
            self.listindex = 0
        self.extendtick = extendtick
        self.extendlabel = extendlabel
        self.epsilon = epsilon
        self.mix = mix

    def defaultpart(self, min, max, extendmin, extendmax):
        "method is part of the implementation of _Ipart"
        self.min, self.max, self.extendmin, self.extendmax = min, max, extendmin, extendmax
        self.morelistindex = self.listindex
        self.lesslistindex = self.listindex
        part = logpart(ticks=self.list[self.listindex][0], labels=self.list[self.listindex][1],
                       extendtick=self.extendtick, extendlabel=self.extendlabel, epsilon=self.epsilon, mix=self.mix)
        return part.defaultpart(self.min, self.max, self.extendmin, self.extendmax)

    def lesspart(self):
        "method is part of the implementation of _Ipart"
        self.lesslistindex += 1
        if self.lesslistindex < len(self.list):
            part = logpart(ticks=self.list[self.lesslistindex][0], labels=self.list[self.lesslistindex][1],
                           extendtick=self.extendtick, extendlabel=self.extendlabel, epsilon=self.epsilon, mix=self.mix)
            return part.defaultpart(self.min, self.max, self.extendmin, self.extendmax)

    def morepart(self):
        "method is part of the implementation of _Ipart"
        self.morelistindex -= 1
        if self.morelistindex >= 0:
            part = logpart(ticks=self.list[self.morelistindex][0], labels=self.list[self.morelistindex][1],
                           extendtick=self.extendtick, extendlabel=self.extendlabel, epsilon=self.epsilon, mix=self.mix)
            return part.defaultpart(self.min, self.max, self.extendmin, self.extendmax)



################################################################################
# rater
# conseptional remarks:
# - raters are used to calculate a rating for a realization of something
# - here, a rating means a positive floating point value
# - ratings are used to order those realizations by their suitability (lower
#   ratings are better)
# - a rating of None means not suitable at all (those realizations should be
#   thrown out)
################################################################################


class cuberate:
    """a cube rater
    - a cube rater has an optimal value, where the rate becomes zero
    - for a left (below the optimum) and a right value (above the optimum),
      the rating is value is set to 1 (modified by an overall weight factor
      for the rating)
    - the analytic form of the rating is cubic for both, the left and
      the right side of the rater, independently"""

    def __init__(self, opt, left=None, right=None, weight=1):
        """initializes the rater
        - by default, left is set to zero, right is set to 3*opt
        - left should be smaller than opt, right should be bigger than opt
        - weight should be positive and is a factor multiplicated to the rates"""
        if left is None:
            left = 0
        if right is None:
            right = 3*opt
        self.opt = opt
        self.left = left
        self.right = right
        self.weight = weight

    def rate(self, value, dense=1):
        """returns a rating for a value
        - the dense factor lineary rescales the rater (the optimum etc.),
          e.g. a value bigger than one increases the optimum (when it is
          positive) and a value lower than one decreases the optimum (when
          it is positive); the dense factor itself should be positive"""
        opt = self.opt * dense
        if value < opt:
            other = self.left * dense
        elif value > opt:
            other = self.right * dense
        else:
            return 0
        factor = (value - opt) / float(other - opt)
        return self.weight * (factor ** 3)


class distancerate:
    """a distance rater (rates a list of distances)
    - the distance rater rates a list of distances by rating each independently
      and returning the average rate
    - there is an optimal value, where the rate becomes zero
    - the analytic form is linary for values above the optimal value
      (twice the optimal value has the rating one, three times the optimal
      value has the rating two, etc.)
    - the analytic form is reciprocal subtracting one for values below the
      optimal value (halve the optimal value has the rating one, one third of
      the optimal value has the rating two, etc.)"""

    def __init__(self, opt, weight=0.1):
        """inititializes the rater
        - opt is the optimal length (a PyX length, by default a visual length)
        - weight should be positive and is a factor multiplicated to the rates"""
        self.opt_str = opt
        self.weight = weight

    def _rate(self, distances, dense=1):
        """rate distances
        - the distances are a sequence of positive floats in PostScript points
        - the dense factor lineary rescales the rater (the optimum etc.),
          e.g. a value bigger than one increases the optimum (when it is
          positive) and a value lower than one decreases the optimum (when
          it is positive); the dense factor itself should be positive"""
        if len(distances):
            opt = unit.topt(unit.length(self.opt_str, default_type="v")) / dense
            rate = 0
            for distance in distances:
                if distance < opt:
                    rate += self.weight * (opt / distance - 1)
                else:
                    rate += self.weight * (distance / opt - 1)
            return rate / float(len(distances))


class axisrater:
    """a rater for axis partitions
    - the rating of axes is splited into two separate parts:
      - rating of the partitions in terms of the number of ticks,
        subticks, labels, etc.
      - rating of the label distances
    - in the end, a rate for an axis partition is the sum of these rates
    - it is useful to first just rate the number of ticks etc.
      and selecting those partitions, where this fits well -> as soon
      as an complete rate (the sum of both parts from the list above)
      of a first partition is below a rate of just the ticks of another
      partition, this second partition will never be better than the
      first one -> we gain speed by minimizing the number of partitions,
      where label distances have to be taken into account)
    - both parts of the rating are shifted into instances of raters
      defined above --- right now, there is not yet a strict interface
      for this delegation (should be done as soon as it is needed)"""

    linticks = (cuberate(4), cuberate(10, weight=0.5), )
    linlabels = (cuberate(4), )
    logticks = (cuberate(5, right=20), cuberate(20, right=100, weight=0.5), )
    loglabels = (cuberate(5, right=20), cuberate(5, left=-20, right=20, weight=0.5), )
    stdtickrange = cuberate(1, weight=2)
    stddistance = distancerate("1 cm")

    def __init__(self, ticks=linticks, labels=linlabels, tickrange=stdtickrange, distance=stddistance):
        """initializes the axis rater
        - ticks and labels are lists of instances of cuberate
        - the first entry in ticks rate the number of ticks, the
          second the number of subticks, etc.; when there are no
          ticks of a level or there is not rater for a level, the
          level is just ignored
        - labels is analogous, but for labels
        - within the rating, all ticks with a higher level are
          considered as ticks for a given level
        - tickrange is a cuberate instance, which rates the covering
          of an axis range by the ticks (as a relative value of the
          tick range vs. the axis range), ticks might cover less or
          more than the axis range (for the standard automatic axis
          partition schemes an extention of the axis range is normal
          and should get some penalty)
        - distance is an distancerate instance"""
        self.ticks = ticks
        self.labels = labels
        self.tickrange = tickrange
        self.distance = distance

    def ratepart(self, axis, part, dense=1):
        """rates a partition by some global parameters
        - takes into account the number of ticks, subticks, etc.,
          number of labels, etc., and the coverage of the axis
          range by the ticks
        - when there are no ticks of a level or there was not rater
          given in the constructor for a level, the level is just
          ignored
        - the method returns the sum of the rating results divided
          by the sum of the weights of the raters
        - within the rating, all ticks with a higher level are
          considered as ticks for a given level"""
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
            rate += rater.rate(tick, dense=dense)
            weight += rater.weight
        for label, rater in zip(labels, self.labels):
            rate += rater.rate(label, dense=dense)
            weight += rater.weight
        if part is not None and len(part):
            tickmin, tickmax = axis.gettickrange() # XXX: tickrange was not yet applied!?
            rate += self.tickrange.rate((float(part[-1]) - float(part[0])) * axis.divisor / (tickmax - tickmin))
        else:
            rate += self.tickrange.rate(0)
        weight += self.tickrange.weight
        return rate/weight

    def _ratedistances(self, distances, dense=1):
        """rate distances
        - the distances should be collected as box distances of
          subsequent labels (of any level))
        - the distances are a sequence of positive floats in
          PostScript points
        - the dense factor is used within the distancerate instance"""
        return self.distance._rate(distances, dense=dense)


################################################################################
# axis painter
################################################################################


class layoutdata: pass


class axistitlepainter:

    paralleltext = -90
    orthogonaltext = 0

    def __init__(self, titledist="0.3 cm",
                       titleattrs=(textmodule.halign.center, textmodule.valign.centerline()),
                       titledirection=-90,
                       titlepos=0.5):
        self.titledist_str = titledist
        self.titleattrs = titleattrs
        self.titledirection = titledirection
        self.titlepos = titlepos

    def reldirection(self, direction, dx, dy, epsilon=1e-10):
        direction += math.atan2(dy, dx) * 180 / math.pi
        while (direction > 90 + epsilon):
            direction -= 180
        while (direction < -90 - epsilon):
            direction += 180
        return direction

    def dolayout(self, graph, axis):
        if axis.title is not None and self.titleattrs is not None:
            titledist = unit.topt(unit.length(self.titledist_str, default_type="v"))
            x, y = axis._vtickpoint(axis, self.titlepos)
            dx, dy = axis.vtickdirection(axis, self.titlepos)
            # no not modify self.titleattrs ... the painter might be used by several axes!!!
            titleattrs = list(helper.ensuresequence(self.titleattrs))
            if self.titledirection is not None:
                titleattrs = titleattrs + [trafo.rotate(self.reldirection(self.titledirection, dx, dy))]
            axis.layoutdata.titlebox = graph.texrunner._text(x, y, axis.title, *titleattrs)
            axis.layoutdata._extent += titledist
            axis.layoutdata.titlebox._linealign(axis.layoutdata._extent, dx, dy)
            axis.layoutdata._extent += axis.layoutdata.titlebox._extent(dx, dy)
        else:
            axis.layoutdata.titlebox = None

    def paint(self, graph, axis):
        if axis.layoutdata.titlebox is not None:
            graph.insert(axis.layoutdata.titlebox)


class axispainter(axistitlepainter):

    defaultticklengths = ["%0.5f cm" % (0.2*goldenrule**(-i)) for i in range(10)]

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
                       labelattrs=((textmodule.halign.center, textmodule.valign.centerline()),
                                   (textmodule.size.footnotesize, textmodule.halign.center, textmodule.valign.centerline())),
                       labeldirection=None,
                       labelhequalize=0,
                       labelvequalize=1,
                       fractype=fractypeauto,
                       ratfracsuffixenum=1,
                       ratfracover=r"\over",
                       decfracpoint=".",
                       decfracequal=0,
                       expfractimes=r"\cdot",
                       expfracpre1=0,
                       expfracminexp=4,
                       suffix0=0,
                       suffix1=0,
                       **args):
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
        self.fractype = fractype
        self.ratfracsuffixenum = ratfracsuffixenum
        self.ratfracover = ratfracover
        self.decfracpoint = decfracpoint
        self.decfracequal = decfracequal
        self.expfractimes = expfractimes
        self.expfracpre1 = expfracpre1
        self.expfracminexp = expfracminexp
        self.suffix0 = suffix0
        self.suffix1 = suffix1
        axistitlepainter.__init__(self, **args)

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

    def decfrac(self, tick, decfraclength=None):
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
        tick.decfraclength = 0
        while (rest):
            tick.decfraclength += 1
            if rest in oldrest:
                periodstart = len(strfrac) - (len(oldrest) - oldrest.index(rest))
                strfrac = strfrac[:periodstart] + r"\overline{" + strfrac[periodstart:] + "}"
                break
            oldrest += [rest]
            rest *= 10
            frac, rest = divmod(rest, n)
            strfrac += str(frac)
        else:
            if decfraclength is not None:
                while tick.decfraclength < decfraclength:
                    strfrac += "0"
                    tick.decfraclength += 1
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
        tick.decfraclength = None
        if self.fractype == self.fractypeauto:
            if tick.suffix is not None:
                tick.text = self.ratfrac(tick)
            else:
                tick.text = self.expfrac(tick, self.expfracminexp)
                if tick.text is None:
                    tick.text = self.decfrac(tick)
        elif self.fractype == self.fractypedec:
            tick.text = self.decfrac(tick)
        elif self.fractype == self.fractypeexp:
            tick.text = self.expfrac(tick)
        elif self.fractype == self.fractyperat:
            tick.text = self.ratfrac(tick)
        else:
            raise ValueError("fractype invalid")
        if textmodule.mathmode not in tick.labelattrs:
            tick.labelattrs.append(textmodule.mathmode)

    def dolayout(self, graph, axis):
        labeldist = unit.topt(unit.length(self.labeldist_str, default_type="v"))
        for tick in axis.ticks:
            tick.virtual = axis.convert(float(tick) * axis.divisor)
            tick.x, tick.y = axis._vtickpoint(axis, tick.virtual)
            tick.dx, tick.dy = axis.vtickdirection(axis, tick.virtual)
        for tick in axis.ticks:
            tick.textbox = None
            if tick.labellevel is not None:
                tick.labelattrs = helper.getsequenceno(self.labelattrs, tick.labellevel)
                if tick.labelattrs is not None:
                    tick.labelattrs = list(helper.ensuresequence(tick.labelattrs))
                    if tick.text is None:
                        tick.suffix = axis.suffix
                        self.createtext(tick)
                    if self.labeldirection is not None:
                        tick.labelattrs += [trafo.rotate(self.reldirection(self.labeldirection, tick.dx, tick.dy))]
                    tick.textbox = textmodule._text(tick.x, tick.y, tick.text, *tick.labelattrs)
        if self.decfracequal:
            maxdecfraclength = max([tick.decfraclength for tick in axis.ticks if tick.labellevel is not None and
                                                                                 tick.labelattrs is not None and
                                                                                 tick.decfraclength is not None])
            for tick in axis.ticks:
                if (tick.labellevel is not None and
                    tick.labelattrs is not None and
                    tick.decfraclength is not None):
                    tick.text = self.decfrac(tick, maxdecfraclength)
        for tick in axis.ticks:
            if tick.labellevel is not None and tick.labelattrs is not None:
                tick.textbox = textmodule._text(tick.x, tick.y, tick.text, *tick.labelattrs)
        if len(axis.ticks) > 1:
            equaldirection = 1
            for tick in axis.ticks[1:]:
                if tick.dx != axis.ticks[0].dx or tick.dy != axis.ticks[0].dy:
                    equaldirection = 0
        else:
            equaldirection = 0
        if equaldirection and ((not axis.ticks[0].dx and self.labelvequalize) or
                               (not axis.ticks[0].dy and self.labelhequalize)):
            box._linealignequal([tick.textbox for tick in axis.ticks if tick.textbox],
                                labeldist, axis.ticks[0].dx, axis.ticks[0].dy)
        else:
            for tick in axis.ticks:
                if tick.textbox:
                    tick.textbox._linealign(labeldist, tick.dx, tick.dy)
        def topt_v_recursive(arg):
            if helper.issequence(arg):
                # return map(topt_v_recursive, arg) needs python2.2
                return [unit.topt(unit.length(a, default_type="v")) for a in arg]
            else:
                if arg is not None:
                    return unit.topt(unit.length(arg, default_type="v"))
        innerticklengths = topt_v_recursive(self.innerticklengths_str)
        outerticklengths = topt_v_recursive(self.outerticklengths_str)
        axis.layoutdata._extent = 0
        for tick in axis.ticks:
            if tick.ticklevel is not None:
                tick.innerticklength = helper.getitemno(innerticklengths, tick.ticklevel)
                tick.outerticklength = helper.getitemno(outerticklengths, tick.ticklevel)
                if tick.innerticklength is not None and tick.outerticklength is None:
                    tick.outerticklength = 0
                if tick.outerticklength is not None and tick.innerticklength is None:
                    tick.innerticklength = 0
            extent = 0
            if tick.textbox is None:
                if tick.outerticklength is not None and tick.outerticklength > 0:
                    extent = tick.outerticklength
            else:
                extent = tick.textbox._extent(tick.dx, tick.dy) + labeldist
            if axis.layoutdata._extent < extent:
                axis.layoutdata._extent = extent
        axistitlepainter.dolayout(self, graph, axis)

    def ratelayout(self, graph, axis, dense=1):
        ticktextboxes = [tick.textbox for tick in axis.ticks if tick.textbox is not None]
        if len(ticktextboxes) > 1:
            try:
                distances = [ticktextboxes[i]._boxdistance(ticktextboxes[i+1]) for i in range(len(ticktextboxes) - 1)]
            except box.BoxCrossError:
                return None
            rate = axis.rate._ratedistances(distances, dense)
            return rate
        else:
            if self.labelattrs is None:
                return 0

    def paint(self, graph, axis):
        for tick in axis.ticks:
            if tick.ticklevel is not None:
                if tick != frac(0, 1) or self.zerolineattrs is None:
                    gridattrs = helper.getsequenceno(self.gridattrs, tick.ticklevel)
                    if gridattrs is not None:
                        graph.stroke(axis.vgridpath(tick.virtual), *helper.ensuresequence(gridattrs))
                tickattrs = helper.getsequenceno(self.tickattrs, tick.ticklevel)
                if None not in (tick.innerticklength, tick.outerticklength, tickattrs):
                    x1 = tick.x - tick.dx * tick.innerticklength
                    y1 = tick.y - tick.dy * tick.innerticklength
                    x2 = tick.x + tick.dx * tick.outerticklength
                    y2 = tick.y + tick.dy * tick.outerticklength
                    graph.stroke(path._line(x1, y1, x2, y2), *helper.ensuresequence(tickattrs))
            if tick.textbox is not None:
                graph.insert(tick.textbox)
        if self.baselineattrs is not None:
            graph.stroke(axis.vbaseline(axis), *helper.ensuresequence(self.baselineattrs))
        if self.zerolineattrs is not None:
            if len(axis.ticks) and axis.ticks[0] * axis.ticks[-1] < frac(0, 1):
                graph.stroke(axis.vgridpath(axis.convert(0)), *helper.ensuresequence(self.zerolineattrs))
        axistitlepainter.paint(self, graph, axis)


class splitaxispainter(axistitlepainter):

    def __init__(self, breaklinesdist=0.05,
                       breaklineslength=0.5,
                       breaklinesangle=-60,
                       breaklinesattrs=(),
                       **args):
        self.breaklinesdist_str = breaklinesdist
        self.breaklineslength_str = breaklineslength
        self.breaklinesangle = breaklinesangle
        self.breaklinesattrs = breaklinesattrs
        axistitlepainter.__init__(self, **args)

    def subvbaseline(self, axis, v1=None, v2=None):
        if v1 is None:
            if self.breaklinesattrs is None:
                left = axis.vmin
            else:
                if axis.vminover is None:
                    left = None
                else:
                    left = axis.vminover
        else:
            left = axis.vmin+v1*(axis.vmax-axis.vmin)
        if v2 is None:
            if self.breaklinesattrs is None:
                right = axis.vmax
            else:
                if axis.vmaxover is None:
                    right = None
                else:
                    right = axis.vmaxover
        else:
            right = axis.vmin+v2*(axis.vmax-axis.vmin)
        return axis.baseaxis.vbaseline(axis.baseaxis, left, right)

    def dolayout(self, graph, axis):
        if self.breaklinesattrs is not None:
            self.breaklinesdist = unit.length(self.breaklinesdist_str, default_type="v")
            self.breaklineslength = unit.length(self.breaklineslength_str, default_type="v")
            self._breaklinesdist = unit.topt(self.breaklinesdist)
            self._breaklineslength = unit.topt(self.breaklineslength)
            self.sin = math.sin(self.breaklinesangle*math.pi/180.0)
            self.cos = math.cos(self.breaklinesangle*math.pi/180.0)
            axis.layoutdata._extent = (math.fabs(0.5 * self._breaklinesdist * self.cos) +
                                       math.fabs(0.5 * self._breaklineslength * self.sin))
        else:
            axis.layoutdata._extent = 0
        for subaxis in axis.axislist:
            subaxis.baseaxis = axis
            subaxis._vtickpoint = lambda axis, v: axis.baseaxis._vtickpoint(axis.baseaxis, axis.vmin+v*(axis.vmax-axis.vmin))
            subaxis.vtickdirection = lambda axis, v: axis.baseaxis.vtickdirection(axis.baseaxis, axis.vmin+v*(axis.vmax-axis.vmin))
            subaxis.vbaseline = self.subvbaseline
            subaxis.dolayout(graph)
            if axis.layoutdata._extent < subaxis.layoutdata._extent:
                axis.layoutdata._extent = subaxis.layoutdata._extent
        axistitlepainter.dolayout(self, graph, axis)

    def paint(self, graph, axis):
        for subaxis in axis.axislist:
            subaxis.dopaint(graph)
        if self.breaklinesattrs is not None:
            for subaxis1, subaxis2 in zip(axis.axislist[:-1], axis.axislist[1:]):
                # use a tangent of the baseline (this is independent of the tickdirection)
                v = 0.5 * (subaxis1.vmax + subaxis2.vmin)
                breakline = path.normpath(axis.vbaseline(axis, v, None)).tangent(0, self.breaklineslength)
                widthline = path.normpath(axis.vbaseline(axis, v, None)).tangent(0, self.breaklinesdist).transformed(trafo.rotate(self.breaklinesangle+90, *breakline.begin()))
                tocenter = map(lambda x: 0.5*(x[0]-x[1]), zip(breakline.begin(), breakline.end()))
                towidth = map(lambda x: 0.5*(x[0]-x[1]), zip(widthline.begin(), widthline.end()))
                breakline = breakline.transformed(trafo.translate(*tocenter).rotated(self.breaklinesangle, *breakline.begin()))
                breakline1 = breakline.transformed(trafo.translate(*towidth))
                breakline2 = breakline.transformed(trafo.translate(-towidth[0], -towidth[1]))
                graph.fill(path.path(path.moveto(*breakline1.begin()),
                                     path.lineto(*breakline1.end()),
                                     path.lineto(*breakline2.end()),
                                     path.lineto(*breakline2.begin()),
                                     path.closepath()), color.gray.white)
                graph.stroke(breakline1, *helper.ensuresequence(self.breaklinesattrs))
                graph.stroke(breakline2, *helper.ensuresequence(self.breaklinesattrs))
        axistitlepainter.paint(self, graph, axis)


class baraxispainter(axistitlepainter):

    def __init__(self, innerticklength=None,
                       outerticklength=None,
                       tickattrs=(),
                       baselineattrs=canvas.linecap.square,
                       namedist="0.3 cm",
                       nameattrs=(textmodule.halign.center, textmodule.valign.centerline()),
                       namedirection=None,
                       namepos=0.5,
                       namehequalize=0,
                       namevequalize=1,
                       **args):
        self.innerticklength_str = innerticklength
        self.outerticklength_str = outerticklength
        self.tickattrs = tickattrs
        self.baselineattrs = baselineattrs
        self.namedist_str = namedist
        self.nameattrs = nameattrs
        self.namedirection = namedirection
        self.namepos = namepos
        self.namehequalize = namehequalize
        self.namevequalize = namevequalize
        axistitlepainter.__init__(self, **args)

    def dolayout(self, graph, axis):
        axis.layoutdata._extent = 0
        if axis.multisubaxis:
            for name, subaxis in zip(axis.names, axis.subaxis):
                subaxis.vmin = axis.convert((name, 0))
                subaxis.vmax = axis.convert((name, 1))
                subaxis.baseaxis = axis
                subaxis._vtickpoint = lambda axis, v: axis.baseaxis._vtickpoint(axis.baseaxis, axis.vmin+v*(axis.vmax-axis.vmin))
                subaxis.vtickdirection = lambda axis, v: axis.baseaxis.vtickdirection(axis.baseaxis, axis.vmin+v*(axis.vmax-axis.vmin))
                subaxis.vbaseline = None
                subaxis.dolayout(graph)
                if axis.layoutdata._extent < subaxis.layoutdata._extent:
                    axis.layoutdata._extent = subaxis.layoutdata._extent
        axis.namepos = []
        for name in axis.names:
            v = axis.convert((name, self.namepos))
            x, y = axis._vtickpoint(axis, v)
            dx, dy = axis.vtickdirection(axis, v)
            axis.namepos.append((v, x, y, dx, dy))
        axis.nameboxes = []
        for (v, x, y, dx, dy), name in zip(axis.namepos, axis.names):
            nameattrs = helper.ensurelist(self.nameattrs)
            if self.namedirection is not None:
                nameattrs += [trafo.rotate(self.reldirection(self.namedirection, dx, dy))]
            if axis.texts.has_key(name):
                axis.nameboxes.append(textmodule._text(x, y, str(axis.texts[name]), *nameattrs))
            elif axis.texts.has_key(str(name)):
                axis.nameboxes.append(textmodule._text(x, y, str(axis.texts[str(name)]), *nameattrs))
            else:
                axis.nameboxes.append(textmodule._text(x, y, str(name), *nameattrs))
        labeldist = axis.layoutdata._extent + unit.topt(unit.length(self.namedist_str, default_type="v"))
        if len(axis.namepos) > 1:
            equaldirection = 1
            for namepos in axis.namepos[1:]:
                if namepos[3] != axis.namepos[0][3] or namepos[4] != axis.namepos[0][4]:
                    equaldirection = 0
        else:
            equaldirection = 0
        if equaldirection and ((not axis.namepos[0][3] and self.namevequalize) or
                               (not axis.namepos[0][4] and self.namehequalize)):
            box._linealignequal(axis.nameboxes, labeldist, axis.namepos[0][3], axis.namepos[0][4])
        else:
            for namebox, namepos in zip(axis.nameboxes, axis.namepos):
                namebox._linealign(labeldist, namepos[3], namepos[4])
        if self.innerticklength_str is not None:
            axis.innerticklength = unit.topt(unit.length(self.innerticklength_str, default_type="v"))
        else:
            if self.outerticklength_str is not None:
                axis.innerticklength = 0
            else:
                axis.innerticklength = None
        if self.outerticklength_str is not None:
            axis.outerticklength = unit.topt(unit.length(self.outerticklength_str, default_type="v"))
        else:
            if self.innerticklength_str is not None:
                axis.outerticklength = 0
            else:
                axis.outerticklength = None
        if axis.outerticklength is not None and self.tickattrs is not None:
            axis.layoutdata._extent += axis.outerticklength
        for (v, x, y, dx, dy), namebox in zip(axis.namepos, axis.nameboxes):
            newextent = namebox._extent(dx, dy) + labeldist
            if axis.layoutdata._extent < newextent:
                axis.layoutdata._extent = newextent
        axistitlepainter.dolayout(self, graph, axis)
        graph.mindbbox(*[namebox.bbox() for namebox in axis.nameboxes])

    def paint(self, graph, axis):
        if axis.subaxis is not None:
            if axis.multisubaxis:
                for subaxis in axis.subaxis:
                    subaxis.dopaint(graph)
        if None not in (self.tickattrs, axis.innerticklength, axis.outerticklength):
            for pos in axis.relsizes:
                if pos == axis.relsizes[0]:
                    pos -= axis.firstdist
                elif pos != axis.relsizes[-1]:
                    pos -= 0.5 * axis.dist
                v = pos / axis.relsizes[-1]
                x, y = axis._vtickpoint(axis, v)
                dx, dy = axis.vtickdirection(axis, v)
                x1 = x - dx * axis.innerticklength
                y1 = y - dy * axis.innerticklength
                x2 = x + dx * axis.outerticklength
                y2 = y + dy * axis.outerticklength
                graph.stroke(path._line(x1, y1, x2, y2), *helper.ensuresequence(self.tickattrs))
        if self.baselineattrs is not None:
            if axis.vbaseline is not None: # XXX: subbaselines (as for splitlines)
                graph.stroke(axis.vbaseline(axis), *helper.ensuresequence(self.baselineattrs))
        for namebox in axis.nameboxes:
            graph.insert(namebox)
        axistitlepainter.paint(self, graph, axis)



################################################################################
# axes
################################################################################

class PartitionError(Exception): pass

class _axis:

    def __init__(self, min=None, max=None, reverse=0, divisor=1,
                       datavmin=None, datavmax=None, tickvmin=0, tickvmax=1,
                       title=None, suffix=None, painter=axispainter(), dense=None):
        if None not in (min, max) and min > max:
            min, max, reverse = max, min, not reverse
        self.fixmin, self.fixmax, self.min, self.max, self.reverse = min is not None, max is not None, min, max, reverse

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
        self.tickvmin = tickvmin
        self.tickvmax = tickvmax

        self.divisor = divisor
        self.title = title
        self.suffix = suffix
        self.painter = painter
        self.dense = dense
        self.canconvert = 0
        self.__setinternalrange()

    def __setinternalrange(self, min=None, max=None):
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

    def __getinternalrange(self):
        return self.min, self.max, self.datamin, self.datamax, self.tickmin, self.tickmax

    def __forceinternalrange(self, range):
        self.min, self.max, self.datamin, self.datamax, self.tickmin, self.tickmax = range
        self.__setinternalrange()

    def setdatarange(self, min, max):
        self.datamin, self.datamax = min, max
        self.__setinternalrange(min, max)

    def settickrange(self, min, max):
        self.tickmin, self.tickmax = min, max
        self.__setinternalrange(min, max)

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

    def dolayout(self, graph):
        if self.dense is not None:
            dense = self.dense
        else:
            dense = graph.dense
        min, max = self.gettickrange()
        self.ticks = self.part.defaultpart(min/self.divisor, max/self.divisor, not self.fixmin, not self.fixmax)
        # lesspart and morepart can be called after defaultpart,
        # although some axes may share their autoparting ---
        # it works, because the axes are processed sequentially
        first = 1
        maxworse = 2
        worse = 0
        while worse < maxworse:
            newticks = self.part.lesspart()
            if newticks is not None:
                if first:
                    bestrate = self.rate.ratepart(self, self.ticks, dense)
                    variants = [[bestrate, self.ticks]]
                    first = 0
                newrate = self.rate.ratepart(self, newticks, dense)
                variants.append([newrate, newticks])
                if newrate < bestrate:
                    bestrate = newrate
                    worse = 0
                else:
                    worse += 1
            else:
                worse += 1
        worse = 0
        while worse < maxworse:
            newticks = self.part.morepart()
            if newticks is not None:
                if first:
                    bestrate = self.rate.ratepart(self, self.ticks, dense)
                    variants = [[bestrate, self.ticks]]
                    first = 0
                newrate = self.rate.ratepart(self, newticks, dense)
                variants.append([newrate, newticks])
                if newrate < bestrate:
                    bestrate = newrate
                    worse = 0
                else:
                    worse += 1
            else:
                worse += 1
        if not first:
            variants.sort()
            if self.painter is not None:
                i = 0
                bestrate = None
                while i < len(variants) and (bestrate is None or variants[i][0] < bestrate):
                    saverange = self.__getinternalrange()
                    self.ticks = variants[i][1]
                    if len(self.ticks):
                        self.settickrange(float(self.ticks[0])*self.divisor, float(self.ticks[-1])*self.divisor)
                    self.layoutdata = layoutdata()
                    self.painter.dolayout(graph, self)
                    ratelayout = self.painter.ratelayout(graph, self, dense)
                    if ratelayout is not None:
                        variants[i][0] += ratelayout
                        variants[i].append(self.layoutdata)
                    else:
                        variants[i][0] = None
                    if variants[i][0] is not None and (bestrate is None or variants[i][0] < bestrate):
                        bestrate = variants[i][0]
                    self.__forceinternalrange(saverange)
                    i += 1
                if bestrate is None:
                    raise PartitionError("no valid axis partitioning found")
                variants = [variant for variant in variants[:i] if variant[0] is not None]
                variants.sort()
            else:
                self.layoutdata._extent = 0
            self.ticks = variants[0][1]
            self.layoutdata = variants[0][2]
            if len(self.ticks):
                self.settickrange(float(self.ticks[0])*self.divisor, float(self.ticks[-1])*self.divisor)
        else:
            if len(self.ticks):
                self.settickrange(float(self.ticks[0])*self.divisor, float(self.ticks[-1])*self.divisor)
            self.layoutdata = layoutdata()
            self.painter.dolayout(graph, self)
        graph.mindbbox(*[tick.textbox.bbox() for tick in self.ticks if tick.textbox is not None])

    def dopaint(self, graph):
        if self.painter is not None:
            self.painter.paint(graph, self)

    def createlinkaxis(self, **args):
        return linkaxis(self, **args)


class linaxis(_axis, _linmap):

    def __init__(self, part=autolinpart(), rate=axisrater(), **args):
        _axis.__init__(self, **args)
        if self.fixmin and self.fixmax:
            self.relsize = self.max - self.min
        self.part = part
        self.rate = rate


class logaxis(_axis, _logmap):

    def __init__(self, part=autologpart(), rate=axisrater(ticks=axisrater.logticks, labels=axisrater.loglabels), **args):
        _axis.__init__(self, **args)
        if self.fixmin and self.fixmax:
            self.relsize = math.log(self.max) - math.log(self.min)
        self.part = part
        self.rate = rate


class linkaxis:

    def __init__(self, linkedaxis, title=None, skipticklevel=None, skiplabellevel=0, painter=axispainter(zerolineattrs=None)):
        self.linkedaxis = linkedaxis
        while isinstance(self.linkedaxis, linkaxis):
            self.linkedaxis = self.linkedaxis.linkedaxis
        self.fixmin = self.linkedaxis.fixmin
        self.fixmax = self.linkedaxis.fixmax
        if self.fixmin:
            self.min = self.linkedaxis.min
        if self.fixmax:
            self.max = self.linkedaxis.max
        self.skipticklevel = skipticklevel
        self.skiplabellevel = skiplabellevel
        self.title = title
        self.painter = painter

    def ticks(self, ticks):
        result = []
        for _tick in ticks:
            ticklevel = _tick.ticklevel
            labellevel = _tick.labellevel
            if self.skipticklevel is not None and ticklevel >= self.skipticklevel:
                ticklevel = None
            if self.skiplabellevel is not None and labellevel >= self.skiplabellevel:
                labellevel = None
            if ticklevel is not None or labellevel is not None:
                result.append(tick(_tick.enum, _tick.denom, ticklevel, labellevel))
        return result
        # XXX: don't forget to calculate new text positions as soon as this is moved
        #      outside of the paint method (when rating is moved into the axispainter)

    def getdatarange(self):
        return self.linkedaxis.getdatarange()

    def setdatarange(self, min, max):
        prevrange = self.linkedaxis.getdatarange()
        self.linkedaxis.setdatarange(min, max)
        if hasattr(self.linkedaxis, "ticks") and prevrange != self.linkedaxis.getdatarange():
            raise RuntimeError("linkaxis datarange setting performed while linked axis layout already fixed")

    def dolayout(self, graph):
        self.ticks = self.ticks(self.linkedaxis.ticks)
        self.convert = self.linkedaxis.convert
        self.divisor = self.linkedaxis.divisor
        self.suffix = self.linkedaxis.suffix
        self.layoutdata = layoutdata()
        self.painter.dolayout(graph, self)

    def dopaint(self, graph):
        self.painter.paint(graph, self)

    def createlinkaxis(self, **args):
        return linkaxis(self.linkedaxis)


class splitaxis:

    def __init__(self, axislist, splitlist=0.5, splitdist=0.1, relsizesplitdist=1, title=None, painter=splitaxispainter()):
        self.title = title
        self.axislist = axislist
        self.painter = painter
        self.splitlist = list(helper.ensuresequence(splitlist))
        self.splitlist.sort()
        if len(self.axislist) != len(self.splitlist) + 1:
            for subaxis in self.axislist:
                if not isinstance(subaxis, linkaxis):
                    raise ValueError("axislist and splitlist lengths do not fit together")
        for subaxis in self.axislist:
            if isinstance(subaxis, linkaxis):
                subaxis.vmin = subaxis.linkedaxis.vmin
                subaxis.vminover = subaxis.linkedaxis.vminover
                subaxis.vmax = subaxis.linkedaxis.vmax
                subaxis.vmaxover = subaxis.linkedaxis.vmaxover
            else:
                subaxis.vmin = None
                subaxis.vmax = None
        self.axislist[0].vmin = 0
        self.axislist[0].vminover = None
        self.axislist[-1].vmax = 1
        self.axislist[-1].vmaxover = None
        for i in xrange(len(self.splitlist)):
            if self.splitlist[i] is not None:
                self.axislist[i].vmax = self.splitlist[i] - 0.5*splitdist
                self.axislist[i].vmaxover = self.splitlist[i]
                self.axislist[i+1].vmin = self.splitlist[i] + 0.5*splitdist
                self.axislist[i+1].vminover = self.splitlist[i]
        i = 0
        while i < len(self.axislist):
            if self.axislist[i].vmax is None:
                j = relsize = relsize2 = 0
                while self.axislist[i + j].vmax is None:
                    relsize += self.axislist[i + j].relsize + relsizesplitdist
                    j += 1
                relsize += self.axislist[i + j].relsize
                vleft = self.axislist[i].vmin
                vright = self.axislist[i + j].vmax
                for k in range(i, i + j):
                    relsize2 += self.axislist[k].relsize
                    self.axislist[k].vmax = vleft + (vright - vleft) * relsize2 / float(relsize)
                    relsize2 += 0.5 * relsizesplitdist
                    self.axislist[k].vmaxover = self.axislist[k + 1].vminover = vleft + (vright - vleft) * relsize2 / float(relsize)
                    relsize2 += 0.5 * relsizesplitdist
                    self.axislist[k+1].vmin = vleft + (vright - vleft) * relsize2 / float(relsize)
                if i == 0 and i + j + 1 == len(self.axislist):
                    self.relsize = relsize
                i += j + 1
            else:
                i += 1

        self.fixmin = self.axislist[0].fixmin
        if self.fixmin:
            self.min = self.axislist[0].min
        self.fixmax = self.axislist[-1].fixmax
        if self.fixmax:
            self.max = self.axislist[-1].max
        self.divisor = 1
        self.suffix = ""

    def getdatarange(self):
        min = self.axislist[0].getdatarange()
        max = self.axislist[-1].getdatarange()
        try:
            return min[0], max[1]
        except TypeError:
            return None

    def setdatarange(self, min, max):
        self.axislist[0].setdatarange(min, None)
        self.axislist[-1].setdatarange(None, max)

    def gettickrange(self):
        min = self.axislist[0].gettickrange()
        max = self.axislist[-1].gettickrange()
        try:
            return min[0], max[1]
        except TypeError:
            return None

    def settickrange(self, min, max):
        self.axislist[0].settickrange(min, None)
        self.axislist[-1].settickrange(None, max)

    def convert(self, value):
        # TODO: proper raising exceptions (which exceptions go thru, which are handled before?)
        if value < self.axislist[0].max:
            return self.axislist[0].vmin + self.axislist[0].convert(value)*(self.axislist[0].vmax-self.axislist[0].vmin)
        for axis in self.axislist[1:-1]:
            if value > axis.min and value < axis.max:
                return axis.vmin + axis.convert(value)*(axis.vmax-axis.vmin)
        if value > self.axislist[-1].min:
            return self.axislist[-1].vmin + self.axislist[-1].convert(value)*(self.axislist[-1].vmax-self.axislist[-1].vmin)
        raise ValueError("value couldn't be assigned to a split region")

    def dolayout(self, graph):
        self.layoutdata = layoutdata()
        self.painter.dolayout(graph, self)

    def dopaint(self, graph):
        self.painter.paint(graph, self)

    def createlinkaxis(self, painter=None, *args):
        if not len(args):
            return splitaxis([x.createlinkaxis() for x in self.axislist], splitlist=None)
        if len(args) != len(self.axislist):
            raise IndexError("length of the argument list doesn't fit to split number")
        if painter is None:
            painter = self.painter
        return splitaxis([x.createlinkaxis(**arg) for x, arg in zip(self.axislist, args)], painter=painter)


class baraxis:

    def __init__(self, subaxis=None, multisubaxis=0, title=None, dist=0.5, firstdist=None, lastdist=None, names=None, texts={}, painter=baraxispainter()):
        self.dist = dist
        if firstdist is not None:
            self.firstdist = firstdist
        else:
            self.firstdist = 0.5 * dist
        if lastdist is not None:
            self.lastdist = lastdist
        else:
            self.lastdist = 0.5 * dist
        self.relsizes = None
        self.fixnames = 0
        self.names = []
        for name in helper.ensuresequence(names):
            self.setname(name)
        self.fixnames = names is not None
        self.multisubaxis = multisubaxis
        if self.multisubaxis:
            self.createsubaxis = subaxis
            self.subaxis = [self.createsubaxis.createsubaxis() for name in self.names]
        else:
            self.subaxis = subaxis
        self.title = title
        self.fixnames = 0
        self.texts = texts
        self.painter = painter

    def getdatarange(self):
        return None

    def setname(self, name, *subnames):
        # setting self.relsizes to None forces later recalculation
        if not self.fixnames:
            if name not in self.names:
                self.relsizes = None
                self.names.append(name)
                if self.multisubaxis:
                    self.subaxis.append(self.createsubaxis.createsubaxis())
        if (not self.fixnames or name in self.names) and len(subnames):
            if self.multisubaxis:
                if self.subaxis[self.names.index(name)].setname(*subnames):
                    self.relsizes = None
            else:
                if self.subaxis.setname(*subnames):
                    self.relsizes = None
        return self.relsizes is not None

    def updaterelsizes(self):
        self.relsizes = [i*self.dist + self.firstdist for i in range(len(self.names) + 1)]
        self.relsizes[-1] += self.lastdist - self.dist
        if self.multisubaxis:
            subrelsize = 0
            for i in range(1, len(self.relsizes)):
                self.subaxis[i-1].updaterelsizes()
                subrelsize += self.subaxis[i-1].relsizes[-1]
                self.relsizes[i] += subrelsize
        else:
            if self.subaxis is None:
                subrelsize = 1
            else:
                self.subaxis.updaterelsizes()
                subrelsize = self.subaxis.relsizes[-1]
            for i in range(1, len(self.relsizes)):
                self.relsizes[i] += i * subrelsize

    def convert(self, value):
        # TODO: proper raising exceptions (which exceptions go thru, which are handled before?)
        if not self.relsizes:
            self.updaterelsizes()
        pos = self.names.index(value[0])
        if len(value) == 2:
            if self.subaxis is None:
                subvalue = value[1]
            else:
                if self.multisubaxis:
                    subvalue = value[1] * self.subaxis[pos].relsizes[-1]
                else:
                    subvalue = value[1] * self.subaxis.relsizes[-1]
        else:
            if self.multisubaxis:
                subvalue = self.subaxis[pos].convert(value[1:]) * self.subaxis[pos].relsizes[-1]
            else:
                subvalue = self.subaxis.convert(value[1:]) * self.subaxis.relsizes[-1]
        return (self.relsizes[pos] + subvalue) / float(self.relsizes[-1])

    def dolayout(self, graph):
        self.layoutdata = layoutdata()
        self.painter.dolayout(graph, self)

    def dopaint(self, graph):
        self.painter.paint(graph, self)

    def createlinkaxis(self, **args):
        if self.subaxis is not None:
            if self.multisubaxis:
                subaxis = [subaxis.createlinkaxis() for subaxis in self.subaxis]
            else:
                subaxis = self.subaxis.createlinkaxis()
        else:
            subaxis = None
        return baraxis(subaxis=subaxis, dist=self.dist, firstdist=self.firstdist, lastdist=self.lastdist, **args)

    createsubaxis = createlinkaxis


################################################################################
# graph key
################################################################################


class key:

    def __init__(self, dist="0.2 cm", pos = "tr", hdist="0.6 cm", vdist="0.4 cm",
                 symbolwidth="0.5 cm", symbolheight="0.25 cm", symbolspace="0.2 cm",
                 textattrs=()):
        self.dist_str = dist
        self.pos = pos
        self.hdist_str = hdist
        self.vdist_str = vdist
        self.symbolwidth_str = symbolwidth
        self.symbolheight_str = symbolheight
        self.symbolspace_str = symbolspace
        if self.pos in ("tr", "rt"):
            self.right = 1
            self.top = 1
        elif self.pos in ("br", "rb"):
            self.right = 1
            self.top = 0
        elif self.pos in ("tl", "lt"):
            self.right = 0
            self.top = 1
        elif self.pos in ("bl", "lb"):
            self.right = 0
            self.top = 0
        else:
            raise RuntimeError("invalid pos attribute")

    def dopaint(self, graph, styles=None):
        self._dist = unit.topt(self.dist_str)
        self._hdist = unit.topt(self.hdist_str)
        self._vdist = unit.topt(self.vdist_str)
        self._symbolwidth = unit.topt(self.symbolwidth_str)
        self._symbolheight = unit.topt(self.symbolheight_str)
        self._symbolspace = unit.topt(self.symbolspace_str)
        if styles is None:
            styles = graph.styles
        titles = []
        if self.top:
            _ypos = graph._ypos + graph._height - self._vdist
        else:
            _ypos = graph._ypos + self._vdist
        if self.right:
            _xpos = graph._xpos + graph._width - self._hdist
        else:
            _xpos = graph._xpos + self._hdist + self._symbolwidth + self._symbolspace
        titles = []
        for style in styles:
            titles.append(graph.texrunner._text(_xpos, _ypos, style.data.title))
        if self.top:
            box.linealignequal(titles, 0, 0, -1)
            box._tile(titles, self._dist, 0, -1)
        else:
            titles.reverse() # change the order
            box.linealignequal(titles, 0, 0, 1)
            box._tile(titles, self._dist, 0, 1)
            titles.reverse() # back change
        if self.right:
            box.linealignequal(titles, 0, -1, 0)
        else:
            box.linealignequal(titles, 0, 1, 0)
        for title in titles:
            graph.insert(title)


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
            if helper.issequence(data):
                raise RuntimeError("list plot needs an explicit style")
            if self.defaultstyle.has_key(data.defaultstyle):
                style = self.defaultstyle[data.defaultstyle].iterate()
            else:
                style = data.defaultstyle()
                self.defaultstyle[data.defaultstyle] = style
        styles = []
        first = 1
        for d in helper.ensuresequence(data):
            if first:
                styles.append(style)
            else:
                styles.append(style.iterate())
            first = 0
            if d is not None:
                d.setstyle(self, styles[-1])
                styles[-1].data = d
                self.data.append(d)
                self.styles.append(styles[-1])
        if helper.issequence(data):
            return styles
        return styles[0]

    def _vxtickpoint(self, axis, v):
        return (self._xpos+v*self._width, axis.axispos)

    def _vytickpoint(self, axis, v):
        return (axis.axispos, self._ypos+v*self._height)

    def vtickdirection(self, axis, v):
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

    def vxbaseline(self, axis, v1=None, v2=None, shift=0):
        if v1 is None: v1 = 0
        if v2 is None: v2 = 1
        return path._line(self._xpos+v1*self._width, axis.axispos+shift,
                          self._xpos+v2*self._width, axis.axispos+shift)

    def vybaseline(self, axis, v1=None, v2=None, shift=0):
        if v1 is None: v1 = 0
        if v2 is None: v2 = 1
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
        # known ranges are also set as ranges for the axes
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
        self.gatherranges()

        # do the layout for all axes
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
                axis._vtickpoint = self._vxtickpoint
                axis.fixtickdirection = (0, num3)
                axis.vgridpath = self.vxgridpath
                axis.vbaseline = self.vxbaseline
                axis.gridpath = self.xgridpath
                axis.baseline = self.xbaseline
            elif YPattern.match(key):
                if needyaxisdist[num2]:
                    self._yaxisextents[num2] += axesdist
                axis.axispos = self._xpos+num2*self._width + num3*self._yaxisextents[num2]
                axis._vtickpoint = self._vytickpoint
                axis.fixtickdirection = (num3, 0)
                axis.vgridpath = self.vygridpath
                axis.vbaseline = self.vybaseline
                axis.gridpath = self.ygridpath
                axis.baseline = self.ybaseline
            else:
                raise ValueError("Axis key '%s' not allowed" % key)
            axis.vtickdirection = self.vtickdirection
            axis.dolayout(self)
            if XPattern.match(key):
                self._xaxisextents[num2] += axis.layoutdata._extent
                needxaxisdist[num2] = 1
            if YPattern.match(key):
                self._yaxisextents[num2] += axis.layoutdata._extent
                needyaxisdist[num2] = 1

    def dobackground(self):
        self.dolayout()
        if not self.removedomethod(self.dobackground): return
        if self.backgroundattrs is not None:
            self.draw(path._rect(self._xpos, self._ypos, self._width, self._height),
                      *helper.ensuresequence(self.backgroundattrs))

    def doaxes(self):
        self.dolayout()
        if not self.removedomethod(self.doaxes): return
        for axis in self.axes.values():
            axis.dopaint(self)

    def dodata(self):
        self.dolayout()
        if not self.removedomethod(self.dodata): return
        for data in self.data:
            data.draw(self)

    def doautokey(self):
        self.dolayout()
        if not self.removedomethod(self.doautokey): return
        if self.autokey is not None:
            self.autokey.dopaint(self)

    def finish(self):
        while len(self.domethods):
            self.domethods[0]()

    def initwidthheight(self, width, height, ratio):
        if (width is not None) and (height is None):
             self.width = unit.length(width)
             self.height = (1/ratio) * self.width
        elif (height is not None) and (width is None):
             self.height = unit.length(height)
             self.width = ratio * self.height
        else:
             self.width = unit.length(width)
             self.height = unit.length(height)
        self._width = unit.topt(self.width)
        self._height = unit.topt(self.height)
        if self._width <= 0: raise ValueError("width <= 0")
        if self._height <= 0: raise ValueError("height <= 0")

    def initaxes(self, axes, addlinkaxes=0):
        for key in self.Names:
            if not axes.has_key(key):
                axes[key] = linaxis()
            elif axes[key] is None:
                del axes[key]
            if addlinkaxes:
                if not axes.has_key(key + "2") and axes.has_key(key):
                    axes[key + "2"] = axes[key].createlinkaxis()
                elif axes[key + "2"] is None:
                    del axes[key + "2"]
        self.axes = axes

    def __init__(self, xpos=0, ypos=0, width=None, height=None, ratio=goldenrule,
                 autokey=None, backgroundattrs=None, dense=1, axesdist="0.8 cm", **axes):
        canvas.canvas.__init__(self)
        self.xpos = unit.length(xpos)
        self.ypos = unit.length(ypos)
        self._xpos = unit.topt(self.xpos)
        self._ypos = unit.topt(self.ypos)
        self.initwidthheight(width, height, ratio)
        self.initaxes(axes, 1)
        self.autokey = autokey
        self.backgroundattrs = backgroundattrs
        self.dense = dense
        self.axesdist_str = axesdist
        self.data = []
        self.styles = []
        self.domethods = [self.dolayout, self.dobackground, self.doaxes, self.dodata, self.doautokey]
        self.haslayout = 0
        self.defaultstyle = {}
        self.mindbboxes = []

    def mindbbox(self, *boxes):
        self.mindbboxes.extend(boxes)

    def bbox(self):
        self.finish()
        result = bbox.bbox(self._xpos - self._yaxisextents[0],
                           self._ypos - self._xaxisextents[0],
                           self._xpos + self._width + self._yaxisextents[1],
                           self._ypos + self._height + self._xaxisextents[1])
        for box in self.mindbboxes:
            result = result + box
        return result

    def write(self, file):
        self.finish()
        canvas.canvas.write(self, file)



# some thoughts, but deferred right now
# 
# class graphxyz(graphxy):
# 
#     Names = "x", "y", "z"
# 
#     def _vxtickpoint(self, axis, v):
#         return self._vpos(v, axis.vypos, axis.vzpos)
# 
#     def _vytickpoint(self, axis, v):
#         return self._vpos(axis.vxpos, v, axis.vzpos)
# 
#     def _vztickpoint(self, axis, v):
#         return self._vpos(axis.vxpos, axis.vypos, v)
# 
#     def vxtickdirection(self, axis, v):
#         x1, y1 = self._vpos(v, axis.vypos, axis.vzpos)
#         x2, y2 = self._vpos(v, 0.5, 0)
#         dx, dy = x1 - x2, y1 - y2
#         norm = math.sqrt(dx*dx + dy*dy)
#         return dx/norm, dy/norm
# 
#     def vytickdirection(self, axis, v):
#         x1, y1 = self._vpos(axis.vxpos, v, axis.vzpos)
#         x2, y2 = self._vpos(0.5, v, 0)
#         dx, dy = x1 - x2, y1 - y2
#         norm = math.sqrt(dx*dx + dy*dy)
#         return dx/norm, dy/norm
# 
#     def vztickdirection(self, axis, v):
#         return -1, 0
#         x1, y1 = self._vpos(axis.vxpos, axis.vypos, v)
#         x2, y2 = self._vpos(0.5, 0.5, v)
#         dx, dy = x1 - x2, y1 - y2
#         norm = math.sqrt(dx*dx + dy*dy)
#         return dx/norm, dy/norm
# 
#     def _pos(self, x, y, z, xaxis=None, yaxis=None, zaxis=None):
#         if xaxis is None: xaxis = self.axes["x"]
#         if yaxis is None: yaxis = self.axes["y"]
#         if zaxis is None: zaxis = self.axes["z"]
#         return self._vpos(xaxis.convert(x), yaxis.convert(y), zaxis.convert(z))
# 
#     def pos(self, x, y, z, xaxis=None, yaxis=None, zaxis=None):
#         if xaxis is None: xaxis = self.axes["x"]
#         if yaxis is None: yaxis = self.axes["y"]
#         if zaxis is None: zaxis = self.axes["z"]
#         return self.vpos(xaxis.convert(x), yaxis.convert(y), zaxis.convert(z))
# 
#     def _vpos(self, vx, vy, vz):
#         x, y, z = (vx - 0.5)*self._depth, (vy - 0.5)*self._width, (vz - 0.5)*self._height
#         d0 = float(self.a[0]*self.b[1]*(z-self.eye[2])
#                  + self.a[2]*self.b[0]*(y-self.eye[1])
#                  + self.a[1]*self.b[2]*(x-self.eye[0])
#                  - self.a[2]*self.b[1]*(x-self.eye[0])
#                  - self.a[0]*self.b[2]*(y-self.eye[1])
#                  - self.a[1]*self.b[0]*(z-self.eye[2]))
#         da = (self.eye[0]*self.b[1]*(z-self.eye[2])
#             + self.eye[2]*self.b[0]*(y-self.eye[1])
#             + self.eye[1]*self.b[2]*(x-self.eye[0])
#             - self.eye[2]*self.b[1]*(x-self.eye[0])
#             - self.eye[0]*self.b[2]*(y-self.eye[1])
#             - self.eye[1]*self.b[0]*(z-self.eye[2]))
#         db = (self.a[0]*self.eye[1]*(z-self.eye[2])
#             + self.a[2]*self.eye[0]*(y-self.eye[1])
#             + self.a[1]*self.eye[2]*(x-self.eye[0])
#             - self.a[2]*self.eye[1]*(x-self.eye[0])
#             - self.a[0]*self.eye[2]*(y-self.eye[1])
#             - self.a[1]*self.eye[0]*(z-self.eye[2]))
#         return da/d0 + self._xpos, db/d0 + self._ypos
# 
#     def vpos(self, vx, vy, vz):
#         tx, ty = self._vpos(vx, vy, vz)
#         return unit.t_pt(tx), unit.t_pt(ty)
# 
#     def xbaseline(self, axis, x1, x2, shift=0, xaxis=None):
#         if xaxis is None: xaxis = self.axes["x"]
#         return self.vxbaseline(axis, xaxis.convert(x1), xaxis.convert(x2), shift)
# 
#     def ybaseline(self, axis, y1, y2, shift=0, yaxis=None):
#         if yaxis is None: yaxis = self.axes["y"]
#         return self.vybaseline(axis, yaxis.convert(y1), yaxis.convert(y2), shift)
# 
#     def zbaseline(self, axis, z1, z2, shift=0, zaxis=None):
#         if zaxis is None: zaxis = self.axes["z"]
#         return self.vzbaseline(axis, zaxis.convert(z1), zaxis.convert(z2), shift)
# 
#     def vxbaseline(self, axis, v1, v2, shift=0):
#         return (path._line(*(self._vpos(v1, 0, 0) + self._vpos(v2, 0, 0))) +
#                 path._line(*(self._vpos(v1, 0, 1) + self._vpos(v2, 0, 1))) +
#                 path._line(*(self._vpos(v1, 1, 1) + self._vpos(v2, 1, 1))) +
#                 path._line(*(self._vpos(v1, 1, 0) + self._vpos(v2, 1, 0))))
# 
#     def vybaseline(self, axis, v1, v2, shift=0):
#         return (path._line(*(self._vpos(0, v1, 0) + self._vpos(0, v2, 0))) +
#                 path._line(*(self._vpos(0, v1, 1) + self._vpos(0, v2, 1))) +
#                 path._line(*(self._vpos(1, v1, 1) + self._vpos(1, v2, 1))) +
#                 path._line(*(self._vpos(1, v1, 0) + self._vpos(1, v2, 0))))
# 
#     def vzbaseline(self, axis, v1, v2, shift=0):
#         return (path._line(*(self._vpos(0, 0, v1) + self._vpos(0, 0, v2))) +
#                 path._line(*(self._vpos(0, 1, v1) + self._vpos(0, 1, v2))) +
#                 path._line(*(self._vpos(1, 1, v1) + self._vpos(1, 1, v2))) +
#                 path._line(*(self._vpos(1, 0, v1) + self._vpos(1, 0, v2))))
# 
#     def xgridpath(self, x, xaxis=None):
#         assert 0
#         if xaxis is None: xaxis = self.axes["x"]
#         v = xaxis.convert(x)
#         return path._line(self._xpos+v*self._width, self._ypos,
#                           self._xpos+v*self._width, self._ypos+self._height)
# 
#     def ygridpath(self, y, yaxis=None):
#         assert 0
#         if yaxis is None: yaxis = self.axes["y"]
#         v = yaxis.convert(y)
#         return path._line(self._xpos, self._ypos+v*self._height,
#                           self._xpos+self._width, self._ypos+v*self._height)
# 
#     def zgridpath(self, z, zaxis=None):
#         assert 0
#         if zaxis is None: zaxis = self.axes["z"]
#         v = zaxis.convert(z)
#         return path._line(self._xpos, self._zpos+v*self._height,
#                           self._xpos+self._width, self._zpos+v*self._height)
# 
#     def vxgridpath(self, v):
#         return path.path(path._moveto(*self._vpos(v, 0, 0)),
#                          path._lineto(*self._vpos(v, 0, 1)),
#                          path._lineto(*self._vpos(v, 1, 1)),
#                          path._lineto(*self._vpos(v, 1, 0)),
#                          path.closepath())
# 
#     def vygridpath(self, v):
#         return path.path(path._moveto(*self._vpos(0, v, 0)),
#                          path._lineto(*self._vpos(0, v, 1)),
#                          path._lineto(*self._vpos(1, v, 1)),
#                          path._lineto(*self._vpos(1, v, 0)),
#                          path.closepath())
# 
#     def vzgridpath(self, v):
#         return path.path(path._moveto(*self._vpos(0, 0, v)),
#                          path._lineto(*self._vpos(0, 1, v)),
#                          path._lineto(*self._vpos(1, 1, v)),
#                          path._lineto(*self._vpos(1, 0, v)),
#                          path.closepath())
# 
#     def _addpos(self, x, y, dx, dy):
#         assert 0
#         return x+dx, y+dy
# 
#     def _connect(self, x1, y1, x2, y2):
#         assert 0
#         return path._lineto(x2, y2)
# 
#     def doaxes(self):
#         self.dolayout()
#         if not self.removedomethod(self.doaxes): return
#         axesdist = unit.topt(unit.length(self.axesdist_str, default_type="v"))
#         XPattern = re.compile(r"%s([2-9]|[1-9][0-9]+)?$" % self.Names[0])
#         YPattern = re.compile(r"%s([2-9]|[1-9][0-9]+)?$" % self.Names[1])
#         ZPattern = re.compile(r"%s([2-9]|[1-9][0-9]+)?$" % self.Names[2])
#         items = list(self.axes.items())
#         items.sort() #TODO: alphabetical sorting breaks for axis numbers bigger than 9
#         for key, axis in items:
#             num = self.keynum(key)
#             num2 = 1 - num % 2 # x1 -> 0, x2 -> 1, x3 -> 0, x4 -> 1, ...
#             num3 = 1 - 2 * (num % 2) # x1 -> -1, x2 -> 1, x3 -> -1, x4 -> 1, ...
#             if XPattern.match(key):
#                 axis.vypos = 0
#                 axis.vzpos = 0
#                 axis._vtickpoint = self._vxtickpoint
#                 axis.vgridpath = self.vxgridpath
#                 axis.vbaseline = self.vxbaseline
#                 axis.vtickdirection = self.vxtickdirection
#             elif YPattern.match(key):
#                 axis.vxpos = 0
#                 axis.vzpos = 0
#                 axis._vtickpoint = self._vytickpoint
#                 axis.vgridpath = self.vygridpath
#                 axis.vbaseline = self.vybaseline
#                 axis.vtickdirection = self.vytickdirection
#             elif ZPattern.match(key):
#                 axis.vxpos = 0
#                 axis.vypos = 0
#                 axis._vtickpoint = self._vztickpoint
#                 axis.vgridpath = self.vzgridpath
#                 axis.vbaseline = self.vzbaseline
#                 axis.vtickdirection = self.vztickdirection
#             else:
#                 raise ValueError("Axis key '%s' not allowed" % key)
#             if axis.painter is not None:
#                 axis.dopaint(self)
# #            if XPattern.match(key):
# #                self._xaxisextents[num2] += axis._extent
# #                needxaxisdist[num2] = 1
# #            if YPattern.match(key):
# #                self._yaxisextents[num2] += axis._extent
# #                needyaxisdist[num2] = 1
# 
#     def __init__(self, tex, xpos=0, ypos=0, width=None, height=None, depth=None,
#                  phi=30, theta=30, distance=1,
#                  backgroundattrs=None, axesdist="0.8 cm", **axes):
#         canvas.canvas.__init__(self)
#         self.tex = tex
#         self.xpos = xpos
#         self.ypos = ypos
#         self._xpos = unit.topt(xpos)
#         self._ypos = unit.topt(ypos)
#         self._width = unit.topt(width)
#         self._height = unit.topt(height)
#         self._depth = unit.topt(depth)
#         self.width = width
#         self.height = height
#         self.depth = depth
#         if self._width <= 0: raise ValueError("width < 0")
#         if self._height <= 0: raise ValueError("height < 0")
#         if self._depth <= 0: raise ValueError("height < 0")
#         self._distance = distance*math.sqrt(self._width*self._width+
#                                             self._height*self._height+
#                                             self._depth*self._depth)
#         phi *= -math.pi/180
#         theta *= math.pi/180
#         self.a = (-math.sin(phi), math.cos(phi), 0)
#         self.b = (-math.cos(phi)*math.sin(theta),
#                   -math.sin(phi)*math.sin(theta),
#                   math.cos(theta))
#         self.eye = (self._distance*math.cos(phi)*math.cos(theta),
#                     self._distance*math.sin(phi)*math.cos(theta),
#                     self._distance*math.sin(theta))
#         self.initaxes(axes)
#         self.axesdist_str = axesdist
#         self.backgroundattrs = backgroundattrs
# 
#         self.data = []
#         self.domethods = [self.dolayout, self.dobackground, self.doaxes, self.dodata]
#         self.haslayout = 0
#         self.defaultstyle = {}
# 
#     def bbox(self):
#         self.finish()
#         return bbox.bbox(self._xpos - 200, self._ypos - 200, self._xpos + 200, self._ypos + 200)


################################################################################
# attr changers
################################################################################


#class _Ichangeattr:
#    """attribute changer
#       is an iterator for attributes where an attribute
#       is not refered by just a number (like for a sequence),
#       but also by the number of attributes requested
#       by calls of the next method (like for an color palette)
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
        for attr in helper.ensuresequence(attrs):
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
        for attr in helper.ensuresequence(attrs):
            if isinstance(attr, _changeattr):
                result.append(attr.iterate())
            else:
                result.append(attr)
        return result


class changecolor(changeattr):

    def __init__(self, palette):
        changeattr.__init__(self)
        self.palette = palette

    def attr(self, index):
        if self.counter != 1:
            return self.palette.getcolor(index/float(self.counter-1))
        else:
            return self.palette.getcolor(0)


class _changecolorgray(changecolor):

    def __init__(self, palette=color.palette.Gray):
        changecolor.__init__(self, palette)

_changecolorgrey = _changecolorgray


class _changecolorreversegray(changecolor):

    def __init__(self, palette=color.palette.ReverseGray):
        changecolor.__init__(self, palette)

_changecolorreversegrey = _changecolorreversegray


class _changecolorredblack(changecolor):

    def __init__(self, palette=color.palette.RedBlack):
        changecolor.__init__(self, palette)


class _changecolorblackred(changecolor):

    def __init__(self, palette=color.palette.BlackRed):
        changecolor.__init__(self, palette)


class _changecolorredwhite(changecolor):

    def __init__(self, palette=color.palette.RedWhite):
        changecolor.__init__(self, palette)


class _changecolorwhitered(changecolor):

    def __init__(self, palette=color.palette.WhiteRed):
        changecolor.__init__(self, palette)


class _changecolorgreenblack(changecolor):

    def __init__(self, palette=color.palette.GreenBlack):
        changecolor.__init__(self, palette)


class _changecolorblackgreen(changecolor):

    def __init__(self, palette=color.palette.BlackGreen):
        changecolor.__init__(self, palette)


class _changecolorgreenwhite(changecolor):

    def __init__(self, palette=color.palette.GreenWhite):
        changecolor.__init__(self, palette)


class _changecolorwhitegreen(changecolor):

    def __init__(self, palette=color.palette.WhiteGreen):
        changecolor.__init__(self, palette)


class _changecolorblueblack(changecolor):

    def __init__(self, palette=color.palette.BlueBlack):
        changecolor.__init__(self, palette)


class _changecolorblackblue(changecolor):

    def __init__(self, palette=color.palette.BlackBlue):
        changecolor.__init__(self, palette)


class _changecolorbluewhite(changecolor):

    def __init__(self, palette=color.palette.BlueWhite):
        changecolor.__init__(self, palette)


class _changecolorwhiteblue(changecolor):

    def __init__(self, palette=color.palette.WhiteBlue):
        changecolor.__init__(self, palette)


class _changecolorredgreen(changecolor):

    def __init__(self, palette=color.palette.RedGreen):
        changecolor.__init__(self, palette)


class _changecolorredblue(changecolor):

    def __init__(self, palette=color.palette.RedBlue):
        changecolor.__init__(self, palette)


class _changecolorgreenred(changecolor):

    def __init__(self, palette=color.palette.GreenRed):
        changecolor.__init__(self, palette)


class _changecolorgreenblue(changecolor):

    def __init__(self, palette=color.palette.GreenBlue):
        changecolor.__init__(self, palette)


class _changecolorbluered(changecolor):

    def __init__(self, palette=color.palette.BlueRed):
        changecolor.__init__(self, palette)


class _changecolorbluegreen(changecolor):

    def __init__(self, palette=color.palette.BlueGreen):
        changecolor.__init__(self, palette)


class _changecolorrainbow(changecolor):

    def __init__(self, palette=color.palette.Rainbow):
        changecolor.__init__(self, palette)


class _changecolorreverserainbow(changecolor):

    def __init__(self, palette=color.palette.ReverseRainbow):
        changecolor.__init__(self, palette)


class _changecolorhue(changecolor):

    def __init__(self, palette=color.palette.Hue):
        changecolor.__init__(self, palette)


class _changecolorreversehue(changecolor):

    def __init__(self, palette=color.palette.ReverseHue):
        changecolor.__init__(self, palette)


changecolor.Gray           = _changecolorgray
changecolor.Grey           = _changecolorgrey
changecolor.Reversegray    = _changecolorreversegray
changecolor.Reversegrey    = _changecolorreversegrey
changecolor.RedBlack       = _changecolorredblack
changecolor.BlackRed       = _changecolorblackred
changecolor.RedWhite       = _changecolorredwhite
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


class symbol:

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

    def __init__(self, symbol=helper.nodefault,
                       size="0.2 cm", symbolattrs=canvas.stroked(),
                       errorscale=0.5, errorbarattrs=(),
                       lineattrs=None):
        self.size_str = size
        if symbol is helper.nodefault:
            self._symbol = changesymbol.cross()
        else:
            self._symbol = symbol
        self._symbolattrs = symbolattrs
        self.errorscale = errorscale
        self._errorbarattrs = errorbarattrs
        self._lineattrs = lineattrs

    def iteratedict(self):
        result = {}
        result["symbol"] = _iterateattr(self._symbol)
        result["size"] = _iterateattr(self.size_str)
        result["symbolattrs"] = _iterateattrs(self._symbolattrs)
        result["errorscale"] = _iterateattr(self.errorscale)
        result["errorbarattrs"] = _iterateattrs(self._errorbarattrs)
        result["lineattrs"] = _iterateattrs(self._lineattrs)
        return result

    def iterate(self):
        return symbol(**self.iteratedict())

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
        self.xaxis = graph.axes[self.xkey]
        self.yaxis = graph.axes[self.ykey]

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

    def _drawsymbol(self, canvas, x, y, point=None):
        canvas.draw(path.path(*self.symbol(self, x, y)), *self.symbolattrs)

    def drawsymbol(self, canvas, x, y, point=None):
        self._drawsymbol(canvas, unit.topt(x), unit.topt(y), point)

    def drawpoints(self, graph, points):
        xaxismin, xaxismax = self.xaxis.getdatarange()
        yaxismin, yaxismax = self.yaxis.getdatarange()
        self.size = unit.length(_getattr(self.size_str), default_type="v")
        self._size = unit.topt(self.size)
        self.symbol = _getattr(self._symbol)
        self.symbolattrs = _getattrs(helper.ensuresequence(self._symbolattrs))
        self.errorbarattrs = _getattrs(helper.ensuresequence(self._errorbarattrs))
        self._errorsize = self.errorscale * self._size
        self.errorsize = self.errorscale * self.size
        self.lineattrs = _getattrs(helper.ensuresequence(self._lineattrs))
        if self._lineattrs is not None:
            clipcanvas = graph.clipcanvas()
        lineels = []
        haserror = filter(None, (self.xmini, self.ymini, self.xmaxi, self.ymaxi,
                                 self.dxi, self.dyi, self.dxmini, self.dymini, self.dxmaxi, self.dymaxi)) is not None
        moveto = 1
        for point in points:
            drawsymbol = 1
            xmin, x, xmax = self.minmidmax(point, self.xi, self.xmini, self.xmaxi, self.dxi, self.dxmini, self.dxmaxi)
            ymin, y, ymax = self.minmidmax(point, self.yi, self.ymini, self.ymaxi, self.dyi, self.dymini, self.dymaxi)
            if x is not None and x < xaxismin: drawsymbol = 0
            elif x is not None and x > xaxismax: drawsymbol = 0
            elif y is not None and y < yaxismin: drawsymbol = 0
            elif y is not None and y > yaxismax: drawsymbol = 0
            elif haserror:
                if xmin is not None and xmin < xaxismin: drawsymbol = 0
                elif xmax is not None and xmax < xaxismin: drawsymbol = 0
                elif xmax is not None and xmax > xaxismax: drawsymbol = 0
                elif xmin is not None and xmin > xaxismax: drawsymbol = 0
                elif ymin is not None and ymin < yaxismin: drawsymbol = 0
                elif ymax is not None and ymax < yaxismin: drawsymbol = 0
                elif ymax is not None and ymax > yaxismax: drawsymbol = 0
                elif ymin is not None and ymin > yaxismax: drawsymbol = 0
            xpos=ypos=topleft=top=topright=left=center=right=bottomleft=bottom=bottomright=None
            if x is not None and y is not None:
                try:
                    center = xpos, ypos = graph._pos(x, y, xaxis=self.xaxis, yaxis=self.yaxis)
                except (ValueError, OverflowError): # XXX: exceptions???
                    pass
            if haserror:
                if y is not None:
                    if xmin is not None: left = graph._pos(xmin, y, xaxis=self.xaxis, yaxis=self.yaxis)
                    if xmax is not None: right = graph._pos(xmax, y, xaxis=self.xaxis, yaxis=self.yaxis)
                if x is not None:
                    if ymax is not None: top = graph._pos(x, ymax, xaxis=self.xaxis, yaxis=self.yaxis)
                    if ymin is not None: bottom = graph._pos(x, ymin, xaxis=self.xaxis, yaxis=self.yaxis)
                if x is None or y is None:
                    if ymax is not None:
                        if xmin is not None: topleft = graph._pos(xmin, ymax, xaxis=self.xaxis, yaxis=self.yaxis)
                        if xmax is not None: topright = graph._pos(xmax, ymax, xaxis=self.xaxis, yaxis=self.yaxis)
                    if ymin is not None:
                        if xmin is not None: bottomleft = graph._pos(xmin, ymin, xaxis=self.xaxis, yaxis=self.yaxis)
                        if xmax is not None: bottomright = graph._pos(xmax, ymin, xaxis=self.xaxis, yaxis=self.yaxis)
            if drawsymbol:
                if self._errorbarattrs is not None and haserror:
                    self._drawerrorbar(graph, topleft, top, topright,
                                              left, center, right,
                                              bottomleft, bottom, bottomright, point)
                if self._symbolattrs is not None and xpos is not None and ypos is not None:
                    self._drawsymbol(graph, xpos, ypos, point)
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


class changesymbol(changesequence): pass


class _changesymbolcross(changesymbol):
    defaultsequence = (symbol.cross, symbol.plus, symbol.square, symbol.triangle, symbol.circle, symbol.diamond)


class _changesymbolplus(changesymbol):
    defaultsequence = (symbol.plus, symbol.square, symbol.triangle, symbol.circle, symbol.diamond, symbol.cross)


class _changesymbolsquare(changesymbol):
    defaultsequence = (symbol.square, symbol.triangle, symbol.circle, symbol.diamond, symbol.cross, symbol.plus)


class _changesymboltriangle(changesymbol):
    defaultsequence = (symbol.triangle, symbol.circle, symbol.diamond, symbol.cross, symbol.plus, symbol.square)


class _changesymbolcircle(changesymbol):
    defaultsequence = (symbol.circle, symbol.diamond, symbol.cross, symbol.plus, symbol.square, symbol.triangle)


class _changesymboldiamond(changesymbol):
    defaultsequence = (symbol.diamond, symbol.cross, symbol.plus, symbol.square, symbol.triangle, symbol.circle)


class _changesymbolsquaretwice(changesymbol):
    defaultsequence = (symbol.square, symbol.square, symbol.triangle, symbol.triangle,
                       symbol.circle, symbol.circle, symbol.diamond, symbol.diamond)


class _changesymboltriangletwice(changesymbol):
    defaultsequence = (symbol.triangle, symbol.triangle, symbol.circle, symbol.circle,
                       symbol.diamond, symbol.diamond, symbol.square, symbol.square)


class _changesymbolcircletwice(changesymbol):
    defaultsequence = (symbol.circle, symbol.circle, symbol.diamond, symbol.diamond,
                       symbol.square, symbol.square, symbol.triangle, symbol.triangle)


class _changesymboldiamondtwice(changesymbol):
    defaultsequence = (symbol.diamond, symbol.diamond, symbol.square, symbol.square,
                       symbol.triangle, symbol.triangle, symbol.circle, symbol.circle)


changesymbol.cross         = _changesymbolcross
changesymbol.plus          = _changesymbolplus
changesymbol.square        = _changesymbolsquare
changesymbol.triangle      = _changesymboltriangle
changesymbol.circle        = _changesymbolcircle
changesymbol.diamond       = _changesymboldiamond
changesymbol.squaretwice   = _changesymbolsquaretwice
changesymbol.triangletwice = _changesymboltriangletwice
changesymbol.circletwice   = _changesymbolcircletwice
changesymbol.diamondtwice  = _changesymboldiamondtwice


class line(symbol):

    def __init__(self, lineattrs=helper.nodefault):
        if lineattrs is helper.nodefault:
            lineattrs = (changelinestyle(), canvas.linejoin.round)
        symbol.__init__(self, symbolattrs=None, errorbarattrs=None, lineattrs=lineattrs)


class rect(symbol):

    def __init__(self, palette=color.palette.Gray):
        self.palette = palette
        self.colorindex = None
        symbol.__init__(self, symbolattrs=None, errorbarattrs=(), lineattrs=None)

    def iterate(self):
        raise RuntimeError("style is not iterateable")

    def othercolumnkey(self, key, index):
        if key == "color":
            self.colorindex = index
        else:
            symbol.othercolumnkey(self, key, index)

    def _drawerrorbar(self, graph, topleft, top, topright,
                                   left, center, right,
                                   bottomleft, bottom, bottomright, point=None):
        color = point[self.colorindex]
        if color is not None:
            if color != self.lastcolor:
                self.rectclipcanvas.set(self.palette.getcolor(color))
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
        symbol.drawpoints(self, graph, points)



class text(symbol):

    def __init__(self, textdx="0", textdy="0.3 cm", textattrs=textmodule.halign.center, **args):
        self.textindex = None
        self.textdx_str = textdx
        self.textdy_str = textdy
        self._textattrs = textattrs
        symbol.__init__(self, **args)

    def iteratedict(self):
        result = symbol.iteratedict()
        result["textattrs"] = _iterateattr(self._textattrs)
        return result

    def iterate(self):
        return textsymbol(**self.iteratedict())

    def othercolumnkey(self, key, index):
        if key == "text":
            self.textindex = index
        else:
            symbol.othercolumnkey(self, key, index)

    def _drawsymbol(self, graph, x, y, point=None):
        symbol._drawsymbol(self, graph, x, y, point)
        if None not in (x, y, point[self.textindex], self._textattrs):
            graph._text(x + self._textdx, y + self._textdy, str(point[self.textindex]), *helper.ensuresequence(self.textattrs))

    def drawpoints(self, graph, points):
        self.textdx = unit.length(_getattr(self.textdx_str), default_type="v")
        self.textdy = unit.length(_getattr(self.textdy_str), default_type="v")
        self._textdx = unit.topt(self.textdx)
        self._textdy = unit.topt(self.textdy)
        if self._textattrs is not None:
            self.textattrs = _getattr(self._textattrs)
        if self.textindex is None:
            raise RuntimeError("column 'text' not set")
        symbol.drawpoints(self, graph, points)


class arrow(symbol):

    def __init__(self, linelength="0.2 cm", arrowattrs=(), arrowsize="0.1 cm", arrowdict={}, epsilon=1e-10):
        self.linelength_str = linelength
        self.arrowsize_str = arrowsize
        self.arrowattrs = arrowattrs
        self.arrowdict = arrowdict
        self.epsilon = epsilon
        self.sizeindex = self.angleindex = None
        symbol.__init__(self, symbolattrs=(), errorbarattrs=None, lineattrs=None)

    def iterate(self):
        raise RuntimeError("style is not iterateable")

    def othercolumnkey(self, key, index):
        if key == "size":
            self.sizeindex = index
        elif key == "angle":
            self.angleindex = index
        else:
            symbol.othercolumnkey(self, key, index)

    def _drawsymbol(self, graph, x, y, point=None):
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
                             *helper.ensuresequence(self.arrowattrs))

    def drawpoints(self, graph, points):
        self.arrowsize = unit.length(_getattr(self.arrowsize_str), default_type="v")
        self.linelength = unit.length(_getattr(self.linelength_str), default_type="v")
        self._arrowsize = unit.topt(self.arrowsize)
        self._linelength = unit.topt(self.linelength)
        if self.sizeindex is None:
            raise RuntimeError("column 'size' not set")
        if self.angleindex is None:
            raise RuntimeError("column 'angle' not set")
        symbol.drawpoints(self, graph, points)


class _bariterator(changeattr):

    def attr(self, index):
        return index, self.counter


class bar:

    def __init__(self, fromzero=1, stacked=0, skipmissing=1, xbar=0,
                       barattrs=(canvas.stroked(color.gray.black), changecolor.Rainbow()),
                       _bariterator=_bariterator(), _previousbar=None):
        self.fromzero = fromzero
        self.stacked = stacked
        self.skipmissing = skipmissing
        self.xbar = xbar
        self._barattrs = barattrs
        self.bariterator = _bariterator
        self.previousbar = _previousbar

    def iteratedict(self):
        result = {}
        result["barattrs"] = _iterateattrs(self._barattrs)
        return result

    def iterate(self):
        return bar(fromzero=self.fromzero, stacked=self.stacked, xbar=self.xbar,
                   _bariterator=_iterateattr(self.bariterator), _previousbar=self, **self.iteratedict())

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

        xkey = ykey = None
        if len(graph.Names) != 2: raise TypeError("style not applicable in graph")
        XPattern = re.compile(r"(%s([2-9]|[1-9][0-9]+)?)$" % graph.Names[0])
        YPattern = re.compile(r"(%s([2-9]|[1-9][0-9]+)?)$" % graph.Names[1])
        xi = yi = None
        for key, index in columns.items():
            key, xkey, xi = checkpattern(key, index, XPattern, xkey, xi)
            key, ykey, yi = checkpattern(key, index, YPattern, ykey, yi)
            if key is not None:
                self.othercolumnkey(key, index)
        if None in (xkey, ykey): raise ValueError("incomplete axis specification")
        if self.xbar:
            self.nkey, self.ni = ykey, yi
            self.vkey, self.vi = xkey, xi
        else:
            self.nkey, self.ni = xkey, xi
            self.vkey, self.vi = ykey, yi
        self.naxis, self.vaxis = graph.axes[self.nkey], graph.axes[self.vkey]

    def getranges(self, points):
        index, count = _getattr(self.bariterator)
        if count != 1 and self.stacked != 1:
            if self.stacked > 1:
                index = divmod(index, self.stacked)[0] # TODO: use this

        vmin = vmax = None
        for point in points:
            if not self.skipmissing:
                if count == 1:
                    self.naxis.setname(point[self.ni])
                else:
                    self.naxis.setname(point[self.ni], index)
            try:
                v = point[self.vi] + 0.0
                if vmin is None or v < vmin: vmin = v
                if vmax is None or v > vmax: vmax = v
            except (TypeError, ValueError):
                pass
            else:
                if self.skipmissing:
                    if count == 1:
                        self.naxis.setname(point[self.ni])
                    else:
                        self.naxis.setname(point[self.ni], index)
        if self.fromzero:
            if vmin > 0: vmin = 0
            if vmax < 0: vmax = 0
        return {self.vkey: (vmin, vmax)}

    def drawpoints(self, graph, points):
        index, count = _getattr(self.bariterator)
        dostacked = (self.stacked != 0 and
                     (self.stacked == 1 or divmod(index, self.stacked)[1]) and
                     (self.stacked != 1 or index))
        if self.stacked > 1:
            index = divmod(index, self.stacked)[0]
        vmin, vmax = self.vaxis.getdatarange()
        self.barattrs = _getattrs(helper.ensuresequence(self._barattrs))
        if self.stacked:
            self.stackedvalue = {}
        for point in points:
            try:
                n = point[self.ni]
                v = point[self.vi]
                if self.stacked:
                    self.stackedvalue[n] = v
                if count != 1 and self.stacked != 1:
                    minid = (n, index, 0)
                    maxid = (n, index, 1)
                else:
                    minid = (n, 0)
                    maxid = (n, 1)
                if self.xbar:
                    x1pos, y1pos = graph._pos(v, minid, xaxis=self.vaxis, yaxis=self.naxis)
                    x2pos, y2pos = graph._pos(v, maxid, xaxis=self.vaxis, yaxis=self.naxis)
                else:
                    x1pos, y1pos = graph._pos(minid, v, xaxis=self.naxis, yaxis=self.vaxis)
                    x2pos, y2pos = graph._pos(maxid, v, xaxis=self.naxis, yaxis=self.vaxis)
                if dostacked:
                    if self.xbar:
                        x3pos, y3pos = graph._pos(self.previousbar.stackedvalue[n], maxid, xaxis=self.vaxis, yaxis=self.naxis)
                        x4pos, y4pos = graph._pos(self.previousbar.stackedvalue[n], minid, xaxis=self.vaxis, yaxis=self.naxis)
                    else:
                        x3pos, y3pos = graph._pos(maxid, self.previousbar.stackedvalue[n], xaxis=self.naxis, yaxis=self.vaxis)
                        x4pos, y4pos = graph._pos(minid, self.previousbar.stackedvalue[n], xaxis=self.naxis, yaxis=self.vaxis)
                else:
                    if self.fromzero:
                        if self.xbar:
                            x3pos, y3pos = graph._pos(0, maxid, xaxis=self.vaxis, yaxis=self.naxis)
                            x4pos, y4pos = graph._pos(0, minid, xaxis=self.vaxis, yaxis=self.naxis)
                        else:
                            x3pos, y3pos = graph._pos(maxid, 0, xaxis=self.naxis, yaxis=self.vaxis)
                            x4pos, y4pos = graph._pos(minid, 0, xaxis=self.naxis, yaxis=self.vaxis)
                    else:
                        x3pos, y3pos = self.naxis._vtickpoint(self.naxis, self.naxis.convert(maxid))
                        x4pos, y4pos = self.naxis._vtickpoint(self.naxis, self.naxis.convert(minid))
                graph.fill(path.path(path._moveto(x1pos, y1pos),
                                     graph._connect(x1pos, y1pos, x2pos, y2pos),
                                     graph._connect(x2pos, y2pos, x3pos, y3pos),
                                     graph._connect(x3pos, y3pos, x4pos, y4pos),
                                     graph._connect(x4pos, y4pos, x1pos, y1pos), # no closepath (might not be straight)
                                     path.closepath()), *self.barattrs)
            except (TypeError, ValueError): pass


#class surface:
#
#    def setcolumns(self, graph, columns):
#        self.columns = columns
#
#    def getranges(self, points):
#        return {"x": (0, 10), "y": (0, 10), "z": (0, 1)}
#
#    def drawpoints(self, graph, points):
#        pass



################################################################################
# data
################################################################################


class data:

    defaultstyle = symbol

    def __init__(self, file, title=helper.nodefault, context={}, **columns):
        self.title = title
        if helper.isstring(file):
            if title is helper.nodefault:
                self.title = file
            self.data = datamodule.datafile(file)
        else:
            self.data = file
            if title is helper.nodefault:
                self.title = "(unknown)"
        self.columns = {}
        for key, column in columns.items():
            try:
                self.columns[key] = self.data.getcolumnno(column)
            except datamodule.ColumnError:
                self.columns[key] = len(self.data.titles)
                self.data.addcolumn(column, context=context)

    def setstyle(self, graph, style):
        self.style = style
        self.style.setcolumns(graph, self.columns)

    def getranges(self):
        return self.style.getranges(self.data.data)

    def setranges(self, ranges):
        pass

    def draw(self, graph):
        self.style.drawpoints(graph, self.data.data)


class function:

    defaultstyle = line

    def __init__(self, expression, title=helper.nodefault, min=None, max=None, points=100, parser=mathtree.parser(), context={}):
        if title is helper.nodefault:
            self.title = expression
        else:
            self.title = title
        self.min = min
        self.max = max
        self.points = points
        self.context = context
        self.result, expression = expression.split("=")
        self.mathtree = parser.parse(expression)
        self.variable = None
        self.evalranges = 0

    def setstyle(self, graph, style):
        for variable in self.mathtree.VarList():
            if variable in graph.axes.keys():
                if self.variable is None:
                    self.variable = variable
                else:
                    raise ValueError("multiple variables found")
        if self.variable is None:
            raise ValueError("no variable found")
        self.xaxis = graph.axes[self.variable]
        self.style = style
        self.style.setcolumns(graph, {self.variable: 0, self.result: 1})

    def getranges(self):
        if self.evalranges:
            return self.style.getranges(self.data)
        if None not in (self.min, self.max):
            return {self.variable: (self.min, self.max)}

    def setranges(self, ranges):
        if ranges.has_key(self.variable):
            min, max = ranges[self.variable]
        if self.min is not None: min = self.min
        if self.max is not None: max = self.max
        vmin = self.xaxis.convert(min)
        vmax = self.xaxis.convert(max)
        self.data = []
        for i in range(self.points):
            self.context[self.variable] = x = self.xaxis.invert(vmin + (vmax-vmin)*i / (self.points-1.0))
            try:
                y = self.mathtree.Calc(**self.context)
            except (ArithmeticError, ValueError):
                y = None
            self.data.append((x, y))
        self.evalranges = 1

    def draw(self, graph):
        self.style.drawpoints(graph, self.data)


class paramfunction:

    defaultstyle = line

    def __init__(self, varname, min, max, expression, title=helper.nodefault, points=100, parser=mathtree.parser(), context={}):
        if title is helper.nodefault:
            self.title = expression
        else:
            self.title = title
        self.varname = varname
        self.min = min
        self.max = max
        self.points = points
        self.expression = {}
        self.mathtrees = {}
        varlist, expressionlist = expression.split("=")
        parsestr = mathtree.ParseStr(expressionlist)
        for key in varlist.split(","):
            key = key.strip()
            if self.mathtrees.has_key(key):
                raise ValueError("multiple assignment in tuple")
            try:
                self.mathtrees[key] = parser.ParseMathTree(parsestr)
                break
            except mathtree.CommaFoundMathTreeParseError, e:
                self.mathtrees[key] = e.MathTree
        else:
            raise ValueError("unpack tuple of wrong size")
        if len(varlist.split(",")) != len(self.mathtrees.keys()):
            raise ValueError("unpack tuple of wrong size")
        self.data = []
        for i in range(self.points):
            context[self.varname] = self.min + (self.max-self.min)*i / (self.points-1.0)
            line = []
            for key, tree in self.mathtrees.items():
                line.append(tree.Calc(**context))
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

