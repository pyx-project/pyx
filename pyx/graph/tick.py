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


from pyx import helper


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
        # if other is None: # XXX disabled -- do we really need this?
        #     return 1
        try:
            return cmp(self.enum * other.denom, other.enum * self.denom)
        except:
            return cmp(float(self), other)

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
