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
from pyx import attr, deco, style, color, unit, canvas, path
from pyx import text as textmodule

try:
    enumerate([])
except NameError:
    # fallback implementation for Python 2.2. and below
    def enumerate(list):
        return zip(xrange(len(list)), list)

class _style:
    """Interface class for graph styles

    Each graph style must support the methods described in this
    class. However, since a graph style might not need to perform
    actions on all the various events, it does not need to overwrite
    all methods of this base class (e.g. this class is not an abstract
    class in any respect).

    A style should never store private data by istance variables
    (i.e. accessing self), but it should use the sharedata and privatedata
    instances instead. A style instance can be used multiple times with
    different sharedata and privatedata instances at the very same time.
    The sharedata and privatedata instances act as data containers and
    sharedata allows for sharing information across several styles.

    Every style contains two class variables, which are not to be
    modified:
     - providesdata is a list of variable names a style offers via
       the sharedata instance. This list is used to determine whether
       all needs of subsequent styles are fullfilled. Otherwise
       getdefaultprovider should return a proper style to be used.
     - needsdata is a list of variable names the style needs to access in the 
       sharedata instance.
    """

    providesdata = [] # by default, we provide nothing
    needsdata = [] # and do not depend on anything

    def columns(self, privatedata, sharedata, graph, columns):
        """Set column information

        This method is used setup the column information to be
        accessible to the style later on. The style should analyse
        the list of strings columns, which contain the column names
        of the data. The method should return a list of column names
        which the style will make use of."""
        return []

    def selectstyle(self, privatedata, sharedata, graph, selectindex, selecttotal):
        """Select stroke/fill attributes

        This method is called to allow for the selection of
        changable attributes of a style."""
        pass

    def adjustaxis(self, privatedata, sharedata, graph, column, data, index):
        """Adjust axis range

        This method is called in order to adjust the axis range to
        the provided data. Column is the name of the column (each
        style is subsequently called for all column names). If index
        is not None, data is a list of points and index is the index
        of the column within a point. Otherwise data is already the
        axis data. Note, that data might be different for different
        columns, e.i. data might come from various places and is
        combined without copying but keeping references."""
        pass

    def initdrawpoints(self, privatedata, sharedata, graph):
        """Initialize drawing of data

        This method might be used to initialize the drawing of data."""
        pass

    def drawpoint(self, privatedata, sharedata, graph):
        """Draw data

        This method is called for each data point. The data is
        available in the dictionary sharedata.point. The dictionary
        keys are the column names."""
        pass

    def donedrawpoints(self, privatedata, sharedata, graph):
        """Finalize drawing of data

        This method is called after the last data point was
        drawn using the drawpoint method above."""
        pass

    def key_pt(self, privatedata, sharedata, graph, x_pt, y_pt, width_pt, height_pt):
        """Draw graph key"""


# The following two methods are used to register and get a default provider
# for keys. A key is a variable name in sharedata. A provider is a style
# which creates variables in sharedata.

_defaultprovider = {}

def registerdefaultprovider(style, keys):
    """sets a style as a default creator for sharedata variables 'keys'"""
    assert not len(style.needsdata), "currently we state, that a style should not depend on other sharedata variables"
    for key in keys:
        assert key in style.providesdata, "key not provided by style"
        # we might allow for overwriting the defaults, i.e. the following is not checked:
        # assert key in _defaultprovider.keys(), "default provider already registered for key"
        _defaultprovider[key] = style

def getdefaultprovider(key):
    """returns a style, which acts as a default creator for the
    sharedata variable 'key'"""
    return _defaultprovider[key]


class pos(_style):

    providesdata = ["vpos", "vposmissing", "vposavailable", "vposvalid"]

    def __init__(self, epsilon=1e-10):
        self.epsilon = epsilon

    def columns(self, privatedata, sharedata, graph, columns):
        privatedata.pointposcolumns = []
        sharedata.vposmissing = []
        for count, axisnames in enumerate(graph.axesnames):
            for axisname in axisnames:
                for column in columns:
                    if axisname == column:
                         privatedata.pointposcolumns.append(column)
            if len(privatedata.pointposcolumns) + len(sharedata.vposmissing) > count+1:
                raise ValueError("multiple axes per graph dimension")
            elif len(privatedata.pointposcolumns) + len(sharedata.vposmissing) < count+1:
                sharedata.vposmissing.append(count)
        return privatedata.pointposcolumns

    def adjustaxis(self, privatedata, sharedata, graph, column, data, index):
        if column in privatedata.pointposcolumns:
            graph.axes[column].adjustrange(data, index)

    def initdrawpoints(self, privatedata, sharedata, graph):
        sharedata.vpos = [None]*(len(privatedata.pointposcolumns) + len(sharedata.vposmissing))
        privatedata.pointpostmplist = [[column, index, graph.axes[column]] # temporarily used by drawpoint only
                                     for index, column in enumerate(privatedata.pointposcolumns)]
        for missing in sharedata.vposmissing:
            for pointpostmp in privatedata.pointpostmplist:
                if pointpostmp[1] >= missing:
                    pointpostmp[1] += 1

    def drawpoint(self, privatedata, sharedata, graph):
        sharedata.vposavailable = 1 # valid position (but might be outside of the graph)
        sharedata.vposvalid = 1 # valid position inside the graph
        for column, index, axis in privatedata.pointpostmplist:
            try:
                v = axis.convert(sharedata.point[column])
            except (ArithmeticError, ValueError, TypeError):
                sharedata.vposavailable = sharedata.vposvalid = 0
                sharedata.vpos[index] = None
            else:
                if v < -self.epsilon or v > 1+self.epsilon:
                    sharedata.vposvalid = 0
                sharedata.vpos[index] = v


registerdefaultprovider(pos(), pos.providesdata)


class range(_style):

    providesdata = ["vrange", "vrangemissing", "vrangeminmissing", "vrangemaxmissing"]

    # internal bit masks
    mask_value = 1
    mask_min = 2
    mask_max = 4
    mask_dmin = 8
    mask_dmax = 16
    mask_d = 32

    def __init__(self, usenames={}, epsilon=1e-10):
        self.usenames = usenames
        self.epsilon = epsilon

    def columns(self, privatedata, sharedata, graph, columns):
        def numberofbits(mask):
            if not mask:
                return 0
            if mask & 1:
                return numberofbits(mask >> 1) + 1
            else:
                return numberofbits(mask >> 1)
        usecolumns = []
        privatedata.rangeposcolumns = []
        sharedata.vrangemissing = []
        sharedata.vrangeminmissing = []
        sharedata.vrangemaxmissing = []
        privatedata.rangeposdeltacolumns = {} # temporarily used by adjustaxis only
        for count, axisnames in enumerate(graph.axesnames):
            for axisname in axisnames:
                try:
                    usename = self.usenames[axisname]
                except KeyError:
                    usename = axisname
                mask = 0
                for column in columns:
                    addusecolumns = 1
                    if usename == column:
                        mask += self.mask_value
                    elif usename + "min" == column:
                        mask += self.mask_min
                    elif usename + "max" == column:
                        mask += self.mask_max
                    elif "d" + usename + "min" == column:
                        mask += self.mask_dmin
                    elif "d" + usename + "max" == column:
                        mask += self.mask_dmax
                    elif "d" + usename == column:
                        mask += self.mask_d
                    else:
                        addusecolumns = 0
                    if addusecolumns:
                        usecolumns.append(column)
                if mask & (self.mask_min | self.mask_max | self.mask_dmin | self.mask_dmax | self.mask_d):
                    if (numberofbits(mask & (self.mask_min | self.mask_dmin | self.mask_d)) > 1 or
                        numberofbits(mask & (self.mask_max | self.mask_dmax | self.mask_d)) > 1):
                        raise ValueError("multiple range definition")
                    if mask & (self.mask_dmin | self.mask_dmax | self.mask_d):
                        if not (mask & self.mask_value):
                            raise ValueError("missing value for delta")
                        privatedata.rangeposdeltacolumns[axisname] = {}
                    privatedata.rangeposcolumns.append((axisname, usename, mask))
                elif mask == self.mask_value:
                    usecolumns = usecolumns[:-1]
            if len(privatedata.rangeposcolumns) + len(sharedata.vrangemissing) > count+1:
                raise ValueError("multiple axes per graph dimension")
            elif len(privatedata.rangeposcolumns) + len(sharedata.vrangemissing) < count+1:
                sharedata.vrangemissing.append(count)
            else:
                if not (privatedata.rangeposcolumns[-1][2] & (self.mask_min | self.mask_dmin | self.mask_d)):
                    sharedata.vrangeminmissing.append(count)
                if not (privatedata.rangeposcolumns[-1][2] & (self.mask_max | self.mask_dmax | self.mask_d)):
                    sharedata.vrangemaxmissing.append(count)
        return usecolumns

    def adjustaxis(self, privatedata, sharedata, graph, column, data, index):
        if column in [c + "min" for a, c, m in privatedata.rangeposcolumns if m & self.mask_min]:
            graph.axes[column[:-3]].adjustrange(data, index)
        if column in [c + "max" for a, c, m in privatedata.rangeposcolumns if m & self.mask_max]:
            graph.axes[column[:-3]].adjustrange(data, index)

        # delta handling: fill rangeposdeltacolumns
        for axisname, usename, mask in privatedata.rangeposcolumns:
            if column == usename and mask & (self.mask_dmin | self.mask_dmax | self.mask_d):
                privatedata.rangeposdeltacolumns[axisname][self.mask_value] = data, index
            if column == "d" + usename + "min" and mask & self.mask_dmin:
                privatedata.rangeposdeltacolumns[axisname][self.mask_dmin] = data, index
            if column == "d" + usename + "max" and mask & self.mask_dmax:
                privatedata.rangeposdeltacolumns[axisname][self.mask_dmax] = data, index
            if column == "d" + usename and mask & self.mask_d:
                privatedata.rangeposdeltacolumns[axisname][self.mask_d] = data, index

        # delta handling: process rangeposdeltacolumns
        for a, d in privatedata.rangeposdeltacolumns.items():
            if d.has_key(self.mask_value):
                for k in d.keys():
                    if k != self.mask_value:
                        if k & (self.mask_dmin | self.mask_d):
                            graph.axes[a].adjustrange(d[self.mask_value][0], d[self.mask_value][1],
                                                      deltamindata=d[k][0], deltaminindex=d[k][1])
                        if k & (self.mask_dmax | self.mask_d):
                            graph.axes[a].adjustrange(d[self.mask_value][0], d[self.mask_value][1],
                                                      deltamaxdata=d[k][0], deltamaxindex=d[k][1])
                        del d[k]

    def initdrawpoints(self, privatedata, sharedata, graph):
        sharedata.vrange = [[None for x in xrange(2)] for y in privatedata.rangeposcolumns + sharedata.vrangemissing]
        privatedata.rangepostmplist = [[usename, mask, index, graph.axes[axisname]] # temporarily used by drawpoint only
                                     for index, (axisname, usename, mask) in enumerate(privatedata.rangeposcolumns)]
        for missing in sharedata.vrangemissing:
            for rangepostmp in privatedata.rangepostmplist:
                if rangepostmp[2] >= missing:
                    rangepostmp[2] += 1

    def drawpoint(self, privatedata, sharedata, graph):
        for usename, mask, index, axis in privatedata.rangepostmplist:
            try:
                if mask & self.mask_min:
                    sharedata.vrange[index][0] = axis.convert(sharedata.point[usename + "min"])
                if mask & self.mask_dmin:
                    sharedata.vrange[index][0] = axis.convert(sharedata.point[usename] - sharedata.point["d" + usename + "min"])
                if mask & self.mask_d:
                    sharedata.vrange[index][0] = axis.convert(sharedata.point[usename] - sharedata.point["d" + usename])
            except (ArithmeticError, ValueError, TypeError):
                sharedata.vrange[index][0] = None
            try:
                if mask & self.mask_max:
                    sharedata.vrange[index][1] = axis.convert(sharedata.point[usename + "max"])
                if mask & self.mask_dmax:
                    sharedata.vrange[index][1] = axis.convert(sharedata.point[usename] + sharedata.point["d" + usename + "max"])
                if mask & self.mask_d:
                    sharedata.vrange[index][1] = axis.convert(sharedata.point[usename] + sharedata.point["d" + usename])
            except (ArithmeticError, ValueError, TypeError):
                sharedata.vrange[index][1] = None

            # some range checks for data consistency
            if (sharedata.vrange[index][0] is not None and sharedata.vrange[index][1] is not None and
                sharedata.vrange[index][0] > sharedata.vrange[index][1] + self.epsilon):
                raise ValueError("inverse range")
            # disabled due to missing vpos access:
            # if (sharedata.vrange[index][0] is not None and sharedata.vpos[index] is not None and
            #     sharedata.vrange[index][0] > sharedata.vpos[index] + self.epsilon):
            #     raise ValueError("negative minimum errorbar")
            # if (sharedata.vrange[index][1] is not None and sharedata.vpos[index] is not None and
            #     sharedata.vrange[index][1] < sharedata.vpos[index] - self.epsilon):
            #     raise ValueError("negative maximum errorbar")


registerdefaultprovider(range(), range.providesdata)


def _crosssymbol(c, x_pt, y_pt, size_pt, attrs):
    c.draw(path.path(path.moveto_pt(x_pt-0.5*size_pt, y_pt-0.5*size_pt),
                     path.lineto_pt(x_pt+0.5*size_pt, y_pt+0.5*size_pt),
                     path.moveto_pt(x_pt-0.5*size_pt, y_pt+0.5*size_pt),
                     path.lineto_pt(x_pt+0.5*size_pt, y_pt-0.5*size_pt)), attrs)

def _plussymbol(c, x_pt, y_pt, size_pt, attrs):
    c.draw(path.path(path.moveto_pt(x_pt-0.707106781*size_pt, y_pt),
                     path.lineto_pt(x_pt+0.707106781*size_pt, y_pt),
                     path.moveto_pt(x_pt, y_pt-0.707106781*size_pt),
                     path.lineto_pt(x_pt, y_pt+0.707106781*size_pt)), attrs)

def _squaresymbol(c, x_pt, y_pt, size_pt, attrs):
    c.draw(path.path(path.moveto_pt(x_pt-0.5*size_pt, y_pt-0.5*size_pt),
                     path.lineto_pt(x_pt+0.5*size_pt, y_pt-0.5*size_pt),
                     path.lineto_pt(x_pt+0.5*size_pt, y_pt+0.5*size_pt),
                     path.lineto_pt(x_pt-0.5*size_pt, y_pt+0.5*size_pt),
                     path.closepath()), attrs)

def _trianglesymbol(c, x_pt, y_pt, size_pt, attrs):
    c.draw(path.path(path.moveto_pt(x_pt-0.759835685*size_pt, y_pt-0.438691337*size_pt),
                     path.lineto_pt(x_pt+0.759835685*size_pt, y_pt-0.438691337*size_pt),
                     path.lineto_pt(x_pt, y_pt+0.877382675*size_pt),
                     path.closepath()), attrs)

def _circlesymbol(c, x_pt, y_pt, size_pt, attrs):
    c.draw(path.path(path.arc_pt(x_pt, y_pt, 0.564189583*size_pt, 0, 360),
                     path.closepath()), attrs)

def _diamondsymbol(c, x_pt, y_pt, size_pt, attrs):
    c.draw(path.path(path.moveto_pt(x_pt-0.537284965*size_pt, y_pt),
                     path.lineto_pt(x_pt, y_pt-0.930604859*size_pt),
                     path.lineto_pt(x_pt+0.537284965*size_pt, y_pt),
                     path.lineto_pt(x_pt, y_pt+0.930604859*size_pt),
                     path.closepath()), attrs)


class _styleneedingpointpos(_style):

    needsdata = ["vposmissing"]

    def columns(self, privatedata, sharedata, graph, columns):
        if len(sharedata.vposmissing):
            raise ValueError("position columns incomplete")
        return []


class symbol(_styleneedingpointpos):

    needsdata = ["vpos", "vposmissing", "vposvalid"]

    # insert symbols
    # note, that statements like cross = _crosssymbol are
    # invalid, since the would lead to unbound methods, but
    # a single entry changeable list does the trick
    cross = attr.changelist([_crosssymbol])
    plus = attr.changelist([_plussymbol])
    square = attr.changelist([_squaresymbol])
    triangle = attr.changelist([_trianglesymbol])
    circle = attr.changelist([_circlesymbol])
    diamond = attr.changelist([_diamondsymbol])

    changecross = attr.changelist([_crosssymbol, _plussymbol, _squaresymbol, _trianglesymbol, _circlesymbol, _diamondsymbol])
    changeplus = attr.changelist([_plussymbol, _squaresymbol, _trianglesymbol, _circlesymbol, _diamondsymbol, cross])
    changesquare = attr.changelist([_squaresymbol, _trianglesymbol, _circlesymbol, _diamondsymbol, cross, _plussymbol])
    changetriangle = attr.changelist([_trianglesymbol, _circlesymbol, _diamondsymbol, cross, _plussymbol, _squaresymbol])
    changecircle = attr.changelist([_circlesymbol, _diamondsymbol, cross, _plussymbol, _squaresymbol, _trianglesymbol])
    changediamond = attr.changelist([_diamondsymbol, cross, _plussymbol, _squaresymbol, _trianglesymbol, _circlesymbol])
    changesquaretwice = attr.changelist([_squaresymbol, _squaresymbol, _trianglesymbol, _trianglesymbol, _circlesymbol, _circlesymbol, _diamondsymbol, _diamondsymbol])
    changetriangletwice = attr.changelist([_trianglesymbol, _trianglesymbol, _circlesymbol, _circlesymbol, _diamondsymbol, _diamondsymbol, _squaresymbol, _squaresymbol])
    changecircletwice = attr.changelist([_circlesymbol, _circlesymbol, _diamondsymbol, _diamondsymbol, _squaresymbol, _squaresymbol, _trianglesymbol, _trianglesymbol])
    changediamondtwice = attr.changelist([_diamondsymbol, _diamondsymbol, _squaresymbol, _squaresymbol, _trianglesymbol, _trianglesymbol, _circlesymbol, _circlesymbol])

    changestrokedfilled = attr.changelist([deco.stroked, deco.filled])
    changefilledstroked = attr.changelist([deco.filled, deco.stroked])

    defaultsymbolattrs = [deco.stroked]

    def __init__(self, symbol=changecross, size=0.2*unit.v_cm, symbolattrs=[]):
        self.symbol = symbol
        self.size = size
        self.symbolattrs = symbolattrs

    def selectstyle(self, privatedata, sharedata, graph, selectindex, selecttotal):
        privatedata.symbol = attr.selectattr(self.symbol, selectindex, selecttotal)
        privatedata.size_pt = unit.topt(attr.selectattr(self.size, selectindex, selecttotal))
        if self.symbolattrs is not None:
            privatedata.symbolattrs = attr.selectattrs(self.defaultsymbolattrs + self.symbolattrs, selectindex, selecttotal)
        else:
            privatedata.symbolattrs = None

    def initdrawpoints(self, privatedata, sharedata, graph):
        privatedata.symbolcanvas = canvas.canvas()

    def drawpoint(self, privatedata, sharedata, graph):
        if sharedata.vposvalid and privatedata.symbolattrs is not None:
            xpos, ypos = graph.vpos_pt(*sharedata.vpos)
            privatedata.symbol(privatedata.symbolcanvas, xpos, ypos, privatedata.size_pt, privatedata.symbolattrs)

    def donedrawpoints(self, privatedata, sharedata, graph):
        graph.insert(privatedata.symbolcanvas)

    def key_pt(self, privatedata, sharedata, graph, x_pt, y_pt, width_pt, height_pt):
        if privatedata.symbolattrs is not None:
            privatedata.symbol(graph, x_pt+0.5*width_pt, y_pt+0.5*height_pt, privatedata.size_pt, privatedata.symbolattrs)


class line(_styleneedingpointpos):

    needsdata = ["vpos", "vposmissing", "vposavailable", "vposvalid"]

    changelinestyle = attr.changelist([style.linestyle.solid,
                                       style.linestyle.dashed,
                                       style.linestyle.dotted,
                                       style.linestyle.dashdotted])

    defaultlineattrs = [changelinestyle]

    def __init__(self, lineattrs=[]):
        self.lineattrs = lineattrs

    def selectstyle(self, privatedata, sharedata, graph, selectindex, selecttotal):
        privatedata.lineattrs = attr.selectattrs(self.defaultlineattrs + self.lineattrs, selectindex, selecttotal)

    def initdrawpoints(self, privatedata, sharedata, graph):
        if privatedata.lineattrs is not None:
            privatedata.linecanvas = canvas.canvas()
            privatedata.linecanvas.set(privatedata.lineattrs)
        privatedata.path = path.path()
        privatedata.linebasepoints = []
        privatedata.lastvpos = None

    def addpointstopath(self, privatedata, sharedata):
        # add baselinepoints to privatedata.path
        if len(privatedata.linebasepoints) > 1:
            privatedata.path.append(path.moveto_pt(*privatedata.linebasepoints[0]))
            if len(privatedata.linebasepoints) > 2:
                privatedata.path.append(path.multilineto_pt(privatedata.linebasepoints[1:]))
            else:
                privatedata.path.append(path.lineto_pt(*privatedata.linebasepoints[1]))
        privatedata.linebasepoints = []

    def drawpoint(self, privatedata, sharedata, graph):
        # append linebasepoints
        if sharedata.vposavailable:
            if len(privatedata.linebasepoints):
                # the last point was inside the graph
                if sharedata.vposvalid: # shortcut for the common case
                    privatedata.linebasepoints.append(graph.vpos_pt(*sharedata.vpos))
                else:
                    # cut end
                    cut = 1
                    for vstart, vend in zip(privatedata.lastvpos, sharedata.vpos):
                        newcut = None
                        if vend > 1:
                            # 1 = vstart + (vend - vstart) * cut
                            try:
                                newcut = (1 - vstart)/(vend - vstart)
                            except ArithmeticError:
                                break
                        if vend < 0:
                            # 0 = vstart + (vend - vstart) * cut
                            try:
                                newcut = - vstart/(vend - vstart)
                            except ArithmeticError:
                                break
                        if newcut is not None and newcut < cut:
                            cut = newcut
                    else:
                        cutvpos = []
                        for vstart, vend in zip(privatedata.lastvpos, sharedata.vpos):
                            cutvpos.append(vstart + (vend - vstart) * cut)
                        privatedata.linebasepoints.append(graph.vpos_pt(*cutvpos))
                    self.addpointstopath(privatedata, sharedata)
            else:
                # the last point was outside the graph
                if privatedata.lastvpos is not None:
                    if sharedata.vposvalid:
                        # cut beginning
                        cut = 0
                        for vstart, vend in zip(privatedata.lastvpos, sharedata.vpos):
                            newcut = None
                            if vstart > 1:
                                # 1 = vstart + (vend - vstart) * cut
                                try:
                                    newcut = (1 - vstart)/(vend - vstart)
                                except ArithmeticError:
                                    break
                            if vstart < 0:
                                # 0 = vstart + (vend - vstart) * cut
                                try:
                                    newcut = - vstart/(vend - vstart)
                                except ArithmeticError:
                                    break
                            if newcut is not None and newcut > cut:
                                cut = newcut
                        else:
                            cutvpos = []
                            for vstart, vend in zip(privatedata.lastvpos, sharedata.vpos):
                                cutvpos.append(vstart + (vend - vstart) * cut)
                            privatedata.linebasepoints.append(graph.vpos_pt(*cutvpos))
                            privatedata.linebasepoints.append(graph.vpos_pt(*sharedata.vpos))
                    else:
                        # sometimes cut beginning and end
                        cutfrom = 0
                        cutto = 1
                        for vstart, vend in zip(privatedata.lastvpos, sharedata.vpos):
                            newcutfrom = None
                            if vstart > 1:
                                if vend > 1:
                                    break
                                # 1 = vstart + (vend - vstart) * cutfrom
                                try:
                                    newcutfrom = (1 - vstart)/(vend - vstart)
                                except ArithmeticError:
                                    break
                            if vstart < 0:
                                if vend < 0:
                                    break
                                # 0 = vstart + (vend - vstart) * cutfrom
                                try:
                                    newcutfrom = - vstart/(vend - vstart)
                                except ArithmeticError:
                                    break
                            if newcutfrom is not None and newcutfrom > cutfrom:
                                cutfrom = newcutfrom
                            newcutto = None
                            if vend > 1:
                                # 1 = vstart + (vend - vstart) * cutto
                                try:
                                    newcutto = (1 - vstart)/(vend - vstart)
                                except ArithmeticError:
                                    break
                            if vend < 0:
                                # 0 = vstart + (vend - vstart) * cutto
                                try:
                                    newcutto = - vstart/(vend - vstart)
                                except ArithmeticError:
                                    break
                            if newcutto is not None and newcutto < cutto:
                                cutto = newcutto
                        else:
                            if cutfrom < cutto:
                                cutfromvpos = []
                                cuttovpos = []
                                for vstart, vend in zip(privatedata.lastvpos, sharedata.vpos):
                                    cutfromvpos.append(vstart + (vend - vstart) * cutfrom)
                                    cuttovpos.append(vstart + (vend - vstart) * cutto)
                                privatedata.linebasepoints.append(graph.vpos_pt(*cutfromvpos))
                                privatedata.linebasepoints.append(graph.vpos_pt(*cuttovpos))
                                self.addpointstopath(privatedata, sharedata)
            privatedata.lastvpos = sharedata.vpos[:]
        else:
            if len(privatedata.linebasepoints) > 1:
                self.addpointstopath(privatedata, sharedata)
            privatedata.lastvpos = None

    def donedrawpoints(self, privatedata, sharedata, graph):
        if len(privatedata.linebasepoints) > 1:
            self.addpointstopath(privatedata, sharedata)
        if privatedata.lineattrs is not None and len(privatedata.path.path):
            graph.insert(privatedata.linecanvas)
            privatedata.linecanvas.stroke(privatedata.path)

    def key_pt(self, privatedata, sharedata, graph, x_pt, y_pt, width_pt, height_pt):
        if privatedata.lineattrs is not None:
            graph.stroke(path.line_pt(x_pt, y_pt+0.5*height_pt, x_pt+width_pt, y_pt+0.5*height_pt), privatedata.lineattrs)


class errorbar(_style):

    needsdata = ["vpos", "vposmissing", "vposavailable", "vposvalid", "vrange", "vrangemissing"]

    defaulterrorbarattrs = []

    def __init__(self, size=0.1*unit.v_cm,
                       errorbarattrs=[],
                       epsilon=1e-10):
        self.size = size
        self.errorbarattrs = errorbarattrs
        self.epsilon = epsilon

    def columns(self, privatedata, sharedata, graph, columns):
        for i in sharedata.vposmissing:
            if i in sharedata.vrangemissing:
                raise ValueError("position and range for a graph dimension missing")
        return []

    def selectstyle(self, privatedata, sharedata, graph, selectindex, selecttotal):
        privatedata.errorsize_pt = unit.topt(attr.selectattr(self.size, selectindex, selecttotal))
        privatedata.errorbarattrs = attr.selectattrs(self.defaulterrorbarattrs + self.errorbarattrs, selectindex, selecttotal)

    def initdrawpoints(self, privatedata, sharedata, graph):
        if privatedata.errorbarattrs is not None:
            privatedata.errorbarcanvas = canvas.canvas()
            privatedata.errorbarcanvas.set(privatedata.errorbarattrs)
            privatedata.dimensionlist = list(xrange(len(sharedata.vpos)))

    def drawpoint(self, privatedata, sharedata, graph):
        if privatedata.errorbarattrs is not None:
            for i in privatedata.dimensionlist:
                for j in privatedata.dimensionlist:
                    if (i != j and
                        (sharedata.vpos[j] is None or
                         sharedata.vpos[j] < -self.epsilon or
                         sharedata.vpos[j] > 1+self.epsilon)):
                        break
                else:
                    if ((sharedata.vrange[i][0] is None and sharedata.vpos[i] is None) or
                        (sharedata.vrange[i][1] is None and sharedata.vpos[i] is None) or
                        (sharedata.vrange[i][0] is None and sharedata.vrange[i][1] is None)):
                        continue
                    vminpos = sharedata.vpos[:]
                    if sharedata.vrange[i][0] is not None:
                        vminpos[i] = sharedata.vrange[i][0]
                        mincap = 1
                    else:
                        mincap = 0
                    if vminpos[i] > 1+self.epsilon:
                        continue
                    if vminpos[i] < -self.epsilon:
                        vminpos[i] = 0
                        mincap = 0
                    vmaxpos = sharedata.vpos[:]
                    if sharedata.vrange[i][1] is not None:
                        vmaxpos[i] = sharedata.vrange[i][1]
                        maxcap = 1
                    else:
                        maxcap = 0
                    if vmaxpos[i] < -self.epsilon:
                        continue
                    if vmaxpos[i] > 1+self.epsilon:
                        vmaxpos[i] = 1
                        maxcap = 0
                    privatedata.errorbarcanvas.stroke(graph.vgeodesic(*(vminpos + vmaxpos)))
                    for j in privatedata.dimensionlist:
                        if i != j:
                            if mincap:
                                privatedata.errorbarcanvas.stroke(graph.vcap_pt(j, privatedata.errorsize_pt, *vminpos))
                            if maxcap:
                                privatedata.errorbarcanvas.stroke(graph.vcap_pt(j, privatedata.errorsize_pt, *vmaxpos))

    def donedrawpoints(self, privatedata, sharedata, graph):
        if privatedata.errorbarattrs is not None:
            graph.insert(privatedata.errorbarcanvas)


class text(_styleneedingpointpos):

    needsdata = ["vpos", "vposmissing", "vposvalid"]

    defaulttextattrs = [textmodule.halign.center, textmodule.vshift.mathaxis]

    def __init__(self, textname="text", textdx=0*unit.v_cm, textdy=0.3*unit.v_cm, textattrs=[]):
        self.textname = textname
        self.textdx = textdx
        self.textdy = textdy
        self.textattrs = textattrs

    def columns(self, privatedata, sharedata, graph, columns):
        if self.textname not in columns:
            raise ValueError("column '%s' missing" % self.textname)
        return [self.textname] + _styleneedingpointpos.columns(self, privatedata, sharedata, graph, columns)

    def selectstyle(self, privatedata, sharedata, graph, selectindex, selecttotal):
        if self.textattrs is not None:
            privatedata.textattrs = attr.selectattrs(self.defaulttextattrs + self.textattrs, selectindex, selecttotal)
        else:
            privatedata.textattrs = None

    def initdrawpoints(self, privatedata, sharedata, grap):
        privatedata.textdx_pt = unit.topt(self.textdx)
        privatedata.textdy_pt = unit.topt(self.textdy)

    def drawpoint(self, privatedata, sharedata, graph):
        if privatedata.textattrs is not None and sharedata.vposvalid:
            x_pt, y_pt = graph.vpos_pt(*sharedata.vpos)
            try:
                text = str(sharedata.point[self.textname])
            except:
                pass
            else:
                graph.text_pt(x_pt + privatedata.textdx_pt, y_pt + privatedata.textdy_pt, text, privatedata.textattrs)

    def key_pt(self, privatedata, sharedata, graph, x_pt, y_pt, width_pt, height_pt):
        raise RuntimeError("Style currently doesn't provide a graph key")


class arrow(_styleneedingpointpos):

    needsdata = ["vpos", "vposmissing", "vposvalid"]

    defaultlineattrs = []
    defaultarrowattrs = []

    def __init__(self, linelength=0.25*unit.v_cm, arrowsize=0.15*unit.v_cm, lineattrs=[], arrowattrs=[], epsilon=1e-5):
        self.linelength = linelength
        self.arrowsize = arrowsize
        self.lineattrs = lineattrs
        self.arrowattrs = arrowattrs
        self.epsilon = epsilon

    def columns(self, privatedata, sharedata, graph, columns):
        if len(graph.axesnames) != 2:
            raise ValueError("arrow style restricted on two-dimensional graphs")
        if "size" not in columns:
            raise ValueError("size missing")
        if "angle" not in columns:
            raise ValueError("angle missing")
        return ["size", "angle"] + _styleneedingpointpos.columns(self, privatedata, sharedata, graph, columns)

    def selectstyle(self, privatedata, sharedata, graph, selectindex, selecttotal):
        if self.lineattrs is not None:
            privatedata.lineattrs = attr.selectattrs(self.defaultlineattrs + self.lineattrs, selectindex, selecttotal)
        else:
            privatedata.lineattrs = None
        if self.arrowattrs is not None:
            privatedata.arrowattrs = attr.selectattrs(self.defaultarrowattrs + self.arrowattrs, selectindex, selecttotal)
        else:
            privatedata.arrowattrs = None

    def initdrawpoints(self, privatedata, sharedata, graph):
        privatedata.arrowcanvas = canvas.canvas()

    def drawpoint(self, privatedata, sharedata, graph):
        if privatedata.lineattrs is not None and privatedata.arrowattrs is not None and sharedata.vposvalid:
            linelength_pt = unit.topt(self.linelength)
            x_pt, y_pt = graph.vpos_pt(*sharedata.vpos)
            try:
                angle = sharedata.point["angle"] + 0.0
                size = sharedata.point["size"] + 0.0
            except:
                pass
            else:
                if sharedata.point["size"] > self.epsilon:
                    dx = math.cos(angle*math.pi/180)
                    dy = math.sin(angle*math.pi/180)
                    x1 = x_pt-0.5*dx*linelength_pt*size
                    y1 = y_pt-0.5*dy*linelength_pt*size
                    x2 = x_pt+0.5*dx*linelength_pt*size
                    y2 = y_pt+0.5*dy*linelength_pt*size
                    privatedata.arrowcanvas.stroke(path.line_pt(x1, y1, x2, y2), privatedata.lineattrs +
                                                 [deco.earrow(privatedata.arrowattrs, size=self.arrowsize*size)])

    def donedrawpoints(self, privatedata, sharedata, graph):
        graph.insert(privatedata.arrowcanvas)

    def key_pt(self, privatedata, sharedata, graph, x_pt, y_pt, width_pt, height_pt):
        raise RuntimeError("Style currently doesn't provide a graph key")


class rect(_style):

    needsdata = ["vrange", "vrangeminmissing", "vrangemaxmissing"]

    def __init__(self, palette=color.palette.Grey):
        self.palette = palette

    def columns(self, privatedata, sharedata, graph, columns):
        if len(graph.axesnames) != 2:
            raise TypeError("arrow style restricted on two-dimensional graphs")
        if "color" not in columns:
            raise ValueError("color missing")
        if len(sharedata.vrangeminmissing) + len(sharedata.vrangemaxmissing):
            raise ValueError("range columns incomplete")
        return ["color"]

    def initdrawpoints(self, privatedata, sharedata, graph):
        privatedata.rectcanvas = graph.insert(canvas.canvas())
        privatedata.lastcolorvalue = None

    def drawpoint(self, privatedata, sharedata, graph):
        xvmin = sharedata.vrange[0][0]
        xvmax = sharedata.vrange[0][1]
        yvmin = sharedata.vrange[1][0]
        yvmax = sharedata.vrange[1][1]
        if (xvmin is not None and xvmin < 1 and
            xvmax is not None and xvmax > 0 and
            yvmin is not None and yvmin < 1 and
            yvmax is not None and yvmax > 0):
            if xvmin < 0:
                xvmin = 0
            elif xvmax > 1:
                xvmax = 1
            if yvmin < 0:
                yvmin = 0
            elif yvmax > 1:
                yvmax = 1
            p = graph.vgeodesic(xvmin, yvmin, xvmax, yvmin)
            p.append(graph.vgeodesic_el(xvmax, yvmin, xvmax, yvmax))
            p.append(graph.vgeodesic_el(xvmax, yvmax, xvmin, yvmax))
            p.append(graph.vgeodesic_el(xvmin, yvmax, xvmin, yvmin))
            p.append(path.closepath())
            colorvalue = sharedata.point["color"]
            try:
                if colorvalue != privatedata.lastcolorvalue:
                    privatedata.rectcanvas.set([self.palette.getcolor(colorvalue)])
            except:
                pass
            else:
                privatedata.rectcanvas.fill(p)

    def key_pt(self, privatedata, sharedata, graph, x_pt, y_pt, width_pt, height_pt):
        raise RuntimeError("Style currently doesn't provide a graph key")


class barpos(_style):

    providesdata = ["vpos", "vposmissing", "vposavailable", "vposvalid", "vbarrange", "barcolumns", "barvalueindex", "stackedbar"]

    defaultfrompathattrs = []

    def __init__(self, fromvalue=None, frompathattrs=[], subindex=0, subnames=None, epsilon=1e-10):
        # NOTE subindex is a perspective for higher dimensional plots
        #      (just ignore it for the moment -- we don't even need to document about it)
        self.fromvalue = fromvalue
        self.frompathattrs = frompathattrs
        self.subindex = subindex
        self.subnames = subnames
        self.epsilon = epsilon

    def columns(self, privatedata, sharedata, graph, columns):
        sharedata.barcolumns = []
        sharedata.barvalueindex = None
        for dimension, axisnames in enumerate(graph.axesnames):
            found = 0
            for axisname in axisnames:
                if axisname in columns:
                    if sharedata.barvalueindex is not None:
                        raise ValueError("multiple values")
                    sharedata.barvalueindex = dimension
                    sharedata.barcolumns.append(axisname)
                    found += 1
                if (axisname + "name") in columns:
                    sharedata.barcolumns.append(axisname + "name")
                    found += 1
                if found > 1:
                    raise ValueError("multiple names")
            if not found:
                raise ValueError("value/name missing")
        if sharedata.barvalueindex is None:
            raise ValueError("missing value")
        if self.subindex >= sharedata.barvalueindex:
            privatedata.barpossubindex = self.subindex + 1
        else:
            privatedata.barpossubindex = self.subindex
        sharedata.vposmissing = []
        return sharedata.barcolumns

    def selectstyle(self, privatedata, sharedata, graph, selectindex, selecttotal):
        if selecttotal == 1:
            if self.subnames is not None:
                raise ValueError("subnames set for single-bar data")
            privatedata.barpossubname = []
        else:
            if self.subnames is not None:
                privatedata.barpossubname = [self.subnames[selectindex]]
            else:
                privatedata.barpossubname = [selectindex]

    def adjustaxis(self, privatedata, sharedata, graph, column, data, index):
        try:
            i = sharedata.barcolumns.index(column)
        except ValueError:
            pass
        else:
            if i == sharedata.barvalueindex:
                if self.fromvalue is not None:
                    graph.axes[sharedata.barcolumns[i]].adjustrange([self.fromvalue], None)
                graph.axes[sharedata.barcolumns[i]].adjustrange(data, index)
            else:
                if i == privatedata.barpossubindex:
                    graph.axes[sharedata.barcolumns[i][:-4]].adjustrange(data, index, privatedata.barpossubname)
                else:
                    graph.axes[sharedata.barcolumns[i][:-4]].adjustrange(data, index)

    def initdrawpoints(self, privatedata, sharedata, graph):
        sharedata.vpos = [None]*(len(sharedata.barcolumns))
        sharedata.vbarrange = [[None for i in xrange(2)] for x in sharedata.barcolumns]
        sharedata.stackedbar = sharedata.stackedbardraw = 0

        if self.fromvalue is not None:
            privatedata.vfromvalue = graph.axes[sharedata.barcolumns[sharedata.barvalueindex][0]].convert(self.fromvalue)
            if privatedata.vfromvalue < 0:
                privatedata.vfromvalue = 0
            if privatedata.vfromvalue > 1:
                privatedata.vfromvalue = 1
            if self.frompathattrs is not None:
                # TODO 2d only
                graph.stroke(graph.axespos[sharedata.barcolumns[sharedata.barvalueindex][0]].vgridpath(privatedata.vfromvalue),
                             self.defaultfrompathattrs + self.frompathattrs)
        else:
            privatedata.vfromvalue = 0

    def drawpoint(self, privatedata, sharedata, graph):
        sharedata.vposavailable = sharedata.vposvalid = 1
        for i, barname in enumerate(sharedata.barcolumns):
            if i == sharedata.barvalueindex:
                sharedata.vbarrange[i][0] = privatedata.vfromvalue
                try:
                    sharedata.vpos[i] = sharedata.vbarrange[i][1] = graph.axes[barname].convert(sharedata.point[barname])
                except (ArithmeticError, ValueError, TypeError):
                    sharedata.vpos[i] = sharedata.vbarrange[i][1] = None
            else:
                for j in xrange(2):
                    try:
                        if i == privatedata.barpossubindex:
                            sharedata.vbarrange[i][j] = graph.axes[barname[:-4]].convert(([sharedata.point[barname]] + privatedata.barpossubname + [j]))
                        else:
                            sharedata.vbarrange[i][j] = graph.axes[barname[:-4]].convert((sharedata.point[barname], j))
                    except (ArithmeticError, ValueError, TypeError):
                        sharedata.vbarrange[i][j] = None
                try:
                    sharedata.vpos[i] = 0.5*(sharedata.vbarrange[i][0]+sharedata.vbarrange[i][1])
                except (ArithmeticError, ValueError, TypeError):
                    sharedata.vpos[i] = None
            if sharedata.vpos[i] is None:
                sharedata.vposavailable = sharedata.vposvalid = 0
            elif sharedata.vpos[i] < -self.epsilon or sharedata.vpos[i] > 1+self.epsilon:
                sharedata.vposvalid = 0

registerdefaultprovider(barpos(), ["vbarrange", "barcolumns", "barvalueindex"])


class stackedbarpos(_style):

    # provides no additional data, but needs some data (and modifies some of them)
    needsdata = ["vbarrange", "barcolumns", "barvalueindex"]

    def __init__(self, stackname, epsilon=1e-10):
        self.stackname = stackname
        self.epsilon = epsilon

    def columns(self, privatedata, sharedata, graph, columns):
        if self.stackname not in columns:
            raise ValueError("stackname column missing")
        return [self.stackname]

    def adjustaxis(self, privatedata, sharedata, graph, column, data, index):
        if column == self.stackname:
            graph.axes[sharedata.barcolumns[sharedata.barvalueindex]].adjustrange(data, index)

    def initdrawpoints(self, privatedata, sharedata, graph):
        if sharedata.stackedbardraw: # do not count the start bar when not gets painted
            sharedata.stackedbar += 1

    def drawpoint(self, privatedata, sharedata, graph):
        sharedata.vbarrange[sharedata.barvalueindex][0] = sharedata.vbarrange[sharedata.barvalueindex][1]
        try:
            sharedata.vpos[sharedata.barvalueindex] = sharedata.vbarrange[sharedata.barvalueindex][1] = graph.axes[sharedata.barcolumns[sharedata.barvalueindex]].convert(sharedata.point[self.stackname])
        except (ArithmeticError, ValueError, TypeError):
            sharedata.vpos[sharedata.barvalueindex] = sharedata.vbarrange[sharedata.barvalueindex][1] = None
            sharedata.vposavailable = sharedata.vposvalid = 0
        else:
            if not sharedata.vposavailable or not sharedata.vposvalid:
                sharedata.vposavailable = sharedata.vposvalid = 1
                for v in sharedata.vpos:
                    if v is None:
                        sharedata.vposavailable = sharedata.vposvalid = 0
                        break
                    if v < -self.epsilon or v > 1+self.epsilon:
                        sharedata.vposvalid = 0


class bar(_style):

    needsdata = ["vbarrange"]

    defaultbarattrs = [color.palette.Rainbow, deco.stroked([color.grey.black])]

    def __init__(self, barattrs=[]):
        self.barattrs = barattrs

    def columns(self, privatedata, sharedata, graph, columns):
        if len(graph.axesnames) != 2:
            raise TypeError("bar style restricted on two-dimensional graphs")
        return []

    def selectstyle(self, privatedata, sharedata, graph, selectindex, selecttotal):
        if selecttotal > 1:
            privatedata.barattrs = attr.selectattrs(self.defaultbarattrs + self.barattrs, selectindex, selecttotal)
        else:
            privatedata.barattrs = self.defaultbarattrs + self.barattrs

    def initdrawpoints(self, privatedata, sharedata, graph):
        privatedata.rectcanvas = graph.insert(canvas.canvas())
        sharedata.stackedbardraw = 1
        privatedata.stackedbar = sharedata.stackedbar

    def drawpoint(self, privatedata, sharedata, graph):
        xvmin = sharedata.vbarrange[0][0]
        xvmax = sharedata.vbarrange[0][1]
        yvmin = sharedata.vbarrange[1][0]
        yvmax = sharedata.vbarrange[1][1]
        if (xvmin is not None and xvmin < 1 and
            xvmax is not None and xvmax > 0 and
            yvmin is not None and yvmin < 1 and
            yvmax is not None and yvmax > 0):
            if xvmin < 0:
                xvmin = 0
            elif xvmax > 1:
                xvmax = 1
            if yvmin < 0:
                yvmin = 0
            elif yvmax > 1:
                yvmax = 1
            p = graph.vgeodesic(xvmin, yvmin, xvmax, yvmin)
            p.append(graph.vgeodesic_el(xvmax, yvmin, xvmax, yvmax))
            p.append(graph.vgeodesic_el(xvmax, yvmax, xvmin, yvmax))
            p.append(graph.vgeodesic_el(xvmin, yvmax, xvmin, yvmin))
            p.append(path.closepath())
            privatedata.rectcanvas.fill(p, privatedata.barattrs)

    def key_pt(self, privatedata, sharedata, graph, x_pt, y_pt, width_pt, height_pt):
        selectindex = privatedata.stackedbar
        selecttotal = sharedata.stackedbar + 1
        graph.fill(path.rect_pt(x_pt + width_pt*selectindex/float(selecttotal), y_pt, width_pt/float(selecttotal), height_pt), privatedata.barattrs)

