#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2002-2004 J�rg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2003-2004 Michael Schindler <m-schindler@users.sourceforge.net>
# Copyright (C) 2002-2004 Andr� Wobst <wobsta@users.sourceforge.net>
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


import math
from pyx import helper


# partitioner (parter)
# please note the nomenclature:
# - a part (partition) is a list of tick instances; thus ticks `==' part
# - a parter (partitioner) is a class creating ticks


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

    # do not destroy original lists
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
        level = 0
        for label in labels:
            usetext = helper.ensuresequence(label)
            i = 0
            for tick in ticks:
                if tick.labellevel == level:
                    tick.label = usetext[i]
                    i += 1
            if i != len(usetext):
                raise IndexError("wrong list length of labels at level %i" % level)
            level += 1
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