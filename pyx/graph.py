#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2002-2004 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2003-2004 Michael Schindler <m-schindler@users.sourceforge.net>
# Copyright (C) 2002-2004 André Wobst <wobsta@users.sourceforge.net>
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
import attr, bbox, box, canvas, color, deco, helper, path, style, unit, mathtree
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

    def setbasepoints(self, basepoints):
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
# - an axis has a part attribute where it stores a partitioner or/and some
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
        "converts a float into a frac with finite resolution"
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
            except (TypeError, AttributeError):
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
        self.labelattrs = labelattrs

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


def _mergeticklists(list1, list2):
    """helper function to merge tick lists
    - return a merged list of ticks out of list1 and list2
    - CAUTION: original lists have to be ordered
      (the returned list is also ordered)"""
    # TODO: improve this using bisect?!

    # XXX do not the original lists
    list1 = list1[:]
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
    - labels need to be a list of lists of strings,
      where the first list contain the strings to be
      used as labels for the ticks with labellevel 0,
      the second list for labellevel 1, etc.
    - when the maximum labellevel is 0, just a list of
      strings might be provided as the labels argument
    - IndexError is raised, when a list length doesn't match"""
    if helper.issequenceofsequences(labels):
        for label, level in zip(labels, xrange(sys.maxint)):
            usetext = helper.ensuresequence(label)
            i = 0
            for tick in ticks:
                if tick.labellevel == level:
                    tick.label = usetext[i]
                    i += 1
            if i != len(usetext):
                raise IndexError("wrong list length of labels at level %i" % level)
    elif labels is not None:
        usetext = helper.ensuresequence(labels)
        i = 0
        for tick in ticks:
            if tick.labellevel == 0:
                tick.label = usetext[i]
                i += 1
        if i != len(usetext):
            raise IndexError("wrong list length of labels")

def _maxlevels(ticks):
    "returns a tuple maxticklist, maxlabellevel from a list of tick instances"
    maxticklevel = maxlabellevel = 0
    for tick in ticks:
        if tick.ticklevel is not None and tick.ticklevel >= maxticklevel:
            maxticklevel = tick.ticklevel + 1
        if tick.labellevel is not None and tick.labellevel >= maxlabellevel:
            maxlabellevel = tick.labellevel + 1
    return maxticklevel, maxlabellevel


class _Iparter:
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


class linparter:
    """linear partition scheme
    ticks and label distances are explicitly provided to the constructor"""

    __implements__ = _Iparter

    def __init__(self, tickdist=None, labeldist=None, labels=None, extendtick=0, extendlabel=None, epsilon=1e-10):
        """configuration of the partition scheme
        - tickdist and labeldist should be a list, where the first value
          is the distance between ticks with ticklevel/labellevel 0,
          the second list for ticklevel/labellevel 1, etc.;
          a single entry is allowed without being a list
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
          without creating another tick specified by extendtick/extendlabel"""
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

        ticks = []
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


class autolinparter:
    """automatic linear partition scheme
    - possible tick distances are explicitly provided to the constructor
    - tick distances are adjusted to the axis range by multiplication or division by 10"""

    __implements__ = _Iparter

    defaultvariants = ((frac((1, 1)), frac((1, 2))),
                       (frac((2, 1)), frac((1, 1))),
                       (frac((5, 2)), frac((5, 4))),
                       (frac((5, 1)), frac((5, 2))))

    def __init__(self, variants=defaultvariants, extendtick=0, epsilon=1e-10):
        """configuration of the partition scheme
        - variants is a list of tickdist
        - tickdist should be a list, where the first value
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
          without creating another tick specified by extendtick"""
        self.variants = variants
        self.extendtick = extendtick
        self.epsilon = epsilon

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
        part = linparter(tickdist=useticks, extendtick=self.extendtick, epsilon=self.epsilon)
        return part.defaultpart(self.min, self.max, self.extendmin, self.extendmax)

    def lesspart(self):
        if self.lesstickindex < len(self.variants) - 1:
            self.lesstickindex += 1
        else:
            self.lesstickindex = 0
            self.lessbase.enum *= 10
        ticks = map(frac, self.variants[self.lesstickindex])
        useticks = [tick * self.lessbase for tick in ticks]
        part = linparter(tickdist=useticks, extendtick=self.extendtick, epsilon=self.epsilon)
        return part.defaultpart(self.min, self.max, self.extendmin, self.extendmax)

    def morepart(self):
        if self.moretickindex:
            self.moretickindex -= 1
        else:
            self.moretickindex = len(self.variants) - 1
            self.morebase.denom *= 10
        ticks = map(frac, self.variants[self.moretickindex])
        useticks = [tick * self.morebase for tick in ticks]
        part = linparter(tickdist=useticks, extendtick=self.extendtick, epsilon=self.epsilon)
        return part.defaultpart(self.min, self.max, self.extendmin, self.extendmax)


class preexp:
    """storage class for the definition of logarithmic axes partitions
    instances of this class define tick positions suitable for
    logarithmic axes by the following instance variables:
    - exp: integer, which defines multiplicator (usually 10)
    - pres: list of tick positions (rational numbers, e.g. instances of frac)
    possible positions are these tick positions and arbitrary divisions
    and multiplications by the exp value"""

    def __init__(self, pres, exp):
         "create a preexp instance and store its pres and exp information"
         self.pres = helper.ensuresequence(pres)
         self.exp = exp


class logparter(linparter):
    """logarithmic partition scheme
    ticks and label positions are explicitly provided to the constructor"""

    __implements__ = _Iparter

    pre1exp5   = preexp(frac((1, 1)), 100000)
    pre1exp4   = preexp(frac((1, 1)), 10000)
    pre1exp3   = preexp(frac((1, 1)), 1000)
    pre1exp2   = preexp(frac((1, 1)), 100)
    pre1exp    = preexp(frac((1, 1)), 10)
    pre125exp  = preexp((frac((1, 1)), frac((2, 1)), frac((5, 1))), 10)
    pre1to9exp = preexp(map(lambda x: frac((x, 1)), range(1, 10)), 10)
    #  ^- we always include 1 in order to get extendto(tick|label)level to work as expected

    def __init__(self, tickpos=None, labelpos=None, labels=None, extendtick=0, extendlabel=None, epsilon=1e-10):
        """configuration of the partition scheme
        - tickpos and labelpos should be a list, where the first entry
          is a preexp instance describing ticks with ticklevel/labellevel 0,
          the second is a preexp instance for ticklevel/labellevel 1, etc.;
          a single entry is allowed without being a list
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
          specified by extendtick/extendlabel"""
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
        ticks = []
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


class autologparter(logparter):
    """automatic logarithmic partition scheme
    possible tick positions are explicitly provided to the constructor"""

    __implements__ = _Iparter

    defaultvariants = (((logparter.pre1exp,      # ticks
                         logparter.pre1to9exp),  # subticks
                        (logparter.pre1exp,      # labels
                         logparter.pre125exp)),  # sublevels

                       ((logparter.pre1exp,      # ticks
                         logparter.pre1to9exp),  # subticks
                        None),                 # labels like ticks

                       ((logparter.pre1exp2,     # ticks
                         logparter.pre1exp),     # subticks
                        None),                 # labels like ticks

                       ((logparter.pre1exp3,     # ticks
                         logparter.pre1exp),     # subticks
                        None),                 # labels like ticks

                       ((logparter.pre1exp4,     # ticks
                         logparter.pre1exp),     # subticks
                        None),                 # labels like ticks

                       ((logparter.pre1exp5,     # ticks
                         logparter.pre1exp),     # subticks
                        None))                 # labels like ticks

    def __init__(self, variants=defaultvariants, extendtick=0, extendlabel=None, epsilon=1e-10):
        """configuration of the partition scheme
        - variants should be a list of pairs of lists of preexp
          instances
        - within each pair the first list contains preexp, where
          the first preexp instance describes ticks positions with
          ticklevel 0, the second preexp for ticklevel 1, etc.
        - the second list within each pair describes the same as
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
          specified by extendtick/extendlabel"""
        self.variants = variants
        if len(variants) > 2:
            self.variantsindex = divmod(len(variants), 2)[0]
        else:
            self.variantsindex = 0
        self.extendtick = extendtick
        self.extendlabel = extendlabel
        self.epsilon = epsilon

    def defaultpart(self, min, max, extendmin, extendmax):
        self.min, self.max, self.extendmin, self.extendmax = min, max, extendmin, extendmax
        self.morevariantsindex = self.variantsindex
        self.lessvariantsindex = self.variantsindex
        part = logparter(tickpos=self.variants[self.variantsindex][0], labelpos=self.variants[self.variantsindex][1],
                         extendtick=self.extendtick, extendlabel=self.extendlabel, epsilon=self.epsilon)
        return part.defaultpart(self.min, self.max, self.extendmin, self.extendmax)

    def lesspart(self):
        self.lessvariantsindex += 1
        if self.lessvariantsindex < len(self.variants):
            part = logparter(tickpos=self.variants[self.lessvariantsindex][0], labelpos=self.variants[self.lessvariantsindex][1],
                             extendtick=self.extendtick, extendlabel=self.extendlabel, epsilon=self.epsilon)
            return part.defaultpart(self.min, self.max, self.extendmin, self.extendmax)

    def morepart(self):
        self.morevariantsindex -= 1
        if self.morevariantsindex >= 0:
            part = logparter(tickpos=self.variants[self.morevariantsindex][0], labelpos=self.variants[self.morevariantsindex][1],
                             extendtick=self.extendtick, extendlabel=self.extendlabel, epsilon=self.epsilon)
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
        - the distances are a list of positive floats in PostScript points
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
    stdrange = cuberater(1, weight=2)
    stddistance = distancerater("1 cm")

    def __init__(self, ticks=linticks, labels=linlabels, range=stdrange, distance=stddistance):
        """initializes the axis rater
        - ticks and labels are lists of instances of a value rater
        - the first entry in ticks rate the number of ticks, the
          second the number of subticks, etc.; when there are no
          ticks of a level or there is not rater for a level, the
          level is just ignored
        - labels is analogous, but for labels
        - within the rating, all ticks with a higher level are
          considered as ticks for a given level
        - range is a value rater instance, which rates the covering
          of an axis range by the ticks (as a relative value of the
          tick range vs. the axis range), ticks might cover less or
          more than the axis range (for the standard automatic axis
          partition schemes an extention of the axis range is normal
          and should get some penalty)
        - distance is an distance rater instance"""
        self.ticks = ticks
        self.labels = labels
        self.range = range
        self.distance = distance

    def rateticks(self, axis, ticks, density):
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
        maxticklevel, maxlabellevel = _maxlevels(ticks)
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
        for numtick, rater in zip(numticks, self.ticks):
            rate += rater.rate(numtick, density)
            weight += rater.weight
        for numlabel, rater in zip(numlabels, self.labels):
            rate += rater.rate(numlabel, density)
            weight += rater.weight
        return rate/weight

    def raterange(self, tickrange, datarange):
        """rate the range covered by the ticks compared to the range
        of the data
        - tickrange and datarange are the ranges covered by the ticks
          and the data in graph coordinates
        - usually, the datarange is 1 (ticks are calculated for a
          given datarange)
        - the ticks might cover less or more than the data range (for
          the standard automatic axis partition schemes an extention
          of the axis range is normal and should get some penalty)"""
        return self.range.rate(tickrange, datarange)

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
                distances = [axiscanvas.labels[i].boxdistance_pt(axiscanvas.labels[i+1]) for i in range(len(axiscanvas.labels) - 1)]
            except box.BoxCrossError:
                return None
            return self.distance.rate(distances, density)
        else:
            return None


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
        - the method might modify the labelattrs attribute of the ticks; be sure
          to not modify it in-place!"""


class rationaltexter:
    "a texter creating rational labels (e.g. 'a/b' or even 'a \over b')"
    # XXX: we use divmod here to be more expicit

    __implements__ = _Itexter

    def __init__(self, prefix="", infix="", suffix="",
                       enumprefix="", enuminfix="", enumsuffix="",
                       denomprefix="", denominfix="", denomsuffix="",
                       plus="", minus="-", minuspos=0, over=r"{{%s}\over{%s}}",
                       equaldenom=0, skip1=1, skipenum0=1, skipenum1=1, skipdenom1=1,
                       labelattrs=[textmodule.mathmode]):
        r"""initializes the instance
        - prefix, infix, and suffix (strings) are added at the begin,
          immediately after the minus, and at the end of the label,
          respectively
        - prefixenum, infixenum, and suffixenum (strings) are added
          to the labels enumerator correspondingly
        - prefixdenom, infixdenom, and suffixdenom (strings) are added
          to the labels denominator correspondingly
        - plus or minus (string) is inserted for non-negative or negative numbers
        - minuspos is an integer, which determines the position, where the
          plus or minus sign has to be placed; the following values are allowed:
            1 - writes the plus or minus in front of the enumerator
            0 - writes the plus or minus in front of the hole fraction
           -1 - writes the plus or minus in front of the denominator
        - over (string) is taken as a format string generating the
          fraction bar; it has to contain exactly two string insert
          operators "%s" -- the first for the enumerator and the second
          for the denominator; by far the most common examples are
          r"{{%s}\over{%s}}" and "{{%s}/{%s}}"
        - usually the enumerator and denominator are canceled; however,
          when equaldenom is set, the least common multiple of all
          denominators is used
        - skip1 (boolean) just prints the prefix, the plus or minus,
          the infix and the suffix, when the value is plus or minus one
          and at least one of prefix, infix and the suffix is present
        - skipenum0 (boolean) just prints a zero instead of
          the hole fraction, when the enumerator is zero;
          no prefixes, infixes, and suffixes are taken into account
        - skipenum1 (boolean) just prints the enumprefix, the plus or minus,
          the enuminfix and the enumsuffix, when the enum value is plus or minus one
          and at least one of enumprefix, enuminfix and the enumsuffix is present
        - skipdenom1 (boolean) just prints the enumerator instead of
          the hole fraction, when the denominator is one and none of the parameters
          denomprefix, denominfix and denomsuffix are set and minuspos is not -1 or the
          fraction is positive
        - labelattrs is a list of attributes for a texrunners text method;
          None is considered as an empty list; labelattrs might be changed
          in the painter as well"""
        self.prefix = prefix
        self.infix = infix
        self.suffix = suffix
        self.enumprefix = enumprefix
        self.enuminfix = enuminfix
        self.enumsuffix = enumsuffix
        self.denomprefix = denomprefix
        self.denominfix = denominfix
        self.denomsuffix = denomsuffix
        self.plus = plus
        self.minus = minus
        self.minuspos = minuspos
        self.over = over
        self.equaldenom = equaldenom
        self.skip1 = skip1
        self.skipenum0 = skipenum0
        self.skipenum1 = skipenum1
        self.skipdenom1 = skipdenom1
        self.labelattrs = labelattrs

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
                    tick.temp_fracminus = -tick.temp_fracminus
                    tick.temp_fracenum = -tick.temp_fracenum
                if tick.temp_fracdenom < 0:
                    tick.temp_fracminus = -tick.temp_fracminus
                    tick.temp_fracdenom = -tick.temp_fracdenom
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
                plusminus = self.minus
            else:
                plusminus = self.plus
            if self.minuspos == 0:
                fracminus = plusminus
            elif self.minuspos == 1:
                fracenumminus = plusminus
            elif self.minuspos == -1:
                fracdenomminus = plusminus
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
            tick.labelattrs = tick.labelattrs + self.labelattrs

            # del tick.temp_fracenum    # we've inserted those temporary variables ... and do not care any longer about them
            # del tick.temp_fracdenom
            # del tick.temp_fracminus



class decimaltexter:
    "a texter creating decimal labels (e.g. '1.234' or even '0.\overline{3}')"

    __implements__ = _Itexter

    def __init__(self, prefix="", infix="", suffix="", equalprecision=0,
                       decimalsep=".", thousandsep="", thousandthpartsep="",
                       plus="", minus="-", period=r"\overline{%s}",
                       labelattrs=[textmodule.mathmode]):
        r"""initializes the instance
        - prefix, infix, and suffix (strings) are added at the begin,
          immediately after the minus, and at the end of the label,
          respectively
        - decimalsep, thousandsep, and thousandthpartsep (strings)
          are used as separators
        - plus or minus (string) is inserted for non-negative or negative numbers
        - period (string) is taken as a format string generating a period;
          it has to contain exactly one string insert operators "%s" for the
          period; usually it should be r"\overline{%s}"
        - labelattrs is a list of attributes for a texrunners text method;
          a single is allowed without being a list; None is considered as
          an empty list; labelattrs might be changed in the painter as well"""
        self.prefix = prefix
        self.infix = infix
        self.suffix = suffix
        self.equalprecision = equalprecision
        self.decimalsep = decimalsep
        self.thousandsep = thousandsep
        self.thousandthpartsep = thousandthpartsep
        self.plus = plus
        self.minus = minus
        self.period = period
        self.labelattrs = labelattrs

    def labels(self, ticks):
        labeledticks = []
        maxdecprecision = 0
        for tick in ticks:
            if tick.label is None and tick.labellevel is not None:
                labeledticks.append(tick)
                m, n = tick.enum, tick.denom
                if m < 0: m = -m
                if n < 0: n = -n
                quotient, remainder = divmod(m, n)
                quotient = str(quotient)
                if len(self.thousandsep):
                    l = len(quotient)
                    tick.label = ""
                    for i in range(l):
                        tick.label += quotient[i]
                        if not ((l-i-1) % 3) and l > i+1:
                            tick.label += self.thousandsep
                else:
                    tick.label = quotient
                if remainder:
                    tick.label += self.decimalsep
                oldremainders = []
                tick.temp_decprecision = 0
                while (remainder):
                    tick.temp_decprecision += 1
                    if remainder in oldremainders:
                        tick.temp_decprecision = None
                        periodstart = len(tick.label) - (len(oldremainders) - oldremainders.index(remainder))
                        tick.label = tick.label[:periodstart] + self.period % tick.label[periodstart:]
                        break
                    oldremainders += [remainder]
                    remainder *= 10
                    quotient, remainder = divmod(remainder, n)
                    if not ((tick.temp_decprecision - 1) % 3) and tick.temp_decprecision > 1:
                        tick.label += self.thousandthpartsep
                    tick.label += str(quotient)
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
                plusminus = self.minus
            else:
                plusminus = self.plus
            tick.label = "%s%s%s%s%s" % (self.prefix, plusminus, self.infix, tick.label, self.suffix)
            tick.labelattrs = tick.labelattrs + self.labelattrs

            # del tick.temp_decprecision  # we've inserted this temporary variable ... and do not care any longer about it


class exponentialtexter:
    "a texter creating labels with exponentials (e.g. '2\cdot10^5')"

    __implements__ = _Itexter

    def __init__(self, plus="", minus="-",
                       mantissaexp=r"{{%s}\cdot10^{%s}}",
                       skipexp0=r"{%s}",
                       skipexp1=None,
                       nomantissaexp=r"{10^{%s}}",
                       minusnomantissaexp=r"{-10^{%s}}",
                       mantissamin=frac((1, 1)), mantissamax=frac((10, 1)),
                       skipmantissa1=0, skipallmantissa1=1,
                       mantissatexter=decimaltexter()):
        r"""initializes the instance
        - plus or minus (string) is inserted for non-negative or negative exponents
        - mantissaexp (string) is taken as a format string generating the exponent;
          it has to contain exactly two string insert operators "%s" --
          the first for the mantissa and the second for the exponent;
          examples are r"{{%s}\cdot10^{%s}}" and r"{{%s}{\rm e}{%s}}"
        - skipexp0 (string) is taken as a format string used for exponent 0;
          exactly one string insert operators "%s" for the mantissa;
          None turns off the special handling of exponent 0;
          an example is r"{%s}"
        - skipexp1 (string) is taken as a format string used for exponent 1;
          exactly one string insert operators "%s" for the mantissa;
          None turns off the special handling of exponent 1;
          an example is r"{{%s}\cdot10}"
        - nomantissaexp (string) is taken as a format string generating the exponent
          when the mantissa is one and should be skipped; it has to contain
          exactly one string insert operators "%s" for the exponent;
          an examples is r"{10^{%s}}"
        - minusnomantissaexp (string) is taken as a format string generating the exponent
          when the mantissa is minus one and should be skipped; it has to contain
          exactly one string insert operators "%s" for the exponent;
          None turns off the special handling of mantissa -1;
          an examples is r"{-10^{%s}}"
        - mantissamin and mantissamax are the minimum and maximum of the mantissa;
          they are frac instances greater than zero and mantissamin < mantissamax;
          the sign of the tick is ignored here
        - skipmantissa1 (boolean) turns on skipping of any mantissa equals one
          (and minus when minusnomantissaexp is set)
        - skipallmantissa1 (boolean) as above, but all mantissas must be 1 (or -1)
        - mantissatexter is the texter for the mantissa
        - the skipping of a mantissa is stronger than the skipping of an exponent"""
        self.plus = plus
        self.minus = minus
        self.mantissaexp = mantissaexp
        self.skipexp0 = skipexp0
        self.skipexp1 = skipexp1
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
                if tick.temp_exp == "0" and self.skipexp0 is not None:
                    tick.label = self.skipexp0 % tick.label
                elif tick.temp_exp == "1" and self.skipexp1 is not None:
                    tick.label = self.skipexp1 % tick.label
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
        """initializes the instance
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


class axiscanvas(canvas._canvas):
    """axis canvas
    - an axis canvas is a regular canvas returned by an
      axispainters painter method
    - it contains a PyX length extent to be used for the
      alignment of additional axes; the axis extent should
      be handled by the axispainters painter method; you may
      apprehend this as a size information comparable to a
      bounding box, which must be handled manually
    - it contains a list of textboxes called labels which are
      used to rate the distances between the labels if needed
      by the axis later on; the painter method has not only to
      insert the labels into this canvas, but should also fill
      this list, when a rating of the distances should be
      performed by the axis"""

    # __implements__ = sole implementation

    def __init__(self, *args, **kwargs):
        """initializes the instance
        - sets extent to zero
        - sets labels to an empty list"""
        canvas._canvas.__init__(self, *args, **kwargs)
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
        while (direction > 180 + self.epsilon):
            direction -= 360
        while (direction < -180 - self.epsilon):
            direction += 360
        while (direction > 90 + self.epsilon):
            direction -= 180
        while (direction < -90 - self.epsilon):
            direction += 180
        return trafomodule.rotate(direction)


rotatetext.parallel = rotatetext(90)
rotatetext.orthogonal = rotatetext(180)


class _Iaxispainter:
    "class for painting axes"

    def paint(self, axispos, axis, ac=None):
        """paint the axis into an axiscanvas
        - returns the axiscanvas
        - when no axiscanvas is provided (the typical case), a new
          axiscanvas is created. however, when extending an painter
          by inheritance, painting on the same axiscanvas is supported
          by setting the axiscanvas attribute
        - axispos is an instance, which implements _Iaxispos to
          define the tick positions
        - the axis and should not be modified (we may
          add some temporary variables like axis.ticks[i].temp_xxx,
          which might be used just temporary) -- the idea is that
          all things can be used several times
        - also do not modify the instance (self) -- even this
          instance might be used several times; thus do not modify
          attributes like self.titleattrs etc. (use local copies)
        - the method might access some additional attributes from
          the axis, e.g. the axis title -- the axis painter should
          document this behavior and rely on the availability of
          those attributes -> it becomes a question of the proper
          usage of the combination of axis & axispainter
        - the axiscanvas is a axiscanvas instance and should be
          filled with ticks, labels, title, etc.; note that the
          extent and labels instance variables should be handled
          as documented in the axiscanvas"""


class _Iaxispos:
    """interface definition of axis tick position methods
    - these methods are used for the postitioning of the ticks
      when painting an axis"""
    # TODO: should we add a local transformation (for label text etc?)
    #       (this might replace tickdirection (and even tickposition?))

    def basepath(self, x1=None, x2=None):
        """return the basepath as a path
        - x1 is the start position; if not set, the basepath starts
          from the beginning of the axis, which might imply a
          value outside of the graph coordinate range [0; 1]
        - x2 is analogous to x1, but for the end position"""

    def vbasepath(self, v1=None, v2=None):
        """return the basepath as a path
        - like basepath, but for graph coordinates"""

    def gridpath(self, x):
        """return the gridpath as a path for a given position x
        - might return None when no gridpath is available"""

    def vgridpath(self, v):
        """return the gridpath as a path for a given position v
        in graph coordinates
        - might return None when no gridpath is available"""

    def tickpoint_pt(self, x):
        """return the position at the basepath as a tuple (x, y) in
        postscript points for the position x"""

    def tickpoint(self, x):
        """return the position at the basepath as a tuple (x, y) in
        in PyX length for the position x"""

    def vtickpoint_pt(self, v):
        "like tickpoint_pt, but for graph coordinates"

    def vtickpoint(self, v):
        "like tickpoint, but for graph coordinates"

    def tickdirection(self, x):
        """return the direction of a tick as a tuple (dx, dy) for the
        position x (the direction points towards the graph)"""

    def vtickdirection(self, v):
        """like tickposition, but for graph coordinates"""


class _axispos:
    """implements those parts of _Iaxispos which can be build
    out of the axis convert method and other _Iaxispos methods
    - base _Iaxispos methods, which need to be implemented:
      - vbasepath
      - vgridpath
      - vtickpoint_pt
      - vtickdirection
    - other methods needed for _Iaxispos are build out of those
      listed above when this class is inherited"""

    def __init__(self, convert):
        """initializes the instance
        - convert is a convert method from an axis"""
        self.convert = convert

    def basepath(self, x1=None, x2=None):
        if x1 is None:
            if x2 is None:
                return self.vbasepath()
            else:
                return self.vbasepath(v2=self.convert(x2))
        else:
            if x2 is None:
                return self.vbasepath(v1=self.convert(x1))
            else:
                return self.vbasepath(v1=self.convert(x1), v2=self.convert(x2))

    def gridpath(self, x):
        return self.vgridpath(self.convert(x))

    def tickpoint_pt(self, x):
        return self.vtickpoint_pt(self.convert(x))

    def tickpoint(self, x):
        return self.vtickpoint(self.convert(x))

    def vtickpoint(self, v):
        return [unit.t_pt(x) for x in self.vtickpoint(v)]

    def tickdirection(self, x):
        return self.vtickdirection(self.convert(x))


class pathaxispos(_axispos):
    """axis tick position methods along an arbitrary path"""

    __implements__ = _Iaxispos

    def __init__(self, p, convert, direction=1):
        self.path = p
        self.normpath = path.normpath(p)
        self.arclength = self.normpath.arclength()
        _axispos.__init__(self, convert)
        self.direction = direction

    def vbasepath(self, v1=None, v2=None):
        if v1 is None:
            if v2 is None:
                return self.path
            else:
                return self.normpath.split(self.normpath.lentopar(v2 * self.arclength))[0]
        else:
            if v2 is None:
                return self.normpath.split(self.normpath.lentopar(v1 * self.arclength))[1]
            else:
                return self.normpath.split(*self.normpath.lentopar([v1 * self.arclength, v2 * self.arclength]))[1]

    def vgridpath(self, v):
        return None

    def vtickpoint_pt(self, v):
        # XXX: path._at missing!
        return [unit.topt(x) for x in self.normpath.at(self.normpath.lentopar(v * self.arclength))]

    def vtickdirection(self, v):
        t = self.normpath.tangent(self.normpath.lentopar(v * self.arclength))
        # XXX: path._begin and path._end missing!
        tbegin = [unit.topt(x) for x in t.begin()]
        tend = [unit.topt(x) for x in t.end()]
        dx = tend[0]-tbegin[0]
        dy = tend[1]-tbegin[1]
        norm = math.sqrt(dx*dx + dy*dy)
        if self.direction == 1:
            return -dy/norm, dx/norm
        elif self.direction == -1:
            return dy/norm, -dx/norm
        raise RuntimeError("unknown direction")


class axistitlepainter:
    """class for painting an axis title
    - the axis must have a title attribute when using this painter;
      this title might be None"""

    __implements__ = _Iaxispainter

    defaulttitleattrs = [textmodule.halign.center, textmodule.vshift.mathaxis]

    def __init__(self, titledist="0.3 cm",
                       titleattrs=[],
                       titledirection=rotatetext.parallel,
                       titlepos=0.5,
                       texrunner=textmodule.defaulttexrunner):
        """initialized the instance
        - titledist is a visual PyX length giving the distance
          of the title from the axis extent already there (a title might
          be added after labels or other things are plotted already)
        - titleattrs is a list of attributes for a texrunners text
          method; a single is allowed without being a list; None
          turns off the title
        - titledirection is an instance of rotatetext or None
        - titlepos is the position of the title in graph coordinates
        - texrunner is the texrunner to be used to create text
          (the texrunner is available for further use in derived
          classes as instance variable texrunner)"""
        self.titledist_str = titledist
        self.titleattrs = titleattrs
        self.titledirection = titledirection
        self.titlepos = titlepos
        self.texrunner = texrunner

    def paint(self, axispos, axis, ac=None):
        if ac is None:
            ac = axiscanvas()
        if axis.title is not None and self.titleattrs is not None:
            titledist = unit.length(self.titledist_str, default_type="v")
            x, y = axispos.vtickpoint_pt(self.titlepos)
            dx, dy = axispos.vtickdirection(self.titlepos)
            titleattrs = self.defaulttitleattrs + self.titleattrs
            if self.titledirection is not None:
                titleattrs.append(self.titledirection.trafo(dx, dy))
            title = self.texrunner.text_pt(x, y, axis.title, titleattrs)
            ac.extent += titledist
            title.linealign(ac.extent, -dx, -dy)
            ac.extent += title.extent(dx, dy)
            ac.insert(title)
        return ac


class geometricseries(attr.changeattr):

    def __init__(self, initial, factor):
        self.initial = initial
        self.factor = factor

    def select(self, index, total):
        return self.initial * (self.factor ** index)


class ticklength(geometricseries): pass

_base = 0.2

#ticklength.short = ticklength("%f cm" % (_base/math.sqrt(64)), 1/goldenmean)
ticklength.short = ticklength(_base/math.sqrt(64), 1/goldenmean)
ticklength.short = ticklength(_base/math.sqrt(32), 1/goldenmean)
ticklength.short = ticklength(_base/math.sqrt(16), 1/goldenmean)
ticklength.short = ticklength(_base/math.sqrt(8), 1/goldenmean)
ticklength.short = ticklength(_base/math.sqrt(4), 1/goldenmean)
ticklength.short = ticklength(_base/math.sqrt(2), 1/goldenmean)
ticklength.normal = ticklength(_base, 1/goldenmean)
ticklength.long = ticklength(_base*math.sqrt(2), 1/goldenmean)
ticklength.long = ticklength(_base*math.sqrt(4), 1/goldenmean)
ticklength.long = ticklength(_base*math.sqrt(8), 1/goldenmean)
ticklength.long = ticklength(_base*math.sqrt(16), 1/goldenmean)
ticklength.long = ticklength(_base*math.sqrt(32), 1/goldenmean)


class axispainter(axistitlepainter):
    """class for painting the ticks and labels of an axis
    - the inherited titleaxispainter is used to paint the title of
      the axis
    - note that the type of the elements of ticks given as an argument
      of the paint method must be suitable for the tick position methods
      of the axis"""

    __implements__ = _Iaxispainter

    defaulttickattrs = []
    defaultgridattrs = []
    defaultbasepathattrs = [style.linecap.square]
    defaultlabelattrs = [textmodule.halign.center, textmodule.vshift.mathaxis]

    def __init__(self, innerticklength=ticklength.short,
                       outerticklength=None,
                       tickattrs=[],
                       gridattrs=None,
                       basepathattrs=[],
                       labeldist="0.3 cm",
                       labelattrs=[],
                       labeldirection=None,
                       labelhequalize=0,
                       labelvequalize=1,
                       **kwargs):
        """initializes the instance
        - innerticklength and outerticklength are two lists of
          visual PyX lengths for ticks, subticks, etc. plotted inside
          and outside of the graph; when a single value is given, it
          is used for all tick levels; None turns off ticks inside or
          outside of the graph
        - tickattrs are a list of stroke attributes for the ticks;
          a single entry is allowed without being a list; None turns
          off ticks
        - gridattrs are a list of lists used as stroke
          attributes for ticks, subticks etc.; when a single list
          is given, it is used for ticks, subticks, etc.; a single
          entry is allowed without being a list; None turns off
          the grid
        - basepathattrs are a list of stroke attributes for a grid
          line at axis value zero; a single entry is allowed without
          being a list; None turns off the basepath
        - labeldist is a visual PyX length for the distance of the labels
          from the axis basepath
        - labelattrs is a list of attributes for a texrunners text
          method; a single entry is allowed without being a list;
          None turns off the labels
        - titledirection is an instance of rotatetext or None
        - labelhequalize and labelvequalize (booleans) perform an equal
          alignment for straight vertical and horizontal axes, respectively
        - futher keyword arguments are passed to axistitlepainter"""
        # TODO: access to axis.divisor -- document, remove, ... ???
        self.innerticklength_str = innerticklength
        self.outerticklength_str = outerticklength
        self.tickattrs = tickattrs
        self.gridattrs = gridattrs
        self.basepathattrs = basepathattrs
        self.labeldist_str = labeldist
        self.labelattrs = labelattrs
        self.labeldirection = labeldirection
        self.labelhequalize = labelhequalize
        self.labelvequalize = labelvequalize
        axistitlepainter.__init__(self, **kwargs)

    def paint(self, axispos, axis, ac=None):
        if ac is None:
            ac = axiscanvas()
        labeldist = unit.length(self.labeldist_str, default_type="v")
        for tick in axis.ticks:
            tick.temp_v = axis.convert(float(tick) * axis.divisor)
            tick.temp_x, tick.temp_y = axispos.vtickpoint_pt(tick.temp_v)
            tick.temp_dx, tick.temp_dy = axispos.vtickdirection(tick.temp_v)
        maxticklevel, maxlabellevel = _maxlevels(axis.ticks)

        # create & align tick.temp_labelbox
        for tick in axis.ticks:
            if tick.labellevel is not None:
                labelattrs = attr.selectattrs(self.labelattrs, tick.labellevel, maxlabellevel)
                if labelattrs is not None:
                    labelattrs = self.defaultlabelattrs + labelattrs
                    if self.labeldirection is not None:
                        labelattrs.append(self.labeldirection.trafo(tick.temp_dx, tick.temp_dy))
                    if tick.labelattrs is not None:
                        labelattrs.extend(tick.labelattrs)
                    tick.temp_labelbox = self.texrunner.text_pt(tick.temp_x, tick.temp_y, tick.label, labelattrs)
        if len(axis.ticks) > 1:
            equaldirection = 1
            for tick in axis.ticks[1:]:
                if tick.temp_dx != axis.ticks[0].temp_dx or tick.temp_dy != axis.ticks[0].temp_dy:
                    equaldirection = 0
        else:
            equaldirection = 0
        if equaldirection and ((not axis.ticks[0].temp_dx and self.labelvequalize) or
                               (not axis.ticks[0].temp_dy and self.labelhequalize)):
            if self.labelattrs is not None:
                box.linealignequal([tick.temp_labelbox for tick in axis.ticks if tick.labellevel is not None],
                                   labeldist, -axis.ticks[0].temp_dx, -axis.ticks[0].temp_dy)
        else:
            for tick in axis.ticks:
                if tick.labellevel is not None and self.labelattrs is not None:
                    tick.temp_labelbox.linealign(labeldist, -tick.temp_dx, -tick.temp_dy)

        for tick in axis.ticks:
            if tick.ticklevel is not None:
                innerticklength = attr.selectattr(self.innerticklength_str, tick.ticklevel, maxticklevel)
                outerticklength = attr.selectattr(self.outerticklength_str, tick.ticklevel, maxticklevel)
                if innerticklength is not None or outerticklength is not None:
                    if innerticklength is None:
                        innerticklength = 0
                    else:
                        innerticklength = unit.length(innerticklength, default_type="v")
                    if outerticklength is None:
                        outerticklength = 0
                    else:
                        outerticklength = unit.length(outerticklength, default_type="v")
                    tickattrs = attr.selectattrs(self.defaulttickattrs + self.tickattrs, tick.ticklevel, maxticklevel)
                    if tickattrs is not None:
                        innerticklength_pt = unit.topt(innerticklength)
                        outerticklength_pt = unit.topt(outerticklength)
                        x1 = tick.temp_x + tick.temp_dx * innerticklength_pt
                        y1 = tick.temp_y + tick.temp_dy * innerticklength_pt
                        x2 = tick.temp_x - tick.temp_dx * outerticklength_pt
                        y2 = tick.temp_y - tick.temp_dy * outerticklength_pt
                        ac.stroke(path.line_pt(x1, y1, x2, y2), tickattrs)
                        if outerticklength is not None and unit.topt(outerticklength) > unit.topt(ac.extent):
                            ac.extent = outerticklength
                        if outerticklength is not None and unit.topt(-innerticklength) > unit.topt(ac.extent):
                            ac.extent = -innerticklength
            if self.gridattrs is not None:
                gridattrs = attr.selectattrs(self.defaultgridattrs + self.gridattrs, tick.ticklevel, maxticklevel)
                ac.stroke(axispos.vgridpath(tick.temp_v), gridattrs)
            if tick.labellevel is not None and self.labelattrs is not None:
                ac.insert(tick.temp_labelbox)
                ac.labels.append(tick.temp_labelbox)
                extent = tick.temp_labelbox.extent(tick.temp_dx, tick.temp_dy) + labeldist
                if unit.topt(extent) > unit.topt(ac.extent):
                    ac.extent = extent
        if self.basepathattrs is not None:
            ac.stroke(axispos.vbasepath(), self.defaultbasepathattrs + self.basepathattrs)

        # for tick in axis.ticks:
        #     del tick.temp_v    # we've inserted those temporary variables ... and do not care any longer about them
        #     del tick.temp_x
        #     del tick.temp_y
        #     del tick.temp_dx
        #     del tick.temp_dy
        #     if tick.labellevel is not None and self.labelattrs is not None:
        #         del tick.temp_labelbox

        axistitlepainter.paint(self, axispos, axis, ac=ac)

        return ac


class linkaxispainter(axispainter):
    """class for painting a linked axis
    - the inherited axispainter is used to paint the axis
    - modifies some constructor defaults"""

    __implements__ = _Iaxispainter

    def __init__(self, labelattrs=None,
                       titleattrs=None,
                       **kwargs):
        """initializes the instance
        - the labelattrs default is set to None thus skipping the labels
        - the titleattrs default is set to None thus skipping the title
        - all keyword arguments are passed to axispainter"""
        axispainter.__init__(self, labelattrs=labelattrs,
                                   titleattrs=titleattrs,
                                   **kwargs)


class subaxispos:
    """implementation of the _Iaxispos interface for a subaxis"""

    __implements__ = _Iaxispos

    def __init__(self, convert, baseaxispos, vmin, vmax, vminover, vmaxover):
        """initializes the instance
        - convert is the subaxis convert method
        - baseaxispos is the axispos instance of the base axis
        - vmin, vmax is the range covered by the subaxis in graph coordinates
        - vminover, vmaxover is the extended range of the subaxis including
          regions between several subaxes (for basepath drawing etc.)"""
        self.convert = convert
        self.baseaxispos = baseaxispos
        self.vmin = vmin
        self.vmax = vmax
        self.vminover = vminover
        self.vmaxover = vmaxover

    def basepath(self, x1=None, x2=None):
        if x1 is not None:
            v1 = self.vmin+self.convert(x1)*(self.vmax-self.vmin)
        else:
            v1 = self.vminover
        if x2 is not None:
            v2 = self.vmin+self.convert(x2)*(self.vmax-self.vmin)
        else:
            v2 = self.vmaxover
        return self.baseaxispos.vbasepath(v1, v2)

    def vbasepath(self, v1=None, v2=None):
        if v1 is not None:
            v1 = self.vmin+v1*(self.vmax-self.vmin)
        else:
            v1 = self.vminover
        if v2 is not None:
            v2 = self.vmin+v2*(self.vmax-self.vmin)
        else:
            v2 = self.vmaxover
        return self.baseaxispos.vbasepath(v1, v2)

    def gridpath(self, x):
        return self.baseaxispos.vgridpath(self.vmin+self.convert(x)*(self.vmax-self.vmin))

    def vgridpath(self, v):
        return self.baseaxispos.vgridpath(self.vmin+v*(self.vmax-self.vmin))

    def tickpoint_pt(self, x, axis=None):
        return self.baseaxispos.vtickpoint_pt(self.vmin+self.convert(x)*(self.vmax-self.vmin))

    def tickpoint(self, x, axis=None):
        return self.baseaxispos.vtickpoint(self.vmin+self.convert(x)*(self.vmax-self.vmin))

    def vtickpoint_pt(self, v, axis=None):
        return self.baseaxispos.vtickpoint_pt(self.vmin+v*(self.vmax-self.vmin))

    def vtickpoint(self, v, axis=None):
        return self.baseaxispos.vtickpoint(self.vmin+v*(self.vmax-self.vmin))

    def tickdirection(self, x, axis=None):
        return self.baseaxispos.vtickdirection(self.vmin+self.convert(x)*(self.vmax-self.vmin))

    def vtickdirection(self, v, axis=None):
        return self.baseaxispos.vtickdirection(self.vmin+v*(self.vmax-self.vmin))


class splitaxispainter(axistitlepainter):
    """class for painting a splitaxis
    - the inherited titleaxispainter is used to paint the title of
      the axis
    - the splitaxispainter access the subaxes attribute of the axis"""

    __implements__ = _Iaxispainter

    defaultbreaklinesattrs = []

    def __init__(self, breaklinesdist="0.05 cm",
                       breaklineslength="0.5 cm",
                       breaklinesangle=-60,
                       breaklinesattrs=[],
                       **args):
        """initializes the instance
        - breaklinesdist is a visual length of the distance between
          the two lines of the axis break
        - breaklineslength is a visual length of the length of the
          two lines of the axis break
        - breaklinesangle is the angle of the lines of the axis break
        - breaklinesattrs are a list of stroke attributes for the
          axis break lines; a single entry is allowed without being a
          list; None turns off the break lines
        - futher keyword arguments are passed to axistitlepainter"""
        self.breaklinesdist_str = breaklinesdist
        self.breaklineslength_str = breaklineslength
        self.breaklinesangle = breaklinesangle
        self.breaklinesattrs = breaklinesattrs
        axistitlepainter.__init__(self, **args)

    def paint(self, axispos, axis, ac=None):
        if ac is None:
            ac = axiscanvas()
        for subaxis in axis.subaxes:
            subaxis.finish(subaxispos(subaxis.convert, axispos, subaxis.vmin, subaxis.vmax, subaxis.vminover, subaxis.vmaxover))
            ac.insert(subaxis.axiscanvas)
            if unit.topt(ac.extent) < unit.topt(subaxis.axiscanvas.extent):
                ac.extent = subaxis.axiscanvas.extent
        if self.breaklinesattrs is not None:
            self.breaklinesdist = unit.length(self.breaklinesdist_str, default_type="v")
            self.breaklineslength = unit.length(self.breaklineslength_str, default_type="v")
            self.sin = math.sin(self.breaklinesangle*math.pi/180.0)
            self.cos = math.cos(self.breaklinesangle*math.pi/180.0)
            breaklinesextent = (0.5*self.breaklinesdist*math.fabs(self.cos) +
                                0.5*self.breaklineslength*math.fabs(self.sin))
            if unit.topt(ac.extent) < unit.topt(breaklinesextent):
                ac.extent = breaklinesextent
            for subaxis1, subaxis2 in zip(axis.subaxes[:-1], axis.subaxes[1:]):
                # use a tangent of the basepath (this is independent of the tickdirection)
                v = 0.5 * (subaxis1.vmax + subaxis2.vmin)
                p = path.normpath(axispos.vbasepath(v, None))
                breakline = p.tangent(0, self.breaklineslength)
                widthline = p.tangent(0, self.breaklinesdist).transformed(trafomodule.rotate(self.breaklinesangle+90, *breakline.begin()))
                tocenter = map(lambda x: 0.5*(x[0]-x[1]), zip(breakline.begin(), breakline.end()))
                towidth = map(lambda x: 0.5*(x[0]-x[1]), zip(widthline.begin(), widthline.end()))
                breakline = breakline.transformed(trafomodule.translate(*tocenter).rotated(self.breaklinesangle, *breakline.begin()))
                breakline1 = breakline.transformed(trafomodule.translate(*towidth))
                breakline2 = breakline.transformed(trafomodule.translate(-towidth[0], -towidth[1]))
                ac.fill(path.path(path.moveto(*breakline1.begin()),
                                          path.lineto(*breakline1.end()),
                                          path.lineto(*breakline2.end()),
                                          path.lineto(*breakline2.begin()),
                                          path.closepath()), [color.gray.white])
                ac.stroke(breakline1, self.defaultbreaklinesattrs + self.breaklinesattrs)
                ac.stroke(breakline2, self.defaultbreaklinesattrs + self.breaklinesattrs)
        axistitlepainter.paint(self, axispos, axis, ac=ac)
        return ac


class linksplitaxispainter(splitaxispainter):
    """class for painting a linked splitaxis
    - the inherited splitaxispainter is used to paint the axis
    - modifies some constructor defaults"""

    __implements__ = _Iaxispainter

    def __init__(self, titleattrs=None, **kwargs):
        """initializes the instance
        - the titleattrs default is set to None thus skipping the title
        - all keyword arguments are passed to splitaxispainter"""
        splitaxispainter.__init__(self, titleattrs=titleattrs, **kwargs)


class baraxispainter(axistitlepainter):
    """class for painting a baraxis
    - the inherited titleaxispainter is used to paint the title of
      the axis
    - the baraxispainter access the multisubaxis, subaxis names, texts, and
      relsizes attributes"""

    __implements__ = _Iaxispainter

    defaulttickattrs = []
    defaultbasepathattrs = [style.linecap.square]
    defaultnameattrs = [textmodule.halign.center, textmodule.vshift.mathaxis]

    def __init__(self, innerticklength=None,
                       outerticklength=None,
                       tickattrs=[],
                       basepathattrs=[],
                       namedist="0.3 cm",
                       nameattrs=[],
                       namedirection=None,
                       namepos=0.5,
                       namehequalize=0,
                       namevequalize=1,
                       **args):
        """initializes the instance
        - innerticklength and outerticklength are a visual length of
          the ticks to be plotted at the axis basepath to visually
          separate the bars; if neither innerticklength nor
          outerticklength are set, not ticks are plotted
        - breaklinesattrs are a list of stroke attributes for the
          axis tick; a single entry is allowed without being a
          list; None turns off the ticks
        - namedist is a visual PyX length for the distance of the bar
          names from the axis basepath
        - nameattrs is a list of attributes for a texrunners text
          method; a single entry is allowed without being a list;
          None turns off the names
        - namedirection is an instance of rotatetext or None
        - namehequalize and namevequalize (booleans) perform an equal
          alignment for straight vertical and horizontal axes, respectively
        - futher keyword arguments are passed to axistitlepainter"""
        self.innerticklength_str = innerticklength
        self.outerticklength_str = outerticklength
        self.tickattrs = tickattrs
        self.basepathattrs = basepathattrs
        self.namedist_str = namedist
        self.nameattrs = nameattrs
        self.namedirection = namedirection
        self.namepos = namepos
        self.namehequalize = namehequalize
        self.namevequalize = namevequalize
        axistitlepainter.__init__(self, **args)

    def paint(self, axispos, axis, ac=None):
        if ac is None:
            ac = axiscanvas()
        if axis.multisubaxis is not None:
            for subaxis in axis.subaxis:
                subaxis.finish(subaxispos(subaxis.convert, axispos, subaxis.vmin, subaxis.vmax, None, None))
                ac.insert(subaxis.axiscanvas)
                if unit.topt(ac.extent) < unit.topt(subaxis.axiscanvas.extent):
                    ac.extent = subaxis.axiscanvas.extent
        namepos = []
        for name in axis.names:
            v = axis.convert((name, self.namepos))
            x, y = axispos.vtickpoint_pt(v)
            dx, dy = axispos.vtickdirection(v)
            namepos.append((v, x, y, dx, dy))
        nameboxes = []
        if self.nameattrs is not None:
            for (v, x, y, dx, dy), name in zip(namepos, axis.names):
                nameattrs = self.defaultnameattrs + self.nameattrs
                if self.namedirection is not None:
                    nameattrs.append(self.namedirection.trafo(tick.temp_dx, tick.temp_dy))
                if axis.texts.has_key(name):
                    nameboxes.append(self.texrunner.text_pt(x, y, str(axis.texts[name]), nameattrs))
                elif axis.texts.has_key(str(name)):
                    nameboxes.append(self.texrunner.text_pt(x, y, str(axis.texts[str(name)]), nameattrs))
                else:
                    nameboxes.append(self.texrunner.text_pt(x, y, str(name), nameattrs))
        labeldist = ac.extent + unit.length(self.namedist_str, default_type="v")
        if len(namepos) > 1:
            equaldirection = 1
            for np in namepos[1:]:
                if np[3] != namepos[0][3] or np[4] != namepos[0][4]:
                    equaldirection = 0
        else:
            equaldirection = 0
        if equaldirection and ((not namepos[0][3] and self.namevequalize) or
                               (not namepos[0][4] and self.namehequalize)):
            box.linealignequal(nameboxes, labeldist, -namepos[0][3], -namepos[0][4])
        else:
            for namebox, np in zip(nameboxes, namepos):
                namebox.linealign(labeldist, -np[3], -np[4])
        if self.basepathattrs is not None:
            p = axispos.vbasepath()
            if p is not None:
                ac.stroke(p, self.defaultbasepathattrs + self.basepathattrs)
        if self.tickattrs is not None and (self.innerticklength_str is not None or
                                           self.outerticklength_str is not None):
            if self.innerticklength_str is not None:
                innerticklength = unit.length(self.innerticklength_str, default_type="v")
                innerticklength_pt = unit.topt(innerticklength)
                if unit.topt(ac.extent) < -innerticklength_pt:
                    ac.extent = -innerticklength
            elif self.outerticklength_str is not None:
                innerticklength = innerticklength_pt = 0
            if self.outerticklength_str is not None:
                outerticklength = unit.length(self.outerticklength_str, default_type="v")
                outerticklength_pt = unit.topt(outerticklength)
                if unit.topt(ac.extent) < outerticklength_pt:
                    ac.extent = outerticklength
            elif self.innerticklength_str is not None:
                outerticklength = outerticklength_pt = 0
            for pos in axis.relsizes:
                if pos == axis.relsizes[0]:
                    pos -= axis.firstdist
                elif pos != axis.relsizes[-1]:
                    pos -= 0.5 * axis.dist
                v = pos / axis.relsizes[-1]
                x, y = axispos.vtickpoint_pt(v)
                dx, dy = axispos.vtickdirection(v)
                x1 = x + dx * innerticklength_pt
                y1 = y + dy * innerticklength_pt
                x2 = x - dx * outerticklength_pt
                y2 = y - dy * outerticklength_pt
                ac.stroke(path.line_pt(x1, y1, x2, y2), self.defaulttickattrs + self.tickattrs)
        for (v, x, y, dx, dy), namebox in zip(namepos, nameboxes):
            newextent = namebox.extent(dx, dy) + labeldist
            if unit.topt(ac.extent) < unit.topt(newextent):
                ac.extent = newextent
        for namebox in nameboxes:
            ac.insert(namebox)
        axistitlepainter.paint(self, axispos, axis, ac=ac)
        return ac


class linkbaraxispainter(baraxispainter):
    """class for painting a linked baraxis
    - the inherited baraxispainter is used to paint the axis
    - modifies some constructor defaults"""

    __implements__ = _Iaxispainter

    def __init__(self, nameattrs=None, titleattrs=None, **kwargs):
        """initializes the instance
        - the titleattrs default is set to None thus skipping the title
        - the nameattrs default is set to None thus skipping the names
        - all keyword arguments are passed to axispainter"""
        baraxispainter.__init__(self, nameattrs=nameattrs, titleattrs=titleattrs, **kwargs)


################################################################################
# axes
################################################################################


class _Iaxis:
    """interface definition of a axis
    - an axis should implement an convert and invert method like
      _Imap, but this is not part of this interface definition;
      one possibility is to mix-in a proper map class, but special
      purpose axes might do something else
    - an axis has the instance variable axiscanvas after the finish
      method was called
    - an axis might have further instance variables (title, ticks)
      to be used in combination with appropriate axispainters"""

    def convert(self, x):
        "convert a value into graph coordinates"

    def invert(self, v):
        "invert a graph coordinate to a axis value"

    def getrelsize(self):
        """returns the relative size (width) of the axis
        - for use in splitaxis, baraxis etc.
        - might return None if no size is available"""

    # TODO: describe adjustrange
    def setrange(self, min=None, max=None):
        """set the axis data range
        - the type of min and max must fit to the axis
        - min<max; the axis might be reversed, but this is
          expressed internally only (min<max all the time)
        - the axis might not apply the change of the range
          (e.g. when the axis range is fixed by the user),
          but usually the range is extended to contain the
          given range
        - for invalid parameters (e.g. negativ values at an
          logarithmic axis), an exception should be raised
        - a RuntimeError is raised, when setrange is called
          after the finish method"""

    def getrange(self):
        """return data range as a tuple (min, max)
        - min<max; the axis might be reversed, but this is
          expressed internally only
        - a RuntimeError exception is raised when no
          range is available"""

    def finish(self, axispos):
        """finishes the axis
        - axispos implements _Iaxispos
        - sets the instance axiscanvas, which is insertable into the
          graph to finally paint the axis
        - any modification of the axis range should be disabled after
          the finish method was called"""
        # TODO: be more specific about exceptions

    def createlinkaxis(self, **kwargs):
        """create a link axis to the axis itself
        - typically, a link axis is a axis, which share almost
          all properties with the axis it is linked to
        - typically, the painter gets replaced by a painter
          which doesn't put any text to the axis"""


class _axis:
    """base implementation a regular axis
    - typical usage is to mix-in a linmap or a logmap to
      complete the axis interface
    - note that some methods of this class want to access a
      parter and a rater; those attributes implementing _Iparter
      and _Irater should be initialized by the constructors
      of derived classes"""

    def __init__(self, min=None, max=None, reverse=0, divisor=1,
                       title=None, painter=axispainter(), texter=defaulttexter(),
                       density=1, maxworse=2, manualticks=[]):
        """initializes the instance
        - min and max fix the axis minimum and maximum, respectively;
          they are determined by the data to be plotted, when not fixed
        - reverse (boolean) reverses the minimum and the maximum of
          the axis
        - numerical divisor for the axis partitioning
        - title is a string containing the axis title
        - axispainter is the axis painter (should implement _Ipainter)
        - texter is the texter (should implement _Itexter)
        - density is a global parameter for the axis paritioning and
          axis rating; its default is 1, but the range 0.5 to 2.5 should
          be usefull to get less or more ticks by the automatic axis
          partitioning
        - maxworse is a number of trials with worse tick rating
          before giving up (usually it should not be needed to increase
          this value; increasing the number will slow down the automatic
          axis partitioning considerably)
        - manualticks and the partitioner results are mixed
          by _mergeticklists
        - note that some methods of this class want to access a
          parter and a rater; those attributes implementing _Iparter
          and _Irater should be initialized by the constructors
          of derived classes"""
        if min is not None and max is not None and min > max:
            min, max, reverse = max, min, not reverse
        self.fixmin, self.fixmax, self.min, self.max, self.reverse = min is not None, max is not None, min, max, reverse
        self.divisor = divisor
        self.title = title
        self.painter = painter
        self.texter = texter
        self.density = density
        self.maxworse = maxworse
        self.manualticks = self.checkfraclist(manualticks)
        self.canconvert = 0
        self.axiscanvas = None
        self._setrange()

    def _setrange(self, min=None, max=None):
        if not self.fixmin and min is not None and (self.min is None or min < self.min):
            self.min = min
        if not self.fixmax and max is not None and (self.max is None or max > self.max):
            self.max = max
        if None not in (self.min, self.max):
            self.canconvert = 1
            if self.reverse:
                self.setbasepoints(((self.min, 1), (self.max, 0)))
            else:
                self.setbasepoints(((self.min, 0), (self.max, 1)))

    def _getrange(self):
        return self.min, self.max

    def _forcerange(self, range):
        self.min, self.max = range
        self._setrange()

    def setrange(self, min=None, max=None):
        oldmin, oldmax = self.min, self.max
        self._setrange(min, max)
        if self.axiscanvas is not None and ((oldmin != self.min) or (oldmax != self.max)):
            raise RuntimeError("range modification while axis was already finished")

    zero = 0.0

    def adjustrange(self, points, index, deltaindex=None, deltaminindex=None, deltamaxindex=None):
        min = max = None
        if len([x for x in [deltaindex, deltaminindex, deltamaxindex] if x is not None]) > 1:
            raise RuntimeError("only one of delta???index should set")
        if deltaindex is not None:
            deltaminindex = deltamaxindex = deltaindex
        if deltaminindex is not None:
            for point in points:
                try:
                    value = point[index] - point[deltaminindex] + self.zero
                except:
                    pass
                else:
                    if min is None or value < min: min = value
                    if max is None or value > max: max = value
        elif deltamaxindex is not None:
            for point in points:
                try:
                    value = point[index] + point[deltamaxindex] + self.zero
                except:
                    pass
                else:
                    if min is None or value < min: min = value
                    if max is None or value > max: max = value
        else:
            for point in points:
                try:
                    value = point[index] + self.zero
                except:
                    pass
                else:
                    if min is None or value < min: min = value
                    if max is None or value > max: max = value
        self.setrange(min, max)

    def getrange(self):
        if self.min is not None and self.max is not None:
            return self.min, self.max

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

    def finish(self, axispos):
        if self.axiscanvas is not None: return

        # lesspart and morepart can be called after defaultpart;
        # this works although some axes may share their autoparting,
        # because the axes are processed sequentially
        first = 1
        if self.parter is not None:
            min, max = self.getrange()
            self.ticks = _mergeticklists(self.manualticks,
                                         self.parter.defaultpart(min/self.divisor,
                                                                 max/self.divisor,
                                                                 not self.fixmin,
                                                                 not self.fixmax))
            worse = 0
            nextpart = self.parter.lesspart
            while nextpart is not None:
                newticks = nextpart()
                if newticks is not None:
                    newticks = _mergeticklists(self.manualticks, newticks)
                    if first:
                        bestrate = self.rater.rateticks(self, self.ticks, self.density)
                        bestrate += self.rater.raterange(self.convert(float(self.ticks[-1])/self.divisor)-
                                                         self.convert(float(self.ticks[0])/self.divisor), 1)
                        variants = [[bestrate, self.ticks]]
                        first = 0
                    newrate = self.rater.rateticks(self, newticks, self.density)
                    newrate += self.rater.raterange(self.convert(float(newticks[-1])/self.divisor)-
                                                    self.convert(float(newticks[0])/self.divisor), 1)
                    variants.append([newrate, newticks])
                    if newrate < bestrate:
                        bestrate = newrate
                        worse = 0
                    else:
                        worse += 1
                else:
                    worse += 1
                if worse == self.maxworse and nextpart == self.parter.lesspart:
                    worse = 0
                    nextpart = self.parter.morepart
                if worse == self.maxworse and nextpart == self.parter.morepart:
                    nextpart = None
        else:
            self.ticks =self.manualticks

        # rating, when several choises are available
        if not first:
            variants.sort()
            if self.painter is not None:
                i = 0
                bestrate = None
                while i < len(variants) and (bestrate is None or variants[i][0] < bestrate):
                    saverange = self._getrange()
                    self.ticks = variants[i][1]
                    if len(self.ticks):
                        self.setrange(float(self.ticks[0])*self.divisor, float(self.ticks[-1])*self.divisor)
                    self.texter.labels(self.ticks)
                    ac = self.painter.paint(axispos, self)
                    ratelayout = self.rater.ratelayout(ac, self.density)
                    if ratelayout is not None:
                        variants[i][0] += ratelayout
                        variants[i].append(ac)
                    else:
                        variants[i][0] = None
                    if variants[i][0] is not None and (bestrate is None or variants[i][0] < bestrate):
                        bestrate = variants[i][0]
                    self._forcerange(saverange)
                    i += 1
                if bestrate is None:
                    raise RuntimeError("no valid axis partitioning found")
                variants = [variant for variant in variants[:i] if variant[0] is not None]
                variants.sort()
                self.ticks = variants[0][1]
                if len(self.ticks):
                    self.setrange(float(self.ticks[0])*self.divisor, float(self.ticks[-1])*self.divisor)
                self.axiscanvas = variants[0][2]
            else:
                self.ticks = variants[0][1]
                self.texter.labels(self.ticks)
                if len(self.ticks):
                    self.setrange(float(self.ticks[0])*self.divisor, float(self.ticks[-1])*self.divisor)
                self.axiscanvas = axiscanvas()
        else:
            if len(self.ticks):
                self.setrange(float(self.ticks[0])*self.divisor, float(self.ticks[-1])*self.divisor)
            self.texter.labels(self.ticks)
            if self.painter is not None:
                self.axiscanvas = self.painter.paint(axispos, self)
            else:
                self.axiscanvas = axiscanvas()

    def createlinkaxis(self, **args):
        return linkaxis(self, **args)


class linaxis(_axis, _linmap):
    """implementation of a linear axis"""

    __implements__ = _Iaxis

    def __init__(self, parter=autolinparter(), rater=axisrater(), **args):
        """initializes the instance
        - the parter attribute implements _Iparter
        - manualticks and the partitioner results are mixed
          by _mergeticklists
        - the rater implements _Irater and is used to rate different
          tick lists created by the partitioner (after merging with
          manully set ticks)
        - futher keyword arguments are passed to _axis"""
        _axis.__init__(self, **args)
        if self.fixmin and self.fixmax:
            self.relsize = self.max - self.min
        self.parter = parter
        self.rater = rater


class logaxis(_axis, _logmap):
    """implementation of a logarithmic axis"""

    __implements__ = _Iaxis

    def __init__(self, parter=autologparter(), rater=axisrater(ticks=axisrater.logticks, labels=axisrater.loglabels), **args):
        """initializes the instance
        - the parter attribute implements _Iparter
        - manualticks and the partitioner results are mixed
          by _mergeticklists
        - the rater implements _Irater and is used to rate different
          tick lists created by the partitioner (after merging with
          manully set ticks)
        - futher keyword arguments are passed to _axis"""
        _axis.__init__(self, **args)
        if self.fixmin and self.fixmax:
            self.relsize = math.log(self.max) - math.log(self.min)
        self.parter = parter
        self.rater = rater


class linkaxis:
    """a axis linked to an already existing regular axis
    - almost all properties of the axis are "copied" from the
      axis this axis is linked to
    - usually, linked axis are used to create an axis to an
      existing axis with different painting properties; linked
      axis can be used to plot an axis twice at the opposite
      sides of a graphxy or even to share an axis between
      different graphs!"""

    __implements__ = _Iaxis

    def __init__(self, linkedaxis, painter=linkaxispainter()):
        """initializes the instance
        - it gets a axis this linkaxis is linked to
        - it gets a painter to be used for this linked axis"""
        self.linkedaxis = linkedaxis
        self.painter = painter
        self.axiscanvas = None

    def __getattr__(self, attr):
        """access to unkown attributes are handed over to the
        axis this linkaxis is linked to"""
        return getattr(self.linkedaxis, attr)

    def finish(self, axispos):
        """finishes the axis
        - instead of performing the hole finish process
          (paritioning, rating, etc.) just a painter call
          is performed"""
        if self.axiscanvas is None:
            if self.linkedaxis.axiscanvas is None:
                raise RuntimeError("link axis finish method called before the finish method of the original axis")
            self.axiscanvas = self.painter.paint(axispos, self)


class splitaxis:
    """implementation of a split axis
    - a split axis contains several (sub-)axes with
      non-overlapping data ranges -- between these subaxes
      the axis is "splitted"
    - (just to get sure: a splitaxis can contain other
      splitaxes as its subaxes)
    - a splitaxis implements the _Iaxispos for its subaxes
      by inheritance from _subaxispos"""

    __implements__ = _Iaxis, _Iaxispos

    def __init__(self, subaxes, splitlist=[0.5], splitdist=0.1, relsizesplitdist=1,
                       title=None, painter=splitaxispainter()):
        """initializes the instance
        - subaxes is a list of subaxes
        - splitlist is a list of graph coordinates, where the splitting
          of the main axis should be performed; if the list isn't long enough
          for the subaxes, missing entries are considered to be None
        - splitdist is the size of the splitting in graph coordinates, when
          the associated splitlist entry is not None
        - relsizesplitdist: a None entry in splitlist means, that the
          position of the splitting should be calculated out of the
          relsize values of conrtibuting subaxes (the size of the
          splitting is relsizesplitdist in values of the relsize values
          of the axes)
        - title is the title of the axis as a string
        - painter is the painter of the axis; it should be specialized to
          the splitaxis
        - the relsize of the splitaxis is the sum of the relsizes of the
          subaxes including the relsizesplitdist"""
        self.subaxes = subaxes
        self.painter = painter
        self.title = title
        self.splitlist = splitlist
        for subaxis in self.subaxes:
            subaxis.vmin = None
            subaxis.vmax = None
        self.subaxes[0].vmin = 0
        self.subaxes[0].vminover = None
        self.subaxes[-1].vmax = 1
        self.subaxes[-1].vmaxover = None
        for i in xrange(len(self.splitlist)):
            if self.splitlist[i] is not None:
                self.subaxes[i].vmax = self.splitlist[i] - 0.5*splitdist
                self.subaxes[i].vmaxover = self.splitlist[i]
                self.subaxes[i+1].vmin = self.splitlist[i] + 0.5*splitdist
                self.subaxes[i+1].vminover = self.splitlist[i]
        i = 0
        while i < len(self.subaxes):
            if self.subaxes[i].vmax is None:
                j = relsize = relsize2 = 0
                while self.subaxes[i + j].vmax is None:
                    relsize += self.subaxes[i + j].relsize + relsizesplitdist
                    j += 1
                relsize += self.subaxes[i + j].relsize
                vleft = self.subaxes[i].vmin
                vright = self.subaxes[i + j].vmax
                for k in range(i, i + j):
                    relsize2 += self.subaxes[k].relsize
                    self.subaxes[k].vmax = vleft + (vright - vleft) * relsize2 / float(relsize)
                    relsize2 += 0.5 * relsizesplitdist
                    self.subaxes[k].vmaxover = self.subaxes[k + 1].vminover = vleft + (vright - vleft) * relsize2 / float(relsize)
                    relsize2 += 0.5 * relsizesplitdist
                    self.subaxes[k+1].vmin = vleft + (vright - vleft) * relsize2 / float(relsize)
                if i == 0 and i + j + 1 == len(self.subaxes):
                    self.relsize = relsize
                i += j + 1
            else:
                i += 1

        self.fixmin = self.subaxes[0].fixmin
        if self.fixmin:
            self.min = self.subaxes[0].min
        self.fixmax = self.subaxes[-1].fixmax
        if self.fixmax:
            self.max = self.subaxes[-1].max

        self.axiscanvas = None

    def getrange(self):
        min = self.subaxes[0].getrange()
        max = self.subaxes[-1].getrange()
        try:
            return min[0], max[1]
        except TypeError:
            return None

    def setrange(self, min, max):
        self.subaxes[0].setrange(min, None)
        self.subaxes[-1].setrange(None, max)

    def adjustrange(self, *args, **kwargs):
        self.subaxes[0].adjustrange(*args, **kwargs)
        self.subaxes[-1].adjustrange(*args, **kwargs)

    def convert(self, value):
        # TODO: proper raising exceptions (which exceptions go thru, which are handled before?)
        if value < self.subaxes[0].max:
            return self.subaxes[0].vmin + self.subaxes[0].convert(value)*(self.subaxes[0].vmax-self.subaxes[0].vmin)
        for axis in self.subaxes[1:-1]:
            if value > axis.min and value < axis.max:
                return axis.vmin + axis.convert(value)*(axis.vmax-axis.vmin)
        if value > self.subaxes[-1].min:
            return self.subaxes[-1].vmin + self.subaxes[-1].convert(value)*(self.subaxes[-1].vmax-self.subaxes[-1].vmin)
        raise ValueError("value couldn't be assigned to a split region")

    def finish(self, axispos):
        if self.axiscanvas is None:
            self.axiscanvas = self.painter.paint(axispos, self)

    def createlinkaxis(self, **args):
        return linksplitaxis(self, **args)


class omitsubaxispainter: pass

class linksplitaxis(linkaxis):
    """a splitaxis linked to an already existing splitaxis
    - inherits the access to a linked axis -- as before,
      basically only the painter is replaced
    - it takes care of the creation of linked axes of
      the subaxes"""

    __implements__ = _Iaxis

    def __init__(self, linkedaxis, painter=linksplitaxispainter(), subaxispainter=omitsubaxispainter):
        """initializes the instance
        - linkedaxis is the axis this axis becomes linked to
        - painter is axispainter instance for this linked axis
        - subaxispainter is a changeable painter to be used for linked
          subaxes; if omitsubaxispainter the createlinkaxis method of
          the subaxis are called without a painter parameter"""
        linkaxis.__init__(self, linkedaxis, painter=painter)
        self.subaxes = []
        for subaxis in linkedaxis.subaxes:
            painter = attr.selectattr(subaxispainter, len(self.subaxes), len(linkedaxis.subaxes))
            if painter is omitsubaxispainter:
                self.subaxes.append(subaxis.createlinkaxis())
            else:
                self.subaxes.append(subaxis.createlinkaxis(painter=painter))


class baraxis:
    """implementation of a axis for bar graphs
    - a bar axes is different from a splitaxis by the way it
      selects its subaxes: the convert method gets a list,
      where the first entry is a name selecting a subaxis out
      of a list; instead of the term "bar" or "subaxis" the term
      "item" will be used here
    - the baraxis stores a list of names be identify the items;
      the names might be of any time (strings, integers, etc.);
      the names can be printed as the titles for the items, but
      alternatively the names might be transformed by the texts
      dictionary, which maps a name to a text to be used to label
      the items in the painter
    - usually, there is only one subaxis, which is used as
      the subaxis for all items
    - alternatively it is also possible to use another baraxis
      as a multisubaxis; it is copied via the createsubaxis
      method whenever another subaxis is needed (by that a
      nested bar axis with a different number of subbars at
      each item can be created)
    - any axis can be a subaxis of a baraxis; if no subaxis
      is specified at all, the baraxis simulates a linear
      subaxis with a fixed range of 0 to 1
    - a splitaxis implements the _Iaxispos for its subaxes
      by inheritance from _subaxispos when the multisubaxis
      feature is turned on"""

    def __init__(self, subaxis=None, multisubaxis=None, title=None,
                       dist=0.5, firstdist=None, lastdist=None, names=None,
                       texts={}, painter=baraxispainter()):
        """initialize the instance
        - subaxis contains a axis to be used as the subaxis
          for all items
        - multisubaxis might contain another baraxis instance
          to be used to construct a new subaxis for each item;
          (by that a nested bar axis with a different number
          of subbars at each item can be created)
        - only one of subaxis or multisubaxis can be set; if neither
          of them is set, the baraxis behaves like having a linaxis
          as its subaxis with a fixed range 0 to 1
        - the title attribute contains the axis title as a string
        - the dist is a relsize to be used as the distance between
          the items
        - the firstdist and lastdist are the distance before the
          first and after the last item, respectively; when set
          to None (the default), 0.5*dist is used
        - names is a predefined list of names to identify the
          items; if set, the name list is fixed
        - texts is a dictionary transforming a name to a text in
          the painter; if a name isn't found in the dictionary
          it gets used itself
        - the relsize of the baraxis is the sum of the
          relsizes including all distances between the items"""
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
        if self.multisubaxis is not None:
            if subaxis is not None:
                raise RuntimeError("either use subaxis or multisubaxis")
            self.subaxis = [self.createsubaxis() for name in self.names]
        else:
            self.subaxis = subaxis
        self.title = title
        self.fixnames = 0
        self.texts = texts
        self.painter = painter
        self.axiscanvas = None

    def createsubaxis(self):
        return baraxis(subaxis=self.multisubaxis.subaxis,
                       multisubaxis=self.multisubaxis.multisubaxis,
                       title=self.multisubaxis.title,
                       dist=self.multisubaxis.dist,
                       firstdist=self.multisubaxis.firstdist,
                       lastdist=self.multisubaxis.lastdist,
                       names=self.multisubaxis.names,
                       texts=self.multisubaxis.texts,
                       painter=self.multisubaxis.painter)

    def getrange(self):
        # TODO: we do not yet have a proper range handling for a baraxis
        return None

    def setrange(self, min=None, max=None):
        # TODO: we do not yet have a proper range handling for a baraxis
        raise RuntimeError("range handling for a baraxis is not implemented")

    def setname(self, name, *subnames):
        """add a name to identify an item at the baraxis
        - by using subnames, nested name definitions are
          possible
        - a style (or the user itself) might use this to
          insert new items into a baraxis
        - setting self.relsizes to None forces later recalculation"""
        if not self.fixnames:
            if name not in self.names:
                self.relsizes = None
                self.names.append(name)
                if self.multisubaxis is not None:
                    self.subaxis.append(self.createsubaxis())
        if (not self.fixnames or name in self.names) and len(subnames):
            if self.multisubaxis is not None:
                if self.subaxis[self.names.index(name)].setname(*subnames):
                    self.relsizes = None
            else:
                if self.subaxis.setname(*subnames):
                    self.relsizes = None
        return self.relsizes is not None

    def adjustrange(self, points, index, subnames=None):
        if subnames is None:
            subnames = []
        for point in points:
            self.setname(point[index], *subnames)

    def updaterelsizes(self):
        # guess what it does: it recalculates relsize attribute
        self.relsizes = [i*self.dist + self.firstdist for i in range(len(self.names) + 1)]
        self.relsizes[-1] += self.lastdist - self.dist
        if self.multisubaxis is not None:
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
        """baraxis convert method
        - the value should be a list, where the first entry is
          a member of the names (set in the constructor or by the
          setname method); this first entry identifies an item in
          the baraxis
        - following values are passed to the appropriate subaxis
          convert method
        - when there is no subaxis, the convert method will behave
          like having a linaxis from 0 to 1 as subaxis"""
        # TODO: proper raising exceptions (which exceptions go thru, which are handled before?)
        if not self.relsizes:
            self.updaterelsizes()
        pos = self.names.index(value[0])
        if len(value) == 2:
            if self.subaxis is None:
                subvalue = value[1]
            else:
                if self.multisubaxis is not None:
                    subvalue = value[1] * self.subaxis[pos].relsizes[-1]
                else:
                    subvalue = value[1] * self.subaxis.relsizes[-1]
        else:
            if self.multisubaxis is not None:
                subvalue = self.subaxis[pos].convert(value[1:]) * self.subaxis[pos].relsizes[-1]
            else:
                subvalue = self.subaxis.convert(value[1:]) * self.subaxis.relsizes[-1]
        return (self.relsizes[pos] + subvalue) / float(self.relsizes[-1])

    def finish(self, axispos):
        if self.axiscanvas is None:
            if self.multisubaxis is not None:
                for name, subaxis in zip(self.names, self.subaxis):
                    subaxis.vmin = self.convert((name, 0))
                    subaxis.vmax = self.convert((name, 1))
            self.axiscanvas = self.painter.paint(axispos, self)

    def createlinkaxis(self, **args):
        return linkbaraxis(self, **args)


class linkbaraxis(linkaxis):
    """a baraxis linked to an already existing baraxis
    - inherits the access to a linked axis -- as before,
      basically only the painter is replaced
    - it must take care of the creation of linked axes of
      the subaxes"""

    __implements__ = _Iaxis

    def __init__(self, linkedaxis, painter=linkbaraxispainter()):
        """initializes the instance
        - it gets a axis this linkaxis is linked to
        - it gets a painter to be used for this linked axis"""
        linkaxis.__init__(self, linkedaxis, painter=painter)
        if self.multisubaxis is not None:
            self.subaxis = [subaxis.createlinkaxis() for subaxis in self.linkedaxis.subaxis]
        elif self.subaxis is not None:
            self.subaxis = self.subaxis.createlinkaxis()


def pathaxis(path, axis, **kwargs):
    """creates an axiscanvas for an axis along a path"""
    mypathaxispos = pathaxispos(path, axis.convert, **kwargs)
    axis.finish(mypathaxispos)
    return axis.axiscanvas

################################################################################
# graph key
################################################################################

class key:

    defaulttextattrs = [textmodule.vshift.mathaxis]

    def __init__(self, dist="0.2 cm", pos="tr", hinside=1, vinside=1, hdist="0.6 cm", vdist="0.4 cm",
                 symbolwidth="0.5 cm", symbolheight="0.25 cm", symbolspace="0.2 cm",
                 textattrs=[]):
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

    def paint(self, plotdata):
        "creates the layout of the key"
        c = canvas.canvas()
        self.dist_pt = unit.topt(unit.length(self.dist_str, default_type="v"))
        self.hdist_pt = unit.topt(unit.length(self.hdist_str, default_type="v"))
        self.vdist_pt = unit.topt(unit.length(self.vdist_str, default_type="v"))
        self.symbolwidth_pt = unit.topt(unit.length(self.symbolwidth_str, default_type="v"))
        self.symbolheight_pt = unit.topt(unit.length(self.symbolheight_str, default_type="v"))
        self.symbolspace_pt = unit.topt(unit.length(self.symbolspace_str, default_type="v"))
        titles = []
        for plotdat in plotdata:
            titles.append(c.texrunner.text_pt(0, 0, plotdat.title, self.defaulttextattrs + self.textattrs))
        box.tile_pt(titles, self.dist_pt, 0, -1)
        box.linealignequal_pt(titles, self.symbolwidth_pt + self.symbolspace_pt, 1, 0)
        for plotdat, title in zip(plotdata, titles):
            plotdat.style.key_pt(c, 0, -0.5 * self.symbolheight_pt + title.center[1],
                                   self.symbolwidth_pt, self.symbolheight_pt, plotdat)
            c.insert(title)
        return c


################################################################################
# graph
################################################################################


class lineaxispos:
    """an axispos linear along a line with a fix direction for the ticks"""

    __implements__ = _Iaxispos

    def __init__(self, convert, x1, y1, x2, y2, fixtickdirection):
        """initializes the instance
        - only the convert method is needed from the axis
        - x1, y1, x2, y2 are PyX lengths (start and end position of the line)
        - fixtickdirection is a tuple tick direction (fixed along the line)"""
        self.convert = convert
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.x1_pt = unit.topt(x1)
        self.y1_pt = unit.topt(y1)
        self.x2_pt = unit.topt(x2)
        self.y2_pt = unit.topt(y2)
        self.fixtickdirection = fixtickdirection

    def vbasepath(self, v1=None, v2=None):
        if v1 is None:
            v1 = 0
        if v2 is None:
            v2 = 1
        return path.line_pt((1-v1)*self.x1_pt+v1*self.x2_pt,
                            (1-v1)*self.y1_pt+v1*self.y2_pt,
                            (1-v2)*self.x1_pt+v2*self.x2_pt,
                            (1-v2)*self.y1_pt+v2*self.y2_pt)

    def basepath(self, x1=None, x2=None):
        if x1 is None:
            v1 = 0
        else:
            v1 = self.convert(x1)
        if x2 is None:
            v2 = 1
        else:
            v2 = self.convert(x2)
        return path.line_pt((1-v1)*self.x1_pt+v1*self.x2_pt,
                            (1-v1)*self.y1_pt+v1*self.y2_pt,
                            (1-v2)*self.x1_pt+v2*self.x2_pt,
                            (1-v2)*self.y1_pt+v2*self.y2_pt)

    def gridpath(self, x):
        raise RuntimeError("gridpath not available")

    def vgridpath(self, v):
        raise RuntimeError("gridpath not available")

    def vtickpoint_pt(self, v):
        return (1-v)*self.x1_pt+v*self.x2_pt, (1-v)*self.y1_pt+v*self.y2_pt

    def vtickpoint(self, v):
        return (1-v)*self.x1+v*self.x2, (1-v)*self.y1+v*self.y2

    def tickpoint_pt(self, x):
        v = self.convert(x)
        return (1-v)*self.x1_pt+v*self.x2_pt, (1-v)*self.y1_pt+v*self.y2_pt

    def tickpoint(self, x):
        v = self.convert(x)
        return (1-v)*self.x1+v*self.x2, (1-v)*self.y1+v*self.y2

    def tickdirection(self, x):
        return self.fixtickdirection

    def vtickdirection(self, v):
        return self.fixtickdirection


class lineaxisposlinegrid(lineaxispos):
    """an axispos linear along a line with a fix direction for the ticks
    with support for grid lines for a rectangular graphs"""

    __implements__ = _Iaxispos

    def __init__(self, convert, x1, y1, x2, y2, fixtickdirection, startgridlength, endgridlength):
        """initializes the instance
        - only the convert method is needed from the axis
        - x1, y1, x2, y2 are PyX lengths (start and end position of the line)
        - fixtickdirection is a tuple tick direction (fixed along the line)
        - startgridlength and endgridlength are PyX lengths for the starting
          and end point of the grid, respectively; the gridpath is a line along
          the fixtickdirection"""
        lineaxispos.__init__(self, convert, x1, y1, x2, y2, fixtickdirection)
        self.startgridlength = startgridlength
        self.endgridlength = endgridlength
        self.startgridlength_pt = unit.topt(self.startgridlength)
        self.endgridlength_pt = unit.topt(self.endgridlength)

    def gridpath(self, x):
        v = self.convert(x)
        return path.line_pt((1-v)*self.x1_pt+v*self.x2_pt+self.fixtickdirection[0]*self.startgridlength_pt,
                          (1-v)*self.y1_pt+v*self.y2_pt+self.fixtickdirection[1]*self.startgridlength_pt,
                          (1-v)*self.x1_pt+v*self.x2_pt+self.fixtickdirection[0]*self.endgridlength_pt,
                          (1-v)*self.y1_pt+v*self.y2_pt+self.fixtickdirection[1]*self.endgridlength_pt)

    def vgridpath(self, v):
        return path.line_pt((1-v)*self.x1_pt+v*self.x2_pt+self.fixtickdirection[0]*self.startgridlength_pt,
                          (1-v)*self.y1_pt+v*self.y2_pt+self.fixtickdirection[1]*self.startgridlength_pt,
                          (1-v)*self.x1_pt+v*self.x2_pt+self.fixtickdirection[0]*self.endgridlength_pt,
                          (1-v)*self.y1_pt+v*self.y2_pt+self.fixtickdirection[1]*self.endgridlength_pt)


class graphxy(canvas.canvas):

    axisnames = "x", "y"

    class axisposdata:

        def __init__(self, type, axispos, tickdirection):
            """
            - type == 0: x-axis; type == 1: y-axis
            - axispos_pt is the y or x position of the x-axis or y-axis
              in postscript points, respectively
            - axispos is analogous to axispos, but as a PyX length
            - dx and dy is the tick direction
            """
            self.type = type
            self.axispos = axispos
            self.axispos_pt = unit.topt(axispos)
            self.tickdirection = tickdirection

    def clipcanvas(self):
        return self.insert(canvas.canvas(canvas.clip(path.rect_pt(self.xpos_pt, self.ypos_pt, self.width_pt, self.height_pt))))

    def plot(self, data, style=None):
        if self.haslayout:
            raise RuntimeError("layout setup was already performed")
        try:
            for d in data:
                pass
        except:
            usedata = [data]
        else:
            usedata = data
        if style is None:
            for d in usedata:
                if style is None:
                    style = d.defaultstyle
                elif style != d.defaultstyle:
                    raise RuntimeError("defaultstyles differ")
        for d in usedata:
            d.setstyle(self, style)
            self.plotdata.append(d)
        return data

    def pos_pt(self, x, y, xaxis=None, yaxis=None):
        if xaxis is None:
            xaxis = self.axes["x"]
        if yaxis is None:
            yaxis = self.axes["y"]
        return self.xpos_pt + xaxis.convert(x)*self.width_pt, self.ypos_pt + yaxis.convert(y)*self.height_pt

    def pos(self, x, y, xaxis=None, yaxis=None):
        if xaxis is None:
            xaxis = self.axes["x"]
        if yaxis is None:
            yaxis = self.axes["y"]
        return self.xpos + xaxis.convert(x)*self.width, self.ypos + yaxis.convert(y)*self.height

    def vpos_pt(self, vx, vy):
        return self.xpos_pt + vx*self.width_pt, self.ypos_pt + vy*self.height_pt

    def vpos(self, vx, vy):
        return self.xpos + vx*self.width, self.ypos + vy*self.height

    def vgeodesic(self, vx1, vy1, vx2, vy2):
        """returns a geodesic path between two points in graph coordinates"""
        return path.line_pt(self.xpos_pt + vx1*self.width_pt,
                            self.ypos_pt + vy1*self.height_pt,
                            self.xpos_pt + vx2*self.width_pt,
                            self.ypos_pt + vy2*self.height_pt)

    def vcap_pt(self, direction, length_pt, vx, vy):
        """returns an error cap path for a given direction, lengths and
        point in graph coordinates"""
        if direction == "x":
            return path.line_pt(self.xpos_pt + vx*self.width_pt - 0.5*length_pt,
                                self.ypos_pt + vy*self.height_pt,
                                self.xpos_pt + vx*self.width_pt + 0.5*length_pt,
                                self.ypos_pt + vy*self.height_pt)
        elif direction == "y":
            return path.line_pt(self.xpos_pt + vx*self.width_pt,
                                self.ypos_pt + vy*self.height_pt - 0.5*length_pt,
                                self.xpos_pt + vx*self.width_pt,
                                self.ypos_pt + vy*self.height_pt + 0.5*length_pt)
        else:
            raise ValueError("direction invalid")

    def keynum(self, key):
        try:
            while key[0] in string.letters:
                key = key[1:]
            return int(key)
        except IndexError:
            return 1

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

        # count the usage of styles and perform selects
        styletotal = {}
        for data in self.plotdata:
            try:
                styletotal[id(data.style)] += 1
            except:
                styletotal[id(data.style)] = 1
        styleindex = {}
        for data in self.plotdata:
            try:
                styleindex[id(data.style)] += 1
            except:
                styleindex[id(data.style)] = 0
            data.selectstyle(self, styleindex[id(data.style)], styletotal[id(data.style)])

        # adjust the axes ranges
        for step in range(3):
            for data in self.plotdata:
                data.adjustaxes(self, step)

        # finish all axes
        axesdist = unit.length(self.axesdist_str, default_type="v")
        XPattern = re.compile(r"%s([2-9]|[1-9][0-9]+)?$" % self.axisnames[0])
        YPattern = re.compile(r"%s([2-9]|[1-9][0-9]+)?$" % self.axisnames[1])
        xaxisextents = [0, 0]
        yaxisextents = [0, 0]
        needxaxisdist = [0, 0]
        needyaxisdist = [0, 0]
        items = list(self.axes.items())
        items.sort() #TODO: alphabetical sorting breaks for axis numbers bigger than 9
        for key, axis in items:
            num = self.keynum(key)
            num2 = 1 - num % 2 # x1 -> 0, x2 -> 1, x3 -> 0, x4 -> 1, ...
            num3 = 2 * (num % 2) - 1 # x1 -> 1, x2 -> -1, x3 -> 1, x4 -> -1, ...
            if XPattern.match(key):
                if needxaxisdist[num2]:
                    xaxisextents[num2] += axesdist
                self.axespos[key] = lineaxisposlinegrid(self.axes[key].convert,
                                                        self.xpos,
                                                        self.ypos + num2*self.height - num3*xaxisextents[num2],
                                                        self.xpos + self.width,
                                                        self.ypos + num2*self.height - num3*xaxisextents[num2],
                                                        (0, num3),
                                                        xaxisextents[num2], xaxisextents[num2] + self.height)
                if num == 1:
                    self.xbasepath = self.axespos[key].basepath
                    self.xvbasepath = self.axespos[key].vbasepath
                    self.xgridpath = self.axespos[key].gridpath
                    self.xvgridpath = self.axespos[key].vgridpath
                    self.xtickpoint_pt = self.axespos[key].tickpoint_pt
                    self.xtickpoint = self.axespos[key].tickpoint
                    self.xvtickpoint_pt = self.axespos[key].vtickpoint_pt
                    self.xvtickpoint = self.axespos[key].tickpoint
                    self.xtickdirection = self.axespos[key].tickdirection
                    self.xvtickdirection = self.axespos[key].vtickdirection
            elif YPattern.match(key):
                if needyaxisdist[num2]:
                    yaxisextents[num2] += axesdist
                self.axespos[key] = lineaxisposlinegrid(self.axes[key].convert,
                                                        self.xpos + num2*self.width - num3*yaxisextents[num2],
                                                        self.ypos,
                                                        self.xpos + num2*self.width - num3*yaxisextents[num2],
                                                        self.ypos + self.height,
                                                        (num3, 0),
                                                        yaxisextents[num2], yaxisextents[num2] + self.width)
                if num == 1:
                    self.ybasepath = self.axespos[key].basepath
                    self.yvbasepath = self.axespos[key].vbasepath
                    self.ygridpath = self.axespos[key].gridpath
                    self.yvgridpath = self.axespos[key].vgridpath
                    self.ytickpoint_pt = self.axespos[key].tickpoint_pt
                    self.ytickpoint = self.axespos[key].tickpoint
                    self.yvtickpoint_pt = self.axespos[key].vtickpoint_pt
                    self.yvtickpoint = self.axespos[key].tickpoint
                    self.ytickdirection = self.axespos[key].tickdirection
                    self.yvtickdirection = self.axespos[key].vtickdirection
            else:
                raise ValueError("Axis key '%s' not allowed" % key)
            axis.finish(self.axespos[key])
            if XPattern.match(key):
                xaxisextents[num2] += axis.axiscanvas.extent
                needxaxisdist[num2] = 1
            if YPattern.match(key):
                yaxisextents[num2] += axis.axiscanvas.extent
                needyaxisdist[num2] = 1
        self.haslayout = 1

    def dobackground(self):
        self.dolayout()
        if not self.removedomethod(self.dobackground): return
        if self.backgroundattrs is not None:
            self.draw(path.rect_pt(self.xpos_pt, self.ypos_pt, self.width_pt, self.height_pt),
                      helper.ensurelist(self.backgroundattrs))

    def doaxes(self):
        self.dolayout()
        if not self.removedomethod(self.doaxes): return
        for axis in self.axes.values():
            self.insert(axis.axiscanvas)

    def dodata(self):
        self.dolayout()
        if not self.removedomethod(self.dodata): return
        for data in self.plotdata:
            data.draw(self)

    def dokey(self):
        self.dolayout()
        if not self.removedomethod(self.dokey): return
        if self.key is not None:
            c = self.key.paint(self.plotdata)
            bbox = c.bbox()
            if self.key.right:
                if self.key.hinside:
                    x = self.xpos_pt + self.width_pt - bbox.urx - self.key.hdist_pt
                else:
                    x = self.xpos_pt + self.width_pt - bbox.llx + self.key.hdist_pt
            else:
                if self.key.hinside:
                    x = self.xpos_pt - bbox.llx + self.key.hdist_pt
                else:
                    x = self.xpos_pt - bbox.urx - self.key.hdist_pt
            if self.key.top:
                if self.key.vinside:
                    y = self.ypos_pt + self.height_pt - bbox.ury - self.key.vdist_pt
                else:
                    y = self.ypos_pt + self.height_pt - bbox.lly + self.key.vdist_pt
            else:
                if self.key.vinside:
                    y = self.ypos_pt - bbox.lly + self.key.vdist_pt
                else:
                    y = self.ypos_pt - bbox.ury - self.key.vdist_pt
            self.insert(c, [trafomodule.translate_pt(x, y)])

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
        self.width_pt = unit.topt(self.width)
        self.height_pt = unit.topt(self.height)
        if self.width_pt <= 0: raise ValueError("width <= 0")
        if self.height_pt <= 0: raise ValueError("height <= 0")

    def initaxes(self, axes, addlinkaxes=0):
        for key in self.axisnames:
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
        self.xpos_pt = unit.topt(self.xpos)
        self.ypos_pt = unit.topt(self.ypos)
        self.initwidthheight(width, height, ratio)
        self.initaxes(axes, 1)
        self.axescanvas = {}
        self.axespos = {}
        self.key = key
        self.backgroundattrs = backgroundattrs
        self.axesdist_str = axesdist
        self.plotdata = []
        self.domethods = [self.dolayout, self.dobackground, self.doaxes, self.dodata, self.dokey]
        self.haslayout = 0
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
#     axisnames = "x", "y", "z"
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
#         XPattern = re.compile(r"%s([2-9]|[1-9][0-9]+)?$" % self.axisnames[0])
#         YPattern = re.compile(r"%s([2-9]|[1-9][0-9]+)?$" % self.axisnames[1])
#         ZPattern = re.compile(r"%s([2-9]|[1-9][0-9]+)?$" % self.axisnames[2])
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
# styles
################################################################################


class _style:

    def setdatapattern(self, graph, columns, pattern):
        for datakey in columns.keys():
            match = pattern.match(datakey)
            if match:
                # XXX match.groups()[0] must contain the full axisname
                axisname = match.groups()[0]
                index = columns[datakey]
                del columns[datakey]
                return graph.axes[axisname], index

    def key_pt(self, c, x_pt, y_pt, width_pt, height_pt, data):
        raise RuntimeError("style doesn't provide a key")


class symbolline(_style):

    def cross(self, x_pt, y_pt, size_pt):
        return (path.moveto_pt(x_pt-0.5*size_pt, y_pt-0.5*size_pt),
                path.lineto_pt(x_pt+0.5*size_pt, y_pt+0.5*size_pt),
                path.moveto_pt(x_pt-0.5*size_pt, y_pt+0.5*size_pt),
                path.lineto_pt(x_pt+0.5*size_pt, y_pt-0.5*size_pt))

    def plus(self, x_pt, y_pt, size_pt):
        return (path.moveto_pt(x_pt-0.707106781*size_pt, y_pt),
                path.lineto_pt(x_pt+0.707106781*size_pt, y_pt),
                path.moveto_pt(x_pt, y_pt-0.707106781*size_pt),
                path.lineto_pt(x_pt, y_pt+0.707106781*size_pt))

    def square(self, x_pt, y_pt, size_pt):
        return (path.moveto_pt(x_pt-0.5*size_pt, y_pt-0.5*size_pt),
                path.lineto_pt(x_pt+0.5*size_pt, y_pt-0.5*size_pt),
                path.lineto_pt(x_pt+0.5*size_pt, y_pt+0.5*size_pt),
                path.lineto_pt(x_pt-0.5*size_pt, y_pt+0.5*size_pt),
                path.closepath())

    def triangle(self, x_pt, y_pt, size_pt):
        return (path.moveto_pt(x_pt-0.759835685*size_pt, y_pt-0.438691337*size_pt),
                path.lineto_pt(x_pt+0.759835685*size_pt, y_pt-0.438691337*size_pt),
                path.lineto_pt(x_pt, y_pt+0.877382675*size_pt),
                path.closepath())

    def circle(self, x_pt, y_pt, size_pt):
        return (path.arc_pt(x_pt, y_pt, 0.564189583*size_pt, 0, 360),
                path.closepath())

    def diamond(self, x_pt, y_pt, size_pt):
        return (path.moveto_pt(x_pt-0.537284965*size_pt, y_pt),
                path.lineto_pt(x_pt, y_pt-0.930604859*size_pt),
                path.lineto_pt(x_pt+0.537284965*size_pt, y_pt),
                path.lineto_pt(x_pt, y_pt+0.930604859*size_pt),
                path.closepath())

    changecross = attr.changelist([cross, plus, square, triangle, circle, diamond])
    changeplus = attr.changelist([plus, square, triangle, circle, diamond, cross])
    changesquare = attr.changelist([square, triangle, circle, diamond, cross, plus])
    changetriangle = attr.changelist([triangle, circle, diamond, cross, plus, square])
    changecircle = attr.changelist([circle, diamond, cross, plus, square, triangle])
    changediamond = attr.changelist([diamond, cross, plus, square, triangle, circle])
    changesquaretwice = attr.changelist([square, square, triangle, triangle, circle, circle, diamond, diamond])
    changetriangletwice = attr.changelist([triangle, triangle, circle, circle, diamond, diamond, square, square])
    changecircletwice = attr.changelist([circle, circle, diamond, diamond, square, square, triangle, triangle])
    changediamondtwice = attr.changelist([diamond, diamond, square, square, triangle, triangle, circle, circle])

    changestrokedfilled = attr.changelist([deco.stroked, deco.filled])
    changefilledstroked = attr.changelist([deco.filled, deco.stroked])

    changelinestyle = attr.changelist([style.linestyle.solid,
                                       style.linestyle.dashed,
                                       style.linestyle.dotted,
                                       style.linestyle.dashdotted])

    defaultsymbolattrs = [deco.stroked]
    defaulterrorbarattrs = []
    defaultlineattrs = [changelinestyle]

    def __init__(self, symbol=changecross,
                       size="0.2 cm",
                       errorscale=0.5,
                       symbolattrs=[],
                       errorbarattrs=[],
                       lineattrs=[],
                       epsilon=1e-10):
        self.size_str = size
        self.symbol = symbol
        self.errorscale = errorscale
        self.symbolattrs = symbolattrs
        self.errorbarattrs = errorbarattrs
        self.lineattrs = lineattrs
        self.epsilon = epsilon

    def setdata(self, graph, columns, data):
        """
        - the instance should be considered read-only
          (it might be shared between several data)
        - data is the place where to store information
        - returns the dictionary of columns not used by the style"""

        # analyse column information
        data.index = {} # a nested index dictionary containing
                        # column numbers, e.g. data.index["x"]["x"],
                        # data.index["y"]["dmin"] etc.; the first key is a axis
                        # name (without the axis number), the second is one of
                        # the datanames ["x", "min", "max", "d", "dmin", "dmax"]
        data.axes = {}  # mapping from axis name (without axis number) to the axis

        columns = columns.copy()
        for axisname in graph.axisnames:
            for dataname, pattern in [("x", re.compile(r"(%s([2-9]|[1-9][0-9]+)?)$" % axisname)),
                                      ("min", re.compile(r"(%s([2-9]|[1-9][0-9]+)?)min$" % axisname)),
                                      ("max", re.compile(r"(%s([2-9]|[1-9][0-9]+)?)max$" % axisname)),
                                      ("d", re.compile(r"d(%s([2-9]|[1-9][0-9]+)?)$" % axisname)),
                                      ("dmin", re.compile(r"d(%s([2-9]|[1-9][0-9]+)?)min$" % axisname)),
                                      ("dmax", re.compile(r"d(%s([2-9]|[1-9][0-9]+)?)max$" % axisname))]:
                matchresult = self.setdatapattern(graph, columns, pattern)
                if matchresult is not None:
                    axis, index = matchresult
                    if data.axes.has_key(axisname):
                        if data.axes[axisname] != axis:
                            raise ValueError("axis mismatch for axis name '%s'" % axisname)
                        data.index[axisname][dataname] = index
                    else:
                        data.index[axisname] = {dataname: index}
                        data.axes[axisname] = axis
            if not data.axes.has_key(axisname):
                raise ValueError("missing columns for axis name '%s'" % axisname)
            if ((data.index[axisname].has_key("min") and data.index[axisname].has_key("d")) or
                (data.index[axisname].has_key("min") and data.index[axisname].has_key("dmin")) or
                (data.index[axisname].has_key("d") and data.index[axisname].has_key("dmin")) or
                (data.index[axisname].has_key("max") and data.index[axisname].has_key("d")) or
                (data.index[axisname].has_key("max") and data.index[axisname].has_key("dmax")) or
                (data.index[axisname].has_key("d") and data.index[axisname].has_key("dmax"))):
                raise ValueError("multiple errorbar definition for axis name '%s'" % axisname)
            if (not data.index[axisname].has_key("x") and
                (data.index[axisname].has_key("d") or
                 data.index[axisname].has_key("dmin") or
                 data.index[axisname].has_key("dmax"))):
                raise ValueError("errorbar definition start value missing for axis name '%s'" % axisname)
        return columns

    def selectstyle(self, selectindex, selecttotal, data):
        data.symbol = attr.selectattr(self.symbol, selectindex, selecttotal)
        data.size_pt = unit.topt(unit.length(attr.selectattr(self.size_str, selectindex, selecttotal), default_type="v"))
        data.errorsize_pt = self.errorscale * data.size_pt
        if self.symbolattrs is not None:
            data.symbolattrs = attr.selectattrs(self.defaultsymbolattrs + self.symbolattrs, selectindex, selecttotal)
        else:
            data.symbolattrs = None
        if self.errorbarattrs is not None:
            data.errorbarattrs = attr.selectattrs(self.defaulterrorbarattrs + self.errorbarattrs, selectindex, selecttotal)
        else:
            data.errorbarattrs = None
        if self.lineattrs is not None:
            data.lineattrs = attr.selectattrs(self.defaultlineattrs + self.lineattrs, selectindex, selecttotal)
        else:
            data.lineattrs = None

    def adjustaxes(self, columns, data):
        # reverse lookup for axisnames
        # TODO: the reverse lookup is ugly
        axisnames = []
        for column in columns:
            for axisname in data.index.keys():
                for thiscolumn in data.index[axisname].values():
                    if thiscolumn == column and axisname not in axisnames:
                        axisnames.append(axisname)
        # TODO: perform check to verify that all columns for a given axisname are available at the same time
        for axisname in axisnames:
            if data.index[axisname].has_key("x"):
                data.axes[axisname].adjustrange(data.points, data.index[axisname]["x"])
            if data.index[axisname].has_key("min"):
                data.axes[axisname].adjustrange(data.points, data.index[axisname]["min"])
            if data.index[axisname].has_key("max"):
                data.axes[axisname].adjustrange(data.points, data.index[axisname]["max"])
            if data.index[axisname].has_key("d"):
                data.axes[axisname].adjustrange(data.points, data.index[axisname]["x"], deltaindex=data.index[axisname]["d"])
            if data.index[axisname].has_key("dmin"):
                data.axes[axisname].adjustrange(data.points, data.index[axisname]["x"], deltaminindex=data.index[axisname]["dmin"])
            if data.index[axisname].has_key("dmax"):
                data.axes[axisname].adjustrange(data.points, data.index[axisname]["x"], deltamaxindex=data.index[axisname]["dmax"])

    def drawsymbol_pt(self, c, x_pt, y_pt, data, point=None):
        if data.symbolattrs is not None:
            c.draw(path.path(*data.symbol(self, x_pt, y_pt, data.size_pt)), data.symbolattrs)

    def drawpoints(self, graph, data):
        if data.lineattrs is not None or data.errorbarattrs is not None:
            clipcanvas = graph.clipcanvas()
        data.line = path.path()
        moveto = 1
        errorlist = []
        if data.errorbarattrs is not None:
            for axisname, axisindex in zip(graph.axisnames, xrange(sys.maxint)):
                if data.index[axisname].keys() != ["x"]:
                    errorlist.append((axisname, axisindex))

        for point in data.points:
            # symbol and line
            vpos = []
            drawsymbol = 1
            for axisname in graph.axisnames:
                try:
                    v = data.axes[axisname].convert(point[data.index[axisname]["x"]])
                except:
                    moveto = 1
                    drawsymbol = 0
                    vpos.append(None)
                else:
                    if v < - self.epsilon or v > 1 + self.epsilon:
                        drawsymbol = 0
                    vpos.append(v)
            if drawsymbol:
                xpos, ypos = graph.vpos_pt(*vpos)
                self.drawsymbol_pt(graph, xpos, ypos, data, point=point)
                if moveto:
                    data.line.append(path.moveto_pt(xpos, ypos))
                    moveto = 0
                else:
                    data.line.append(path.lineto_pt(xpos, ypos))

            # errorbar loop over the different direction having errorbars
            for erroraxisname, erroraxisindex in errorlist:

                # check for validity of other point components
                for v, i in zip(vpos, xrange(sys.maxint)):
                    if v is None and i != erroraxisindex:
                        break
                else:
                    # calculate min and max
                    errorindex = data.index[erroraxisname]
                    try:
                        min = point[errorindex["x"]] - point[errorindex["d"]]
                    except:
                        try:
                            min = point[errorindex["x"]] - point[errorindex["dmin"]]
                        except:
                            try:
                                min = point[errorindex["min"]]
                            except:
                                min = None
                    try:
                        max = point[errorindex["x"]] + point[errorindex["d"]]
                    except:
                        try:
                            max = point[errorindex["x"]] + point[errorindex["dmax"]]
                        except:
                            try:
                                max = point[errorindex["max"]]
                            except:
                                max = None

                    # calculate vmin and vmax
                    try:
                        vmin = data.axes[erroraxisname].convert(min)
                    except:
                        vmin = None
                    try:
                        vmax = data.axes[erroraxisname].convert(max)
                    except:
                        vmax = None

                    # create vminpos and vmaxpos
                    vcaps = []
                    if vmin is not None:
                        vminpos = vpos[:]
                        if vmin > - self.epsilon and vmin < 1 + self.epsilon:
                            vminpos[erroraxisindex] = vmin
                            vcaps.append(vminpos)
                        else:
                            vminpos[erroraxisindex] = 0
                    elif vpos[erroraxisindex] is not None:
                        vminpos = vpos
                    else:
                        break
                    if vmax is not None:
                        vmaxpos = vpos[:]
                        if vmax > - self.epsilon and vmax < 1 + self.epsilon:
                            vmaxpos[erroraxisindex] = vmax
                            vcaps.append(vmaxpos)
                        else:
                            vmaxpos[erroraxisindex] = 1
                    elif vpos[erroraxisindex] is not None:
                        vmaxpos = vpos
                    else:
                        break

                    # create path for errorbars
                    errorpath = path.path()
                    errorpath += graph.vgeodesic(*(vminpos + vmaxpos))
                    for vcap in vcaps:
                        for axisname in graph.axisnames:
                            if axisname != erroraxisname:
                                errorpath += graph.vcap_pt(axisname, data.errorsize_pt, *vcap)

                    # stroke errorpath
                    if len(errorpath.path):
                        graph.stroke(errorpath, data.errorbarattrs)

        if data.lineattrs is not None:
            clipcanvas.stroke(data.line, data.lineattrs)

    def key_pt(self, c, x_pt, y_pt, width_pt, height_pt, data):
        self.drawsymbol_pt(c, x_pt+0.5*width_pt, y_pt+0.5*height_pt, data)
        if data.lineattrs is not None:
            c.stroke(path.line_pt(x_pt, y_pt+0.5*height_pt, x_pt+width_pt, y_pt+0.5*height_pt), data.lineattrs)


class line(symbolline):

    def __init__(self, lineattrs=[]):
        symbolline.__init__(self, symbolattrs=None, errorbarattrs=None, lineattrs=lineattrs)


class symbol(symbolline):

    def __init__(self, **kwargs):
        symbolline.__init__(self, lineattrs=None, **kwargs)



# class rect(symbollines):
# 
#     def __init__(self, palette=color.palette.Gray):
#         self.palette = palette
#         self.colorindex = None
#         symbol.__init__(self, symbolattrs=None, errorbarattrs=(), lineattrs=None)
# 
#     def iterate(self):
#         raise RuntimeError("style is not iterateable")
# 
#     def othercolumnkey(self, key, index):
#         if key == "color":
#             self.colorindex = index
#         else:
#             symbol.othercolumnkey(self, key, index)
# 
#     def drawerrorbar_pt(self, graph, topleft, top, topright,
#                                    left, center, right,
#                                    bottomleft, bottom, bottomright, point=None):
#         color = point[self.colorindex]
#         if color is not None:
#             if color != self.lastcolor:
#                 self.rectclipcanvas.set([self.palette.getcolor(color)])
#             if bottom is not None and left is not None:
#                 bottomleft = left[0], bottom[1]
#             if bottom is not None and right is not None:
#                 bottomright = right[0], bottom[1]
#             if top is not None and right is not None:
#                 topright = right[0], top[1]
#             if top is not None and left is not None:
#                 topleft = left[0], top[1]
#             if bottomleft is not None and bottomright is not None and topright is not None and topleft is not None:
#                 self.rectclipcanvas.fill(path.path(path.moveto_pt(*bottomleft),
#                                          graph._connect(*(bottomleft+bottomright)),
#                                          graph._connect(*(bottomright+topright)),
#                                          graph._connect(*(topright+topleft)),
#                                          path.closepath()))
# 
#     def drawpoints(self, graph, points):
#         if self.colorindex is None:
#             raise RuntimeError("column 'color' not set")
#         self.lastcolor = None
#         self.rectclipcanvas = graph.clipcanvas()
#         symbol.drawpoints(self, graph, points)


class text(symbol):

    defaulttextattrs = [textmodule.halign.center, textmodule.vshift.mathaxis]

    def __init__(self, textdx="0", textdy="0.3 cm", textattrs=[], **kwargs):
        self.textdx_str = textdx
        self.textdy_str = textdy
        self.textattrs = textattrs
        symbol.__init__(self, **kwargs)

    def setdata(self, graph, columns, data):
        columns = columns.copy()
        data.textindex = columns["text"]
        del columns["text"]
        return symbol.setdata(self, graph, columns, data)

    def selectstyle(self, selectindex, selecttotal, data):
        if self.textattrs is not None:
            data.textattrs = attr.selectattrs(self.defaulttextattrs + self.textattrs, selectindex, selecttotal)
        else:
            data.textattrs = None
        symbol.selectstyle(self, selectindex, selecttotal, data)

    def drawsymbol_pt(self, c, x, y, data, point=None):
        symbol.drawsymbol_pt(self, c, x, y, data, point)
        if None not in (x, y, point[data.textindex]) and data.textattrs is not None:
            c.text_pt(x + data.textdx_pt, y + data.textdy_pt, str(point[data.textindex]), data.textattrs)

    def drawpoints(self, graph, points):
        data.textdx = unit.length(self.textdx_str, default_type="v")
        data.textdy = unit.length(self.textdy_str, default_type="v")
        data.textdx_pt = unit.topt(data.textdx)
        data.textdy_pt = unit.topt(data.textdy)
        symbol.drawpoints(self, graph, points)


class arrow(_style):

    defaultlineattrs = []
    defaultarrowattrs = []

    def __init__(self, linelength="0.2 cm", arrowsize="0.1 cm", lineattrs=[], arrowattrs=[], epsilon=1e-10):
        self.linelength_str = linelength
        self.arrowsize_str = arrowsize
        self.lineattrs = lineattrs
        self.arrowattrs = arrowattrs
        self.epsilon = epsilon

    def setdata(self, graph, columns, data):
        if len(graph.axisnames) != 2:
            raise TypeError("arrow style restricted on two-dimensional graphs")
        columns = columns.copy()
        data.xaxis, data.xindex = _style.setdatapattern(self, graph, columns, re.compile(r"(%s([2-9]|[1-9][0-9]+)?)$" % graph.axisnames[0]))
        data.yaxis, data.yindex = _style.setdatapattern(self, graph, columns, re.compile(r"(%s([2-9]|[1-9][0-9]+)?)$" % graph.axisnames[1]))
        data.sizeindex = columns["size"]
        del columns["size"]
        data.angleindex = columns["angle"]
        del columns["angle"]
        return columns

    def adjustaxes(self, columns, data):
        if data.xindex in columns:
            data.xaxis.adjustrange(data.points, data.xindex)
        if data.yindex in columns:
            data.yaxis.adjustrange(data.points, data.yindex)

    def selectstyle(self, selectindex, selecttotal, data):
        if self.lineattrs is not None:
            data.lineattrs = attr.selectattrs(self.defaultlineattrs + self.lineattrs, selectindex, selecttotal)
        else:
            data.lineattrs = None
        if self.arrowattrs is not None:
            data.arrowattrs = attr.selectattrs(self.defaultarrowattrs + self.arrowattrs, selectindex, selecttotal)
        else:
            data.arrowattrs = None

    def drawpoints(self, graph, data):
        if data.lineattrs is not None and data.arrowattrs is not None:
            arrowsize = unit.length(self.arrowsize_str, default_type="v")
            linelength = unit.length(self.linelength_str, default_type="v")
            arrowsize_pt = unit.topt(arrowsize)
            linelength_pt = unit.topt(linelength)
            for point in data.points:
                xpos, ypos = graph.pos_pt(point[data.xindex], point[data.yindex], xaxis=data.xaxis, yaxis=data.yaxis)
                if point[data.sizeindex] > self.epsilon:
                    dx = math.cos(point[data.angleindex]*math.pi/180.0)
                    dy = math.sin(point[data.angleindex]*math.pi/180)
                    x1 = xpos-0.5*dx*linelength_pt*point[data.sizeindex]
                    y1 = ypos-0.5*dy*linelength_pt*point[data.sizeindex]
                    x2 = xpos+0.5*dx*linelength_pt*point[data.sizeindex]
                    y2 = ypos+0.5*dy*linelength_pt*point[data.sizeindex]
                    graph.stroke(path.line_pt(x1, y1, x2, y2), data.lineattrs +
                                 [deco.earrow(data.arrowattrs, size=arrowsize*point[data.sizeindex])])


class bar(_style):

    defaultfrompathattrs = []
    defaultbarattrs = [color.palette.Rainbow, deco.stroked([color.gray.black])]

    def __init__(self, fromvalue=None, frompathattrs=[], barattrs=[], subnames=None, epsilon=1e-10):
        self.fromvalue = fromvalue
        self.frompathattrs = frompathattrs
        self.barattrs = barattrs
        self.subnames = subnames
        self.epsilon = epsilon

    def setdata(self, graph, columns, data):
        # TODO: remove limitation to 2d graphs
        if len(graph.axisnames) != 2:
            raise TypeError("arrow style currently restricted on two-dimensional graphs")
        columns = columns.copy()
        xvalue = _style.setdatapattern(self, graph, columns, re.compile(r"(%s([2-9]|[1-9][0-9]+)?)$" % graph.axisnames[0]))
        yvalue = _style.setdatapattern(self, graph, columns, re.compile(r"(%s([2-9]|[1-9][0-9]+)?)$" % graph.axisnames[1]))
        if (xvalue is None and yvalue is None) or (xvalue is not None and yvalue is not None):
            raise TypeError("must specify exactly one value axis")
        if xvalue is not None:
            data.valuepos = 0
            data.nameaxis, data.nameindex = _style.setdatapattern(self, graph, columns, re.compile(r"(%s([2-9]|[1-9][0-9]+)?)name$" % graph.axisnames[1]))
            data.valueaxis = xvalue[0]
            data.valueindices = [xvalue[1]]
        else:
            data.valuepos = 1
            data.nameaxis, data.nameindex = _style.setdatapattern(self, graph, columns, re.compile(r"(%s([2-9]|[1-9][0-9]+)?)name$" % graph.axisnames[0]))
            data.valueaxis = yvalue[0]
            data.valueindices = [yvalue[1]]
        for i in xrange(1, sys.maxint):
            try:
                valueaxis, valueindex = _style.setdatapattern(self, graph, columns, re.compile(r"(%s([2-9]|[1-9][0-9]+)?)stack%i$" % (graph.axisnames[data.valuepos], i)))
            except:
                break
            if data.valueaxis != valueaxis:
                raise ValueError("different value axes for stacked bars")
            data.valueindices.append(valueindex)
        return columns

    def selectstyle(self, selectindex, selecttotal, data):
        if selectindex:
            data.frompathattrs = None
        else:
            data.frompathattrs = self.defaultfrompathattrs + self.frompathattrs
        if self.barattrs is not None:
            data.barattrs = attr.selectattrs(self.defaultbarattrs + self.barattrs, selectindex, selecttotal)
        else:
            data.barattrs = None
        data.selectindex = selectindex
        data.selecttotal = selecttotal
        if data.selecttotal != 1 and self.subnames is not None:
            raise ValueError("subnames not allowed when iterating over bars")

    def adjustaxes(self, columns, data):
        if data.nameindex in columns:
            if data.selecttotal == 1:
                data.nameaxis.adjustrange(data.points, data.nameindex, subnames=self.subnames)
            else:
                for i in range(data.selecttotal):
                    data.nameaxis.adjustrange(data.points, data.nameindex, subnames=[i])
        for valueindex in data.valueindices:
            if valueindex in columns:
                data.valueaxis.adjustrange(data.points, valueindex)

    def drawpoints(self, graph, data):
        if self.fromvalue is not None:
            vfromvalue = data.valueaxis.convert(self.fromvalue)
            if vfromvalue < -self.epsilon:
                vfromvalue = 0
            if vfromvalue > 1 + self.epsilon:
                vfromvalue = 1
            if data.frompathattrs is not None and vfromvalue > self.epsilon and vfromvalue < 1 - self.epsilon:
                if data.valuepos:
                    p = graph.vgeodesic(0, vfromvalue, 1, vfromvalue)
                else:
                    p = graph.vgeodesic(vfromvalue, 0, vfromvalue, 1)
                graph.stroke(p, data.frompathattrs)
        else:
            vfromvalue = 0
        l = len(data.valueindices)
        if l > 1:
            barattrslist = []
            for i in range(l):
                barattrslist.append(attr.selectattrs(data.barattrs, i, l))
        else:
            barattrslist = [data.barattrs]
        for point in data.points:
            vvaluemax = vfromvalue
            for valueindex, barattrs in zip(data.valueindices, barattrslist):
                vvaluemin = vvaluemax
                try:
                    vvaluemax = data.valueaxis.convert(point[valueindex])
                except:
                    continue

                if data.selecttotal == 1:
                    try:
                        vnamemin = data.nameaxis.convert((point[data.nameindex], 0))
                    except:
                        continue
                    try:
                        vnamemax = data.nameaxis.convert((point[data.nameindex], 1))
                    except:
                        continue
                else:
                    try:
                        vnamemin = data.nameaxis.convert((point[data.nameindex], data.selectindex, 0))
                    except:
                        continue
                    try:
                        vnamemax = data.nameaxis.convert((point[data.nameindex], data.selectindex, 1))
                    except:
                        continue

                if data.valuepos:
                    p = (graph.vgeodesic(vnamemin, vvaluemin, vnamemin, vvaluemax) <<
                         graph.vgeodesic(vnamemin, vvaluemax, vnamemax, vvaluemax) <<
                         graph.vgeodesic(vnamemax, vvaluemax, vnamemax, vvaluemin) <<
                         graph.vgeodesic(vnamemax, vvaluemin, vnamemin, vvaluemin))
                    p.append(path.closepath())
                else:
                    p = (graph.vgeodesic(vvaluemin, vnamemin, vvaluemin, vnamemax) <<
                         graph.vgeodesic(vvaluemin, vnamemax, vvaluemax, vnamemax) <<
                         graph.vgeodesic(vvaluemax, vnamemax, vvaluemax, vnamemin) <<
                         graph.vgeodesic(vvaluemax, vnamemin, vvaluemin, vnamemin))
                    p.append(path.closepath())
                if barattrs is not None:
                    graph.fill(p, barattrs)

    def key_pt(self, c, x_pt, y_pt, width_pt, height_pt, data):
        l = len(data.valueindices)
        if l > 1:
            for i in range(l):
                c.fill(path.rect_pt(x_pt+i*width_pt/l, y_pt, width_pt/l, height_pt), attr.selectattrs(data.barattrs, i, l))
        else:
            c.fill(path.rect_pt(x_pt, y_pt, width_pt, height_pt), data.barattrs)



################################################################################
# data
################################################################################


class data:

    defaultstyle = symbol()

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
        self.points = self.data.data

    def setstyle(self, graph, style):
        self.style = style
        unhandledcolumns = self.style.setdata(graph, self.columns, self)
        unhandledcolumnkeys = unhandledcolumns.keys()
        if len(unhandledcolumnkeys):
            raise ValueError("style couldn't handle column keys %s" % unhandledcolumnkeys)

    def selectstyle(self, graph, selectindex, selecttotal):
        self.style.selectstyle(selectindex, selecttotal, self)

    def adjustaxes(self, graph, step):
        """
        - on step == 0 axes with fixed data should be adjusted
        - on step == 1 the current axes ranges might be used to
          calculate further data (e.g. y data for a function y=f(x)
          where the y range depends on the x range)
        - on step == 2 axes ranges not previously set should be
          updated by data accumulated by step 1"""
        if step == 0:
            self.style.adjustaxes(self.columns.values(), self)

    def draw(self, graph):
        self.style.drawpoints(graph, self)


class function:

    defaultstyle = line()

    def __init__(self, expression, title=helper.nodefault, min=None, max=None, points=100, parser=mathtree.parser(), context={}):
        if title is helper.nodefault:
            self.title = expression
        else:
            self.title = title
        self.min = min
        self.max = max
        self.nopoints = points
        self.context = context
        self.result, expression = [x.strip() for x in expression.split("=")]
        self.mathtree = parser.parse(expression)
        self.variable = None

    def setstyle(self, graph, style):
        self.style = style
        for variable in self.mathtree.VarList():
            if variable in graph.axes.keys():
                if self.variable is None:
                    self.variable = variable
                else:
                    raise ValueError("multiple variables found")
        if self.variable is None:
            raise ValueError("no variable found")
        self.xaxis = graph.axes[self.variable]
        unhandledcolumns = self.style.setdata(graph, {self.variable: 0, self.result: 1}, self)
        unhandledcolumnkeys = unhandledcolumns.keys()
        if len(unhandledcolumnkeys):
            raise ValueError("style couldn't handle column keys %s" % unhandledcolumnkeys)

    def selectstyle(self, graph, selectindex, selecttotal):
        self.style.selectstyle(selectindex, selecttotal, self)

    def adjustaxes(self, graph, step):
        """
        - on step == 0 axes with fixed data should be adjusted
        - on step == 1 the current axes ranges might be used to
          calculate further data (e.g. y data for a function y=f(x)
          where the y range depends on the x range)
        - on step == 2 axes ranges not previously set should be
          updated by data accumulated by step 1"""
        if step == 0:
            min, max = graph.axes[self.variable].getrange()
            if self.min is not None: min = self.min
            if self.max is not None: max = self.max
            vmin = self.xaxis.convert(min)
            vmax = self.xaxis.convert(max)
            self.points = []
            for i in range(self.nopoints):
                x = self.xaxis.invert(vmin + (vmax-vmin)*i / (self.nopoints-1.0))
                self.points.append([x])
            self.style.adjustaxes([0], self)
        elif step == 1:
            for point in self.points:
                self.context[self.variable] = point[0]
                try:
                    point.append(self.mathtree.Calc(**self.context))
                except (ArithmeticError, ValueError):
                    point.append(None)
        elif step == 2:
            self.style.adjustaxes([1], self)

    def draw(self, graph):
        self.style.drawpoints(graph, self)


class paramfunction:

    defaultstyle = line()

    def __init__(self, varname, min, max, expression, title=helper.nodefault, points=100, parser=mathtree.parser(), context={}):
        if title is helper.nodefault:
            self.title = expression
        else:
            self.title = title
        self.varname = varname
        self.min = min
        self.max = max
        self.nopoints = points
        self.expression = {}
        self.mathtrees = {}
        varlist, expressionlist = expression.split("=")
        if mathtree.__useparser__ == mathtree.__newparser__: # XXX: switch between mathtree-parsers
            keys = varlist.split(",")
            mtrees = helper.ensurelist(parser.parse(expressionlist))
            if len(keys) != len(mtrees):
                raise ValueError("unpack tuple of wrong size")
            for i in range(len(keys)):
                key = keys[i].strip()
                if self.mathtrees.has_key(key):
                    raise ValueError("multiple assignment in tuple")
                self.mathtrees[key] = mtrees[i]
            if len(keys) != len(self.mathtrees.keys()):
                raise ValueError("unpack tuple of wrong size")
        else:
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
        self.points = []
        for i in range(self.nopoints):
            context[self.varname] = self.min + (self.max-self.min)*i / (self.nopoints-1.0)
            line = []
            for key, tree in self.mathtrees.items():
                line.append(tree.Calc(**context))
            self.points.append(line)

    def setstyle(self, graph, style):
        self.style = style
        columns = {}
        for key, index in zip(self.mathtrees.keys(), xrange(sys.maxint)):
            columns[key] = index
        unhandledcolumns = self.style.setdata(graph, columns, self)
        unhandledcolumnkeys = unhandledcolumns.keys()
        if len(unhandledcolumnkeys):
            raise ValueError("style couldn't handle column keys %s" % unhandledcolumnkeys)

    def selectstyle(self, graph, selectindex, selecttotal):
        self.style.selectstyle(selectindex, selecttotal, self)

    def adjustaxes(self, graph, step):
        if step == 0:
            self.style.adjustaxes(list(range(len(self.mathtrees.items()))), self)

    def draw(self, graph):
        self.style.drawpoints(graph, self)

