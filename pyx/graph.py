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


import re, math, string, sys
import bbox, box, canvas, path, unit, mathtree, color, helper
import text as textmodule
import data as datamodule
import trafo as trafomodule


goldenmean = 0.5 * (math.sqrt(5) + 1)


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
# partitioner
# please note the nomenclature:
# - a partition is a list of tick instances; to reduce name clashes, a
#   partition is called ticks
# - a partitioner is a class creating a single or several ticks
# - a axis has a part attribute where it stores a partitioner or/and some
#   (manually set) ticks -> the part attribute is used to create the ticks
#   in the axis finish method
################################################################################


class frac:
    """fraction class for rational arithmetics
    the axis partitioning uses rational arithmetics (with infinite accuracy)
    basically it contains self.enum and self.denom"""

    def stringfrac(self, s):
        "converts a string 0.123 into a frac"
        expparts = s.split("e")
        if len(expparts) > 2:
            raise ValueError("multiple 'e' found in '%s'" % s)
        commaparts = expparts[0].split(".")
        if len(commaparts) > 2:
            raise ValueError("multiple '.' found in '%s'" % expparts[0])
        if len(commaparts) == 1:
            commaparts = [commaparts[0], ""]
        result = frac((1, 10l), power=len(commaparts[1]))
        neg = len(commaparts[0]) and commaparts[0][0] == "-"
        if neg:
            commaparts[0] = commaparts[0][1:]
        elif len(commaparts[0]) and commaparts[0][0] == "+":
            commaparts[0] = commaparts[0][1:]
        if len(commaparts[0]):
            if not commaparts[0].isdigit():
                raise ValueError("unrecognized characters in '%s'" % s)
            x = long(commaparts[0])
        else:
            x = 0
        if len(commaparts[1]):
            if not commaparts[1].isdigit():
                raise ValueError("unrecognized characters in '%s'" % s)
            y = long(commaparts[1])
        else:
            y = 0
        result.enum = x*result.denom+y
        if neg:
            result.enum = -result.enum
        if len(expparts) == 2:
            neg = expparts[1][0] == "-"
            if neg:
                expparts[1] = expparts[1][1:]
            elif expparts[1][0] == "+":
                expparts[1] = expparts[1][1:]
            if not expparts[1].isdigit():
                raise ValueError("unrecognized characters in '%s'" % s)
            if neg:
                result *= frac((1, 10l),  power=long(expparts[1]))
            else:
                result *= frac((10, 1l),  power=long(expparts[1]))
        return result

    def floatfrac(self, x, floatprecision):
        "converts a float into a frac with final resolution"
        if helper.isinteger(floatprecision) and floatprecision < 0:
            # this would be extremly vulnerable
            raise RuntimeError("float resolution must be non-negative integer")
        return self.stringfrac(("%%.%ig" % floatprecision) % x)

    def __init__(self, x, power=None, floatprecision=10):
        "for power!=None: frac=(enum/denom)**power"
        if helper.isnumber(x):
            value = self.floatfrac(x, floatprecision)
            enum, denom = value.enum, value.denom
        elif helper.isstring(x):
            fraction = x.split("/")
            if len(fraction) > 2:
                raise ValueError("multiple '/' found in '%s'" % x)
            value = self.stringfrac(fraction[0])
            if len(fraction) == 2:
                value2 = self.stringfrac(fraction[1])
                value = value / value2
            enum, denom = value.enum, value.denom
        else:
            try:
                enum, denom = x
            except TypeError:
                enum, denom = x.enum, x.denom
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

    def __abs__(self):
        return frac((abs(self.enum), abs(self.denom)))

    def __mul__(self, other):
        return frac((self.enum * other.enum, self.denom * other.denom))

    def __div__(self, other):
        return frac((self.enum * other.denom, self.denom * other.enum))

    def __float__(self):
        "caution: avoid final precision of floats"
        return float(self.enum) / self.denom

    def __str__(self):
        return "%i/%i" % (self.enum, self.denom)


class tick(frac):
    """tick class
    a tick is a frac enhanced by
    - self.ticklevel (0 = tick, 1 = subtick, etc.)
    - self.labellevel (0 = label, 1 = sublabel, etc.)
    - self.label (a string) and self.labelattrs (a list, defaults to [])
    When ticklevel or labellevel is None, no tick or label is present at that value.
    When label is None, it should be automatically created (and stored), once the
    an axis painter needs it. Classes, which implement _Itexter do precisely that."""

    def __init__(self, pos, ticklevel=0, labellevel=0, label=None, labelattrs=[], **kwargs):
        """initializes the instance
        - see class description for the parameter description
        - **kwargs are passed to the frac constructor"""
        frac.__init__(self, pos, **kwargs)
        self.ticklevel = ticklevel
        self.labellevel = labellevel
        self.label = label
        self.labelattrs = helper.ensurelist(labelattrs)[:]

    def merge(self, other):
        """merges two ticks together:
          - the lower ticklevel/labellevel wins
          - the label is *never* taken over from other
          - the ticks should be at the same position (otherwise it doesn't make sense)
            -> this is NOT checked"""
        if self.ticklevel is None or (other.ticklevel is not None and other.ticklevel < self.ticklevel):
            self.ticklevel = other.ticklevel
        if self.labellevel is None or (other.labellevel is not None and other.labellevel < self.labellevel):
            self.labellevel = other.labellevel

    def __repr__(self):
        return "tick(%r, %r, %s, %s, %s)" % (self.enum, self.denom, self.ticklevel, self.labellevel, self.label)


def _mergeticklists(list1, list2):
    """helper function to merge tick lists
    - return a merged list of ticks out of list1 and list2
    - CAUTION: original lists have to be ordered
      (the returned list is also ordered)
    - CAUTION: original lists are modified and they share references to
      the result list!"""
    # TODO: improve this using bisect?!
    if list1 is None: return list2
    if list2 is None: return list1
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


def _mergelabels(ticks, labels):
    """helper function to merge labels into ticks
    - when labels is not None, the label of all ticks with
      labellevel different from None are set
    - labels need to be a sequence of sequences of strings,
      where the first sequence contain the strings to be
      used as labels for the ticks with labellevel 0,
      the second sequence for labellevel 1, etc.
    - when the maximum labellevel is 0, just a sequence of
      strings might be provided as the labels argument
    - IndexError is raised, when a sequence length doesn't match"""
    if helper.issequenceofsequences(labels):
        for label, level in zip(labels, xrange(sys.maxint)):
            usetext = helper.ensuresequence(label)
            i = 0
            for tick in ticks:
                if tick.labellevel == level:
                    tick.label = usetext[i]
                    i += 1
            if i != len(usetext):
                raise IndexError("wrong sequence length of labels at level %i" % level)
    elif labels is not None:
        usetext = helper.ensuresequence(labels)
        i = 0
        for tick in ticks:
            if tick.labellevel == 0:
                tick.label = usetext[i]
                i += 1
        if i != len(usetext):
            raise IndexError("wrong sequence length of labels")


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

    def __init__(self, tickpos=None, labelpos=None, labels=None, mix=()):
        """configuration of the partition scheme
        - tickpos and labelpos should be a sequence of sequences, where
          the first sequence contains the values to be used for
          ticks with ticklevel/labellevel 0, the second sequence for
          ticklevel/labellevel 1, etc.
        - tickpos and labelpos values are passed to the frac constructor
        - when the maximum ticklevel/labellevel is 0, just a sequence
          might be provided in tickpos and labelpos
        - when labelpos is None and tickpos is not None, the tick entries
          for ticklevel 0 are used for labels and vice versa (ticks<->labels)
        - labels are applied to the resulting partition via the
          mergelabels function (additional information available there)
        - mix specifies another partition to be merged into the
          created partition"""
        if tickpos is None and labelpos is not None:
            self.tickpos = helper.ensuresequence(helper.getsequenceno(labelpos, 0))
        else:
            self.tickpos = tickpos
        if labelpos is None and tickpos is not None:
            self.labelpos = helper.ensuresequence(helper.getsequenceno(tickpos, 0))
        else:
            self.labelpos = labelpos
        self.labels = labels
        self.mix = mix

    def checkfraclist(self, *fracs):
        "orders a list of fracs, equal entries are not allowed"
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
        if helper.issequenceofsequences(self.tickpos):
            for fracs, level in zip(self.tickpos, xrange(sys.maxint)):
                ticks = _mergeticklists(ticks, [tick((f.enum, f.denom), ticklevel=level, labellevel=None)
                                                for f in self.checkfraclist(*map(frac, helper.ensuresequence(fracs)))])
        else:
            map(frac, helper.ensuresequence(self.tickpos))
            ticks = _mergeticklists(ticks, [tick((f.enum, f.denom), ticklevel=0, labellevel=None)
                                            for f in self.checkfraclist(*map(frac, helper.ensuresequence(self.tickpos)))])

        if helper.issequenceofsequences(self.labelpos):
            for fracs, level in zip(self.labelpos, xrange(sys.maxint)):
                ticks = _mergeticklists(ticks, [tick((f.enum, f.denom), ticklevel=None, labellevel = level)
                                                for f in self.checkfraclist(*map(frac, helper.ensuresequence(fracs)))])
        else:
            ticks = _mergeticklists(ticks, [tick((f.enum, f.denom), ticklevel=None, labellevel = 0)
                                            for f in self.checkfraclist(*map(frac, helper.ensuresequence(self.labelpos)))])

        _mergelabels(ticks, self.labels)

        return ticks

    def defaultpart(self, min, max, extendmin, extendmax):
        # XXX: we do not take care of the parameters -> correct?
        return self.part()

    def lesspart(self):
        return None

    def morepart(self):
        return None


class linpart:
    """linear partition scheme
    ticks and label distances are explicitly provided to the constructor"""

    __implements__ = _Ipart

    def __init__(self, tickdist=None, labeldist=None, labels=None, extendtick=0, extendlabel=None, epsilon=1e-10, mix=()):
        """configuration of the partition scheme
        - tickdist and labeldist should be a sequence, where the first value
          is the distance between ticks with ticklevel/labellevel 0,
          the second sequence for ticklevel/labellevel 1, etc.;
          a single entry is allowed without being a sequence
        - tickdist and labeldist values are passed to the frac constructor
        - when labeldist is None and tickdist is not None, the tick entries
          for ticklevel 0 are used for labels and vice versa (ticks<->labels)
        - labels are applied to the resulting partition via the
          mergelabels function (additional information available there)
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
        if tickdist is None and labeldist is not None:
            self.ticklist = (frac(helper.ensuresequence(labeldist)[0]),)
        else:
            self.ticklist = map(frac, helper.ensuresequence(tickdist))
        if labeldist is None and tickdist is not None:
            self.labellist = (frac(helper.ensuresequence(tickdist)[0]),)
        else:
            self.labellist = map(frac, helper.ensuresequence(labeldist))
        self.labels = labels
        self.extendtick = extendtick
        self.extendlabel = extendlabel
        self.epsilon = epsilon
        self.mix = mix

    def extendminmax(self, min, max, frac, extendmin, extendmax):
        """return new min, max tuple extending the range min, max
        - frac is the tick distance to be used
        - extendmin and extendmax are booleans to allow for the extension"""
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
            ticks.append(tick((long(i) * frac.enum, frac.denom), ticklevel=ticklevel, labellevel=labellevel))
        return ticks

    def defaultpart(self, min, max, extendmin, extendmax):
        if self.extendtick is not None and len(self.ticklist) > self.extendtick:
            min, max = self.extendminmax(min, max, self.ticklist[self.extendtick], extendmin, extendmax)
        if self.extendlabel is not None and len(self.labellist) > self.extendlabel:
            min, max = self.extendminmax(min, max, self.labellist[self.extendlabel], extendmin, extendmax)

        ticks = list(self.mix)
        for i in range(len(self.ticklist)):
            ticks = _mergeticklists(ticks, self.getticks(min, max, self.ticklist[i], ticklevel = i))
        for i in range(len(self.labellist)):
            ticks = _mergeticklists(ticks, self.getticks(min, max, self.labellist[i], labellevel = i))

        _mergelabels(ticks, self.labels)

        return ticks

    def lesspart(self):
        return None

    def morepart(self):
        return None


class autolinpart:
    """automatic linear partition scheme
    - possible tick distances are explicitly provided to the constructor
    - tick distances are adjusted to the axis range by multiplication or division by 10"""

    __implements__ = _Ipart

    defaultvariants = ((frac((1, 1)), frac((1, 2))),
                       (frac((2, 1)), frac((1, 1))),
                       (frac((5, 2)), frac((5, 4))),
                       (frac((5, 1)), frac((5, 2))))

    def __init__(self, variants=defaultvariants, extendtick=0, epsilon=1e-10, mix=()):
        """configuration of the partition scheme
        - variants is a sequence of tickdist
        - tickdist should be a sequence, where the first value
          is the distance between ticks with ticklevel 0,
          the second for ticklevel 1, etc.
        - tickdist values are passed to the frac constructor
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
        self.variants = variants
        self.extendtick = extendtick
        self.epsilon = epsilon
        self.mix = mix

    def defaultpart(self, min, max, extendmin, extendmax):
        logmm = math.log(max - min) / math.log(10)
        if logmm < 0: # correction for rounding towards zero of the int routine
            base = frac((10L, 1), int(logmm - 1))
        else:
            base = frac((10L, 1), int(logmm))
        ticks = map(frac, self.variants[0])
        useticks = [tick * base for tick in ticks]
        self.lesstickindex = self.moretickindex = 0
        self.lessbase = frac((base.enum, base.denom))
        self.morebase = frac((base.enum, base.denom))
        self.min, self.max, self.extendmin, self.extendmax = min, max, extendmin, extendmax
        part = linpart(tickdist=useticks, extendtick=self.extendtick, epsilon=self.epsilon, mix=self.mix)
        return part.defaultpart(self.min, self.max, self.extendmin, self.extendmax)

    def lesspart(self):
        if self.lesstickindex < len(self.variants) - 1:
            self.lesstickindex += 1
        else:
            self.lesstickindex = 0
            self.lessbase.enum *= 10
        ticks = map(frac, self.variants[self.lesstickindex])
        useticks = [tick * self.lessbase for tick in ticks]
        part = linpart(tickdist=useticks, extendtick=self.extendtick, epsilon=self.epsilon, mix=self.mix)
        return part.defaultpart(self.min, self.max, self.extendmin, self.extendmax)

    def morepart(self):
        if self.moretickindex:
            self.moretickindex -= 1
        else:
            self.moretickindex = len(self.variants) - 1
            self.morebase.denom *= 10
        ticks = map(frac, self.variants[self.moretickindex])
        useticks = [tick * self.morebase for tick in ticks]
        part = linpart(tickdist=useticks, extendtick=self.extendtick, epsilon=self.epsilon, mix=self.mix)
        return part.defaultpart(self.min, self.max, self.extendmin, self.extendmax)


class preexp:
    """storage class for the definition of logarithmic axes partitions
    instances of this class define tick positions suitable for
    logarithmic axes by the following instance variables:
    - exp: integer, which defines multiplicator (usually 10)
    - pres: sequence of tick positions (rational numbers, e.g. instances of frac)
    possible positions are these tick positions and arbitrary divisions
    and multiplications by the exp value"""

    def __init__(self, pres, exp):
         "create a preexp instance and store its pres and exp information"
         self.pres = helper.ensuresequence(pres)
         self.exp = exp


class logpart(linpart):
    """logarithmic partition scheme
    ticks and label positions are explicitly provided to the constructor"""

    __implements__ = _Ipart

    pre1exp5   = preexp(frac((1, 1)), 100000)
    pre1exp4   = preexp(frac((1, 1)), 10000)
    pre1exp3   = preexp(frac((1, 1)), 1000)
    pre1exp2   = preexp(frac((1, 1)), 100)
    pre1exp    = preexp(frac((1, 1)), 10)
    pre125exp  = preexp((frac((1, 1)), frac((2, 1)), frac((5, 1))), 10)
    pre1to9exp = preexp(map(lambda x: frac((x, 1)), range(1, 10)), 10)
    #  ^- we always include 1 in order to get extendto(tick|label)level to work as expected

    def __init__(self, tickpos=None, labelpos=None, labels=None, extendtick=0, extendlabel=None, epsilon=1e-10, mix=()):
        """configuration of the partition scheme
        - tickpos and labelpos should be a sequence, where the first entry
          is a preexp instance describing ticks with ticklevel/labellevel 0,
          the second is a preexp instance for ticklevel/labellevel 1, etc.;
          a single entry is allowed without being a sequence
        - when labelpos is None and tickpos is not None, the tick entries
          for ticklevel 0 are used for labels and vice versa (ticks<->labels)
        - labels are applied to the resulting partition via the
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
        if tickpos is None and labels is not None:
            self.ticklist = (helper.ensuresequence(labelpos)[0],)
        else:
            self.ticklist = helper.ensuresequence(tickpos)

        if labelpos is None and tickpos is not None:
            self.labellist = (helper.ensuresequence(tickpos)[0],)
        else:
            self.labellist = helper.ensuresequence(labelpos)
        self.labels = labels
        self.extendtick = extendtick
        self.extendlabel = extendlabel
        self.epsilon = epsilon
        self.mix = mix

    def extendminmax(self, min, max, preexp, extendmin, extendmax):
        """return new min, max tuple extending the range min, max
        preexp describes the allowed tick positions
        extendmin and extendmax are booleans to allow for the extension"""
        minpower = None
        maxpower = None
        for i in xrange(len(preexp.pres)):
            imin = int(math.floor(math.log(min / float(preexp.pres[i])) /
                                  math.log(preexp.exp) + self.epsilon)) + 1
            imax = int(math.ceil(math.log(max / float(preexp.pres[i])) /
                                 math.log(preexp.exp) - self.epsilon)) - 1
            if minpower is None or imin < minpower:
                minpower, minindex = imin, i
            if maxpower is None or imax >= maxpower:
                maxpower, maxindex = imax, i
        if minindex:
            minfrac = preexp.pres[minindex - 1]
        else:
            minfrac = preexp.pres[-1]
            minpower -= 1
        if maxindex != len(preexp.pres) - 1:
            maxfrac = preexp.pres[maxindex + 1]
        else:
            maxfrac = preexp.pres[0]
            maxpower += 1
        if extendmin:
            min = float(minfrac) * float(preexp.exp) ** minpower
        if extendmax:
            max = float(maxfrac) * float(preexp.exp) ** maxpower
        return min, max

    def getticks(self, min, max, preexp, ticklevel=None, labellevel=None):
        """return a list of ticks
        - preexp describes the allowed tick positions
        - the ticklevel of the ticks is set to ticklevel and
          the labellevel is set to labellevel
        -  min, max is the range where ticks should be placed"""
        ticks = list(self.mix)
        minimin = 0
        maximax = 0
        for f in preexp.pres:
            fracticks = []
            imin = int(math.ceil(math.log(min / float(f)) /
                                 math.log(preexp.exp) - 0.5 * self.epsilon))
            imax = int(math.floor(math.log(max / float(f)) /
                                  math.log(preexp.exp) + 0.5 * self.epsilon))
            for i in range(imin, imax + 1):
                pos = f * frac((preexp.exp, 1), i)
                fracticks.append(tick((pos.enum, pos.denom), ticklevel = ticklevel, labellevel = labellevel))
            ticks = _mergeticklists(ticks, fracticks)
        return ticks


class autologpart(logpart):
    """automatic logarithmic partition scheme
    possible tick positions are explicitly provided to the constructor"""

    __implements__ = _Ipart

    defaultvariants = (((logpart.pre1exp,      # ticks
                         logpart.pre1to9exp),  # subticks
                        (logpart.pre1exp,      # labels
                         logpart.pre125exp)),  # sublevels

                       ((logpart.pre1exp,      # ticks
                         logpart.pre1to9exp),  # subticks
                        None),                 # labels like ticks

                       ((logpart.pre1exp2,     # ticks
                         logpart.pre1exp),     # subticks
                        None),                 # labels like ticks

                       ((logpart.pre1exp3,     # ticks
                         logpart.pre1exp),     # subticks
                        None),                 # labels like ticks

                       ((logpart.pre1exp4,     # ticks
                         logpart.pre1exp),     # subticks
                        None),                 # labels like ticks

                       ((logpart.pre1exp5,     # ticks
                         logpart.pre1exp),     # subticks
                        None))                 # labels like ticks

    def __init__(self, variants=defaultvariants, extendtick=0, extendlabel=None, epsilon=1e-10, mix=()):
        """configuration of the partition scheme
        - variants should be a sequence of pairs of sequences of preexp
          instances
        - within each pair the first sequence contains preexp, where
          the first preexp instance describes ticks positions with
          ticklevel 0, the second preexp for ticklevel 1, etc.
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
        self.variants = variants
        if len(variants) > 2:
            self.variantsindex = divmod(len(variants), 2)[0]
        else:
            self.variantsindex = 0
        self.extendtick = extendtick
        self.extendlabel = extendlabel
        self.epsilon = epsilon
        self.mix = mix

    def defaultpart(self, min, max, extendmin, extendmax):
        self.min, self.max, self.extendmin, self.extendmax = min, max, extendmin, extendmax
        self.morevariantsindex = self.variantsindex
        self.lessvariantsindex = self.variantsindex
        part = logpart(tickpos=self.variants[self.variantsindex][0], labelpos=self.variants[self.variantsindex][1],
                       extendtick=self.extendtick, extendlabel=self.extendlabel, epsilon=self.epsilon, mix=self.mix)
        return part.defaultpart(self.min, self.max, self.extendmin, self.extendmax)

    def lesspart(self):
        self.lessvariantsindex += 1
        if self.lessvariantsindex < len(self.variants):
            part = logpart(tickpos=self.variants[self.lessvariantsindex][0], labelpos=self.variants[self.lessvariantsindex][1],
                           extendtick=self.extendtick, extendlabel=self.extendlabel, epsilon=self.epsilon, mix=self.mix)
            return part.defaultpart(self.min, self.max, self.extendmin, self.extendmax)

    def morepart(self):
        self.morevariantsindex -= 1
        if self.morevariantsindex >= 0:
            part = logpart(tickpos=self.variants[self.morevariantsindex][0], labelpos=self.variants[self.morevariantsindex][1],
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


class cuberater:
    """a value rater
    - a cube rater has an optimal value, where the rate becomes zero
    - for a left (below the optimum) and a right value (above the optimum),
      the rating is value is set to 1 (modified by an overall weight factor
      for the rating)
    - the analytic form of the rating is cubic for both, the left and
      the right side of the rater, independently"""

    # __implements__ = sole implementation

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

    def rate(self, value, density):
        """returns a rating for a value
        - the density lineary rescales the rater (the optimum etc.),
          e.g. a value bigger than one increases the optimum (when it is
          positive) and a value lower than one decreases the optimum (when
          it is positive); the density itself should be positive"""
        opt = self.opt * density
        if value < opt:
            other = self.left * density
        elif value > opt:
            other = self.right * density
        else:
            return 0
        factor = (value - opt) / float(other - opt)
        return self.weight * (factor ** 3)


class distancerater:
    # TODO: update docstring
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

    # __implements__ = sole implementation

    def __init__(self, opt, weight=0.1):
        """inititializes the rater
        - opt is the optimal length (a visual PyX length)
        - weight should be positive and is a factor multiplicated to the rates"""
        self.opt_str = opt
        self.weight = weight

    def rate(self, distances, density):
        """rate distances
        - the distances are a sequence of positive floats in PostScript points
        - the density lineary rescales the rater (the optimum etc.),
          e.g. a value bigger than one increases the optimum (when it is
          positive) and a value lower than one decreases the optimum (when
          it is positive); the density itself should be positive"""
        if len(distances):
            opt = unit.topt(unit.length(self.opt_str, default_type="v")) / density
            rate = 0
            for distance in distances:
                if distance < opt:
                    rate += self.weight * (opt / distance - 1)
                else:
                    rate += self.weight * (distance / opt - 1)
            return rate / float(len(distances))


class axisrater:
    """a rater for ticks
    - the rating of axes is splited into two separate parts:
      - rating of the ticks in terms of the number of ticks, subticks,
        labels, etc.
      - rating of the label distances
    - in the end, a rate for ticks is the sum of these rates
    - it is useful to first just rate the number of ticks etc.
      and selecting those partitions, where this fits well -> as soon
      as an complete rate (the sum of both parts from the list above)
      of a first ticks is below a rate of just the number of ticks,
      subticks labels etc. of other ticks, those other ticks will never
      be better than the first one -> we gain speed by minimizing the
      number of ticks, where label distances have to be taken into account)
    - both parts of the rating are shifted into instances of raters
      defined above --- right now, there is not yet a strict interface
      for this delegation (should be done as soon as it is needed)"""

    # __implements__ = sole implementation

    linticks = (cuberater(4), cuberater(10, weight=0.5), )
    linlabels = (cuberater(4), )
    logticks = (cuberater(5, right=20), cuberater(20, right=100, weight=0.5), )
    loglabels = (cuberater(5, right=20), cuberater(5, left=-20, right=20, weight=0.5), )
    stdtickrange = cuberater(1, weight=2)
    stddistance = distancerater("1 cm")

    def __init__(self, ticks=linticks, labels=linlabels, tickrange=stdtickrange, distance=stddistance):
        """initializes the axis rater
        - ticks and labels are lists of instances of a value rater
        - the first entry in ticks rate the number of ticks, the
          second the number of subticks, etc.; when there are no
          ticks of a level or there is not rater for a level, the
          level is just ignored
        - labels is analogous, but for labels
        - within the rating, all ticks with a higher level are
          considered as ticks for a given level
        - tickrange is a value rater instance, which rates the covering
          of an axis range by the ticks (as a relative value of the
          tick range vs. the axis range), ticks might cover less or
          more than the axis range (for the standard automatic axis
          partition schemes an extention of the axis range is normal
          and should get some penalty)
        - distance is an distance rater instance"""
        self.rateticks = ticks
        self.ratelabels = labels
        self.tickrange = tickrange
        self.distance = distance

    def ratepart(self, axis, ticks, density):
        """rates ticks by the number of ticks, subticks, labels etc.
        - takes into account the number of ticks, subticks, labels
          etc. and the coverage of the axis range by the ticks
        - when there are no ticks of a level or there was not rater
          given in the constructor for a level, the level is just
          ignored
        - the method returns the sum of the rating results divided
          by the sum of the weights of the raters
        - within the rating, all ticks with a higher level are
          considered as ticks for a given level"""
        maxticklevel = maxlabellevel = 0
        for tick in ticks:
            if tick.ticklevel >= maxticklevel:
                maxticklevel = tick.ticklevel + 1
            if tick.labellevel >= maxlabellevel:
                maxlabellevel = tick.labellevel + 1
        numticks = [0]*maxticklevel
        numlabels = [0]*maxlabellevel
        for tick in ticks:
            if tick.ticklevel is not None:
                for level in range(tick.ticklevel, maxticklevel):
                    numticks[level] += 1
            if tick.labellevel is not None:
                for level in range(tick.labellevel, maxlabellevel):
                    numlabels[level] += 1
        rate = 0
        weight = 0
        for numtick, rater in zip(numticks, self.rateticks):
            rate += rater.rate(numtick, density)
            weight += rater.weight
        for numlabel, rater in zip(numlabels, self.ratelabels):
            rate += rater.rate(numlabel, density)
            weight += rater.weight
        if len(ticks):
            # XXX: tickrange was not yet applied
            rate += self.tickrange.rate(axis.convert(float(ticks[-1]) * axis.divisor) -
                                        axis.convert(float(ticks[0]) * axis.divisor), 1)
        else:
            rate += self.tickrange.rate(0)
        weight += self.tickrange.weight
        return rate/weight

    def ratelayout(self, axiscanvas, density):
        """rate distances of the labels in an axis canvas
        - the distances should be collected as box distances of
          subsequent labels
        - the axiscanvas provides a labels attribute for easy
          access to the labels whose distances have to be taken
          into account
        - the density is used within the distancerate instance"""
        if len(axiscanvas.labels) > 1:
            try:
                distances = [axiscanvas.labels[i]._boxdistance(axiscanvas.labels[i+1]) for i in range(len(axiscanvas.labels) - 1)]
            except box.BoxCrossError:
                return None
            return self.distance.rate(distances, density)
        else:
            return 0


################################################################################
# texter
# texter automatically create labels for tick instances
################################################################################


class _Itexter:

    def labels(self, ticks):
        """fill the label attribute of ticks
        - ticks is a list of instances of tick
        - for each element of ticks the value of the attribute label is set to
          a string appropriate to the attributes enum and denom of that tick
          instance
        - label attributes of the tick instances are just kept, whenever they
          are not equal to None
        - the method might extend the labelattrs attribute of the ticks"""


class rationaltexter:
    "a texter creating rational labels (e.g. 'a/b' or even 'a \over b')"
    # XXX: we use divmod here to be more expicit

    __implements__ = _Itexter

    def __init__(self, prefix="", infix="", suffix="",
                       enumprefix="", enuminfix="", enumsuffix="",
                       denomprefix="", denominfix="", denomsuffix="",
                       minus="-", minuspos=0, over=r"{{%s}\over{%s}}",
                       equaldenom=0, skip1=1, skipenum0=1, skipenum1=1, skipdenom1=1,
                       labelattrs=textmodule.mathmode):
        r"""initializes the instance
        - prefix, infix, and suffix (strings) are added at the begin,
          immediately after the minus, and at the end of the label,
          respectively
        - prefixenum, infixenum, and suffixenum (strings) are added
          to the labels enumerator correspondingly
        - prefixdenom, infixdenom, and suffixdenom (strings) are added
          to the labels denominator correspondingly
        - minus (string) is inserted for negative numbers
        - minuspos is an integer, which determines the position, where the
          minus sign has to be placed; the following values are allowed:
            1 - writes the minus in front of the enumerator
            0 - writes the minus in front of the hole fraction
           -1 - writes the minus in front of the denominator
        - over (string) is taken as a format string generating the
          fraction bar; it has to contain exactly two string insert
          operators "%s" -- the first for the enumerator and the second
          for the denominator; by far the most common examples are
          r"{{%s}\over{%s}}" and "{{%s}/{%s}}"
        - usually the enumerator and denominator are canceled; however,
          when equaldenom is set, the least common multiple of all
          denominators is used
        - skip1 (boolean) just prints the prefix, the minus (if present),
          the infix and the suffix, when the value is plus or minus one
          and at least one of prefix, infix and the suffix is present
        - skipenum0 (boolean) just prints a zero instead of
          the hole fraction, when the enumerator is zero;
          no prefixes, infixes, and suffixes are taken into account
        - skipenum1 (boolean) just prints the enumprefix, the minus (if present),
          the enuminfix and the enumsuffix, when the enum value is plus or minus one
          and at least one of enumprefix, enuminfix and the enumsuffix is present
        - skipdenom1 (boolean) just prints the enumerator instead of
          the hole fraction, when the denominator is one and none of the parameters
          denomprefix, denominfix and denomsuffix are set and minuspos is not -1 or the
          fraction is positive
        - labelattrs is a sequence of attributes for a texrunners text method;
          a single is allowed without being a sequence; None is considered as
          an empty sequence"""
        self.prefix = prefix
        self.infix = infix
        self.suffix = suffix
        self.enumprefix = enumprefix
        self.enuminfix = enuminfix
        self.enumsuffix = enumsuffix
        self.denomprefix = denomprefix
        self.denominfix = denominfix
        self.denomsuffix = denomsuffix
        self.minus = minus
        self.minuspos = minuspos
        self.over = over
        self.equaldenom = equaldenom
        self.skip1 = skip1
        self.skipenum0 = skipenum0
        self.skipenum1 = skipenum1
        self.skipdenom1 = skipdenom1
        self.labelattrs = helper.ensurelist(labelattrs)

    def gcd(self, *n):
        """returns the greates common divisor of all elements in n
        - the elements of n must be non-negative integers
        - return None if the number of elements is zero
        - the greates common divisor is not affected when some
          of the elements are zero, but it becomes zero when
          all elements are zero"""
        if len(n) == 2:
            i, j = n
            if i < j:
                i, j = j, i
            while j > 0:
                i, (dummy, j) = j, divmod(i, j)
            return i
        if len(n):
            res = n[0]
            for i in n[1:]:
                res = self.gcd(res, i)
            return res

    def lcm(self, *n):
        """returns the least common multiple of all elements in n
        - the elements of n must be non-negative integers
        - return None if the number of elements is zero
        - the least common multiple is zero when some of the
          elements are zero"""
        if len(n):
            res = n[0]
            for i in n[1:]:
                res = divmod(res * i, self.gcd(res, i))[0]
            return res

    def labels(self, ticks):
        labeledticks = []
        for tick in ticks:
            if tick.label is None and tick.labellevel is not None:
                labeledticks.append(tick)
                tick.temp_fracenum = tick.enum
                tick.temp_fracdenom = tick.denom
                tick.temp_fracminus = 1
                if tick.temp_fracenum < 0:
                    tick.temp_fracminus *= -1
                    tick.temp_fracenum *= -1
                if tick.temp_fracdenom < 0:
                    tick.temp_fracminus *= -1
                    tick.temp_fracdenom *= -1
                gcd = self.gcd(tick.temp_fracenum, tick.temp_fracdenom)
                (tick.temp_fracenum, dummy1), (tick.temp_fracdenom, dummy2) = divmod(tick.temp_fracenum, gcd), divmod(tick.temp_fracdenom, gcd)
        if self.equaldenom:
            equaldenom = self.lcm(*[tick.temp_fracdenom for tick in ticks if tick.label is None])
            if equaldenom is not None:
                for tick in labeledticks:
                    factor, dummy = divmod(equaldenom, tick.temp_fracdenom)
                    tick.temp_fracenum, tick.temp_fracdenom = factor * tick.temp_fracenum, factor * tick.temp_fracdenom
        for tick in labeledticks:
            fracminus = fracenumminus = fracdenomminus = ""
            if tick.temp_fracminus == -1:
                if self.minuspos == 0:
                    fracminus = self.minus
                elif self.minuspos == 1:
                    fracenumminus = self.minus
                elif self.minuspos == -1:
                    fracdenomminus = self.minus
                else:
                    raise RuntimeError("invalid minuspos")
            if self.skipenum0 and tick.temp_fracenum == 0:
                tick.label = "0"
            elif (self.skip1 and self.skipdenom1 and tick.temp_fracenum == 1 and tick.temp_fracdenom == 1 and
                  (len(self.prefix) or len(self.infix) or len(self.suffix)) and
                  not len(fracenumminus) and not len(self.enumprefix) and not len(self.enuminfix) and not len(self.enumsuffix) and
                  not len(fracdenomminus) and not len(self.denomprefix) and not len(self.denominfix) and not len(self.denomsuffix)):
                tick.label = "%s%s%s%s" % (self.prefix, fracminus, self.infix, self.suffix)
            else:
                if self.skipenum1 and tick.temp_fracenum == 1 and (len(self.enumprefix) or len(self.enuminfix) or len(self.enumsuffix)):
                    tick.temp_fracenum = "%s%s%s%s" % (self.enumprefix, fracenumminus, self.enuminfix, self.enumsuffix)
                else:
                    tick.temp_fracenum = "%s%s%s%i%s" % (self.enumprefix, fracenumminus, self.enuminfix, tick.temp_fracenum, self.enumsuffix)
                if self.skipdenom1 and tick.temp_fracdenom == 1 and not len(fracdenomminus) and not len(self.denomprefix) and not len(self.denominfix) and not len(self.denomsuffix):
                    frac = tick.temp_fracenum
                else:
                    tick.temp_fracdenom = "%s%s%s%i%s" % (self.denomprefix, fracdenomminus, self.denominfix, tick.temp_fracdenom, self.denomsuffix)
                    frac = self.over % (tick.temp_fracenum, tick.temp_fracdenom)
                tick.label = "%s%s%s%s%s" % (self.prefix, fracminus, self.infix, frac, self.suffix)
            tick.labelattrs.extend(self.labelattrs)

            # del tick.temp_fracenum    # we've inserted those temporary variables ... and do not care any longer about them
            # del tick.temp_fracdenom
            # del tick.temp_fracminus



class decimaltexter:
    "a texter creating decimal labels (e.g. '1.234' or even '0.\overline{3}')"

    __implements__ = _Itexter

    def __init__(self, prefix="", infix="", suffix="", equalprecision=0,
                       decimalsep=".", thousandsep="", thousandthpartsep="",
                       minus="-", period=r"\overline{%s}", labelattrs=textmodule.mathmode):
        r"""initializes the instance
        - prefix, infix, and suffix (strings) are added at the begin,
          immediately after the minus, and at the end of the label,
          respectively
        - decimalsep, thousandsep, and thousandthpartsep (strings)
          are used as separators
        - minus (string) is inserted for negative numbers
        - period (string) is taken as a format string generating a period;
          it has to contain exactly one string insert operators "%s" for the
          period; usually it should be r"\overline{%s}"
        - labelattrs is a sequence of attributes for a texrunners text method;
          a single is allowed without being a sequence; None is considered as
          an empty sequence"""
        self.prefix = prefix
        self.infix = infix
        self.suffix = suffix
        self.equalprecision = equalprecision
        self.decimalsep = decimalsep
        self.thousandsep = thousandsep
        self.thousandthpartsep = thousandthpartsep
        self.minus = minus
        self.period = period
        self.labelattrs = helper.ensurelist(labelattrs)

    def labels(self, ticks):
        labeledticks = []
        maxdecprecision = 0
        for tick in ticks:
            if tick.label is None and tick.labellevel is not None:
                labeledticks.append(tick)
                m, n = tick.enum, tick.denom
                if m < 0: m *= -1
                if n < 0: n *= -1
                whole, reminder = divmod(m, n)
                whole = str(whole)
                if len(self.thousandsep):
                    l = len(whole)
                    tick.label = ""
                    for i in range(l):
                        tick.label += whole[i]
                        if not ((l-i-1) % 3) and l > i+1:
                            tick.label += self.thousandsep
                else:
                    tick.label = whole
                if reminder:
                    tick.label += self.decimalsep
                oldreminders = []
                tick.temp_decprecision = 0
                while (reminder):
                    tick.temp_decprecision += 1
                    if reminder in oldreminders:
                        tick.temp_decprecision = None
                        periodstart = len(tick.label) - (len(oldreminders) - oldreminders.index(reminder))
                        tick.label = tick.label[:periodstart] + self.period % tick.label[periodstart:]
                        break
                    oldreminders += [reminder]
                    reminder *= 10
                    whole, reminder = divmod(reminder, n)
                    if not ((tick.temp_decprecision - 1) % 3) and tick.temp_decprecision > 1:
                        tick.label += self.thousandthpartsep
                    tick.label += str(whole)
                if maxdecprecision < tick.temp_decprecision:
                    maxdecprecision = tick.temp_decprecision
        if self.equalprecision:
            for tick in labeledticks:
                if tick.temp_decprecision is not None:
                    if tick.temp_decprecision == 0 and maxdecprecision > 0:
                        tick.label += self.decimalsep
                    for i in range(tick.temp_decprecision, maxdecprecision):
                        if not ((i - 1) % 3) and i > 1:
                            tick.label += self.thousandthpartsep
                        tick.label += "0"
        for tick in labeledticks:
            if tick.enum * tick.denom < 0:
                minus = self.minus
            else:
                minus = ""
            tick.label = "%s%s%s%s%s" % (self.prefix, minus, self.infix, tick.label, self.suffix)
            tick.labelattrs.extend(self.labelattrs)

            # del tick.temp_decprecision  # we've inserted this temporary variable ... and do not care any longer about it


class exponentialtexter:
    "a texter creating labels with exponentials (e.g. '2\cdot10^5')"

    __implements__ = _Itexter

    def __init__(self, plus="", minus="-",
                       mantissaexp=r"{{%s}\cdot10^{%s}}",
                       nomantissaexp=r"{10^{%s}}",
                       minusnomantissaexp=r"{-10^{%s}}",
                       mantissamin=frac((1, 1)), mantissamax=frac((10, 1)),
                       skipmantissa1=0, skipallmantissa1=1,
                       mantissatexter=decimaltexter()):
        r"""initializes the instance
        - plus or minus (string) is inserted for positive or negative exponents
        - mantissaexp (string) is taken as a format string generating the exponent;
          it has to contain exactly two string insert operators "%s" --
          the first for the mantissa and the second for the exponent;
          examples are r"{{%s}\cdot10^{%s}}" and r"{{%s}{\rm e}^{%s}}"
        - nomantissaexp (string) is taken as a format string generating the exponent
          when the mantissa is one and should be skipped; it has to contain
          exactly one string insert operators "%s" for the exponent;
          an examples is r"{10^{%s}}"
        - minusnomantissaexp (string) is taken as a format string generating the exponent
          when the mantissa is minus one and should be skipped; it has to contain
          exactly one string insert operators "%s" for the exponent; might be set to None
          to disallow skipping of any mantissa minus one
          an examples is r"{-10^{%s}}"
        - mantissamin and mantissamax are the minimum and maximum of the mantissa;
          they are frac instances greater than zero and mantissamin < mantissamax;
          the sign of the tick is ignored here
        - skipmantissa1 (boolean) turns on skipping of any mantissa equals one
          (and minus when minusnomantissaexp is set)
        - skipallmantissa1 (boolean) as above, but all mantissas must be 1
        - mantissatexter is the texter for the mantissa"""
        self.plus = plus
        self.minus = minus
        self.mantissaexp = mantissaexp
        self.nomantissaexp = nomantissaexp
        self.minusnomantissaexp = minusnomantissaexp
        self.mantissamin = mantissamin
        self.mantissamax = mantissamax
        self.mantissamindivmax = self.mantissamin / self.mantissamax
        self.mantissamaxdivmin = self.mantissamax / self.mantissamin
        self.skipmantissa1 = skipmantissa1
        self.skipallmantissa1 = skipallmantissa1
        self.mantissatexter = mantissatexter

    def labels(self, ticks):
        labeledticks = []
        for tick in ticks:
            if tick.label is None and tick.labellevel is not None:
                tick.temp_orgenum, tick.temp_orgdenom = tick.enum, tick.denom
                labeledticks.append(tick)
                tick.temp_exp = 0
                if tick.enum:
                    while abs(tick) >= self.mantissamax:
                        tick.temp_exp += 1
                        x = tick * self.mantissamindivmax
                        tick.enum, tick.denom = x.enum, x.denom
                    while abs(tick) < self.mantissamin:
                        tick.temp_exp -= 1
                        x = tick * self.mantissamaxdivmin
                        tick.enum, tick.denom = x.enum, x.denom
                if tick.temp_exp < 0:
                    tick.temp_exp = "%s%i" % (self.minus, -tick.temp_exp)
                else:
                    tick.temp_exp = "%s%i" % (self.plus, tick.temp_exp)
        self.mantissatexter.labels(labeledticks)
        if self.minusnomantissaexp is not None:
            allmantissa1 = len(labeledticks) == len([tick for tick in labeledticks if abs(tick.enum) == abs(tick.denom)])
        else:
            allmantissa1 = len(labeledticks) == len([tick for tick in labeledticks if tick.enum == tick.denom])
        for tick in labeledticks:
            if (self.skipallmantissa1 and allmantissa1 or
                (self.skipmantissa1 and (tick.enum == tick.denom or
                                         (tick.enum == -tick.denom and self.minusnomantissaexp is not None)))):
                if tick.enum == tick.denom:
                    tick.label = self.nomantissaexp % tick.temp_exp
                else:
                    tick.label = self.minusnomantissaexp % tick.temp_exp
            else:
                tick.label = self.mantissaexp % (tick.label, tick.temp_exp)
            tick.enum, tick.denom = tick.temp_orgenum, tick.temp_orgdenom

            # del tick.temp_orgenum    # we've inserted those temporary variables ... and do not care any longer about them
            # del tick.temp_orgdenom
            # del tick.temp_exp


class defaulttexter:
    "a texter creating decimal or exponential labels"

    __implements__ = _Itexter

    def __init__(self, smallestdecimal=frac((1, 1000)),
                       biggestdecimal=frac((9999, 1)),
                       equaldecision=1,
                       decimaltexter=decimaltexter(),
                       exponentialtexter=exponentialtexter()):
        r"""initializes the instance
        - smallestdecimal and biggestdecimal are the smallest and
          biggest decimal values, where the decimaltexter should be used;
          they are frac instances; the sign of the tick is ignored here;
          a tick at zero is considered for the decimaltexter as well
        - equaldecision (boolean) uses decimaltexter or exponentialtexter
          globaly (set) or for each tick separately (unset)
        - decimaltexter and exponentialtexter are texters to be used"""
        self.smallestdecimal = smallestdecimal
        self.biggestdecimal = biggestdecimal
        self.equaldecision = equaldecision
        self.decimaltexter = decimaltexter
        self.exponentialtexter = exponentialtexter

    def labels(self, ticks):
        decticks = []
        expticks = []
        for tick in ticks:
            if tick.label is None and tick.labellevel is not None:
                if not tick.enum or (abs(tick) >= self.smallestdecimal and abs(tick) <= self.biggestdecimal):
                    decticks.append(tick)
                else:
                    expticks.append(tick)
        if self.equaldecision:
            if len(expticks):
                self.exponentialtexter.labels(ticks)
            else:
                self.decimaltexter.labels(ticks)
        else:
            for tick in decticks:
                self.decimaltexter.labels([tick])
            for tick in expticks:
                self.exponentialtexter.labels([tick])


################################################################################
# axis painter
################################################################################


class axiscanvas(canvas.canvas):
    """axis canvas
    - an axis canvas is a regular canvas to be filled by
      a axispainters painter method
    - it contains extent (a pyx length) to be used for the
      alignment of additional axes; the axis extent should
      be filled by the axispainters painter method; you may
      grasp this as a size information comparable to a bounding
      box
    - it contains labels (a list of textboxes) to be used to rate the
      distances between the labels if needed by the axis later on;
      the painter method has not only to insert the labels into this
      canvas, but should also fill this list"""

    # __implements__ = sole implementation

    def __init__(self, *args, **kwargs):
        """initializes the instance
        - sets extent to zero
        - sets labels to an empty list"""
        canvas.canvas.__init__(self, *args, **kwargs)
        self.extent = 0
        self.labels = []


class rotatetext:
    """create rotations accordingly to tick directions
    - upsidedown rotations are suppressed by rotating them by another 180 degree"""

    # __implements__ = sole implementation

    def __init__(self, direction, epsilon=1e-10):
        """initializes the instance
        - direction is an angle to be used relative to the tick direction
        - epsilon is the value by which 90 degrees can be exceeded before
          an 180 degree rotation is added"""
        self.direction = direction
        self.epsilon = epsilon

    def trafo(self, dx, dy):
        """returns a rotation transformation accordingly to the tick direction
        - dx and dy are the direction of the tick"""
        direction = self.direction + math.atan2(dy, dx) * 180 / math.pi
        while (direction > 90 + self.epsilon):
            direction -= 180
        while (direction < -90 - self.epsilon):
            direction += 180
        return trafomodule.rotate(direction)


paralleltext = rotatetext(-90)
orthogonaltext = rotatetext(0)


class _Iaxispainter:
    "class for painting axes"

    def paint(self, axis, ticks, axiscanvas):
        """paint ticks into the axiscanvas
        - the axis and the ticks should not be modified (we may
          add some temporary variables like ticks[i].temp_xxx,
          which might be used just temporary) -- the idea is that
          all things can be used several times
        - also do not modify the instance (self) -- even this
          instance might be used several times; thus do not modify
          attributes like self.titleattrs etc. (just use a copy of it)
        - the axis should be accessed to get the tick positions
          namely by _Iaxispos and _Imap; see those interface
          definitions for details
        - the method might access some additional attributes from
          the axis, e.g. the axis title -- the axis painter should
          document this behavior and rely on the availability of
          those attributes -> it becomes a question of the proper
          usage of the combination of axis & axispainter
        - the ticks are a list of tick instances; there type must
          be suitable for the tick position methods of the axis ->
          it should again be a question ov the proper usage of the
          combination of axis & axispainter
        - the axiscanvas is a axiscanvas instance and should be
          filled with the ticks and labels; note that the extent
          and labels instance variables should be filled as
          documented in the axiscanvas"""


class axistitlepainter:
    """class for painting an axis title
    - the axis must have a title attribute when using this painter;
      this title might be None"""

    __implements__ = _Iaxispainter

    def __init__(self, titledist="0.3 cm",
                       titleattrs=(textmodule.halign.center, textmodule.vshift.mathaxis),
                       titledirection=paralleltext,
                       titlepos=0.5):
        """initialized the instance
        - titledist is a visual PyX length giving the distance
          of the title from the axis extent already there (a title might
          be added after labels or other things are plotted already)
        - labelattrs is a sequence of attributes for a texrunners text
          method; a single is allowed without being a sequence; None
          turns off the title
        - titledirection is an instance of rotatetext or None
        - titlepos is the position of the title in graph coordinates"""
        self.titledist_str = titledist
        self.titleattrs = titleattrs
        self.titledirection = titledirection
        self.titlepos = titlepos

    def paint(self, axis, ticks, axiscanvas):
        if axis.title is not None and self.titleattrs is not None:
            titledist = unit.length(self.titledist_str, default_type="v")
            x, y = axis._vtickpoint(self.titlepos, axis=axis)
            dx, dy = axis.vtickdirection(self.titlepos, axis=axis)
            titleattrs = helper.ensurelist(self.titleattrs)
            if self.titledirection is not None:
                titleattrs.append(self.titledirection.trafo(dx, dy))
            title = axiscanvas.texrunner._text(x, y, axis.title, *titleattrs)
            axiscanvas.extent += titledist
            title.linealign(axiscanvas.extent, dx, dy)
            axiscanvas.extent += title.extent(dx, dy)
            axiscanvas.insert(title)


class axispainter(axistitlepainter):
    """class for painting the ticks and labels of an axis
    - the inherited titleaxispainter is used to paint the title of
      the axis as well
    - note that the type of the elements of ticks given as an argument
      of the paint method must be suitable for the tick position methods
      of the axis"""

    __implements__ = _Iaxispainter

    defaultticklengths = ["%0.5f cm" % (0.2*goldenmean**(-i)) for i in range(10)]

    def __init__(self, innerticklengths=defaultticklengths,
                       outerticklengths=None,
                       tickattrs=(),
                       gridattrs=None,
                       zerolineattrs=(),
                       baselineattrs=canvas.linecap.square,
                       labeldist="0.3 cm",
                       labelattrs=(textmodule.halign.center, textmodule.vshift.mathaxis),
                       labeldirection=None,
                       labelhequalize=0,
                       labelvequalize=1,
                       **kwargs):
        """initializes the instance
        - innerticklenths and outerticklengths are two sequences of
          visual PyX lengths for ticks, subticks, etc. plotted inside
          and outside of the graph; when a single value is given, it
          is used for all tick levels; None turns off ticks inside or
          outside of the graph
        - tickattrs are a sequence of stroke attributes for the ticks;
          a single entry is allowed without being a sequence; None turns
          off ticks
        - gridlineattrs are a sequence of sequences used as stroke
          attributes for ticks, subticks etc.; when a single sequence
          is given, it is used for ticks, subticks, etc.; a single
          entry is allowed without being a sequence; None turns off
          gridlines
        - zerolineattrs are a sequence of stroke attributes for a grid
          line at axis value zero; a single entry is allowed without
          being a sequence; None turns off the zeroline
        - baselineattrs are a sequence of stroke attributes for a grid
          line at axis value zero; a single entry is allowed without
          being a sequence; None turns off the baseline
        - labeldist is a visual PyX length for the distance of the labels
          from the axis baseline
        - labelattrs is a sequence of attributes for a texrunners text
          method; a single entry is allowed without being a sequence;
          None turns off the labels
        - titledirection is an instance of rotatetext or None
        - labelhequalize and labelvequalize (booleans) perform an equal
          alignment for straight vertical and horizontal axes, respectively
        - futher keyword arguments are passed to axistitlepainter"""
        # TODO: access to axis.divisor -- document, remove, ... ???
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
        axistitlepainter.__init__(self, **kwargs)

    def paint(self, axis, ticks, axiscanvas):
        labeldist = unit.length(self.labeldist_str, default_type="v")
        for tick in ticks:
            tick.temp_v = axis.convert(float(tick) * axis.divisor)
            tick.temp_x, tick.temp_y = axis._vtickpoint(tick.temp_v, axis=axis)
            tick.temp_dx, tick.temp_dy = axis.vtickdirection(tick.temp_v, axis=axis)

        # create & align tick.temp_labelbox
        for tick in ticks:
            if tick.labellevel is not None:
                labelattrs = helper.getsequenceno(self.labelattrs, tick.labellevel)
                if labelattrs is not None:
                    labelattrs = helper.ensurelist(labelattrs)[:]
                    if self.labeldirection is not None:
                        labelattrs.append(self.labeldirection.trafo(tick.temp_dx, tick.temp_dy))
                    if tick.labelattrs is not None:
                        labelattrs.extend(helper.ensurelist(tick.labelattrs))
                    tick.temp_labelbox = axiscanvas.texrunner._text(tick.temp_x, tick.temp_y, tick.label, *labelattrs)
        if len(ticks) > 1:
            equaldirection = 1
            for tick in ticks[1:]:
                if tick.temp_dx != ticks[0].temp_dx or tick.temp_dy != ticks[0].temp_dy:
                    equaldirection = 0
        else:
            equaldirection = 0
        if equaldirection and ((not ticks[0].temp_dx and self.labelvequalize) or
                               (not ticks[0].temp_dy and self.labelhequalize)):
            if self.labelattrs is not None:
                box.linealignequal([tick.temp_labelbox for tick in ticks if tick.labellevel is not None],
                                   labeldist, ticks[0].temp_dx, ticks[0].temp_dy)
        else:
            for tick in ticks:
                if tick.labellevel is not None and self.labelattrs is not None:
                    tick.temp_labelbox.linealign(labeldist, tick.temp_dx, tick.temp_dy)

        def mkv(arg):
            if helper.issequence(arg):
                return [unit.length(a, default_type="v") for a in arg]
            if arg is not None:
                return unit.length(arg, default_type="v")
        innerticklengths = mkv(self.innerticklengths_str)
        outerticklengths = mkv(self.outerticklengths_str)

        for tick in ticks:
            if tick.ticklevel is not None:
                innerticklength = helper.getitemno(innerticklengths, tick.ticklevel)
                outerticklength = helper.getitemno(outerticklengths, tick.ticklevel)
                if not (innerticklength is None and outerticklength is None):
                    if innerticklength is None:
                        innerticklength = 0
                    if outerticklength is None:
                        outerticklength = 0
                    tickattrs = helper.getsequenceno(self.tickattrs, tick.ticklevel)
                    if tickattrs is not None:
                        _innerticklength = unit.topt(innerticklength)
                        _outerticklength = unit.topt(outerticklength)
                        x1 = tick.temp_x - tick.temp_dx * _innerticklength
                        y1 = tick.temp_y - tick.temp_dy * _innerticklength
                        x2 = tick.temp_x + tick.temp_dx * _outerticklength
                        y2 = tick.temp_y + tick.temp_dy * _outerticklength
                        axiscanvas.stroke(path._line(x1, y1, x2, y2), *helper.ensuresequence(tickattrs))
                if tick != frac((0, 1)) or self.zerolineattrs is None:
                    gridattrs = helper.getsequenceno(self.gridattrs, tick.ticklevel)
                    if gridattrs is not None:
                        axiscanvas.stroke(axis.vgridline(tick.temp_v, axis=axis), *helper.ensuresequence(gridattrs))
                if unit.topt(outerticklength) > unit.topt(axiscanvas.extent):
                    axiscanvas.extent = outerticklength
                if unit.topt(-innerticklength) > unit.topt(axiscanvas.extent):
                    axiscanvas.extent = -innerticklength
            if tick.labellevel is not None and self.labelattrs is not None:
                axiscanvas.insert(tick.temp_labelbox)
                axiscanvas.labels.append(tick.temp_labelbox)
                extent = tick.temp_labelbox.extent(tick.temp_dx, tick.temp_dy) + labeldist
                if unit.topt(extent) > unit.topt(axiscanvas.extent):
                    axiscanvas.extent = extent
        if self.baselineattrs is not None:
            axiscanvas.stroke(axis.vbaseline(axis=axis), *helper.ensuresequence(self.baselineattrs))
        if self.zerolineattrs is not None:
            if len(ticks) and ticks[0] * ticks[-1] < frac((0, 1)):
                axiscanvas.stroke(axis.gridline(0, axis=axis), *helper.ensuresequence(self.zerolineattrs))

        # for tick in ticks:
        #     del tick.temp_v    # we've inserted those temporary variables ... and do not care any longer about them
        #     del tick.temp_x
        #     del tick.temp_y
        #     del tick.temp_dx
        #     del tick.temp_dy
        #     if tick.labellevel is not None and self.labelattrs is not None:
        #         del tick.temp_labelbox

        axistitlepainter.paint(self, axis, ticks, axiscanvas)


class linkaxispainter(axispainter):
    """class for painting a linked axis
    - the inherited axispainter is used to paint the axis
    - modifies some constructor defaults"""

    __implements__ = _Iaxispainter

    def __init__(self, gridattrs=None,
                       zerolineattrs=None,
                       labelattrs=None,
                       titleattrs=None,
                       **kwargs):
        """initializes the instance
        - the gridattrs default is set to None thus skipping the girdlines
        - the zerolineattrs default is set to None thus skipping the zeroline
        - the labelattrs default is set to None thus skipping the labels
        - the titleattrs default is set to None thus skipping the title
        - all keyword arguments are passed to axispainter"""
        axispainter.__init__(self, gridattrs=gridattrs,
                                   zerolineattrs=zerolineattrs,
                                   labelattrs=labelattrs,
                                   titleattrs=titleattrs,
                                   **kwargs)


class splitaxispainter(axistitlepainter): pass
# class splitaxispainter(axistitlepainter):
# 
#     def __init__(self, breaklinesdist=0.05,
#                        breaklineslength=0.5,
#                        breaklinesangle=-60,
#                        breaklinesattrs=(),
#                        **args):
#         self.breaklinesdist_str = breaklinesdist
#         self.breaklineslength_str = breaklineslength
#         self.breaklinesangle = breaklinesangle
#         self.breaklinesattrs = breaklinesattrs
#         axistitlepainter.__init__(self, **args)
# 
#     def subvbaseline(self, axis, v1=None, v2=None):
#         if v1 is None:
#             if self.breaklinesattrs is None:
#                 left = axis.vmin
#             else:
#                 if axis.vminover is None:
#                     left = None
#                 else:
#                     left = axis.vminover
#         else:
#             left = axis.vmin+v1*(axis.vmax-axis.vmin)
#         if v2 is None:
#             if self.breaklinesattrs is None:
#                 right = axis.vmax
#             else:
#                 if axis.vmaxover is None:
#                     right = None
#                 else:
#                     right = axis.vmaxover
#         else:
#             right = axis.vmin+v2*(axis.vmax-axis.vmin)
#         return axis.baseaxis.vbaseline(axis.baseaxis, left, right)
# 
#     def dolayout(self, graph, axis):
#         if self.breaklinesattrs is not None:
#             self.breaklinesdist = unit.length(self.breaklinesdist_str, default_type="v")
#             self.breaklineslength = unit.length(self.breaklineslength_str, default_type="v")
#             self._breaklinesdist = unit.topt(self.breaklinesdist)
#             self._breaklineslength = unit.topt(self.breaklineslength)
#             self.sin = math.sin(self.breaklinesangle*math.pi/180.0)
#             self.cos = math.cos(self.breaklinesangle*math.pi/180.0)
#             axis.layoutdata._extent = (math.fabs(0.5 * self._breaklinesdist * self.cos) +
#                                        math.fabs(0.5 * self._breaklineslength * self.sin))
#         else:
#             axis.layoutdata._extent = 0
#         for subaxis in axis.axislist:
#             subaxis.baseaxis = axis
#             subaxis._vtickpoint = lambda axis, v: axis.baseaxis._vtickpoint(axis.baseaxis, axis.vmin+v*(axis.vmax-axis.vmin))
#             subaxis.vtickdirection = lambda axis, v: axis.baseaxis.vtickdirection(axis.baseaxis, axis.vmin+v*(axis.vmax-axis.vmin))
#             subaxis.vbaseline = self.subvbaseline
#             subaxis.dolayout(graph)
#             if axis.layoutdata._extent < subaxis.layoutdata._extent:
#                 axis.layoutdata._extent = subaxis.layoutdata._extent
#         axistitlepainter.dolayout(self, graph, axis)
# 
#     def paint(self, graph, axis):
#         for subaxis in axis.axislist:
#             subaxis.dopaint(graph)
#         if self.breaklinesattrs is not None:
#             for subaxis1, subaxis2 in zip(axis.axislist[:-1], axis.axislist[1:]):
#                 # use a tangent of the baseline (this is independent of the tickdirection)
#                 v = 0.5 * (subaxis1.vmax + subaxis2.vmin)
#                 breakline = path.normpath(axis.vbaseline(axis, v, None)).tangent(0, self.breaklineslength)
#                 widthline = path.normpath(axis.vbaseline(axis, v, None)).tangent(0, self.breaklinesdist).transformed(trafomodule.rotate(self.breaklinesangle+90, *breakline.begin()))
#                 tocenter = map(lambda x: 0.5*(x[0]-x[1]), zip(breakline.begin(), breakline.end()))
#                 towidth = map(lambda x: 0.5*(x[0]-x[1]), zip(widthline.begin(), widthline.end()))
#                 breakline = breakline.transformed(trafomodule.translate(*tocenter).rotated(self.breaklinesangle, *breakline.begin()))
#                 breakline1 = breakline.transformed(trafomodule.translate(*towidth))
#                 breakline2 = breakline.transformed(trafomodule.translate(-towidth[0], -towidth[1]))
#                 graph.fill(path.path(path.moveto(*breakline1.begin()),
#                                      path.lineto(*breakline1.end()),
#                                      path.lineto(*breakline2.end()),
#                                      path.lineto(*breakline2.begin()),
#                                      path.closepath()), color.gray.white)
#                 graph.stroke(breakline1, *helper.ensuresequence(self.breaklinesattrs))
#                 graph.stroke(breakline2, *helper.ensuresequence(self.breaklinesattrs))
#         axistitlepainter.paint(self, graph, axis)
# 
# 
class baraxispainter(axistitlepainter): pass
# class baraxispainter(axistitlepainter):
# 
#     def __init__(self, innerticklength=None,
#                        outerticklength=None,
#                        tickattrs=(),
#                        baselineattrs=canvas.linecap.square,
#                        namedist="0.3 cm",
#                        nameattrs=(textmodule.halign.center, textmodule.vshift.mathaxis),
#                        namedirection=None,
#                        namepos=0.5,
#                        namehequalize=0,
#                        namevequalize=1,
#                        **args):
#         self.innerticklength_str = innerticklength
#         self.outerticklength_str = outerticklength
#         self.tickattrs = tickattrs
#         self.baselineattrs = baselineattrs
#         self.namedist_str = namedist
#         self.nameattrs = nameattrs
#         self.namedirection = namedirection
#         self.namepos = namepos
#         self.namehequalize = namehequalize
#         self.namevequalize = namevequalize
#         axistitlepainter.__init__(self, **args)
# 
#     def dolayout(self, graph, axis):
#         axis.layoutdata._extent = 0
#         if axis.multisubaxis:
#             for name, subaxis in zip(axis.names, axis.subaxis):
#                 subaxis.vmin = axis.convert((name, 0))
#                 subaxis.vmax = axis.convert((name, 1))
#                 subaxis.baseaxis = axis
#                 subaxis._vtickpoint = lambda axis, v: axis.baseaxis._vtickpoint(axis.baseaxis, axis.vmin+v*(axis.vmax-axis.vmin))
#                 subaxis.vtickdirection = lambda axis, v: axis.baseaxis.vtickdirection(axis.baseaxis, axis.vmin+v*(axis.vmax-axis.vmin))
#                 subaxis.vbaseline = None
#                 subaxis.dolayout(graph)
#                 if axis.layoutdata._extent < subaxis.layoutdata._extent:
#                     axis.layoutdata._extent = subaxis.layoutdata._extent
#         axis.namepos = []
#         for name in axis.names:
#             v = axis.convert((name, self.namepos))
#             x, y = axis._vtickpoint(axis, v)
#             dx, dy = axis.vtickdirection(axis, v)
#             axis.namepos.append((v, x, y, dx, dy))
#         axis.nameboxes = []
#         if self.nameattrs is not None:
#             for (v, x, y, dx, dy), name in zip(axis.namepos, axis.names):
#                 nameattrs = helper.ensurelist(self.nameattrs)
#                 if self.namedirection is not None:
#                     nameattrs += [trafomodule.rotate(self.reldirection(self.namedirection, dx, dy))]
#                 if axis.texts.has_key(name):
#                     axis.nameboxes.append(graph.texrunner._text(x, y, str(axis.texts[name]), *nameattrs))
#                 elif axis.texts.has_key(str(name)):
#                     axis.nameboxes.append(graph.texrunner._text(x, y, str(axis.texts[str(name)]), *nameattrs))
#                 else:
#                     axis.nameboxes.append(graph.texrunner._text(x, y, str(name), *nameattrs))
#         labeldist = axis.layoutdata._extent + unit.topt(unit.length(self.namedist_str, default_type="v"))
#         if len(axis.namepos) > 1:
#             equaldirection = 1
#             for namepos in axis.namepos[1:]:
#                 if namepos[3] != axis.namepos[0][3] or namepos[4] != axis.namepos[0][4]:
#                     equaldirection = 0
#         else:
#             equaldirection = 0
#         if equaldirection and ((not axis.namepos[0][3] and self.namevequalize) or
#                                (not axis.namepos[0][4] and self.namehequalize)):
#             box._linealignequal(axis.nameboxes, labeldist, axis.namepos[0][3], axis.namepos[0][4])
#         else:
#             for namebox, namepos in zip(axis.nameboxes, axis.namepos):
#                 namebox._linealign(labeldist, namepos[3], namepos[4])
#         if self.innerticklength_str is not None:
#             axis.innerticklength = unit.topt(unit.length(self.innerticklength_str, default_type="v"))
#         else:
#             if self.outerticklength_str is not None:
#                 axis.innerticklength = 0
#             else:
#                 axis.innerticklength = None
#         if self.outerticklength_str is not None:
#             axis.outerticklength = unit.topt(unit.length(self.outerticklength_str, default_type="v"))
#         else:
#             if self.innerticklength_str is not None:
#                 axis.outerticklength = 0
#             else:
#                 axis.outerticklength = None
#         if axis.outerticklength is not None and self.tickattrs is not None:
#             axis.layoutdata._extent += axis.outerticklength
#         for (v, x, y, dx, dy), namebox in zip(axis.namepos, axis.nameboxes):
#             newextent = namebox._extent(dx, dy) + labeldist
#             if axis.layoutdata._extent < newextent:
#                 axis.layoutdata._extent = newextent
#         #graph.mindbbox(*[namebox.bbox() for namebox in axis.nameboxes])
#         axistitlepainter.dolayout(self, graph, axis)
# 
#     def paint(self, graph, axis):
#         if axis.subaxis is not None:
#             if axis.multisubaxis:
#                 for subaxis in axis.subaxis:
#                     subaxis.dopaint(graph)
#         if None not in (self.tickattrs, axis.innerticklength, axis.outerticklength):
#             for pos in axis.relsizes:
#                 if pos == axis.relsizes[0]:
#                     pos -= axis.firstdist
#                 elif pos != axis.relsizes[-1]:
#                     pos -= 0.5 * axis.dist
#                 v = pos / axis.relsizes[-1]
#                 x, y = axis._vtickpoint(axis, v)
#                 dx, dy = axis.vtickdirection(axis, v)
#                 x1 = x - dx * axis.innerticklength
#                 y1 = y - dy * axis.innerticklength
#                 x2 = x + dx * axis.outerticklength
#                 y2 = y + dy * axis.outerticklength
#                 graph.stroke(path._line(x1, y1, x2, y2), *helper.ensuresequence(self.tickattrs))
#         if self.baselineattrs is not None:
#             if axis.vbaseline is not None: # XXX: subbaselines (as for splitlines)
#                 graph.stroke(axis.vbaseline(axis), *helper.ensuresequence(self.baselineattrs))
#         for namebox in axis.nameboxes:
#             graph.insert(namebox)
#         axistitlepainter.paint(self, graph, axis)



################################################################################
# axes
################################################################################


class _Iaxis:
    """interface definition of a axis
    - data and tick range are handled separately
    - an axis implements _Imap as well to convert between
      axis values and graph coordinates; this is usually done
      by mixin a proper mapping
    - instance variables:
      - axiscanvas: an axiscanvas instance, which is available after
        calling the finish method
      - relsize: relative size (width) of the axis (for use
        in splitaxis etc.) -- this might not be available for
        all axes, which will just create an name error right now
    - configuration of the range handling is not subject
      of this interface definition"""
    # TODO: - add a mechanism to allow for a different range
    #         handling of x and y ranges
    #       - should we document instance variables this way?

    __implements__ = _Imap

    def setdatarange(self, min, max):
        """set the axis data range
        - the type of min and max must fit to the axis
        - min<max; the axis might be reversed, but this is
          expressed internally only
        - the axis might not apply this change of the range
          (e.g. when the axis range is fixed by the user)
        - for invalid parameters (e.g. negativ values at an
          logarithmic axis), an exception should be raised"""
        # TODO: be more specific about the type of the exception

    def settickrange(self, min, max):
        """set the axis tick range
        - as before, but for the tick range"""

    def getdatarange(self):
        """return data range as a tuple (min, max)
        - min<max; the axis might be reversed, but this is
          expressed internally only"""
        # TODO: exceptions???

    def gettickrange(self):
        """return tick range as a tuple (min, max)
        - as before, but for the tick range"""
        # TODO: exceptions???

    def finish(self, graph):
        """paint the axis into the graph
        - the graph should not be modified (read-only); the only
          important property of the graph should be its texrunner
          instance
        - the axis instance (self) should be accessed to get the
          tick positions namely by _Iaxispos and _Imap; see
          those interface definitions for details -- again, the
          graph should not be needed for that
        - the finish method creates an axiscanvas, which should be
          insertable into the graph to finally paint the axis
        - any modification of the axis range should be disabled after
          the finish method was called; a possible implementation would
          be to raise an error in these methods as soon as an axiscanvas
          is available"""


class _Iaxispos:
    """interface definition of axis tick position methods
    - these methods are used for the postitioning of the ticks
      when painting an axis
    - a graph should insert these methods appropriate to its design
      before the painting of the axis takes place, thus self is the
      graph instance and the axis must be provided as a separate
      argument"""

    def baseline(self, x1=None, x2=None, axis=None):
        """return the baseline as a path
        - x1 is the start position; if not set, the baseline starts
          from the beginning of the axis, which might imply a
          value outside of the graph coordinate range [0; 1]
        - x2 is analogous to x1, but for the end position"""

    def vbaseline(self, v1=None, v2=None, axis=None):
        """return the baseline as a path
        - like baseline, but for graph coordinates"""

    def gridline(self, a, axis=None):
        "return the gridline as a path for a given position x"

    def vgridline(self, v, axis=None):
        """return the gridline as a path for a given position v
        in graph coordinates"""

    def _tickpoint(self, x, axis=None):
        """return the position at the baseline as a tuple (x, y) in
        postscript points for the position x"""

    def tickpoint(self, x, axis=None):
        """return the position at the baseline as a tuple (x, y) in
        in PyX length for the position x"""

    def _vtickpoint(self, v, axis=None):
        "like _tickpoint, but for graph coordinates"

    def tickpoint(self, x, axis=None):
        "like tickpoint, but for graph coordinates"

    def tickdirection(self, x, axis=None):
        """return the direction of a tick as a tuple (dx, dy) for the
        position x"""

    def vtickdirection(self, v, axis=None):
        """like tickposition, but for graph coordinates"""


class _axis:

    __implements__ = _Iaxis

    def __init__(self, min=None, max=None, reverse=0, divisor=1,
                       datavmin=None, datavmax=None, tickvmin=0, tickvmax=1,
                       title=None, painter=axispainter(), texter=defaulttexter(),
                       density=1, maxworse=2):
# - a axis has a part attribute where it stores a partitioner or/and some
#   (manually set) ticks -> the part attribute is used to create the ticks
#   in the axis finish method
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
        self.painter = painter
        self.texter = texter
        self.density = density
        self.maxworse = maxworse
        self.axiscanvas = None
        self.canconvert = 0
        self.finished = 0
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
        if self.axiscanvas is not None:
            raise RuntimeError("axis was already finished")
        self.datamin, self.datamax = min, max
        self.__setinternalrange(min, max)

    def settickrange(self, min, max):
        if self.axiscanvas is not None:
            raise RuntimeError("axis was already finished")
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

    def checkfraclist(self, fracs):
        "orders a list of fracs, equal entries are not allowed"
        if not len(fracs): return []
        sorted = list(fracs)
        sorted.sort()
        last = sorted[0]
        for item in sorted[1:]:
            if last == item:
                raise ValueError("duplicate entry found")
            last = item
        return sorted

    def finish(self, graph):
        if self.finished:
            return
        self.finished = 1

        min, max = self.gettickrange()
        if self.part is not None:
            parter = parterpos = None
            if helper.issequence(self.part):
                for p, i in zip(self.part, xrange(sys.maxint)):
                    if hasattr(p, "defaultpart"):
                        if parter is not None:
                            raise RuntimeError("only one partitioner allowed")
                        parter = p
                        parterpos = i
                self.part[:parterpos] = self.checkfraclist(self.part[:parterpos])
                self.part[parterpos+1:] = self.checkfraclist(self.part[parterpos+1:])
            else:
                parter = self.part
            if parter is not None:
                self.ticks = parter.defaultpart(min/self.divisor,
                                                max/self.divisor,
                                                not self.fixmin,
                                                not self.fixmax)
            if parterpos is not None:
                self.ticks = _mergeticklists(_mergeticklists(self.part[:parterpos], self.ticks), self.part[parterpos+1:])
        else:
            self.ticks = []
        # lesspart and morepart can be called after defaultpart;
        # this works although some axes may share their autoparting,
        # because the axes are processed sequentially
        first = 1
        worse = 0
        while worse < self.maxworse:
            if parter is not None:
                newticks = parter.lesspart()
                if parterpos is not None:
                    newticks = _mergeticklists(_mergeticklists(self.part[:parterpos], newticks), self.part[parterpos+1:])
            else:
                newticks = None
            if newticks is not None:
                if first:
                    bestrate = self.rater.ratepart(self, self.ticks, self.density)
                    variants = [[bestrate, self.ticks]]
                    first = 0
                newrate = self.rater.ratepart(self, newticks, self.density)
                variants.append([newrate, newticks])
                if newrate < bestrate:
                    bestrate = newrate
                    worse = 0
                else:
                    worse += 1
            else:
                worse += 1
        worse = 0
        while worse < self.maxworse:
            if parter is not None:
                newticks = parter.morepart()
                if parterpos is not None:
                    newticks = _mergeticklists(_mergeticklists(self.part[:parterpos], newticks), self.part[parterpos+1:])
            else:
                newticks = None
            if newticks is not None:
                if first:
                    bestrate = self.rater.ratepart(self, self.ticks, self.density)
                    variants = [[bestrate, self.ticks]]
                    first = 0
                newrate = self.rater.ratepart(self, newticks, self.density)
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
                    ac = axiscanvas()
                    ac.settexrunner(graph.texrunner)
                    self.texter.labels(self.ticks)
                    self.painter.paint(self, self.ticks, ac)
                    ratelayout = self.rater.ratelayout(ac, self.density)
                    if ratelayout is not None:
                        variants[i][0] += ratelayout
                        variants[i].append(ac)
                    else:
                        variants[i][0] = None
                    if variants[i][0] is not None and (bestrate is None or variants[i][0] < bestrate):
                        bestrate = variants[i][0]
                    self.__forceinternalrange(saverange)
                    i += 1
                if bestrate is None:
                    raise RuntimeError("no valid axis partitioning found")
                variants = [variant for variant in variants[:i] if variant[0] is not None]
                variants.sort()
                self.ticks = variants[0][1]
                if len(self.ticks):
                    self.settickrange(float(self.ticks[0])*self.divisor, float(self.ticks[-1])*self.divisor)
                self.axiscanvas = variants[0][2]
            else:
                if len(self.ticks):
                    self.settickrange(float(self.ticks[0])*self.divisor, float(self.ticks[-1])*self.divisor)
                self.axiscanvas = axiscanvas()
                self.axiscanvas.settexrunner(graph.texrunner)
        else:
            if len(self.ticks):
                self.settickrange(float(self.ticks[0])*self.divisor, float(self.ticks[-1])*self.divisor)
            self.axiscanvas = axiscanvas()
            self.axiscanvas.settexrunner(graph.texrunner)
            self.texter.labels(self.ticks)
            self.painter.paint(self, self.ticks, self.axiscanvas)

    def createlinkaxis(self, **args):
        return linkaxis(self, **args)


class linaxis(_axis, _linmap):

    def __init__(self, part=autolinpart(), rater=axisrater(), **args):
        _axis.__init__(self, **args)
        if self.fixmin and self.fixmax:
            self.relsize = self.max - self.min
        self.part = part
        self.rater = rater


class logaxis(_axis, _logmap):

    def __init__(self, part=autologpart(), rater=axisrater(ticks=axisrater.logticks, labels=axisrater.loglabels), **args):
        _axis.__init__(self, **args)
        if self.fixmin and self.fixmax:
            self.relsize = math.log(self.max) - math.log(self.min)
        self.part = part
        self.rater = rater


class linkaxis:

    def __init__(self, linkedaxis, painter=linkaxispainter()):
        self.linkedaxis = linkedaxis
        self.painter = painter
        self.finished = 0

    def __getattr__(self, attr):
        return getattr(self.linkedaxis, attr)

    def finish(self, graph):
        if self.finished:
            return
        self.finished = 1
        self.axiscanvas = axiscanvas()
        self.axiscanvas.settexrunner(graph.texrunner)
        self.linkedaxis.finish(graph)
        self.painter.paint(self, self.ticks, self.axiscanvas)

    def createlinkaxis(self, **args):
        return linkaxis(self, **args)


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
                #print self.subaxis, self.multisubaxis, subnames, name
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

#
# g = graph.graphxy(key=graph.key())
# g.addkey(graph.key(), ...)
#

class key:

    def __init__(self, dist="0.2 cm", pos = "tr", hinside = 1, vinside = 1, hdist="0.6 cm", vdist="0.4 cm",
                 symbolwidth="0.5 cm", symbolheight="0.25 cm", symbolspace="0.2 cm",
                 textattrs=textmodule.vshift.mathaxis):
        self.dist_str = dist
        self.pos = pos
        self.hinside = hinside
        self.vinside = vinside
        self.hdist_str = hdist
        self.vdist_str = vdist
        self.symbolwidth_str = symbolwidth
        self.symbolheight_str = symbolheight
        self.symbolspace_str = symbolspace
        self.textattrs = textattrs
        self.plotinfos = None
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

    def setplotinfos(self, *plotinfos):
        """set the plotinfos to be used in the key
        - call it exactly once"""
        if self.plotinfos is not None:
            raise RuntimeError("setplotinfo is called multiple times")
        self.plotinfos = plotinfos

    def dolayout(self, graph):
        "creates the layout of the key"
        self._dist = unit.topt(unit.length(self.dist_str, default_type="v"))
        self._hdist = unit.topt(unit.length(self.hdist_str, default_type="v"))
        self._vdist = unit.topt(unit.length(self.vdist_str, default_type="v"))
        self._symbolwidth = unit.topt(unit.length(self.symbolwidth_str, default_type="v"))
        self._symbolheight = unit.topt(unit.length(self.symbolheight_str, default_type="v"))
        self._symbolspace = unit.topt(unit.length(self.symbolspace_str, default_type="v"))
        self.titles = []
        for plotinfo in self.plotinfos:
            self.titles.append(graph.texrunner._text(0, 0, plotinfo.data.title, *helper.ensuresequence(self.textattrs)))
        box._tile(self.titles, self._dist, 0, -1)
        box._linealignequal(self.titles, self._symbolwidth + self._symbolspace, 1, 0)

    def bbox(self):
        """return a bbox for the key
        method should be called after dolayout"""
        result = self.titles[0].bbox()
        for title in self.titles[1:]:
            result = result + title.bbox() + bbox._bbox(0, title.center[1] - 0.5 * self._symbolheight,
                                                        0, title.center[1] + 0.5 * self._symbolheight)
        return result

    def paint(self, c, x, y):
        """paint the graph key into a canvas c at the position x and y (in postscript points)
        - method should be called after dolayout
        - the x, y alignment might be calculated by the graph using:
          - the bbox of the key as returned by the keys bbox method
          - the attributes _hdist, _vdist, hinside, and vinside of the key
          - the dimension and geometry of the graph"""
        sc = c.insert(canvas.canvas(trafomodule._translate(x, y)))
        for plotinfo, title in zip(self.plotinfos, self.titles):
            plotinfo.style.key(sc, 0, -0.5 * self._symbolheight + title.center[1],
                                   self._symbolwidth, self._symbolheight)
            sc.insert(title)


################################################################################
# graph
################################################################################


class plotinfo:

    def __init__(self, data, style):
        self.data = data
        self.style = style


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
        plotinfos = []
        first = 1
        for d in helper.ensuresequence(data):
            if not first:
                style = style.iterate()
            first = 0
            if d is not None:
                d.setstyle(self, style)
                plotinfos.append(plotinfo(d, style))
        self.plotinfos.extend(plotinfos)
        if helper.issequence(data):
            return plotinfos
        return plotinfos[0]

    def addkey(self, key, *plotinfos):
        if self.haslayout:
            raise RuntimeError("layout setup was already performed")
        self.addkeys.append((key, plotinfos))

    def _pos(self, x, y, xaxis=None, yaxis=None):
        if xaxis is None:
            xaxis = self.axes["x"]
        if yaxis is None:
            yaxis = self.axes["y"]
        return self._xpos+xaxis.convert(x)*self._width, self._ypos+yaxis.convert(y)*self._height

    def pos(self, x, y, xaxis=None, yaxis=None):
        if xaxis is None:
            xaxis = self.axes["x"]
        if yaxis is None:
            yaxis = self.axes["y"]
        return self.xpos+xaxis.convert(x)*self.width, self.ypos+yaxis.convert(y)*self.height

    def _vpos(self, vx, vy, xaxis=None, yaxis=None):
        if xaxis is None:
            xaxis = self.axes["x"]
        if yaxis is None:
            yaxis = self.axes["y"]
        return self._xpos+vx*self._width, self._ypos+vy*self._height

    def vpos(self, vx, vy, xaxis=None, yaxis=None):
        if xaxis is None:
            xaxis = self.axes["x"]
        if yaxis is None:
            yaxis = self.axes["y"]
        return self.xpos+vx*self.width, self.ypos+vy*self.height

    def xbaseline(self, x1=None, x2=None, axis=None):
        if axis is None:
            axis = self.axes["x"]
        if x1 is not None:
            v1 = axis.convert(x1)
        else:
            v1 = 0
        if x2 is not None:
            v2 = axis.convert(x2)
        else:
            v2 = 1
        return path._line(self._xpos+v1*self._width, axis._axispos,
                          self._xpos+v2*self._width, axis._axispos)

    def ybaseline(self, y1=None, y2=None, axis=None):
        if axis is None:
            axis = self.axes["y"]
        if y1 is not None:
            v1 = axis.convert(y1)
        else:
            v1 = 0
        if y2 is not None:
            v2 = axis.convert(y2)
        else:
            v2 = 1
        return path._line(axis._axispos, self._ypos+v1*self._height,
                          axis._axispos, self._ypos+v2*self._height)

    def vxbaseline(self, v1=None, v2=None, axis=None):
        if axis is None:
            axis = self.axes["x"]
        if v1 is None:
            v1 = 0
        if v2 is None:
            v2 = 1
        return path._line(self._xpos+v1*self._width, axis._axispos,
                          self._xpos+v2*self._width, axis._axispos)

    def vybaseline(self, v1=None, v2=None, axis=None):
        if axis is None:
            axis = self.axes["y"]
        if v1 is None:
            v1 = 0
        if v2 is None:
            v2 = 1
        return path._line(axis._axispos, self._ypos+v1*self._height,
                          axis._axispos, self._ypos+v2*self._height)

    def xgridline(self, x, axis=None):
        if axis is None:
            axis = self.axes["x"]
        v = axis.convert(x)
        return path._line(self._xpos+v*self._width, self._ypos,
                          self._xpos+v*self._width, self._ypos+self._height)

    def ygridline(self, y, axis=None):
        if axis is None:
            axis = self.axes["y"]
        v = axis.convert(y)
        return path._line(self._xpos, self._ypos+v*self._height,
                          self._xpos+self._width, self._ypos+v*self._height)

    def vxgridline(self, v, axis=None):
        if axis is None:
            axis = self.axes["x"]
        return path._line(self._xpos+v*self._width, self._ypos,
                          self._xpos+v*self._width, self._ypos+self._height)

    def vygridline(self, v, axis=None):
        if axis is None:
            axis = self.axes["y"]
        return path._line(self._xpos, self._ypos+v*self._height,
                          self._xpos+self._width, self._ypos+v*self._height)

    def _xtickpoint(self, x, axis=None):
        if axis is None:
            axis = self.axes["x"]
        return self._xpos+axis.convert(x)*self._width, axis._axispos

    def _ytickpoint(self, y, axis=None):
        if axis is None:
            axis = self.axes["y"]
        return axis._axispos, self._ypos+axis.convert(y)*self._height

    def xtickpoint(self, x, axis=None):
        if axis is None:
            axis = self.axes["x"]
        return self.xpos+axis.convert(x)*self.width, axis.axispos

    def ytickpoint(self, y, axis=None):
        if axis is None:
            axis = self.axes["y"]
        return axis.axispos, self.ypos+axis.convert(y)*self.height

    def _vxtickpoint(self, v, axis=None):
        if axis is None:
            axis = self.axes["x"]
        return self._xpos+v*self._width, axis._axispos

    def _vytickpoint(self, v, axis=None):
        if axis is None:
            axis = self.axes["y"]
        return axis._axispos, self._ypos+v*self._height

    def vxtickpoint(self, v, axis=None):
        if axis is None:
            axis = self.axes["x"]
        return self.xpos+v*self.width, axis.axispos

    def vytickpoint(self, v, axis=None):
        if axis is None:
            axis = self.axes["y"]
        return axis.axispos, self.ypos+v*self.height

    def xtickdirection(self, x, axis=None):
        if axis is None:
            axis = self.axes["x"]
        return axis.fixtickdirection

    def ytickdirection(self, y, axis=None):
        if axis is None:
            axis = self.axes["y"]
        return axis.fixtickdirection

    def vxtickdirection(self, v, axis=None):
        if axis is None:
            axis = self.axes["x"]
        return axis.fixtickdirection

    def vytickdirection(self, v, axis=None):
        if axis is None:
            axis = self.axes["y"]
        return axis.fixtickdirection

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
        for plotinfo in self.plotinfos:
            pdranges = plotinfo.data.getranges()
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
        for plotinfo in self.plotinfos:
            plotinfo.data.setranges(ranges)
        # 3. gather ranges again
        self.gatherranges()

        # do the layout for all axes
        axesdist = unit.length(self.axesdist_str, default_type="v")

        XPattern = re.compile(r"%s([2-9]|[1-9][0-9]+)?$" % self.Names[0])
        YPattern = re.compile(r"%s([2-9]|[1-9][0-9]+)?$" % self.Names[1])
        xaxisextents = [0, 0]
        yaxisextents = [0, 0]
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
                    xaxisextents[num2] += axesdist

                axis.axispos = self.ypos + num2*self.height + num3*xaxisextents[num2]
                axis._axispos = unit.topt(axis.axispos)
                axis.fixtickdirection = (0, num3)

                axis.baseline = self.xbaseline
                axis.vbaseline = self.vxbaseline
                axis.gridline = self.xgridline
                axis.vgridline = self.vxgridline
                axis._tickpoint = self._xtickpoint
                axis.tickpoint = self.xtickpoint
                axis._vtickpoint = self._vxtickpoint
                axis.vtickpoint = self.vxtickpoint
                axis.tickdirection = self.xtickdirection
                axis.vtickdirection = self.vxtickdirection

            elif YPattern.match(key):

                if needyaxisdist[num2]:
                    yaxisextents[num2] += axesdist

                axis.axispos = self.xpos + num2*self.width + num3*yaxisextents[num2]
                axis._axispos = unit.topt(axis.axispos)
                axis.fixtickdirection = (num3, 0)

                axis.baseline = self.ybaseline
                axis.vbaseline = self.vybaseline
                axis.gridline = self.ygridline
                axis.vgridline = self.vygridline
                axis._tickpoint = self._ytickpoint
                axis.tickpoint = self.ytickpoint
                axis._vtickpoint = self._vytickpoint
                axis.vtickpoint = self.vytickpoint
                axis.tickdirection = self.ytickdirection
                axis.vtickdirection = self.vytickdirection

            else:
                raise ValueError("Axis key '%s' not allowed" % key)

            axis.finish(self)

            if XPattern.match(key):
                xaxisextents[num2] += axis.axiscanvas.extent
                needxaxisdist[num2] = 1
            if YPattern.match(key):
                yaxisextents[num2] += axis.axiscanvas.extent
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
            self.insert(axis.axiscanvas)

    def dodata(self):
        self.dolayout()
        if not self.removedomethod(self.dodata): return
        for plotinfo in self.plotinfos:
            plotinfo.data.draw(self)

    def _dokey(self, key, *plotinfos):
        key.setplotinfos(*plotinfos)
        key.dolayout(self)
        bbox = key.bbox()
        if key.right:
            if key.hinside:
                x = self._xpos + self._width - bbox.urx - key._hdist
            else:
                x = self._xpos + self._width - bbox.llx + key._hdist
        else:
            if key.hinside:
                x = self._xpos - bbox.llx + key._hdist
            else:
                x = self._xpos - bbox.urx - key._hdist
        if key.top:
            if key.vinside:
                y = self._ypos + self._height - bbox.ury - key._vdist
            else:
                y = self._ypos + self._height - bbox.lly + key._vdist
        else:
            if key.vinside:
                y = self._ypos - bbox.lly + key._vdist
            else:
                y = self._ypos - bbox.ury - key._vdist
        key.paint(self, x, y)

    def dokey(self):
        self.dolayout()
        if not self.removedomethod(self.dokey): return
        if self.key is not None:
            self._dokey(self.key, *self.plotinfos)
        for key, plotinfos in self.addkeys:
            self._dokey(key, *plotinfos)

    def finish(self):
        while len(self.domethods):
            self.domethods[0]()

    def initwidthheight(self, width, height, ratio):
        if (width is not None) and (height is None):
             self.width = unit.length(width)
             self.height = (1.0/ratio) * self.width
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

    def __init__(self, xpos=0, ypos=0, width=None, height=None, ratio=goldenmean,
                 key=None, backgroundattrs=None, axesdist="0.8 cm", **axes):
        canvas.canvas.__init__(self)
        self.xpos = unit.length(xpos)
        self.ypos = unit.length(ypos)
        self._xpos = unit.topt(self.xpos)
        self._ypos = unit.topt(self.ypos)
        self.initwidthheight(width, height, ratio)
        self.initaxes(axes, 1)
        self.key = key
        self.backgroundattrs = backgroundattrs
        self.axesdist_str = axesdist
        self.plotinfos = []
        self.domethods = [self.dolayout, self.dobackground, self.doaxes, self.dodata, self.dokey]
        self.haslayout = 0
        self.defaultstyle = {}
        self.addkeys = []

    def bbox(self):
        self.finish()
        return canvas.canvas.bbox(self)

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
#     def xbaseline(self, axis, x1, x2, xaxis=None):
#         if xaxis is None: xaxis = self.axes["x"]
#         return self.vxbaseline(axis, xaxis.convert(x1), xaxis.convert(x2))
# 
#     def ybaseline(self, axis, y1, y2, yaxis=None):
#         if yaxis is None: yaxis = self.axes["y"]
#         return self.vybaseline(axis, yaxis.convert(y1), yaxis.convert(y2))
# 
#     def zbaseline(self, axis, z1, z2, zaxis=None):
#         if zaxis is None: zaxis = self.axes["z"]
#         return self.vzbaseline(axis, zaxis.convert(z1), zaxis.convert(z2))
# 
#     def vxbaseline(self, axis, v1, v2):
#         return (path._line(*(self._vpos(v1, 0, 0) + self._vpos(v2, 0, 0))) +
#                 path._line(*(self._vpos(v1, 0, 1) + self._vpos(v2, 0, 1))) +
#                 path._line(*(self._vpos(v1, 1, 1) + self._vpos(v2, 1, 1))) +
#                 path._line(*(self._vpos(v1, 1, 0) + self._vpos(v2, 1, 0))))
# 
#     def vybaseline(self, axis, v1, v2):
#         return (path._line(*(self._vpos(0, v1, 0) + self._vpos(0, v2, 0))) +
#                 path._line(*(self._vpos(0, v1, 1) + self._vpos(0, v2, 1))) +
#                 path._line(*(self._vpos(1, v1, 1) + self._vpos(1, v2, 1))) +
#                 path._line(*(self._vpos(1, v1, 0) + self._vpos(1, v2, 0))))
# 
#     def vzbaseline(self, axis, v1, v2):
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
#         return bbox._bbox(self._xpos - 200, self._ypos - 200, self._xpos + 200, self._ypos + 200)


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
    "get attr out of a attr/changeattr"
    if isinstance(attr, _changeattr):
        return attr.getattr()
    return attr


def _getattrs(attrs):
    "get attrs out of a sequence of attr/changeattr"
    if attrs is not None:
        result = []
        for attr in helper.ensuresequence(attrs):
            if isinstance(attr, _changeattr):
                attr = attr.getattr()
            if attr is not None:
                result.append(attr)
        if len(result) or not len(attrs):
            return result


def _iterateattr(attr):
    "perform next to a attr/changeattr"
    if isinstance(attr, _changeattr):
        return attr.iterate()
    return attr


def _iterateattrs(attrs):
    "perform next to a sequence of attr/changeattr"
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
    "cycles through a sequence"

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

    def key(self, c, x, y, width, height):
        if self._symbolattrs is not None:
            self._drawsymbol(c, x + 0.5 * width, y + 0.5 * height)
        if self._lineattrs is not None:
            c.stroke(path._line(x, y + 0.5 * height, x + width, y + 0.5 * height), *self.lineattrs)

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

    def key(self, c, x, y, width, height):
        raise RuntimeError("style doesn't yet provide a key")


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
        if None not in (x, y, point[self.textindex]) and self._textattrs is not None:
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

    def key(self, c, x, y, width, height):
        raise RuntimeError("style doesn't yet provide a key")


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

    def key(self, c, x, y, width, height):
        raise RuntimeError("style doesn't yet provide a key")


class _bariterator(changeattr):

    def attr(self, index):
        return index, self.counter


class bar:

    def __init__(self, fromzero=1, stacked=0, skipmissing=1, xbar=0,
                       barattrs=helper.nodefault, _usebariterator=helper.nodefault, _previousbar=None):
        self.fromzero = fromzero
        self.stacked = stacked
        self.skipmissing = skipmissing
        self.xbar = xbar
        if barattrs is helper.nodefault:
            self._barattrs = (canvas.stroked(color.gray.black), changecolor.Rainbow())
        else:
            self._barattrs = barattrs
        if _usebariterator is helper.nodefault:
            self.bariterator = _bariterator()
        else:
            self.bariterator = _usebariterator
        self.previousbar = _previousbar

    def iteratedict(self):
        result = {}
        result["barattrs"] = _iterateattrs(self._barattrs)
        return result

    def iterate(self):
        return bar(fromzero=self.fromzero, stacked=self.stacked, xbar=self.xbar,
                   _usebariterator=_iterateattr(self.bariterator), _previousbar=self, **self.iteratedict())

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
                index = divmod(index, self.stacked)[0]

        vmin = vmax = None
        for point in points:
            if not self.skipmissing:
                if count != 1 and self.stacked != 1:
                    self.naxis.setname(point[self.ni], index)
                else:
                    self.naxis.setname(point[self.ni])
            try:
                v = point[self.vi] + 0.0
                if vmin is None or v < vmin: vmin = v
                if vmax is None or v > vmax: vmax = v
            except (TypeError, ValueError):
                pass
            else:
                if self.skipmissing:
                    if count != 1 and self.stacked != 1:
                        self.naxis.setname(point[self.ni], index)
                    else:
                        self.naxis.setname(point[self.ni])
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
                if self.barattrs is not None:
                    graph.fill(path.path(path._moveto(x1pos, y1pos),
                                         graph._connect(x1pos, y1pos, x2pos, y2pos),
                                         graph._connect(x2pos, y2pos, x3pos, y3pos),
                                         graph._connect(x3pos, y3pos, x4pos, y4pos),
                                         graph._connect(x4pos, y4pos, x1pos, y1pos), # no closepath (might not be straight)
                                         path.closepath()), *self.barattrs)
            except (TypeError, ValueError): pass

    def key(self, c, x, y, width, height):
        c.fill(path._rect(x, y, width, height), *self.barattrs)


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
            self.data = datamodule.datafile(file)
        else:
            self.data = file
        if title is helper.nodefault:
            self.title = "(unknown)"
        else:
            self.title = title
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

