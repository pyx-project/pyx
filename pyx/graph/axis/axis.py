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
from pyx import attr, helper
from pyx.graph.axis import painter, parter, rater, texter, tick


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
        self.x1 = float(basepoints[0][0])
        self.y1 = float(basepoints[0][1])
        self.x2 = float(basepoints[1][0])
        self.y2 = float(basepoints[1][1])
        self.dydx = (self.y2 - self.y1) / (self.x2 - self.x1)
        self.dxdy = (self.x2 - self.x1) / (self.y2 - self.y1)

    def convert(self, value):
        return self.y1 + self.dydx * (float(value) - self.x1)

    def invert(self, value):
        return self.x1 + self.dxdy * (float(value) - self.y1)


class _logmap:
    "logarithmic mapping"
    __implements__ = _Imap

    def setbasepoints(self, basepoints):
        self.x1 = float(math.log(basepoints[0][0]))
        self.y1 = float(basepoints[0][1])
        self.x2 = float(math.log(basepoints[1][0]))
        self.y2 = float(basepoints[1][1])
        self.dydx = (self.y2 - self.y1) / (self.x2 - self.x1)
        self.dxdy = (self.x2 - self.x1) / (self.y2 - self.y1)

    def convert(self, value):
        return self.y1 + self.dydx * (math.log(float(value)) - self.x1)

    def invert(self, value):
        return math.exp(self.x1 + self.dxdy * (float(value) - self.y1))


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
        - for use in split axis, bar axis etc.
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

    def __init__(self, min=None, max=None, reverse=0, divisor=None,
                       title=None, painter=painter.regular(), texter=texter.mixed(),
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
          by mergeticklists
        - note that some methods of this class want to access a
          parter and a rater; those attributes implementing _Iparter
          and _Irater should be initialized by the constructors
          of derived classes"""
        if min is not None and max is not None and min > max:
            min, max, reverse = max, min, not reverse
        self.fixmin, self.fixmax, self.min, self.max, self.reverse = min is not None, max is not None, min, max, reverse
        self.divisor = divisor
        self.usedivisor = 0
        self.title = title
        self.painter = painter
        self.texter = texter
        self.density = density
        self.maxworse = maxworse
        self.manualticks = self.checkfraclist(manualticks)
        self.axiscanvas = None
        self._setrange()

    def _setrange(self, min=None, max=None):
        if not self.fixmin and min is not None and (self.min is None or min < self.min):
            self.min = min
        if not self.fixmax and max is not None and (self.max is None or max > self.max):
            self.max = max
        if None not in (self.min, self.max) and self.min != self.max:
            if self.reverse:
                if self.usedivisor and self.divisor is not None:
                    self.setbasepoints(((self.min/self.divisor, 1), (self.max/self.divisor, 0)))
                else:
                    self.setbasepoints(((self.min, 1), (self.max, 0)))
            else:
                if self.usedivisor and self.divisor is not None:
                    self.setbasepoints(((self.min/self.divisor, 0), (self.max/self.divisor, 1)))
                else:
                    self.setbasepoints(((self.min, 0), (self.max, 1)))

    def _getrange(self):
        return self.min, self.max

    def _forcerange(self, range):
        self.min, self.max = range
        self._setrange()

    def setrange(self, min=None, max=None):
        if self.usedivisor and self.divisor is not None:
            min = float(self.divisor) * self.divisor
            max = float(self.divisor) * self.divisor
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
        if deltamaxindex is not None:
            for point in points:
                try:
                    value = point[index] + point[deltamaxindex] + self.zero
                except:
                    pass
                else:
                    if min is None or value < min: min = value
                    if max is None or value > max: max = value
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
            if self.usedivisor and self.divisor is not None:
                return float(self.min) / self.divisor, float(self.max) / self.divisor
            else:
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

        # temorarily enable the axis divisor
        self.usedivisor = 1
        self._setrange()

        # lesspart and morepart can be called after defaultpart;
        # this works although some axes may share their autoparting,
        # because the axes are processed sequentially
        first = 1
        if self.parter is not None:
            min, max = self.getrange()
            self.ticks = tick.mergeticklists(self.manualticks,
                                             self.parter.defaultpart(min, max, not self.fixmin, not self.fixmax))
            worse = 0
            nextpart = self.parter.lesspart
            while nextpart is not None:
                newticks = nextpart()
                if newticks is not None:
                    newticks = tick.mergeticklists(self.manualticks, newticks)
                    if first:
                        bestrate = self.rater.rateticks(self, self.ticks, self.density)
                        bestrate += self.rater.raterange(self.convert(self.ticks[-1])-
                                                         self.convert(self.ticks[0]), 1)
                        variants = [[bestrate, self.ticks]]
                        first = 0
                    newrate = self.rater.rateticks(self, newticks, self.density)
                    newrate += self.rater.raterange(self.convert(newticks[-1])-
                                                    self.convert(newticks[0]), 1)
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
                        self.setrange(self.ticks[0], self.ticks[-1])
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
                    self.setrange(self.ticks[0], self.ticks[-1])
                self.axiscanvas = variants[0][2]
            else:
                self.ticks = variants[0][1]
                self.texter.labels(self.ticks)
                if len(self.ticks):
                    self.setrange(self.ticks[0], self.ticks[-1])
                self.axiscanvas = painter.axiscanvas()
        else:
            if len(self.ticks):
                self.setrange(self.ticks[0], self.ticks[-1])
            self.texter.labels(self.ticks)
            if self.painter is not None:
                self.axiscanvas = self.painter.paint(axispos, self)
            else:
                self.axiscanvas = painter.axiscanvas()

        # disable the axis divisor
        self.usedivisor = 0
        self._setrange()

    def createlinkaxis(self, **args):
        return linked(self, **args)


class linear(_axis, _linmap):
    """implementation of a linear axis"""

    __implements__ = _Iaxis

    def __init__(self, parter=parter.autolinear(), rater=rater.linear(), **args):
        """initializes the instance
        - the parter attribute implements _Iparter
        - manualticks and the partitioner results are mixed
          by mergeticklists
        - the rater implements _Irater and is used to rate different
          tick lists created by the partitioner (after merging with
          manully set ticks)
        - futher keyword arguments are passed to _axis"""
        _axis.__init__(self, **args)
        if self.fixmin and self.fixmax:
            self.relsize = self.max - self.min
        self.parter = parter
        self.rater = rater

lin = linear


class logarithmic(_axis, _logmap):
    """implementation of a logarithmic axis"""

    __implements__ = _Iaxis

    def __init__(self, parter=parter.autologarithmic(), rater=rater.logarithmic(), **args):
        """initializes the instance
        - the parter attribute implements _Iparter
        - manualticks and the partitioner results are mixed
          by mergeticklists
        - the rater implements _Irater and is used to rate different
          tick lists created by the partitioner (after merging with
          manully set ticks)
        - futher keyword arguments are passed to _axis"""
        _axis.__init__(self, **args)
        if self.fixmin and self.fixmax:
            self.relsize = math.log(self.max) - math.log(self.min)
        self.parter = parter
        self.rater = rater

log = logarithmic


class _linked:
    """base for a axis linked to an already existing axis
    - almost all properties of the axis are "copied" from the
      axis this axis is linked to
    - usually, linked axis are used to create an axis to an
      existing axis with different painting properties; linked
      axis can be used to plot an axis twice at the opposite
      sides of a graphxy or even to share an axis between
      different graphs!"""

    __implements__ = _Iaxis

    def __init__(self, linkedaxis, painter=painter.linked()):
        """initializes the instance
        - it gets a axis this axis is linked to
        - it gets a painter to be used for this linked axis"""
        self.linkedaxis = linkedaxis
        self.painter = painter
        self.axiscanvas = None

    def __getattr__(self, attr):
        """access to unkown attributes are handed over to the
        axis this axis is linked to"""
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


class linked(_linked):
    """a axis linked to an already existing regular axis
    - adds divisor handling to _linked"""

    __implements__ = _Iaxis

    def finish(self, axispos):
        # temporarily enable the linkedaxis divisor
        self.linkedaxis.usedivisor = 1
        self.linkedaxis._setrange()

        _linked.finish(self, axispos)

        # disable the linkedaxis divisor again
        self.linkedaxis.usedivisor = 0
        self.linkedaxis._setrange()


class split:
    """implementation of a split axis
    - a split axis contains several (sub-)axes with
      non-overlapping data ranges -- between these subaxes
      the axis is "splitted"
    - (just to get sure: a split axis can contain other
      split axes as its subaxes)"""

    __implements__ = _Iaxis, painter._Iaxispos

    def __init__(self, subaxes, splitlist=[0.5], splitdist=0.1, relsizesplitdist=1,
                       title=None, painter=painter.split()):
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
          the split axis
        - the relsize of the split axis is the sum of the relsizes of the
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
        return linkedsplit(self, **args)


class omitsubaxispainter: pass

class linkedsplit(_linked):
    """a split axis linked to an already existing split axis
    - inherits the access to a linked axis -- as before,
      basically only the painter is replaced
    - it takes care of the creation of linked axes of
      the subaxes"""

    __implements__ = _Iaxis

    def __init__(self, linkedaxis, painter=painter.linkedsplit(), subaxispainter=omitsubaxispainter):
        """initializes the instance
        - linkedaxis is the axis this axis becomes linked to
        - painter is axispainter instance for this linked axis
        - subaxispainter is a changeable painter to be used for linked
          subaxes; if omitsubaxispainter the createlinkaxis method of
          the subaxis are called without a painter parameter"""
        _linked.__init__(self, linkedaxis, painter=painter)
        self.subaxes = []
        for subaxis in linkedaxis.subaxes:
            painter = attr.selectattr(subaxispainter, len(self.subaxes), len(linkedaxis.subaxes))
            if painter is omitsubaxispainter:
                self.subaxes.append(subaxis.createlinkaxis())
            else:
                self.subaxes.append(subaxis.createlinkaxis(painter=painter))


class bar:
    """implementation of a axis for bar graphs
    - a bar axes is different from a split axis by the way it
      selects its subaxes: the convert method gets a list,
      where the first entry is a name selecting a subaxis out
      of a list; instead of the term "bar" or "subaxis" the term
      "item" will be used here
    - the bar axis stores a list of names be identify the items;
      the names might be of any time (strings, integers, etc.);
      the names can be printed as the titles for the items, but
      alternatively the names might be transformed by the texts
      dictionary, which maps a name to a text to be used to label
      the items in the painter
    - usually, there is only one subaxis, which is used as
      the subaxis for all items
    - alternatively it is also possible to use another bar axis
      as a multisubaxis; it is copied via the createsubaxis
      method whenever another subaxis is needed (by that a
      nested bar axis with a different number of subbars at
      each item can be created)
    - any axis can be a subaxis of a bar axis; if no subaxis
      is specified at all, the bar axis simulates a linear
      subaxis with a fixed range of 0 to 1"""

    def __init__(self, subaxis=None, multisubaxis=None,
                       dist=0.5, firstdist=None, lastdist=None,
                       names=None, texts={},
                       title=None, painter=painter.bar()):
        """initialize the instance
        - subaxis contains a axis to be used as the subaxis
          for all items
        - multisubaxis might contain another bar axis instance
          to be used to construct a new subaxis for each item;
          (by that a nested bar axis with a different number
          of subbars at each item can be created)
        - only one of subaxis or multisubaxis can be set; if neither
          of them is set, the bar axis behaves like having a linear axis
          as its subaxis with a fixed range 0 to 1
        - the title attribute contains the axis title as a string
        - the dist is a relsize to be used as the distance between
          the items
        - the firstdist and lastdist are the distance before the
          first and after the last item, respectively; when set
          to None (the default), 0.5*dist is used
        - the relsize of the bar axis is the sum of the
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
        self.multisubaxis = multisubaxis
        if self.multisubaxis is not None:
            if subaxis is not None:
                raise RuntimeError("either use subaxis or multisubaxis")
            self.subaxis = []
        else:
            self.subaxis = subaxis
        self.title = title
        self.painter = painter
        self.axiscanvas = None
        self.names = []

    def createsubaxis(self):
        return bar(subaxis=self.multisubaxis.subaxis,
                   multisubaxis=self.multisubaxis.multisubaxis,
                   title=self.multisubaxis.title,
                   dist=self.multisubaxis.dist,
                   firstdist=self.multisubaxis.firstdist,
                   lastdist=self.multisubaxis.lastdist,
                   painter=self.multisubaxis.painter)

    def getrange(self):
        # TODO: we do not yet have a proper range handling for a bar axis
        return None

    def setrange(self, min=None, max=None):
        # TODO: we do not yet have a proper range handling for a bar axis
        raise RuntimeError("range handling for a bar axis is not implemented")

    def setname(self, name, *subnames):
        """add a name to identify an item at the bar axis
        - by using subnames, nested name definitions are
          possible
        - a style (or the user itself) might use this to
          insert new items into a bar axis
        - setting self.relsizes to None forces later recalculation"""
        if name not in self.names:
            self.relsizes = None
            self.names.append(name)
            if self.multisubaxis is not None:
                self.subaxis.append(self.createsubaxis())
        if len(subnames):
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
        """bar axis convert method
        - the value should be a list, where the first entry is
          a member of the names (set in the constructor or by the
          setname method); this first entry identifies an item in
          the bar axis
        - following values are passed to the appropriate subaxis
          convert method
        - when there is no subaxis, the convert method will behave
          like having a linear axis from 0 to 1 as subaxis"""
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
        return linkedbar(self, **args)


class linkedbar(_linked):
    """a bar axis linked to an already existing bar axis
    - inherits the access to a linked axis -- as before,
      basically only the painter is replaced
    - it must take care of the creation of linked axes of
      the subaxes"""

    __implements__ = _Iaxis

    def __init__(self, linkedaxis, painter=painter.linkedbar()):
        """initializes the instance
        - it gets a axis this linkaxis is linked to
        - it gets a painter to be used for this linked axis"""
        _linked.__init__(self, linkedaxis, painter=painter)
        if self.multisubaxis is not None:
            self.subaxis = [subaxis.createlinkaxis() for subaxis in self.linkedaxis.subaxis]
        elif self.subaxis is not None:
            self.subaxis = self.subaxis.createlinkaxis()


def pathaxis(path, axis, **kwargs):
    """creates an axiscanvas for an axis along a path"""
    axis.finish(painter.pathaxispos(path, axis.convert, **kwargs))
    return axis.axiscanvas
