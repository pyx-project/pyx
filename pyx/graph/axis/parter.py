# -*- encoding: utf-8 -*-
#
#
# Copyright (C) 2002-2004 Jörg Lehmann <joerg@pyx-project.org>
# Copyright (C) 2003-2004 Michael Schindler <m-schindler@users.sourceforge.net>
# Copyright (C) 2002-2006 André Wobst <wobsta@pyx-project.org>
#
# This file is part of PyX (https://pyx-project.org/).
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

import math
from pyx.graph.axis import tick

# helpers:
def float_to_int(x):
    """converts the integer-precise float x into an int type"""
    # int() rounds towards zero:
    if x < -0.5: result = -int(-x+0.1)
    else: result = int(x+0.1)
    assert abs(x - result) < 1.0e-6
    return result


# Note: A partition is a list of ticks.

class _partdata:
    """state storage class for a partfunction

    partdata is used to keep local data and a current state to emulate
    generators. In the future we might use yield statements within a
    partfunction. Currently we add partdata by a lambda construct and
    do inplace modifications within partdata to keep track of the state.
    """

    def __init__(self, **kwargs):
        for key, value in list(kwargs.items()):
            setattr(self, key, value)


class _parter:
    """interface of a partitioner"""

    def partfunctions(self, min, max, extendmin, extendmax):
        """returns a list of partfunctions

        A partfunction can be called without further arguments and
        it will return a new partition each time, or None. Several
        partfunctions are used to walk in different "directions"
        (like more and less partitions).

        Note that we do not alternate walking in different directions
        (i.e. alternate the partfunction calls). Instead we first walk
        into one direction (which should give less and less ticks) until
        the rating becomes bad and when try more ticks. We want to keep
        the number of ticks small compared to a simple alternate search.
        """
        # This is a (useless) empty partitioner.
        return []


class linear(_parter):
    """partitioner to create a single linear partition"""

    def __init__(self, tickdists=None, labeldists=None, extendtick=0, extendlabel=None, epsilon=1e-10):
        if tickdists is None and labeldists is not None:
            self.ticklist = [tick.rational(labeldists[0])]
        else:
            self.ticklist = list(map(tick.rational, tickdists))
        if labeldists is None and tickdists is not None:
            self.labellist = [tick.rational(tickdists[0])]
        else:
            self.labellist = list(map(tick.rational, labeldists))
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

    def partfunction(self, data):
        if data.first:
            data.first = 0
            min = data.min
            max = data.max
            if self.extendtick is not None and len(self.ticklist) > self.extendtick:
                min, max = self.extendminmax(min, max, self.ticklist[self.extendtick], data.extendmin, data.extendmax)
            if self.extendlabel is not None and len(self.labellist) > self.extendlabel:
                min, max = self.extendminmax(min, max, self.labellist[self.extendlabel], data.extendmin, data.extendmax)

            ticks = []
            for i in range(len(self.ticklist)):
                ticks = tick.mergeticklists(ticks, self.getticks(min, max, self.ticklist[i], ticklevel=i))
            for i in range(len(self.labellist)):
                ticks = tick.mergeticklists(ticks, self.getticks(min, max, self.labellist[i], labellevel=i))

            return ticks

        return None

    def partfunctions(self, min, max, extendmin, extendmax):
        return [lambda d=_partdata(first=1, min=min, max=max, extendmin=extendmin, extendmax=extendmax):
                       self.partfunction(d)]

lin = linear


class autolinear(_parter):
    """partitioner to create an arbitrary number of linear partitions"""

    defaultvariants = [[tick.rational((1, 1)), tick.rational((1, 2))],
                       [tick.rational((2, 1)), tick.rational((1, 1))],
                       [tick.rational((5, 2)), tick.rational((5, 4))],
                       [tick.rational((5, 1)), tick.rational((5, 2))]]

    def __init__(self, variants=defaultvariants, extendtick=0, epsilon=1e-10):
        self.variants = variants
        self.extendtick = extendtick
        self.epsilon = epsilon

    def partfunctions(self, min, max, extendmin, extendmax):
        try:
            logmm = math.log(max - min) / math.log(10)
        except ArithmeticError:
            raise RuntimeError("partitioning failed due to empty or invalid axis range")
        if logmm < 0: # correction for rounding towards zero of the int routine
            base = tick.rational((10, 1), power=int(logmm-1))
        else:
            base = tick.rational((10, 1), power=int(logmm))
        ticks = list(map(tick.rational, self.variants[0]))
        useticks = [t * base for t in ticks]

        return [lambda d=_partdata(min=min, max=max, extendmin=extendmin, extendmax=extendmax,
                                   sign=1, tickindex=-1, base=tick.rational(base)):
                       self.partfunction(d),
                lambda d=_partdata(min=min, max=max, extendmin=extendmin, extendmax=extendmax,
                                   sign=-1, tickindex=0, base=tick.rational(base)):
                       self.partfunction(d)]

    def partfunction(self, data):
        if data.sign == 1:
            if data.tickindex < len(self.variants) - 1:
                data.tickindex += 1
            else:
                data.tickindex = 0
                data.base.num *= 10
        else:
            if data.tickindex:
                data.tickindex -= 1
            else:
                data.tickindex = len(self.variants) - 1
                data.base.denom *= 10
        tickdists = [tick.rational(t) * data.base for t in self.variants[data.tickindex]]
        linearparter = linear(tickdists=tickdists, extendtick=self.extendtick, epsilon=self.epsilon)
        return linearparter.partfunctions(min=data.min, max=data.max, extendmin=data.extendmin, extendmax=data.extendmax)[0]()

autolin = autolinear


class preexp:
    """definition of a logarithmic partition

    exp is an integer, which defines multiplicator (usually 10).
    pres are a list of tick positions (rational numbers, e.g.
    instances of rational). possible positions are the tick
    positions and arbitrary divisions and multiplications of
    the tick positions by exp."""

    def __init__(self, pres, exp):
         self.pres = pres
         self.exp = exp


class logarithmic(linear):
    """partitioner to create a single logarithmic partition"""

    # define some useful constants
    pre1exp    = preexp([tick.rational((1, 1))], 10)
    pre125exp  = preexp([tick.rational((1, 1)), tick.rational((2, 1)), tick.rational((5, 1))], 10)
    pre1to9exp = preexp([tick.rational((x, 1)) for x in range(1, 10)], 10)
    #  ^- we always include 1 in order to get extendto(tick|label)level to work as expected

    def __init__(self, tickpreexps=None, labelpreexps=None, extendtick=0, extendlabel=None, epsilon=1e-10):
        if tickpreexps is None and labelpreexps is not None:
            self.ticklist = [labelpreexps[0]]
        else:
            self.ticklist = tickpreexps

        if labelpreexps is None and tickpreexps is not None:
            self.labellist = [tickpreexps[0]]
        else:
            self.labellist = labelpreexps
        self.extendtick = extendtick
        self.extendlabel = extendlabel
        self.epsilon = epsilon

    def extendminmax(self, min, max, preexp, extendmin, extendmax):
        # this bracketing function is similar to the one used for negative logarithmic axes,
        # it is here to convince that the algorithm is right
        assert min > 0
        assert max > 0
        # precondition: the preexp.pres must be strictly increasing and positive
        for x, y in zip(preexp.pres, preexp.pres[1:]):
            assert x > 0  and y > 0
            assert x < y

        # bracketing the minimum value:

        # thelogs is a decreasing list:
        thelogs = [math.log(min/float(x)) / math.log(preexp.exp) + self.epsilon for x in preexp.pres]
        assert thelogs[0] >= thelogs[-1]
        # find the integer-step in thelogs:
        n = float_to_int(math.floor(thelogs[0]))
        # find the index of the integer-step:
        # we need the last index before the step, or if the integer-step is exactly at one value, we need that one.
        i = len(thelogs)-1 # take the last entry if no step will be found:
        for ii in range(len(thelogs)-1):
            if thelogs[ii] >= n and n > thelogs[ii+1]:
                i = ii
                break

        # check the original condition for min (without the log)
        assert 0 <= i < len(preexp.pres)
        lower = float(preexp.pres[i])*preexp.exp**n
        upper = (float(preexp.pres[i+1])*preexp.exp**n if i+1<len(preexp.pres) else float(preexp.pres[0])*preexp.exp**(n+1))
        #print("bracketing minimum:", lower, "<=", min, "<", upper, sep=" ")
        assert lower <= min and min < upper

        # bracketing the maximum value:

        # thelogs is a decreasing list:
        thelogs = [math.log(max/float(x)) / math.log(preexp.exp) - self.epsilon for x in preexp.pres]
        assert thelogs[0] >= thelogs[-1]
        # find the integer-step in thelogs:
        m = float_to_int(math.ceil(thelogs[-1]))
        # find the index of the integer-step:
        # we need the first index after the step, or if the integer-step is exactly at one value, we need that one.
        k = 0 # take the first entry if no step will be found:
        for kk in range(len(thelogs)-1, 0, -1):
            if thelogs[kk-1] > m and m >= thelogs[kk]:
                k = kk
                break

        # check the original equations (without the log)
        assert 0 <= k < len(preexp.pres)
        lower = (float(preexp.pres[k-1])*preexp.exp**m if k >= 1 else float(preexp.pres[-1])*preexp.exp**(m-1))
        upper = float(preexp.pres[k])*preexp.exp**m
        #print("bracketing maximum:", lower, "<", max, "<=", upper, sep=" ")
        assert max - upper <= 0 and lower - max < 0

        # prepare return values:
        if extendmin:
            min = float(preexp.pres[i]) * float(preexp.exp)**n
        if extendmax:
            max = float(preexp.pres[k]) * float(preexp.exp)**m
        return min, max

    def getticks(self, min, max, preexp, ticklevel=None, labellevel=None):
        ticks = []
        for f in preexp.pres:
            thisticks = []
            imin = float_to_int(math.ceil(math.log(min / float(f)) /
                                          math.log(preexp.exp) - self.epsilon))
            imax = float_to_int(math.floor(math.log(max / float(f)) /
                                           math.log(preexp.exp) + self.epsilon))
            for i in range(imin, imax + 1):
                pos = f * tick.rational((preexp.exp, 1), power=i)
                thisticks.append(tick.tick((pos.num, pos.denom), ticklevel = ticklevel, labellevel = labellevel))
            ticks = tick.mergeticklists(ticks, thisticks)
        return ticks

log = logarithmic


class negative_logarithmic(linear):
    """partitioner to create a single logarithmic partition of negative values"""

    # define some useful constants
    pre1exp    = preexp([tick.rational((-1, 1))], 10)
    pre125exp  = preexp([tick.rational((-5, 1)), tick.rational((-2, 1)), tick.rational((-1, 1))], 10)
    pre1to9exp = preexp([tick.rational((x, 1)) for x in range(-9, 0)], 10)
    #  ^- we always include 1 in order to get extendto(tick|label)level to work as expected

    def __init__(self, tickpreexps=None, labelpreexps=None, extendtick=0, extendlabel=None, epsilon=1e-10):
        if tickpreexps is None and labelpreexps is not None:
            self.ticklist = [labelpreexps[0]]
        else:
            self.ticklist = tickpreexps

        if labelpreexps is None and tickpreexps is not None:
            self.labellist = [tickpreexps[0]]
        else:
            self.labellist = labelpreexps
        self.extendtick = extendtick
        self.extendlabel = extendlabel
        self.epsilon = epsilon

    def extendminmax(self, min, max, preexp, extendmin, extendmax):
        assert min < 0
        assert max < 0
        # precondition: the preexp.pres must be strictly increasing and negative
        for x, y in zip(preexp.pres, preexp.pres[1:]):
            assert x < 0  and y < 0
            assert x < y

        # bracketing the minimum value:

        # thelogs is an increasing list:
        thelogs = [math.log(min/float(x)) / math.log(preexp.exp) - self.epsilon for x in preexp.pres]
        assert thelogs[0] <= thelogs[-1]
        # find the integer-step in thelogs:
        n = float_to_int(math.ceil(thelogs[0]))
        # find the index of the integer-step:
        # we need the last index before the step, or if the integer-step is exactly at one value, we need that one.
        i = len(thelogs)-1 # take the last entry if no step will be found:
        for ii in range(len(thelogs)-1):
            if thelogs[ii] <= n and n < thelogs[ii+1]:
                i = ii
                break

        # check the original equations (without the log)
        assert 0 <= i < len(preexp.pres)
        lower = float(preexp.pres[i])*preexp.exp**n
        upper = (float(preexp.pres[i+1])*preexp.exp**n if i+1<len(preexp.pres) else float(preexp.pres[0])*preexp.exp**(n-1))
        #print("bracketing minimum:", lower, "<=", min, "<", upper, sep=" ")
        assert lower <= min
        assert min < upper

        # bracketing the maximum value:

        # thelogs is an increasing list:
        thelogs = [math.log(max/float(x)) / math.log(preexp.exp) + self.epsilon for x in preexp.pres]
        assert thelogs[0] <= thelogs[-1]
        # find the integer-step in thelogs:
        m = float_to_int(math.floor(thelogs[-1]))
        # find the index of the integer-step:
        # we need the first index after the step, or if the integer-step is exactly at one value, we need that one.
        k = 0 # take the first entry if no step will be found:
        for kk in range(len(thelogs)-1, 0, -1):
            if thelogs[kk-1] < m and m <= thelogs[kk]:
                k = kk
                break

        # check the original equations (without the log)
        assert 0 <= k < len(preexp.pres)
        lower = (float(preexp.pres[k-1])*preexp.exp**m if k >= 1 else float(preexp.pres[-1])*preexp.exp**(m+1))
        upper = float(preexp.pres[k])*preexp.exp**m
        #print("bracketing maximum:", lower, "<", max, "<=", upper, sep=" ")
        #ssert max <= upper      # comparison of large numbers cannot do the low-bit corrections
        assert max - upper <= 0  # that the subtraction apparently can do
        #ssert lower < max
        assert lower - max < 0

        # prepare return values:
        if extendmin:
            min = float(preexp.pres[i]) * float(preexp.exp)**n
        if extendmax:
            max = float(preexp.pres[k]) * float(preexp.exp)**m
        print("extended minmax:", min, max)
        return min, max

    def getticks(self, min, max, preexp, ticklevel=None, labellevel=None):
        assert min <= max
        ticks = []
        for f in preexp.pres:
            thisticks = []
            imin = float_to_int(math.ceil(math.log(max / float(f)) /
                                math.log(preexp.exp) - self.epsilon))
            imax = float_to_int(math.floor(math.log(min / float(f)) /
                                math.log(preexp.exp) + self.epsilon))
            assert imin <= imax
            for i in range(imin, imax + 1):
                pos = f * tick.rational((preexp.exp, 1), power=i)
                assert min - 1.0e-8 <= float(pos)
                assert float(pos) <= max + 1.0e-8
                thisticks.append(tick.tick((pos.num, pos.denom), ticklevel = ticklevel, labellevel = labellevel))
            ticks = tick.mergeticklists(ticks, thisticks)
        return ticks

neglog = negative_logarithmic


class autologarithmic(logarithmic):
    """partitioner to create several logarithmic partitions"""

    defaultvariants = [([logarithmic.pre1exp,      # ticks
                         logarithmic.pre1to9exp],  # subticks
                        [logarithmic.pre1exp,      # labels
                         logarithmic.pre125exp]),  # sublevels

                       ([logarithmic.pre1exp,      # ticks
                         logarithmic.pre1to9exp],  # subticks
                        None)]                     # labels like ticks

    def __init__(self, variants=defaultvariants, extendtick=0, extendlabel=None, autoexponent=10, epsilon=1e-10):
        self.variants = variants
        self.extendtick = extendtick
        self.extendlabel = extendlabel
        self.autoexponent = autoexponent
        self.epsilon = epsilon

    def partfunctions(self, min, max, extendmin, extendmax):
        return [lambda d=_partdata(min=min, max=max, extendmin=extendmin, extendmax=extendmax,
                                   variantsindex=len(self.variants)):
                       self.variantspartfunction(d),
                lambda d=_partdata(min=min, max=max, extendmin=extendmin, extendmax=extendmax,
                                   exponent=self.autoexponent):
                       self.autopartfunction(d)]

    def variantspartfunction(self, data):
        data.variantsindex -= 1
        if 0 <= data.variantsindex:
            logarithmicparter= logarithmic(tickpreexps=self.variants[data.variantsindex][0], labelpreexps=self.variants[data.variantsindex][1],
                                           extendtick=self.extendtick, extendlabel=self.extendlabel, epsilon=self.epsilon)
            return logarithmicparter.partfunctions(min=data.min, max=data.max, extendmin=data.extendmin, extendmax=data.extendmax)[0]()
        return None

    def autopartfunction(self, data):
        data.exponent *= self.autoexponent
        logarithmicparter= logarithmic(tickpreexps=[preexp([tick.rational((1, 1))], data.exponent), logarithmic.pre1exp],
                                       extendtick=self.extendtick, extendlabel=self.extendlabel, epsilon=self.epsilon)
        return logarithmicparter.partfunctions(min=data.min, max=data.max, extendmin=data.extendmin, extendmax=data.extendmax)[0]()

autolog = autologarithmic


class negative_autologarithmic(negative_logarithmic):
    """partitioner to create several logarithmic partitions of negative values"""

    defaultvariants = [([negative_logarithmic.pre1exp,      # ticks
                         negative_logarithmic.pre1to9exp],  # subticks
                        [negative_logarithmic.pre1exp,      # labels
                         negative_logarithmic.pre125exp]),  # not all sublabels

                       ([negative_logarithmic.pre1exp,      # ticks
                         negative_logarithmic.pre1to9exp],  # subticks
                        None)]                              # labels like ticks

    def __init__(self, variants=defaultvariants, extendtick=0, extendlabel=None, autoexponent=10, epsilon=1e-10):
        self.variants = variants
        self.extendtick = extendtick
        self.extendlabel = extendlabel
        self.autoexponent = autoexponent
        self.epsilon = epsilon

    def partfunctions(self, min, max, extendmin, extendmax):
        return [lambda d=_partdata(min=min, max=max, extendmin=extendmin, extendmax=extendmax,
                                   variantsindex=len(self.variants)):
                       self.variantspartfunction(d),
                lambda d=_partdata(min=min, max=max, extendmin=extendmin, extendmax=extendmax,
                                   exponent=self.autoexponent):
                       self.autopartfunction(d)]

    def variantspartfunction(self, data):
        data.variantsindex -= 1
        if 0 <= data.variantsindex:
            logarithmicparter = negative_logarithmic(
                tickpreexps=self.variants[data.variantsindex][0], labelpreexps=self.variants[data.variantsindex][1],
                extendtick=self.extendtick, extendlabel=self.extendlabel, epsilon=self.epsilon)
            return logarithmicparter.partfunctions(min=data.min, max=data.max, extendmin=data.extendmin, extendmax=data.extendmax)[0]()
        return None

    def autopartfunction(self, data):
        data.exponent *= self.autoexponent
        logarithmicparter = negative_logarithmic(
            tickpreexps=[preexp([tick.rational((-1, 1))], data.exponent), negative_logarithmic.pre1exp],
            extendtick=self.extendtick, extendlabel=self.extendlabel, epsilon=self.epsilon)
        return logarithmicparter.partfunctions(min=data.min, max=data.max, extendmin=data.extendmin, extendmax=data.extendmax)[0]()

negautolog = negative_autologarithmic


