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


import math
from pyx import helper
from pyx.graph.axis import tick


# partitioner (parter)
# please note the nomenclature:
# - a part (partition) is a list of tick instances; thus ticks `==' part
# - a parter (partitioner) is a class creating ticks


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


class linear:
    """linear partition scheme
    ticks and label distances are explicitly provided to the constructor"""

    __implements__ = _Iparter

    def __init__(self, tickdist=None, labeldist=None, extendtick=0, extendlabel=None, epsilon=1e-10):
        """configuration of the partition scheme
        - tickdist and labeldist should be a list, where the first value
          is the distance between ticks with ticklevel/labellevel 0,
          the second list for ticklevel/labellevel 1, etc.;
          a single entry is allowed without being a list
        - tickdist and labeldist values are passed to the rational constructor
        - when labeldist is None and tickdist is not None, the tick entries
          for ticklevel 0 are used for labels and vice versa (ticks<->labels)
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
            self.ticklist = (tick.rational(helper.ensuresequence(labeldist)[0]),)
        else:
            self.ticklist = map(tick.rational, helper.ensuresequence(tickdist))
        if labeldist is None and tickdist is not None:
            self.labellist = (tick.rational(helper.ensuresequence(tickdist)[0]),)
        else:
            self.labellist = map(tick.rational, helper.ensuresequence(labeldist))
        self.extendtick = extendtick
        self.extendlabel = extendlabel
        self.epsilon = epsilon

    def extendminmax(self, min, max, dist, extendmin, extendmax):
        """return new min, max tuple extending the range min, max
        - dist is the tick distance to be used
        - extendmin and extendmax are booleans to allow for the extension"""
        if extendmin:
            min = float(dist) * math.floor(min / float(dist) + self.epsilon)
        if extendmax:
            max = float(dist) * math.ceil(max / float(dist) - self.epsilon)
        return min, max

    def getticks(self, min, max, dist, ticklevel=None, labellevel=None):
        """return a list of equal spaced ticks
        - the tick distance is dist, the ticklevel is set to ticklevel and
          the labellevel is set to labellevel
        - min, max is the range where ticks should be placed"""
        imin = int(math.ceil(min/float(dist) - 0.5*self.epsilon))
        imax = int(math.floor(max/float(dist) + 0.5*self.epsilon))
        ticks = []
        for i in range(imin, imax + 1):
            ticks.append(tick.tick((i*dist.num, dist.denom), ticklevel=ticklevel, labellevel=labellevel))
        return ticks

    def defaultpart(self, min, max, extendmin, extendmax):
        if self.extendtick is not None and len(self.ticklist) > self.extendtick:
            min, max = self.extendminmax(min, max, self.ticklist[self.extendtick], extendmin, extendmax)
        if self.extendlabel is not None and len(self.labellist) > self.extendlabel:
            min, max = self.extendminmax(min, max, self.labellist[self.extendlabel], extendmin, extendmax)

        ticks = []
        for i in range(len(self.ticklist)):
            ticks = tick.mergeticklists(ticks, self.getticks(min, max, self.ticklist[i], ticklevel = i))
        for i in range(len(self.labellist)):
            ticks = tick.mergeticklists(ticks, self.getticks(min, max, self.labellist[i], labellevel = i))

        return ticks

    def lesspart(self):
        return None

    def morepart(self):
        return None

lin = linear


class autolinear:
    """automatic linear partition scheme
    - possible tick distances are explicitly provided to the constructor
    - tick distances are adjusted to the axis range by multiplication or division by 10"""

    __implements__ = _Iparter

    defaultvariants = [[tick.rational((1, 1)), tick.rational((1, 2))],
                       [tick.rational((2, 1)), tick.rational((1, 1))],
                       [tick.rational((5, 2)), tick.rational((5, 4))],
                       [tick.rational((5, 1)), tick.rational((5, 2))]]

    def __init__(self, variants=defaultvariants, extendtick=0, epsilon=1e-10):
        """configuration of the partition scheme
        - variants is a list of tickdist
        - tickdist should be a list, where the first value
          is the distance between ticks with ticklevel 0,
          the second for ticklevel 1, etc.
        - tickdist values are passed to the rational constructor
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
            base = tick.rational((10, 1), power=int(logmm-1))
        else:
            base = tick.rational((10, 1), power=int(logmm))
        ticks = map(tick.rational, self.variants[0])
        useticks = [t * base for t in ticks]
        self.lesstickindex = self.moretickindex = 0
        self.lessbase = tick.rational((base.num, base.denom))
        self.morebase = tick.rational((base.num, base.denom))
        self.min, self.max, self.extendmin, self.extendmax = min, max, extendmin, extendmax
        part = linear(tickdist=useticks, extendtick=self.extendtick, epsilon=self.epsilon)
        return part.defaultpart(self.min, self.max, self.extendmin, self.extendmax)

    def lesspart(self):
        if self.lesstickindex < len(self.variants) - 1:
            self.lesstickindex += 1
        else:
            self.lesstickindex = 0
            self.lessbase.num *= 10
        ticks = map(tick.rational, self.variants[self.lesstickindex])
        useticks = [t * self.lessbase for t in ticks]
        part = linear(tickdist=useticks, extendtick=self.extendtick, epsilon=self.epsilon)
        return part.defaultpart(self.min, self.max, self.extendmin, self.extendmax)

    def morepart(self):
        if self.moretickindex:
            self.moretickindex -= 1
        else:
            self.moretickindex = len(self.variants) - 1
            self.morebase.denom *= 10
        ticks = map(tick.rational, self.variants[self.moretickindex])
        useticks = [t * self.morebase for t in ticks]
        part = linear(tickdist=useticks, extendtick=self.extendtick, epsilon=self.epsilon)
        return part.defaultpart(self.min, self.max, self.extendmin, self.extendmax)

autolin = autolinear


class preexp:
    """storage class for the definition of logarithmic axes partitions
    instances of this class define tick positions suitable for
    logarithmic axes by the following instance variables:
    - exp: integer, which defines multiplicator (usually 10)
    - pres: list of tick positions (rational numbers, e.g. instances of rational)
    possible positions are these tick positions and arbitrary divisions
    and multiplications by the exp value"""

    def __init__(self, pres, exp):
         "create a preexp instance and store its pres and exp information"
         self.pres = pres
         self.exp = exp


class logarithmic(linear):
    """logarithmic partition scheme
    ticks and label positions are explicitly provided to the constructor"""

    __implements__ = _Iparter

    pre1exp5   = preexp([tick.rational((1, 1))], 100000)
    pre1exp4   = preexp([tick.rational((1, 1))], 10000)
    pre1exp3   = preexp([tick.rational((1, 1))], 1000)
    pre1exp2   = preexp([tick.rational((1, 1))], 100)
    pre1exp    = preexp([tick.rational((1, 1))], 10)
    pre125exp  = preexp([tick.rational((1, 1)), tick.rational((2, 1)), tick.rational((5, 1))], 10)
    pre1to9exp = preexp([tick.rational((x, 1)) for x in range(1, 10)], 10)
    #  ^- we always include 1 in order to get extendto(tick|label)level to work as expected

    def __init__(self, tickpos=None, labelpos=None, extendtick=0, extendlabel=None, epsilon=1e-10):
        """configuration of the partition scheme
        - tickpos and labelpos should be a list, where the first entry
          is a preexp instance describing ticks with ticklevel/labellevel 0,
          the second is a preexp instance for ticklevel/labellevel 1, etc.;
          a single entry is allowed without being a list
        - when labelpos is None and tickpos is not None, the tick entries
          for ticklevel 0 are used for labels and vice versa (ticks<->labels)
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
        if tickpos is None and labelpos is not None:
            self.ticklist = (helper.ensuresequence(labelpos)[0],)
        else:
            self.ticklist = helper.ensuresequence(tickpos)

        if labelpos is None and tickpos is not None:
            self.labellist = (helper.ensuresequence(tickpos)[0],)
        else:
            self.labellist = helper.ensuresequence(labelpos)
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
            minrational = preexp.pres[minindex - 1]
        else:
            minrational = preexp.pres[-1]
            minpower -= 1
        if maxindex != len(preexp.pres) - 1:
            maxrational = preexp.pres[maxindex + 1]
        else:
            maxrational = preexp.pres[0]
            maxpower += 1
        if extendmin:
            min = float(minrational) * float(preexp.exp) ** minpower
        if extendmax:
            max = float(maxrational) * float(preexp.exp) ** maxpower
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
            thisticks = []
            imin = int(math.ceil(math.log(min / float(f)) /
                                 math.log(preexp.exp) - 0.5 * self.epsilon))
            imax = int(math.floor(math.log(max / float(f)) /
                                  math.log(preexp.exp) + 0.5 * self.epsilon))
            for i in range(imin, imax + 1):
                pos = f * tick.rational((preexp.exp, 1), power=i)
                thisticks.append(tick.tick((pos.num, pos.denom), ticklevel = ticklevel, labellevel = labellevel))
            ticks = tick.mergeticklists(ticks, thisticks)
        return ticks

log = logarithmic


class autologarithmic(logarithmic):
    """automatic logarithmic partition scheme
    possible tick positions are explicitly provided to the constructor"""

    __implements__ = _Iparter

    defaultvariants = [([logarithmic.pre1exp,      # ticks
                         logarithmic.pre1to9exp],  # subticks
                        [logarithmic.pre1exp,      # labels
                         logarithmic.pre125exp]),  # sublevels

                       ([logarithmic.pre1exp,      # ticks
                         logarithmic.pre1to9exp],  # subticks
                        None),                     # labels like ticks

                       ([logarithmic.pre1exp2,     # ticks
                         logarithmic.pre1exp],     # subticks
                        None),                     # labels like ticks

                       ([logarithmic.pre1exp3,     # ticks
                         logarithmic.pre1exp],     # subticks
                        None),                     # labels like ticks

                       ([logarithmic.pre1exp4,     # ticks
                         logarithmic.pre1exp],     # subticks
                        None),                     # labels like ticks

                       ([logarithmic.pre1exp5,     # ticks
                         logarithmic.pre1exp],     # subticks
                        None)]                     # labels like ticks

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
        part = logarithmic(tickpos=self.variants[self.variantsindex][0], labelpos=self.variants[self.variantsindex][1],
                           extendtick=self.extendtick, extendlabel=self.extendlabel, epsilon=self.epsilon)
        return part.defaultpart(self.min, self.max, self.extendmin, self.extendmax)

    def lesspart(self):
        self.lessvariantsindex += 1
        if self.lessvariantsindex < len(self.variants):
            part = logarithmic(tickpos=self.variants[self.lessvariantsindex][0], labelpos=self.variants[self.lessvariantsindex][1],
                               extendtick=self.extendtick, extendlabel=self.extendlabel, epsilon=self.epsilon)
            return part.defaultpart(self.min, self.max, self.extendmin, self.extendmax)

    def morepart(self):
        self.morevariantsindex -= 1
        if self.morevariantsindex >= 0:
            part = logarithmic(tickpos=self.variants[self.morevariantsindex][0], labelpos=self.variants[self.morevariantsindex][1],
                               extendtick=self.extendtick, extendlabel=self.extendlabel, epsilon=self.epsilon)
            return part.defaultpart(self.min, self.max, self.extendmin, self.extendmax)

autolog = autologarithmic
