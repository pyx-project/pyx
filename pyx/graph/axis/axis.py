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
from pyx.graph.axis import painter, parter, positioner, rater, texter, tick


class axisdata:
    """axis data storage class

    Instances of this class are used to store axis data local to the
    graph. It will always contain an axispos instance provided by the
    graph during initialization."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class _linmap:
    "linear conversion methods"

    def convert(self, data, value):
        """axis coordinates -> graph coordinates"""
        return (float(value) - data.min) / (data.max - data.min)

    def invert(self, data, value):
        """graph coordinates -> axis coordinates"""
        return data.min + value * (data.max - data.min)


class _logmap:
    "logarithmic convertion methods"

    def convert(self, data, value):
        """axis coordinates -> graph coordinates"""
        # TODO: store log(data.min) and log(data.max)
        return (math.log(float(value)) - math.log(data.min)) / (math.log(data.max) - math.log(data.min))

    def invert(self, data, value):
        """graph coordinates -> axis coordinates"""
        return math.exp(math.log(data.min) + value * (math.log(data.max) - math.log(data.min)))


class _axis:
    """base implementation a regular axis

    Regular axis have a continuous variable like linear axes,
    logarithmic axes, time axes etc."""

    def __init__(self, min=None, max=None, reverse=0, divisor=None, title=None,
                       painter=painter.regular(), texter=texter.mixed(), linkpainter=painter.linked(),
                       density=1, maxworse=2, manualticks=[]):
        if min is not None and max is not None and min > max:
            min, max, reverse = max, min, not reverse
        self.min = min
        self.max = max
        self.reverse = reverse
        self.divisor = divisor
        self.title = title
        self.painter = painter
        self.texter = texter
        self.linkpainter = linkpainter
        self.density = density
        self.maxworse = maxworse
        self.manualticks = self.checkfraclist(manualticks)

    zero = 0.0

    def createdata(self):
        return axisdata(min=self.min, max=self.max)

    def adjustrange(self, data, points, index, deltamindata=None, deltaminindex=None, deltamaxdata=None, deltamaxindex=None):
        assert deltamindata is None or deltamaxdata is None
        if self.min is None or self.max is None:
            if deltamindata is not None:
                for point, minpoint in zip(points, deltamindata):
                    try:
                        if index is not None:
                            if deltaminindex is not None:
                                value = point[index] - minpoint[deltaminindex] + self.zero
                            else:
                                value = point[index] - minpoint + self.zero
                        else:
                            if deltaminindex is not None:
                                value = point - minpoint[deltaminindex] + self.zero
                            else:
                                value = point - minpoint + self.zero
                    except:
                        pass
                    else:
                        if self.min is None and (data.min is None or value < data.min): data.min = value
                        if self.max is None and (data.max is None or value > data.max): data.max = value
            elif deltamaxdata is not None:
                for point, maxpoint in zip(points, deltamaxdata):
                    try:
                        if index is not None:
                            if deltamaxindex is not None:
                                value = point[index] + maxpoint[deltamaxindex] + self.zero
                            else:
                                value = point[index] + maxpoint + self.zero
                        else:
                            if deltamaxindex is not None:
                                value = point + maxpoint[deltamaxindex] + self.zero
                            else:
                                value = point + maxpoint + self.zero
                    except:
                        pass
                    else:
                        if self.min is None and (data.min is None or value < data.min): data.min = value
                        if self.max is None and (data.max is None or value > data.max): data.max = value
            else:
                for point in points:
                    try:
                        if index is not None:
                            value = point[index] + self.zero
                        else:
                            value = point + self.zero
                    except:
                        pass
                    else:
                        if self.min is None and (data.min is None or value < data.min): data.min = value
                        if self.max is None and (data.max is None or value > data.max): data.max = value

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

    def create(self, data, positioner, graphtexrunner=None):
        if data.min is None or data.max is None:
            raise RuntimeError("incomplete axis range")

        # a variant is a data copy with local modifications to test several partitions
        class variant:
            def __init__(self, data, **kwargs):
                self.data = data
                for key, value in kwargs.items():
                    setattr(self, key, value)

            def __getattr__(self, key):
                return getattr(data, key)

            def __cmp__(self, other):
                return cmp(self.rate, other.rate)

        # build a list of variants
        bestrate = None
        if self.parter is not None:
            if self.divisor is not None:
                partfunctions = self.parter.partfunctions(data.min/self.divisor, data.max/self.divisor, self.min is None, self.max is None)
            else:
                partfunctions = self.parter.partfunctions(data.min, data.max, self.min is None, self.max is None)
            variants = []
            for partfunction in partfunctions:
                worse = 0
                while worse < self.maxworse:
                    worse += 1
                    ticks = partfunction()
                    if ticks is None:
                        break
                    ticks = tick.mergeticklists(self.manualticks, ticks, mergeequal=0)
                    if ticks:
                        rate = ( self.rater.rateticks(self, ticks, self.density) +
                                 self.rater.raterange(self.convert(data, ticks[-1]) -
                                                      self.convert(data, ticks[0]), 1) )
                        if bestrate is None or rate < bestrate:
                            bestrate = rate
                            worse = 0
                        variants.append(variant(data, rate=rate, ticks=ticks))
            if not variants:
                raise RuntimeError("no axis partitioning found")
        else:
            variants = [variant(data, rate=0, ticks=self.manualticks)]

        # get best variant
        if self.painter is None or len(variants) == 1:
            # in case of a single variant we're almost done
            self.adjustrange(data, variants[0].ticks, None)
            self.texter.labels(variants[0].ticks)
            if self.divisor:
                for t in variants[0].ticks:
                    t *= tick.rational(self.divisor)
            canvas = painter.axiscanvas(self.painter, graphtexrunner)
            data.ticks = variants[0].ticks
            if self.painter is not None:
                self.painter.paint(canvas, data, self, positioner)
            return canvas
        else:
            # build the layout for best variants
            for variant in variants:
                variant.storedcanvas = None
            variants.sort()
            while not variants[0].storedcanvas:
                self.adjustrange(variants[0], variants[0].ticks, None)
                self.texter.labels(variants[0].ticks)
                if self.divisor:
                    for t in variants[0].ticks:
                        t *= tick.rational(self.divisor)
                canvas = painter.axiscanvas(self.painter, graphtexrunner)
                self.painter.paint(canvas, variants[0], self, positioner)
                ratelayout = self.rater.ratelayout(canvas, self.density)
                if ratelayout is None:
                    del variants[0]
                    if not variants:
                        raise RuntimeError("no valid axis partitioning found")
                else:
                    variants[0].rate += ratelayout
                    variants[0].storedcanvas = canvas
                variants.sort()
            self.adjustrange(data, variants[0].ticks, None)
            data.ticks = variants[0].ticks
            return variants[0].storedcanvas

    def createlinkaxis(self, **args):
        return linked(self, **args)


class linear(_axis, _linmap):
    """linear axis"""

    def __init__(self, parter=parter.autolinear(), rater=rater.linear(), **args):
        _axis.__init__(self, **args)
        if self.min is not None and self.max is not None:
            self.relsize = self.max - self.min
        self.parter = parter
        self.rater = rater

lin = linear


class logarithmic(_axis, _logmap):
    """logarithmic axis"""

    def __init__(self, parter=parter.autologarithmic(), rater=rater.logarithmic(), **args):
        _axis.__init__(self, **args)
        if self.min is not None and self.max is not None:
            self.relsize = math.log(self.max) - math.log(self.min)
        self.parter = parter
        self.rater = rater

log = logarithmic


# class split:
#     """implementation of a split axis
#     - a split axis contains several (sub-)axes with
#       non-overlapping data ranges -- between these subaxes
#       the axis is "splitted"
#     - (just to get sure: a split axis can contain other
#       split axes as its subaxes)"""
# 
# 
#     def __init__(self, subaxes, splitlist=[0.5], splitdist=0.1, relsizesplitdist=1,
#                        title=None, painter=painter.split()):
#         """initializes the instance
#         - subaxes is a list of subaxes
#         - splitlist is a list of graph coordinates, where the splitting
#           of the main axis should be performed; if the list isn't long enough
#           for the subaxes, missing entries are considered to be None
#         - splitdist is the size of the splitting in graph coordinates, when
#           the associated splitlist entry is not None
#         - relsizesplitdist: a None entry in splitlist means, that the
#           position of the splitting should be calculated out of the
#           relsize values of conrtibuting subaxes (the size of the
#           splitting is relsizesplitdist in values of the relsize values
#           of the axes)
#         - title is the title of the axis as a string
#         - painter is the painter of the axis; it should be specialized to
#           the split axis
#         - the relsize of the split axis is the sum of the relsizes of the
#           subaxes including the relsizesplitdist"""
#         self.subaxes = subaxes
#         self.painter = painter
#         self.title = title
#         self.splitlist = splitlist
#         for subaxis in self.subaxes:
#             subaxis.vmin = None
#             subaxis.vmax = None
#         self.subaxes[0].vmin = 0
#         self.subaxes[0].vminover = None
#         self.subaxes[-1].vmax = 1
#         self.subaxes[-1].vmaxover = None
#         for i in xrange(len(self.splitlist)):
#             if self.splitlist[i] is not None:
#                 self.subaxes[i].vmax = self.splitlist[i] - 0.5*splitdist
#                 self.subaxes[i].vmaxover = self.splitlist[i]
#                 self.subaxes[i+1].vmin = self.splitlist[i] + 0.5*splitdist
#                 self.subaxes[i+1].vminover = self.splitlist[i]
#         i = 0
#         while i < len(self.subaxes):
#             if self.subaxes[i].vmax is None:
#                 j = relsize = relsize2 = 0
#                 while self.subaxes[i + j].vmax is None:
#                     relsize += self.subaxes[i + j].relsize + relsizesplitdist
#                     j += 1
#                 relsize += self.subaxes[i + j].relsize
#                 vleft = self.subaxes[i].vmin
#                 vright = self.subaxes[i + j].vmax
#                 for k in range(i, i + j):
#                     relsize2 += self.subaxes[k].relsize
#                     self.subaxes[k].vmax = vleft + (vright - vleft) * relsize2 / float(relsize)
#                     relsize2 += 0.5 * relsizesplitdist
#                     self.subaxes[k].vmaxover = self.subaxes[k + 1].vminover = vleft + (vright - vleft) * relsize2 / float(relsize)
#                     relsize2 += 0.5 * relsizesplitdist
#                     self.subaxes[k+1].vmin = vleft + (vright - vleft) * relsize2 / float(relsize)
#                 if i == 0 and i + j + 1 == len(self.subaxes):
#                     self.relsize = relsize
#                 i += j + 1
#             else:
#                 i += 1
# 
#         self.fixmin = self.subaxes[0].fixmin
#         if self.fixmin:
#             self.min = self.subaxes[0].min
#         self.fixmax = self.subaxes[-1].fixmax
#         if self.fixmax:
#             self.max = self.subaxes[-1].max
# 
#         self.axiscanvas = None
# 
#     def getrange(self):
#         min = self.subaxes[0].getrange()
#         max = self.subaxes[-1].getrange()
#         try:
#             return min[0], max[1]
#         except TypeError:
#             return None
# 
#     def setrange(self, min, max):
#         self.subaxes[0].setrange(min, None)
#         self.subaxes[-1].setrange(None, max)
# 
#     def adjustrange(self, *args, **kwargs):
#         self.subaxes[0].adjustrange(*args, **kwargs)
#         self.subaxes[-1].adjustrange(*args, **kwargs)
# 
#     def convert(self, value):
#         # TODO: proper raising exceptions (which exceptions go thru, which are handled before?)
#         if value < self.subaxes[0].max:
#             return self.subaxes[0].vmin + self.subaxes[0].convert(value)*(self.subaxes[0].vmax-self.subaxes[0].vmin)
#         for axis in self.subaxes[1:-1]:
#             if value > axis.min and value < axis.max:
#                 return axis.vmin + axis.convert(value)*(axis.vmax-axis.vmin)
#         if value > self.subaxes[-1].min:
#             return self.subaxes[-1].vmin + self.subaxes[-1].convert(value)*(self.subaxes[-1].vmax-self.subaxes[-1].vmin)
#         raise ValueError("value couldn't be assigned to a split region")
# 
#     def finish(self, axispos):
#         if self.axiscanvas is None:
#             self.axiscanvas = self.painter.paint(axispos, self)
# 
#     def createlinkaxis(self, **args):
#         return linkedsplit(self, **args)
# 
# 
# class omitsubaxispainter: pass
# 
# class linkedsplit(_linked):
#     """a split axis linked to an already existing split axis
#     - inherits the access to a linked axis -- as before,
#       basically only the painter is replaced
#     - it takes care of the creation of linked axes of
#       the subaxes"""
# 
# 
#     def __init__(self, linkedaxis, painter=painter.linkedsplit(), subaxispainter=omitsubaxispainter):
#         """initializes the instance
#         - linkedaxis is the axis this axis becomes linked to
#         - painter is axispainter instance for this linked axis
#         - subaxispainter is a changeable painter to be used for linked
#           subaxes; if omitsubaxispainter the createlinkaxis method of
#           the subaxis are called without a painter parameter"""
#         _linked.__init__(self, linkedaxis, painter=painter)
#         self.subaxes = []
#         for subaxis in linkedaxis.subaxes:
#             painter = attr.selectattr(subaxispainter, len(self.subaxes), len(linkedaxis.subaxes))
#             if painter is omitsubaxispainter:
#                 self.subaxes.append(subaxis.createlinkaxis())
#             else:
#                 self.subaxes.append(subaxis.createlinkaxis(painter=painter))
# 
# 
# class bar:
#     """implementation of a axis for bar graphs
#     - a bar axes is different from a split axis by the way it
#       selects its subaxes: the convert method gets a list,
#       where the first entry is a name selecting a subaxis out
#       of a list; instead of the term "bar" or "subaxis" the term
#       "item" will be used here
#     - the bar axis stores a list of names be identify the items;
#       the names might be of any time (strings, integers, etc.)
#     - usually, there is only one subaxis, which is used as
#       the subaxis for all items
#     - alternatively it is also possible to use another bar axis
#       as a multisubaxis; it is copied via the createsubaxis
#       method whenever another subaxis is needed (by that a
#       nested bar axis with a different number of subbars at
#       each item can be created)
#     - any axis can be a subaxis of a bar axis; if no subaxis
#       is specified at all, the bar axis simulates a linear
#       subaxis with a fixed range of 0 to 1"""
# 
#     def __init__(self, subaxis=None, multisubaxis=None,
#                        dist=0.5, firstdist=None, lastdist=None,
#                        title=None, painter=painter.bar()):
#         """initialize the instance
#         - subaxis contains a axis to be used as the subaxis
#           for all items
#         - multisubaxis might contain another bar axis instance
#           to be used to construct a new subaxis for each item;
#           (by that a nested bar axis with a different number
#           of subbars at each item can be created)
#         - only one of subaxis or multisubaxis can be set; if neither
#           of them is set, the bar axis behaves like having a linear axis
#           as its subaxis with a fixed range 0 to 1
#         - the title attribute contains the axis title as a string
#         - the dist is a relsize to be used as the distance between
#           the items
#         - the firstdist and lastdist are the distance before the
#           first and after the last item, respectively; when set
#           to None (the default), 0.5*dist is used
#         - the relsize of the bar axis is the sum of the
#           relsizes including all distances between the items"""
#         self.dist = dist
#         if firstdist is not None:
#             self.firstdist = firstdist
#         else:
#             self.firstdist = 0.5 * dist
#         if lastdist is not None:
#             self.lastdist = lastdist
#         else:
#             self.lastdist = 0.5 * dist
#         self.relsizes = None
#         self.multisubaxis = multisubaxis
#         if self.multisubaxis is not None:
#             if subaxis is not None:
#                 raise RuntimeError("either use subaxis or multisubaxis")
#             self.subaxis = []
#         else:
#             self.subaxis = subaxis
#         self.title = title
#         self.painter = painter
#         self.axiscanvas = None
#         self.names = []
# 
#     def createsubaxis(self):
#         return bar(subaxis=self.multisubaxis.subaxis,
#                    multisubaxis=self.multisubaxis.multisubaxis,
#                    title=self.multisubaxis.title,
#                    dist=self.multisubaxis.dist,
#                    firstdist=self.multisubaxis.firstdist,
#                    lastdist=self.multisubaxis.lastdist,
#                    painter=self.multisubaxis.painter)
# 
#     def getrange(self):
#         # TODO: we do not yet have a proper range handling for a bar axis
#         return None
# 
#     def setrange(self, min=None, max=None):
#         # TODO: we do not yet have a proper range handling for a bar axis
#         raise RuntimeError("range handling for a bar axis is not implemented")
# 
#     def setname(self, name, *subnames):
#         """add a name to identify an item at the bar axis
#         - by using subnames, nested name definitions are
#           possible
#         - a style (or the user itself) might use this to
#           insert new items into a bar axis
#         - setting self.relsizes to None forces later recalculation"""
#         if name not in self.names:
#             self.relsizes = None
#             self.names.append(name)
#             if self.multisubaxis is not None:
#                 self.subaxis.append(self.createsubaxis())
#         if len(subnames):
#             if self.multisubaxis is not None:
#                 if self.subaxis[self.names.index(name)].setname(*subnames):
#                     self.relsizes = None
#             else:
#                 if self.subaxis.setname(*subnames):
#                     self.relsizes = None
#         return self.relsizes is not None
# 
#     def adjustrange(self, points, index, subnames=[]):
#         for point in points:
#             if index is not None:
#                 self.setname(point[index], *subnames)
#             else:
#                 self.setname(point, *subnames)
# 
#     def updaterelsizes(self):
#         # guess what it does: it recalculates relsize attribute
#         self.relsizes = [i*self.dist + self.firstdist for i in range(len(self.names) + 1)]
#         self.relsizes[-1] += self.lastdist - self.dist
#         if self.multisubaxis is not None:
#             subrelsize = 0
#             for i in range(1, len(self.relsizes)):
#                 self.subaxis[i-1].updaterelsizes()
#                 subrelsize += self.subaxis[i-1].relsizes[-1]
#                 self.relsizes[i] += subrelsize
#         else:
#             if self.subaxis is None:
#                 subrelsize = 1
#             else:
#                 self.subaxis.updaterelsizes()
#                 subrelsize = self.subaxis.relsizes[-1]
#             for i in range(1, len(self.relsizes)):
#                 self.relsizes[i] += i * subrelsize
# 
#     def convert(self, value):
#         """bar axis convert method
#         - the value should be a list, where the first entry is
#           a member of the names (set in the constructor or by the
#           setname method); this first entry identifies an item in
#           the bar axis
#         - following values are passed to the appropriate subaxis
#           convert method
#         - when there is no subaxis, the convert method will behave
#           like having a linear axis from 0 to 1 as subaxis"""
#         # TODO: proper raising exceptions (which exceptions go thru, which are handled before?)
#         if not self.relsizes:
#             self.updaterelsizes()
#         pos = self.names.index(value[0])
#         if len(value) == 2:
#             if self.subaxis is None:
#                 subvalue = value[1]
#             else:
#                 if self.multisubaxis is not None:
#                     subvalue = value[1] * self.subaxis[pos].relsizes[-1]
#                 else:
#                     subvalue = value[1] * self.subaxis.relsizes[-1]
#         else:
#             if self.multisubaxis is not None:
#                 subvalue = self.subaxis[pos].convert(value[1:]) * self.subaxis[pos].relsizes[-1]
#             else:
#                 subvalue = self.subaxis.convert(value[1:]) * self.subaxis.relsizes[-1]
#         return (self.relsizes[pos] + subvalue) / float(self.relsizes[-1])
# 
#     def finish(self, axispos):
#         if self.axiscanvas is None:
#             if self.multisubaxis is not None:
#                 for name, subaxis in zip(self.names, self.subaxis):
#                     subaxis.vmin = self.convert((name, 0))
#                     subaxis.vmax = self.convert((name, 1))
#             self.axiscanvas = self.painter.paint(axispos, self)
# 
#     def createlinkaxis(self, **args):
#         return linkedbar(self, **args)
# 
# 
# class linkedbar(_linked):
#     """a bar axis linked to an already existing bar axis
#     - inherits the access to a linked axis -- as before,
#       basically only the painter is replaced
#     - it must take care of the creation of linked axes of
#       the subaxes"""
# 
# 
#     def __init__(self, linkedaxis, painter=painter.linkedbar()):
#         """initializes the instance
#         - it gets a axis this linkaxis is linked to
#         - it gets a painter to be used for this linked axis"""
#         _linked.__init__(self, linkedaxis, painter=painter)
#         if self.multisubaxis is not None:
#             self.subaxis = [subaxis.createlinkaxis() for subaxis in self.linkedaxis.subaxis]
#         elif self.subaxis is not None:
#             self.subaxis = self.subaxis.createlinkaxis()


class anchoredaxis:

    def __init__(self, axis):
        assert not isinstance(axis, anchoredaxis)
        self.axis = axis
        self.data = axis.createdata()
        self.canvas = None

    def convert(self, x):
        return self.axis.convert(self.data, x)

    def invert(self, y):
        return self.axis.invert(self.data, y)

    def adjustrange(self, *args, **kwargs):
        self.axis.adjustrange(self.data, *args, **kwargs)

    def setpositioner(self, positioner):
        self.positioner = positioner

    def basepath(self, x1=None, x2=None):
        if x1 is None:
            if x2 is None:
                return self.positioner.vbasepath()
            else:
                return self.positioner.vbasepath(v2=self.axis.convert(self.data, x2))
        else:
            if x2 is None:
                return self.positioner.vbasepath(v1=self.axis.convert(self.data, x1))
            else:
                return self.positioner.vbasepath(v1=self.axis.convert(self.data, x1),
                                                 v2=self.axis.convert(self.data, x2))

    def gridpath(self, x):
        return self.positioner.vgridpath(self.axis.convert(self.data, x))

    def tickpoint_pt(self, x):
        return self.positioner.vtickpoint_pt(self.axis.convert(self.data, x))

    def tickpoint(self, x):
        return self.positioner.vtickpoint(self.axis.convert(self.data, x))

    def tickdirection(self, x):
        return self.positioner.vtickdirection(self.axis.convert(self.data, x))

    def create(self, graphtexrunner=None):
        if self.canvas is None:
            self.canvas = self.axis.create(self.data, self.positioner)

    def get(self, graphtexrunner=None):
        self.create(graphtexrunner=graphtexrunner)
        return self.canvas


class _unset: pass

class linkedaxis(anchoredaxis):

    def __init__(self, axis, painter=_unset):
        assert isinstance(axis, anchoredaxis)
        if painter is _unset:
            self.painter = axis.axis.linkpainter
        else:
            self.painter = painter
        self.linkedto = axis
        self.axis = axis.axis
        self.data = axis.data
        self.canvas = None

    def create(self, graphtexrunner=None):
        if self.canvas is None:
            self.linkedto.create()
            self.canvas = painter.axiscanvas(self.painter, graphtexrunner)
            if self.painter is not None:
                self.painter.paint(self.canvas, self.data, self.axis, self.positioner)


def pathaxis(path, axis, **kwargs):
    """creates an axiscanvas for an axis along a path"""
    aanchoredaxis = anchoredaxis(axis)
    aanchoredaxis.setpositioner(positioner.pathpositioner(path, **kwargs))
    return aanchoredaxis.get()

