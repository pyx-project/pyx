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


import sys

# test automatic long conversion
try:
    sys.maxint+1
    autolong = 1
except OverflowError:
    autolong = 0


class rational:
    """rational class performing some basic rational arithmetics
    the axis partitioning uses rational arithmetics (with infinite accuracy)
    basically it contains self.enum and self.denom"""

    def initfromstring(self, s):
        "converts a string 0.123 into a rational"
        expparts = s.strip().replace("E", "e").split("e")
        if len(expparts) > 2:
            raise ValueError("multiple 'e' found in '%s'" % s)
        commaparts = expparts[0].split(".")
        if len(commaparts) > 2:
            raise ValueError("multiple '.' found in '%s'" % expparts[0])
        if len(commaparts) == 1:
            commaparts = [commaparts[0], ""]
        self.enum = 1
        if autolong:
            self.denom = 10 ** len(commaparts[1])
        else:
            self.denom = 10L ** len(commaparts[1])
        neg = len(commaparts[0]) and commaparts[0][0] == "-"
        if neg:
            commaparts[0] = commaparts[0][1:]
        elif len(commaparts[0]) and commaparts[0][0] == "+":
            commaparts[0] = commaparts[0][1:]
        if len(commaparts[0]):
            if not commaparts[0].isdigit():
                raise ValueError("unrecognized characters in '%s'" % s)
            try:
                x = int(commaparts[0])
            except:
                x = long(commaparts[0])
        else:
            x = 0
        if len(commaparts[1]):
            if not commaparts[1].isdigit():
                raise ValueError("unrecognized characters in '%s'" % s)
            try:
                y = int(commaparts[1])
            except:
                y = long(commaparts[1])
        else:
            y = 0
        self.enum = x*self.denom + y
        if neg:
            self.enum = -self.enum
        if len(expparts) == 2:
            neg = expparts[1][0] == "-"
            if neg:
                expparts[1] = expparts[1][1:]
            elif expparts[1][0] == "+":
                expparts[1] = expparts[1][1:]
            if not expparts[1].isdigit():
                raise ValueError("unrecognized characters in '%s'" % s)
            if neg:
                if autolong:
                    self.denom *= 10 ** int(expparts[1])
                else:
                    self.denom *= 10L ** int(expparts[1])
            else:
                if autolong:
                    self.enum *= 10 ** int(expparts[1])
                else:
                    self.enum *= 10L ** int(expparts[1])

    def initfromfloat(self, x, floatprecision):
        "converts a float into a rational with finite resolution"
        if floatprecision < 0:
            raise RuntimeError("float resolution must be non-negative")
        self.initfromstring(("%%.%ig" % floatprecision) % x)

    def __init__(self, x, power=1, floatprecision=10):
        """initializes a rational
        - rational=(enum/denom)**power
        - x must be one of:
          - a string (like "1.2", "1.2e3", "1.2/3.4", etc.)
          - a float (converted using floatprecision)
          - a sequence of two integers
          - a rational instance"""
        if power == 0:
            self.enum = 1
            self.denom = 1
            return
        try:
            # does x behave like a number
            x + 0
        except:
            try:
                # does x behave like a string
                x + ""
            except:
                try:
                    # x might be a tuple
                    self.enum, self.denom = x
                except:
                    # otherwise it should have a enum and denom
                    self.enum, self.denom = x.enum, x.denom
            else:
                # x is a string
                fraction = x.split("/")
                if len(fraction) > 2:
                    raise ValueError("multiple '/' found in '%s'" % x)
                self.initfromstring(fraction[0])
                if len(fraction) == 2:
                    self /= rational(fraction[1])
        else:
            # x is a number
            self.initfromfloat(x, floatprecision)
        if not self.denom: raise ZeroDivisionError("zero denominator")
        if power == -1:
            self.enum, self.denom = self.denom, self.enum
        elif power < -1:
            if autolong:
                self.enum, self.denom = self.denom ** (-power), self.enum ** (-power)
            else:
                self.enum, self.denom = long(self.denom) ** (-power), long(self.enum) ** (-power)
        elif power > 1:
            if autolong:
                self.enum = self.enum ** power
                self.denom = self.denom ** power
            else:
                self.enum = long(self.enum) ** power
                self.denom = long(self.denom) ** power

    def __cmp__(self, other):
        try:
            return cmp(self.enum * other.denom, other.enum * self.denom)
        except:
            return cmp(float(self), other)

    def __abs__(self):
        return rational((abs(self.enum), abs(self.denom)))

    def __mul__(self, other):
        return rational((self.enum * other.enum, self.denom * other.denom))

    def __imul__(self, other):
        self.enum *= other.enum
        self.denom *= other.denom
        return self

    def __div__(self, other):
        return rational((self.enum * other.denom, self.denom * other.enum))

    def __idiv__(self, other):
        self.enum *= other.denom
        self.denom *= other.enum
        return self

    def __float__(self):
        "caution: avoid final precision of floats"
        return float(self.enum) / self.denom

    def __str__(self):
        return "%i/%i" % (self.enum, self.denom)


class tick(rational):
    """tick class
    a tick is a rational enhanced by
    - self.ticklevel (0 = tick, 1 = subtick, etc.)
    - self.labellevel (0 = label, 1 = sublabel, etc.)
    - self.label (a string) and self.labelattrs (a list, defaults to [])
    When ticklevel or labellevel is None, no tick or label is present at that value.
    When label is None, it should be automatically created (and stored), once the
    an axis painter needs it. Classes, which implement _Itexter do precisely that."""

    def __init__(self, pos, ticklevel=0, labellevel=0, label=None, labelattrs=[], **kwargs):
        """initializes the instance
        - see class description for the parameter description
        - **kwargs are passed to the rational constructor"""
        rational.__init__(self, pos, **kwargs)
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


def mergeticklists(list1, list2):
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


def maxlevels(ticks):
    "returns a tuple maxticklevel, maxlabellevel from a list of tick instances"
    maxticklevel = maxlabellevel = 0
    for tick in ticks:
        if tick.ticklevel is not None and tick.ticklevel >= maxticklevel:
            maxticklevel = tick.ticklevel + 1
        if tick.labellevel is not None and tick.labellevel >= maxlabellevel:
            maxlabellevel = tick.labellevel + 1
    return maxticklevel, maxlabellevel
