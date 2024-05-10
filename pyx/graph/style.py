# -*- encoding: utf-8 -*-
#
#
# Copyright (C) 2002-2012 Jörg Lehmann <joerg@pyx-project.org>
# Copyright (C) 2003-2004 Michael Schindler <m-schindler@users.sourceforge.net>
# Copyright (C) 2002-2012 André Wobst <wobsta@pyx-project.org>
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


import io, logging, math
from pyx import attr, deco, bitmap, style, color, unit, canvas, path, mesh, trafo
from pyx import text as textmodule
from .graph import registerdefaultprovider, graphx
from . import axis

builtinrange = range
logger = logging.getLogger("pyx")


class _style:
    """Interface class for graph styles

    Each graph style must support the methods described in this
    class. However, since a graph style might not need to perform
    actions on all the various events, it does not need to overwrite
    all methods of this base class (e.g. this class is not an abstract
    class in any respect).

    A style should never store private data by instance variables
    (i.e. accessing self), but it should use the sharedata and privatedata
    instances instead. A style instance can be used multiple times with
    different sharedata and privatedata instances at the very same time.
    The sharedata and privatedata instances act as data containers and
    sharedata allows for sharing information across several styles.

    Every style contains two class variables, which are not to be
    modified:
     - providesdata is a list of variable names a style offers via
       the sharedata instance. This list is used to determine whether
       all needs of subsequent styles are fulfilled. Otherwise
       getdefaultprovider should return a proper style to be used.
     - needsdata is a list of variable names the style needs to access in the
       sharedata instance.
    """

    providesdata = [] # by default, we provide nothing
    needsdata = [] # and do not depend on anything

    def columnnames(self, privatedata, sharedata, graph, columnnames, dataaxisnames):
        """Set column information

        This method is used setup the column name information to be
        accessible to the style later on. The style should analyse
        the list of column names. The method should return a list of
        column names which the style will make use of. If a style
        uses some column data to feed into an axis with a different
        name, it should add an entry into the dataaxisnames dictionary
        with key begin the column name and the value being the axis
        name."""
        return []

    def adjustaxis(self, privatedata, sharedata, graph, plotitem, columnname, data):
        """Adjust axis range

        This method is called in order to adjust the axis range to
        the provided data. columnname is the column name (each style
        is subsequently called for all column names)."""
        pass

    def selectstyle(self, privatedata, sharedata, graph, selectindex, selecttotal):
        """Select stroke/fill attributes

        This method is called to allow for the selection of
        changable attributes of a style."""
        pass

    def initdrawpoints(self, privatedata, sharedata, graph):
        """Initialize drawing of data

        This method might be used to initialize the drawing of data."""
        pass

    def drawpoint(self, privatedata, sharedata, graph, point):
        """Draw data

        This method is called for each data point. The data is
        available in the dictionary point. The dictionary
        keys are the column names."""
        pass

    def donedrawpoints(self, privatedata, sharedata, graph):
        """Finalize drawing of data

        This method is called after the last data point was
        drawn using the drawpoint method above."""
        pass

    def key_pt(self, privatedata, sharedata, graph, x_pt, y_pt, width_pt, height_pt):
        """Draw graph key"""
        pass


class _marker: pass
class _autokeygraph: pass


class _keygraphstyle(_style):

    autographkey = _autokeygraph

    def __init__(self, colorname="color", gradient=color.gradient.Grey, coloraxis=None, keygraph=_autokeygraph):
        self.colorname = colorname
        self.gradient = gradient
        self.coloraxis = coloraxis
        self.keygraph = keygraph

    def columnnames(self, privatedata, sharedata, graph, columnnames, dataaxisnames):
        return [self.colorname]

    def adjustaxis(self, privatedata, sharedata, graph, plotitem, columnname, data):
        if columnname == self.colorname:
            if self.keygraph is None:
                # we always need a keygraph, but we might not show it
                if self.coloraxis is None:
                    coloraxis = axis.lin()
                else:
                    coloraxis = self.coloraxis
                privatedata.keygraph = graphx(length=10, direction="vertical", x=coloraxis)
            elif self.keygraph is _autokeygraph:
                if self.coloraxis is None:
                    coloraxis = axis.lin(title=plotitem.title)
                    plotitem.title = None # Huui!?
                else:
                    coloraxis = self.coloraxis
                privatedata.keygraph = graphx(x=coloraxis, **graph.autokeygraphattrs())
            else:
                privatedata.keygraph = self.keygraph
            # TODO: we shouldn't have multiple plotitems
            from . import data as datamodule
            privatedata.keygraph.plot(datamodule.values(x=data), [gradient(gradient=self.gradient)])

    def color(self, privatedata, c):
        vc = privatedata.keygraph.axes["x"].convert(c)
        if vc < 0:
            logger.warning("gradient color range is exceeded (lower bound)")
            vc = 0
        if vc > 1:
            logger.warning("gradient color range is exceeded (upper bound)")
            vc = 1
        return self.gradient.getcolor(vc)

    def donedrawpoints(self, privatedata, sharedata, graph):
        if self.keygraph is _autokeygraph:
            graph.layer("key").insert(privatedata.keygraph, [graph.autokeygraphtrafo(privatedata.keygraph)])


class pos(_style):

    providesdata = ["vpos", "vposmissing", "vposavailable", "vposvalid", "poscolumnnames"]

    def __init__(self, usenames={}, epsilon=1e-10):
        self.usenames = usenames
        self.epsilon = epsilon

    def columnnames(self, privatedata, sharedata, graph, columnnames, dataaxisnames):
        privatedata.poscolumnnames = []
        privatedata.vposmissing = []
        privatedata.axisnames = {}
        for count, axisnames in enumerate(graph.axesnames):
            for axisname in axisnames:
                try:
                    usename = self.usenames[axisname]
                except KeyError:
                    usename = axisname
                for columnname in columnnames:
                    if usename == columnname:
                        privatedata.poscolumnnames.append(columnname)
                        privatedata.axisnames[columnname] = axisname
            if len(privatedata.poscolumnnames) > count+1:
                raise ValueError("multiple axes per graph dimension")
            elif len(privatedata.poscolumnnames) < count+1:
                privatedata.vposmissing.append(count)
                privatedata.poscolumnnames.append(None)
        # Make poscolumnnames and vposmissing available to the outside,
        # but keep a private reference. A copy is not needed, because
        # the data is not altered in place, but might be exchanged my a
        # later, different pos style in the styles list (due to different
        # usenames).
        sharedata.poscolumnnames = privatedata.poscolumnnames
        sharedata.vposmissing = privatedata.vposmissing
        dataaxisnames.update(privatedata.axisnames)
        return [columnname for columnname in privatedata.poscolumnnames if columnname is not None]

    def adjustaxis(self, privatedata, sharedata, graph, plotitem, columnname, data):
        if columnname in privatedata.axisnames:
            graph.axes[privatedata.axisnames[columnname]].adjustaxis(data)

    def initdrawpoints(self, privatedata, sharedata, graph):
        sharedata.vpos = [None]*(len(graph.axesnames))
        privatedata.pointpostmplist = [[columnname, index, graph.axes[privatedata.axisnames[columnname]]] # temporarily used by drawpoint only
                                       for index, columnname in enumerate([columnname for columnname in privatedata.poscolumnnames if columnname is not None])]
        for missing in privatedata.vposmissing:
            for pointpostmp in privatedata.pointpostmplist:
                if pointpostmp[1] >= missing:
                    pointpostmp[1] += 1

    def drawpoint(self, privatedata, sharedata, graph, point):
        sharedata.vposavailable = 1 # valid position (but might be outside of the graph)
        sharedata.vposvalid = 1 # valid position inside the graph
        for columnname, index, axis in privatedata.pointpostmplist:
            try:
                v = axis.convert(point[columnname])
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

    def _numberofbits(self, mask):
        if not mask:
            return 0
        if mask & 1:
            return self._numberofbits(mask >> 1) + 1
        else:
            return self._numberofbits(mask >> 1)

    def columnnames(self, privatedata, sharedata, graph, columnnames, dataaxisnames):
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
                for columnname in columnnames:
                    addusecolumns = 1
                    if usename == columnname:
                        mask += self.mask_value
                    elif usename + "min" == columnname:
                        mask += self.mask_min
                    elif usename + "max" == columnname:
                        mask += self.mask_max
                    elif "d" + usename + "min" == columnname:
                        mask += self.mask_dmin
                    elif "d" + usename + "max" == columnname:
                        mask += self.mask_dmax
                    elif "d" + usename == columnname:
                        mask += self.mask_d
                    else:
                        addusecolumns = 0
                    if addusecolumns:
                        usecolumns.append(columnname)
                        dataaxisnames[columnname] = axisname
                if mask & (self.mask_min | self.mask_max | self.mask_dmin | self.mask_dmax | self.mask_d):
                    if (self._numberofbits(mask & (self.mask_min | self.mask_dmin | self.mask_d)) > 1 or
                        self._numberofbits(mask & (self.mask_max | self.mask_dmax | self.mask_d)) > 1):
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
                sharedata.vrangeminmissing.append(count)
                sharedata.vrangemaxmissing.append(count)
            else:
                if not (privatedata.rangeposcolumns[-1][2] & (self.mask_min | self.mask_dmin | self.mask_d)):
                    sharedata.vrangeminmissing.append(count)
                if not (privatedata.rangeposcolumns[-1][2] & (self.mask_max | self.mask_dmax | self.mask_d)):
                    sharedata.vrangemaxmissing.append(count)
        return usecolumns

    def adjustaxis(self, privatedata, sharedata, graph, plotitem, columnname, data):
        for axisname, usename, mask in privatedata.rangeposcolumns:
            if columnname == usename + "min" and mask & self.mask_min:
                graph.axes[axisname].adjustaxis(data)
            if columnname == usename + "max" and mask & self.mask_max:
                graph.axes[axisname].adjustaxis(data)

        # delta handling: fill rangeposdeltacolumns
        for axisname, usename, mask in privatedata.rangeposcolumns:
            if columnname == usename and mask & (self.mask_dmin | self.mask_dmax | self.mask_d):
                privatedata.rangeposdeltacolumns[axisname][self.mask_value] = data
            if columnname == "d" + usename + "min" and mask & self.mask_dmin:
                privatedata.rangeposdeltacolumns[axisname][self.mask_dmin] = data
            if columnname == "d" + usename + "max" and mask & self.mask_dmax:
                privatedata.rangeposdeltacolumns[axisname][self.mask_dmax] = data
            if columnname == "d" + usename and mask & self.mask_d:
                privatedata.rangeposdeltacolumns[axisname][self.mask_d] = data

        # delta handling: process rangeposdeltacolumns
        for a, d in list(privatedata.rangeposdeltacolumns.items()):
            if self.mask_value in d:
                for k in list(d.keys()):
                    if k != self.mask_value:
                        if k & (self.mask_dmin | self.mask_d):
                            mindata = []
                            for value, delta in zip(d[self.mask_value], d[k]):
                                try:
                                    mindata.append(value-delta)
                                except Exception:
                                    pass
                            graph.axes[a].adjustaxis(mindata)
                        if k & (self.mask_dmax | self.mask_d):
                            maxdata = []
                            for value, delta in zip(d[self.mask_value], d[k]):
                                try:
                                    maxdata.append(value+delta)
                                except Exception:
                                    pass
                            graph.axes[a].adjustaxis(maxdata)
                        del d[k]

    def initdrawpoints(self, privatedata, sharedata, graph):
        sharedata.vrange = [[None for x in builtinrange(2)] for y in privatedata.rangeposcolumns + sharedata.vrangemissing]
        privatedata.rangepostmplist = [[usename, mask, index, graph.axes[axisname]] # temporarily used by drawpoint only
                                       for index, (axisname, usename, mask) in enumerate(privatedata.rangeposcolumns)]
        for missing in sharedata.vrangemissing:
            for rangepostmp in privatedata.rangepostmplist:
                if rangepostmp[2] >= missing:
                    rangepostmp[2] += 1

    def drawpoint(self, privatedata, sharedata, graph, point):
        for usename, mask, index, axis in privatedata.rangepostmplist:
            try:
                if mask & self.mask_min:
                    sharedata.vrange[index][0] = axis.convert(point[usename + "min"])
                if mask & self.mask_dmin:
                    sharedata.vrange[index][0] = axis.convert(point[usename] - point["d" + usename + "min"])
                if mask & self.mask_d:
                    sharedata.vrange[index][0] = axis.convert(point[usename] - point["d" + usename])
            except (ArithmeticError, ValueError, TypeError):
                sharedata.vrange[index][0] = None
            try:
                if mask & self.mask_max:
                    sharedata.vrange[index][1] = axis.convert(point[usename + "max"])
                if mask & self.mask_dmax:
                    sharedata.vrange[index][1] = axis.convert(point[usename] + point["d" + usename + "max"])
                if mask & self.mask_d:
                    sharedata.vrange[index][1] = axis.convert(point[usename] + point["d" + usename])
            except (ArithmeticError, ValueError, TypeError):
                sharedata.vrange[index][1] = None



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

    def columnnames(self, privatedata, sharedata, graph, columnnames, dataaxisnames):
        if len(sharedata.vposmissing):
            raise ValueError("incomplete position information")
        return []


class symbol(_styleneedingpointpos):

    needsdata = ["vpos", "vposmissing", "vposvalid"]

    # "inject" the predefinied symbols into the class:
    #
    # Note, that statements like cross = _crosssymbol are
    # invalid, since the would lead to unbound methods, but
    # a single entry changeable list does the trick.
    #
    # Once we require Python 2.2+ we should use staticmethods
    # to implement the default symbols inplace.

    cross = attr.changelist([_crosssymbol])
    plus = attr.changelist([_plussymbol])
    square = attr.changelist([_squaresymbol])
    triangle = attr.changelist([_trianglesymbol])
    circle = attr.changelist([_circlesymbol])
    diamond = attr.changelist([_diamondsymbol])

    changecross = attr.changelist([_crosssymbol, _plussymbol, _squaresymbol, _trianglesymbol, _circlesymbol, _diamondsymbol])
    changeplus = attr.changelist([_plussymbol, _squaresymbol, _trianglesymbol, _circlesymbol, _diamondsymbol, _crosssymbol])
    changesquare = attr.changelist([_squaresymbol, _trianglesymbol, _circlesymbol, _diamondsymbol, _crosssymbol, _plussymbol])
    changetriangle = attr.changelist([_trianglesymbol, _circlesymbol, _diamondsymbol, _crosssymbol, _plussymbol, _squaresymbol])
    changecircle = attr.changelist([_circlesymbol, _diamondsymbol, _crosssymbol, _plussymbol, _squaresymbol, _trianglesymbol])
    changediamond = attr.changelist([_diamondsymbol, _crosssymbol, _plussymbol, _squaresymbol, _trianglesymbol, _circlesymbol])
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

    def drawpoint(self, privatedata, sharedata, graph, point):
        if sharedata.vposvalid and privatedata.symbolattrs is not None:
            x_pt, y_pt = graph.vpos_pt(*sharedata.vpos)
            privatedata.symbol(privatedata.symbolcanvas, x_pt, y_pt, privatedata.size_pt, privatedata.symbolattrs)

    def donedrawpoints(self, privatedata, sharedata, graph):
        graph.layer("data").insert(privatedata.symbolcanvas)

    def key_pt(self, privatedata, sharedata, graph, x_pt, y_pt, width_pt, height_pt):
        if privatedata.symbolattrs is not None:
            privatedata.symbol(graph, x_pt+0.5*width_pt, y_pt+0.5*height_pt, privatedata.size_pt, privatedata.symbolattrs)


class _line(_styleneedingpointpos):

    # this style is not a complete style, but it provides the basic functionality to
    # create a line, which is cut at the graph boundaries (or at otherwise invalid points)

    def __init__(self, epsilon=1e-10):
        self.epsilon = epsilon

    def initpointstopath(self, privatedata):
        privatedata.path = path.path()
        privatedata.linebasepoints = []
        privatedata.lastvpos = None

    def addpointstopath(self, privatedata):
        # add baselinepoints to privatedata.path
        if len(privatedata.linebasepoints) > 1:
            privatedata.path.append(path.moveto_pt(*privatedata.linebasepoints[0]))
            if len(privatedata.linebasepoints) > 2:
                privatedata.path.append(path.multilineto_pt(privatedata.linebasepoints[1:]))
            else:
                privatedata.path.append(path.lineto_pt(*privatedata.linebasepoints[1]))
        privatedata.linebasepoints = []

    def addpoint(self, privatedata, graphvpos_pt, vposavailable, vposvalid, vpos):
        # append linebasepoints
        if vposavailable:
            if len(privatedata.linebasepoints):
                # the last point was inside the graph
                if vposvalid: # shortcut for the common case
                    privatedata.linebasepoints.append(graphvpos_pt(*vpos))
                else:
                    # cut end
                    cut = 1
                    for vstart, vend in zip(privatedata.lastvpos, vpos):
                        if abs(vend - vstart) > self.epsilon:
                            newcut = None
                            if vend > 1:
                                # 1 = vstart + (vend - vstart) * cut
                                newcut = (1 - vstart)/(vend - vstart)
                            if vend < 0:
                                # 0 = vstart + (vend - vstart) * cut
                                newcut = - vstart/(vend - vstart)
                            if newcut is not None and newcut < cut:
                                cut = newcut
                    cutvpos = []
                    for vstart, vend in zip(privatedata.lastvpos, vpos):
                        cutvpos.append(vstart + (vend - vstart) * cut)
                    privatedata.linebasepoints.append(graphvpos_pt(*cutvpos))
                    self.addpointstopath(privatedata)
            else:
                # the last point was outside the graph
                if privatedata.lastvpos is not None:
                    if vposvalid:
                        # cut beginning
                        cut = 0
                        for vstart, vend in zip(privatedata.lastvpos, vpos):
                            if abs(vend - vstart) > self.epsilon:
                                newcut = None
                                if vstart > 1:
                                    # 1 = vstart + (vend - vstart) * cut
                                    newcut = (1 - vstart)/(vend - vstart)
                                if vstart < 0:
                                    # 0 = vstart + (vend - vstart) * cut
                                    newcut = - vstart/(vend - vstart)
                                if newcut is not None and newcut > cut:
                                    cut = newcut
                        cutvpos = []
                        for vstart, vend in zip(privatedata.lastvpos, vpos):
                            cutvpos.append(vstart + (vend - vstart) * cut)
                        privatedata.linebasepoints.append(graphvpos_pt(*cutvpos))
                        privatedata.linebasepoints.append(graphvpos_pt(*vpos))
                    else:
                        # sometimes cut beginning and end
                        cutfrom = 0
                        cutto = 1
                        for vstart, vend in zip(privatedata.lastvpos, vpos):
                            if vstart > 1 and vend > 1: break
                            if vstart < 0 and vend < 0: break
                            if abs(vend - vstart) > self.epsilon:
                                newcutfrom = None
                                if vstart > 1:
                                    newcutfrom = (1 - vstart)/(vend - vstart)
                                if vstart < 0:
                                    # 0 = vstart + (vend - vstart) * cutfrom
                                    newcutfrom = - vstart/(vend - vstart)
                                if newcutfrom is not None and newcutfrom > cutfrom:
                                    cutfrom = newcutfrom
                                newcutto = None
                                if vend > 1:
                                    # 1 = vstart + (vend - vstart) * cutto
                                    newcutto = (1 - vstart)/(vend - vstart)
                                if vend < 0:
                                    # 0 = vstart + (vend - vstart) * cutto
                                    newcutto = - vstart/(vend - vstart)
                                if newcutto is not None and newcutto < cutto:
                                    cutto = newcutto
                        else:
                            if cutfrom < cutto:
                                cutfromvpos = []
                                cuttovpos = []
                                for vstart, vend in zip(privatedata.lastvpos, vpos):
                                    cutfromvpos.append(vstart + (vend - vstart) * cutfrom)
                                    cuttovpos.append(vstart + (vend - vstart) * cutto)
                                privatedata.linebasepoints.append(graphvpos_pt(*cutfromvpos))
                                privatedata.linebasepoints.append(graphvpos_pt(*cuttovpos))
                                self.addpointstopath(privatedata)
            privatedata.lastvpos = vpos[:]
        else:
            if len(privatedata.linebasepoints) > 1:
                self.addpointstopath(privatedata)
            privatedata.lastvpos = None

    def addinvalid(self, privatedata):
        if len(privatedata.linebasepoints) > 1:
            self.addpointstopath(privatedata)
        privatedata.lastvpos = None

    def donepointstopath(self, privatedata):
        if len(privatedata.linebasepoints) > 1:
            self.addpointstopath(privatedata)
        return privatedata.path


class line(_line):

    needsdata = ["vpos", "vposmissing", "vposavailable", "vposvalid"]

    changelinestyle = attr.changelist([style.linestyle.solid,
                                       style.linestyle.dashed,
                                       style.linestyle.dotted,
                                       style.linestyle.dashdotted])

    defaultlineattrs = [changelinestyle]

    def __init__(self, lineattrs=[], **kwargs):
        _line.__init__(self, **kwargs)
        self.lineattrs = lineattrs

    def selectstyle(self, privatedata, sharedata, graph, selectindex, selecttotal):
        if self.lineattrs is not None:
            privatedata.lineattrs = attr.selectattrs(self.defaultlineattrs + self.lineattrs, selectindex, selecttotal)
        else:
            privatedata.lineattrs = None

    def initdrawpoints(self, privatedata, sharedata, graph):
        self.initpointstopath(privatedata)

    def drawpoint(self, privatedata, sharedata, graph, point):
        self.addpoint(privatedata, graph.vpos_pt, sharedata.vposavailable, sharedata.vposvalid, sharedata.vpos)

    def donedrawpoints(self, privatedata, sharedata, graph):
        path = self.donepointstopath(privatedata)
        if privatedata.lineattrs is not None and len(path):
            graph.layer("data").stroke(path, privatedata.lineattrs)

    def key_pt(self, privatedata, sharedata, graph, x_pt, y_pt, width_pt, height_pt):
        if privatedata.lineattrs is not None:
            graph.stroke(path.line_pt(x_pt, y_pt+0.5*height_pt, x_pt+width_pt, y_pt+0.5*height_pt), privatedata.lineattrs)


class impulses(_styleneedingpointpos):

    needsdata = ["vpos", "vposmissing", "vposavailable", "vposvalid", "poscolumnnames"]

    defaultlineattrs = [line.changelinestyle]
    defaultfrompathattrs = []

    def __init__(self, lineattrs=[], fromvalue=0, frompathattrs=[], valueaxisindex=1):
        self.lineattrs = lineattrs
        self.fromvalue = fromvalue
        self.frompathattrs = frompathattrs
        self.valueaxisindex = valueaxisindex

    def selectstyle(self, privatedata, sharedata, graph, selectindex, selecttotal):
        privatedata.insertfrompath = selectindex == 0
        if self.lineattrs is not None:
            privatedata.lineattrs = attr.selectattrs(self.defaultlineattrs + self.lineattrs, selectindex, selecttotal)
        else:
            privatedata.lineattrs = None

    def adjustaxis(self, privatedata, sharedata, graph, plotitem, columnname, data):
        if self.fromvalue is not None:
            try:
                i = sharedata.poscolumnnames.index(columnname)
            except ValueError:
                pass
            else:
                if i == self.valueaxisindex:
                    graph.axes[sharedata.poscolumnnames[i]].adjustaxis([self.fromvalue])

    def initdrawpoints(self, privatedata, sharedata, graph):
        privatedata.impulsescanvas = canvas.canvas()
        if self.fromvalue is not None:
            valueaxisname = sharedata.poscolumnnames[self.valueaxisindex]
            privatedata.vfromvalue = graph.axes[valueaxisname].convert(self.fromvalue)
            privatedata.vfromvaluecut = 0
            if privatedata.vfromvalue < 0:
                privatedata.vfromvalue = 0
            if privatedata.vfromvalue > 1:
                privatedata.vfromvalue = 1
            if self.frompathattrs is not None and privatedata.insertfrompath:
                graph.layer("data").stroke(graph.axes[valueaxisname].vgridpath(privatedata.vfromvalue),
                                           self.defaultfrompathattrs + self.frompathattrs)
        else:
            privatedata.vfromvalue = 0

    def drawpoint(self, privatedata, sharedata, graph, point):
        if sharedata.vposvalid and privatedata.lineattrs is not None:
            vpos = sharedata.vpos[:]
            vpos[self.valueaxisindex] = privatedata.vfromvalue
            privatedata.impulsescanvas.stroke(graph.vgeodesic(*(vpos + sharedata.vpos)), privatedata.lineattrs)

    def donedrawpoints(self, privatedata, sharedata, graph):
        graph.layer("data").insert(privatedata.impulsescanvas)

    def key_pt(self, privatedata, sharedata, graph, x_pt, y_pt, width_pt, height_pt):
        if privatedata.lineattrs is not None:
            graph.stroke(path.line_pt(x_pt, y_pt+0.5*height_pt, x_pt+width_pt, y_pt+0.5*height_pt), privatedata.lineattrs)


class errorbar(_style):

    needsdata = ["vpos", "vposmissing", "vposavailable", "vposvalid", "vrange", "vrangeminmissing", "vrangemaxmissing"]

    defaulterrorbarattrs = []

    def __init__(self, size=0.1*unit.v_cm,
                       errorbarattrs=[],
                       epsilon=1e-10):
        self.size = size
        self.errorbarattrs = errorbarattrs
        self.epsilon = epsilon

    def columnnames(self, privatedata, sharedata, graph, columnnames, dataaxisnames):
        for i in sharedata.vposmissing:
            if i in sharedata.vrangeminmissing and i in sharedata.vrangemaxmissing:
                raise ValueError("position and range for a graph dimension missing")
        return []

    def selectstyle(self, privatedata, sharedata, graph, selectindex, selecttotal):
        privatedata.errorsize_pt = unit.topt(attr.selectattr(self.size, selectindex, selecttotal))
        privatedata.errorbarattrs = attr.selectattrs(self.defaulterrorbarattrs + self.errorbarattrs, selectindex, selecttotal)

    def initdrawpoints(self, privatedata, sharedata, graph):
        if privatedata.errorbarattrs is not None:
            privatedata.errorbarcanvas = canvas.canvas(privatedata.errorbarattrs)
            privatedata.dimensionlist = list(builtinrange(len(sharedata.vpos)))

    def drawpoint(self, privatedata, sharedata, graph, point):
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
            graph.layer("data").insert(privatedata.errorbarcanvas)


class text(_styleneedingpointpos):

    needsdata = ["vpos", "vposmissing", "vposvalid"]

    defaulttextattrs = [textmodule.halign.center, textmodule.vshift.mathaxis]

    def __init__(self, textname="text", dxname=None, dyname=None,
                       dxunit=0.3*unit.v_cm, dyunit=0.3*unit.v_cm,
                       textdx=0*unit.v_cm, textdy=0.3*unit.v_cm, textattrs=[]):
        self.textname = textname
        self.dxname = dxname
        self.dyname = dyname
        self.dxunit = dxunit
        self.dyunit = dyunit
        self.textdx = textdx
        self.textdy = textdy
        self.textattrs = textattrs

    def columnnames(self, privatedata, sharedata, graph, columnnames, dataaxisnames):
        if self.textname not in columnnames:
            raise ValueError("column '%s' missing" % self.textname)
        names = [self.textname]
        if self.dxname is not None:
            if self.dxname not in columnnames:
                raise ValueError("column '%s' missing" % self.dxname)
            names.append(self.dxname)
        if self.dyname is not None:
            if self.dyname not in columnnames:
                raise ValueError("column '%s' missing" % self.dyname)
            names.append(self.dyname)
        return names + _styleneedingpointpos.columnnames(self, privatedata, sharedata, graph, columnnames, dataaxisnames)

    def selectstyle(self, privatedata, sharedata, graph, selectindex, selecttotal):
        if self.textattrs is not None:
            privatedata.textattrs = attr.selectattrs(self.defaulttextattrs + self.textattrs, selectindex, selecttotal)
        else:
            privatedata.textattrs = None

    def initdrawpoints(self, privatedata, sharedata, grap):
        if self.dxname is None:
            privatedata.textdx_pt = unit.topt(self.textdx)
        else:
            privatedata.dxunit_pt = unit.topt(self.dxunit)
        if self.dyname is None:
            privatedata.textdy_pt = unit.topt(self.textdy)
        else:
            privatedata.dyunit_pt = unit.topt(self.dyunit)

    def drawpoint(self, privatedata, sharedata, graph, point):
        if privatedata.textattrs is not None and sharedata.vposvalid:
            x_pt, y_pt = graph.vpos_pt(*sharedata.vpos)
            try:
                text = str(point[self.textname])
            except Exception:
                pass
            else:
                if self.dxname is None:
                    dx_pt = privatedata.textdx_pt
                else:
                    dx_pt = float(point[self.dxname]) * privatedata.dxunit_pt
                if self.dyname is None:
                    dy_pt = privatedata.textdy_pt
                else:
                    dy_pt = float(point[self.dyname]) * privatedata.dyunit_pt
                graph.layer("data").text_pt(x_pt + dx_pt, y_pt + dy_pt, text, privatedata.textattrs)

    def key_pt(self, privatedata, sharedata, graph, x_pt, y_pt, width_pt, height_pt):
        raise RuntimeError("Style currently doesn't provide a graph key")


class arrow(_styleneedingpointpos):

    needsdata = ["vpos", "vposmissing", "vposvalid"]

    defaultlineattrs = []
    defaultarrowattrs = []

    def __init__(self, linelength=0.25*unit.v_cm, arrowsize=0.15*unit.v_cm, lineattrs=[], arrowattrs=[], arrowpos=0.5, epsilon=1e-5, decorator=deco.earrow):
        self.linelength = linelength
        self.arrowsize = arrowsize
        self.lineattrs = lineattrs
        self.arrowattrs = arrowattrs
        self.arrowpos = arrowpos
        self.epsilon = epsilon
        self.decorator = decorator

    def columnnames(self, privatedata, sharedata, graph, columnnames, dataaxisnames):
        if len(graph.axesnames) != 2:
            raise ValueError("arrow style restricted on two-dimensional graphs")
        if "size" not in columnnames:
            raise ValueError("size missing")
        if "angle" not in columnnames:
            raise ValueError("angle missing")
        return ["size", "angle"] + _styleneedingpointpos.columnnames(self, privatedata, sharedata, graph, columnnames, dataaxisnames)

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

    def drawpoint(self, privatedata, sharedata, graph, point):
        if privatedata.lineattrs is not None and privatedata.arrowattrs is not None and sharedata.vposvalid:
            linelength_pt = unit.topt(self.linelength)
            x_pt, y_pt = graph.vpos_pt(*sharedata.vpos)
            try:
                angle = point["angle"] + 0.0
                size = point["size"] + 0.0
            except Exception:
                pass
            else:
                if point["size"] > self.epsilon:
                    dx = math.cos(angle*math.pi/180)
                    dy = math.sin(angle*math.pi/180)
                    x1 = x_pt-self.arrowpos*dx*linelength_pt*size
                    y1 = y_pt-self.arrowpos*dy*linelength_pt*size
                    x2 = x_pt+(1-self.arrowpos)*dx*linelength_pt*size
                    y2 = y_pt+(1-self.arrowpos)*dy*linelength_pt*size
                    if self.decorator:
                        privatedata.arrowcanvas.stroke(path.line_pt(x1, y1, x2, y2),
                                                       privatedata.lineattrs+[self.decorator(privatedata.arrowattrs, size=self.arrowsize*size)])
                    else:
                        privatedata.arrowcanvas.stroke(path.line_pt(x1, y1, x2, y2), privatedata.lineattrs)

    def donedrawpoints(self, privatedata, sharedata, graph):
        graph.layer("data").insert(privatedata.arrowcanvas)

    def key_pt(self, privatedata, sharedata, graph, x_pt, y_pt, width_pt, height_pt):
        raise RuntimeError("Style currently doesn't provide a graph key")


class rect(_keygraphstyle):

    needsdata = ["vrange", "vrangeminmissing", "vrangemaxmissing"]

    def columnnames(self, privatedata, sharedata, graph, columnnames, dataaxisnames):
        if len(graph.axesnames) != 2:
            raise TypeError("rect style restricted on two-dimensional graphs")
        if len(sharedata.vrangeminmissing) + len(sharedata.vrangemaxmissing):
            raise ValueError("incomplete range")
        return _keygraphstyle.columnnames(self, privatedata, sharedata, graph, columnnames, dataaxisnames)

    def initdrawpoints(self, privatedata, sharedata, graph):
        privatedata.rectcanvas = graph.layer("filldata").insert(canvas.canvas())

    def drawpoint(self, privatedata, sharedata, graph, point):
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
            privatedata.rectcanvas.fill(p, [self.color(privatedata, point["color"])])


class histogram(_style):

    needsdata = ["vpos", "vposmissing", "vrange", "vrangeminmissing", "vrangemaxmissing"]

    defaultlineattrs = [deco.stroked]
    defaultfrompathattrs = []

    def __init__(self, lineattrs=[], steps=0, fromvalue=0, frompathattrs=[], fillable=0, rectkey=0,
                       autohistogramaxisindex=0, autohistogrampointpos=0.5, epsilon=1e-10):
        self.lineattrs = lineattrs
        self.steps = steps
        self.fromvalue = fromvalue
        self.frompathattrs = frompathattrs
        self.fillable = fillable # TODO: fillable paths might not properly be closed by straight lines on curved graph geometries
        self.rectkey = rectkey
        self.autohistogramaxisindex = autohistogramaxisindex
        self.autohistogrampointpos = autohistogrampointpos
        self.epsilon = epsilon

    def columnnames(self, privatedata, sharedata, graph, columnnames, dataaxisnames):
        if len(graph.axesnames) != 2:
            raise TypeError("histogram style restricted on two-dimensional graphs")
        privatedata.rangeaxisindex = None
        for i in builtinrange(len(graph.axesnames)):
            if i in sharedata.vrangeminmissing or i in sharedata.vrangemaxmissing:
                if i in sharedata.vposmissing:
                    raise ValueError("pos and range missing")
            else:
                if privatedata.rangeaxisindex is not None:
                    raise ValueError("multiple ranges")
                privatedata.rangeaxisindex = i
        if privatedata.rangeaxisindex is None:
            privatedata.rangeaxisindex = self.autohistogramaxisindex
            privatedata.autohistogram = 1
        else:
            privatedata.autohistogram = 0
        return []

    def adjustaxis(self, privatedata, sharedata, graph, plotitem, columnname, data):
        if privatedata.autohistogram and columnname == sharedata.poscolumnnames[privatedata.rangeaxisindex]:
            if len(data) == 1:
                raise ValueError("several data points needed for automatic histogram width calculation")
            if len(data) > 1:
                delta = data[1] - data[0]
                min = data[0] - self.autohistogrampointpos * delta
                max = data[-1] + (1-self.autohistogrampointpos) * delta
                graph.axes[columnname].adjustaxis([min, max])
        elif self.fromvalue is not None and columnname == sharedata.poscolumnnames[1-privatedata.rangeaxisindex]:
            graph.axes[columnname].adjustaxis([self.fromvalue])

    def selectstyle(self, privatedata, sharedata, graph, selectindex, selecttotal):
        privatedata.insertfrompath = selectindex == 0
        if self.lineattrs is not None:
            privatedata.lineattrs = attr.selectattrs(self.defaultlineattrs + self.lineattrs, selectindex, selecttotal)
        else:
            privatedata.lineattrs = None

    def vmoveto(self, privatedata, sharedata, graph, vpos, vvalue):
        if -self.epsilon < vpos < 1+self.epsilon and -self.epsilon < vvalue < 1+self.epsilon:
            if privatedata.rangeaxisindex:
                privatedata.path.append(path.moveto_pt(*graph.vpos_pt(vvalue, vpos)))
            else:
                privatedata.path.append(path.moveto_pt(*graph.vpos_pt(vpos, vvalue)))

    def vposline(self, privatedata, sharedata, graph, vpos, vvalue1, vvalue2):
        if -self.epsilon < vpos < 1+self.epsilon:
            vvalue1cut = 0
            if vvalue1 < 0:
                vvalue1 = 0
                vvalue1cut = -1
            elif vvalue1 > 1:
                vvalue1 = 1
                vvalue1cut = 1
            vvalue2cut = 0
            if vvalue2 < 0:
                vvalue2 = 0
                vvalue2cut = -1
            elif vvalue2 > 1:
                vvalue2 = 1
                vvalue2cut = 1
            if abs(vvalue1cut + vvalue2cut) <= 1:
                if vvalue1cut and not self.fillable:
                    if privatedata.rangeaxisindex:
                        privatedata.path.append(path.moveto_pt(*graph.vpos_pt(vvalue1, vpos)))
                    else:
                        privatedata.path.append(path.moveto_pt(*graph.vpos_pt(vpos, vvalue1)))
                if privatedata.rangeaxisindex:
                    privatedata.path.append(graph.vgeodesic_el(vvalue1, vpos, vvalue2, vpos))
                else:
                    privatedata.path.append(graph.vgeodesic_el(vpos, vvalue1, vpos, vvalue2))

    def vvalueline(self, privatedata, sharedata, graph, vvalue, vpos1, vpos2):
        if self.fillable:
            if vvalue < -self.epsilon:
                vvalue = 0
                logger.warning("cut at graph boundary adds artificial lines to fillable step histogram path")
            if vvalue > 1+self.epsilon:
                vvalue = 1
                logger.warning("cut at graph boundary adds artificial lines to fillable step histogram path")
        if self.fillable or (-self.epsilon < vvalue < 1+self.epsilon):
            vpos1cut = 0
            if vpos1 < 0:
                vpos1 = 0
                vpos1cut = -1
            elif vpos1 > 1:
                vpos1 = 1
                vpos1cut = 1
            vpos2cut = 0
            if vpos2 < 0:
                vpos2 = 0
                vpos2cut = -1
            elif vpos2 > 1:
                vpos2 = 1
                vpos2cut = 1
            if abs(vpos1cut + vpos2cut) <= 1:
                if vpos1cut:
                    if self.fillable:
                        if privatedata.rangeaxisindex:
                            privatedata.path.append(path.moveto_pt(*graph.vpos_pt(privatedata.vfromvalue, vpos1)))
                            privatedata.path.append(graph.vgeodesic_el(privatedata.vfromvalue, vpos1, vvalue, vpos1))
                        else:
                            privatedata.path.append(path.moveto_pt(*graph.vpos_pt(vpos1, privatedata.vfromvalue)))
                            privatedata.path.append(graph.vgeodesic_el(vpos1, privatedata.vfromvalue, vpos1, vvalue))
                    else:
                        if privatedata.rangeaxisindex:
                            privatedata.path.append(path.moveto_pt(*graph.vpos_pt(vvalue, vpos1)))
                        else:
                            privatedata.path.append(path.moveto_pt(*graph.vpos_pt(vpos1, vvalue)))
                if privatedata.rangeaxisindex:
                    privatedata.path.append(graph.vgeodesic_el(vvalue, vpos1, vvalue, vpos2))
                else:
                    privatedata.path.append(graph.vgeodesic_el(vpos1, vvalue, vpos2, vvalue))
                if self.fillable and vpos2cut:
                    logger.warning("cut at graph boundary adds artificial lines to fillable step histogram path")
                    if privatedata.rangeaxisindex:
                        privatedata.path.append(graph.vgeodesic_el(vvalue, vpos2, privatedata.vfromvalue, vpos2))
                    else:
                        privatedata.path.append(graph.vgeodesic_el(vpos2, vvalue, vpos2, privatedata.vfromvalue))

    def drawvalue(self, privatedata, sharedata, graph, vmin, vmax, vvalue):
        currentvalid = vmin is not None and vmax is not None and vvalue is not None
        if self.fillable and not self.steps:
            if not currentvalid:
                return
            vmincut = 0
            if vmin < -self.epsilon:
                vmin = 0
                vmincut = -1
            elif vmin > 1+self.epsilon:
                vmin = 1
                vmincut = 1
            vmaxcut = 0
            if vmax < -self.epsilon:
                vmax = 0
                vmaxcut = -1
            if vmax > 1+self.epsilon:
                vmax = 1
                vmaxcut = 1
            vvaluecut = 0
            if vvalue < -self.epsilon:
                vvalue = 0
                vvaluecut = -1
            if vvalue > 1+self.epsilon:
                vvalue = 1
                vvaluecut = 1
            done = 0
            if abs(vmincut) + abs(vmaxcut) + abs(vvaluecut) + abs(privatedata.vfromvaluecut) > 1:
                if abs(vmincut + vmaxcut) > 1 or abs(vvaluecut+privatedata.vfromvaluecut) > 1:
                    done = 1
                else:
                    logger.warning("multiple cuts at graph boundary add artificial lines to fillable rectangle histogram path")
            elif vmincut:
                done = 1
                if privatedata.rangeaxisindex:
                    privatedata.path.append(path.moveto_pt(*graph.vpos_pt(privatedata.vfromvalue, vmin)))
                    privatedata.path.append(graph.vgeodesic_el(privatedata.vfromvalue, vmin, privatedata.vfromvalue, vmax))
                    privatedata.path.append(graph.vgeodesic_el(privatedata.vfromvalue, vmax, vvalue, vmax))
                    privatedata.path.append(graph.vgeodesic_el(vvalue, vmax, vvalue, vmin))
                else:
                    privatedata.path.append(path.moveto_pt(*graph.vpos_pt(vmin, privatedata.vfromvalue)))
                    privatedata.path.append(graph.vgeodesic_el(vmin, privatedata.vfromvalue, vmax, privatedata.vfromvalue))
                    privatedata.path.append(graph.vgeodesic_el(vmax, privatedata.vfromvalue, vmax, vvalue))
                    privatedata.path.append(graph.vgeodesic_el(vmax, vvalue, vmin, vvalue))
            elif vmaxcut:
                done = 1
                if privatedata.rangeaxisindex:
                    privatedata.path.append(path.moveto_pt(*graph.vpos_pt(vvalue, vmax)))
                    privatedata.path.append(graph.vgeodesic_el(vvalue, vmax, vvalue, vmin))
                    privatedata.path.append(graph.vgeodesic_el(vvalue, vmin, privatedata.vfromvalue, vmin))
                    privatedata.path.append(graph.vgeodesic_el(privatedata.vfromvalue, vmin, privatedata.vfromvalue, vmax))
                else:
                    privatedata.path.append(path.moveto_pt(*graph.vpos_pt(vmax, vvalue)))
                    privatedata.path.append(graph.vgeodesic_el(vmax, vvalue, vmin, vvalue))
                    privatedata.path.append(graph.vgeodesic_el(vmin, vvalue, vmin, privatedata.vfromvalue))
                    privatedata.path.append(graph.vgeodesic_el(vmin, privatedata.vfromvalue, vmax, privatedata.vfromvalue))
            elif privatedata.vfromvaluecut:
                done = 1
                if privatedata.rangeaxisindex:
                    privatedata.path.append(path.moveto_pt(*graph.vpos_pt(privatedata.vfromvalue, vmax)))
                    privatedata.path.append(graph.vgeodesic_el(privatedata.vfromvalue, vmax, vvalue, vmax))
                    privatedata.path.append(graph.vgeodesic_el(vvalue, vmax, vvalue, vmin))
                    privatedata.path.append(graph.vgeodesic_el(vvalue, vmin, privatedata.vfromvalue, vmin))
                else:
                    privatedata.path.append(path.moveto_pt(*graph.vpos_pt(vmax, privatedata.vfromvalue)))
                    privatedata.path.append(graph.vgeodesic_el(vmax, privatedata.vfromvalue, vmax, vvalue))
                    privatedata.path.append(graph.vgeodesic_el(vmax, vvalue, vmin, vvalue))
                    privatedata.path.append(graph.vgeodesic_el(vmin, vvalue, vmin, privatedata.vfromvalue))
            elif vvaluecut:
                done = 1
                if privatedata.rangeaxisindex:
                    privatedata.path.append(path.moveto_pt(*graph.vpos_pt(vvalue, vmin)))
                    privatedata.path.append(graph.vgeodesic_el(vvalue, vmin, privatedata.vfromvalue, vmin))
                    privatedata.path.append(graph.vgeodesic_el(privatedata.vfromvalue, vmin, privatedata.vfromvalue, vmax))
                    privatedata.path.append(graph.vgeodesic_el(privatedata.vfromvalue, vmax, vvalue, vmax))
                else:
                    privatedata.path.append(path.moveto_pt(*graph.vpos_pt(vmin, vvalue)))
                    privatedata.path.append(graph.vgeodesic_el(vmin, vvalue, vmin, privatedata.vfromvalue))
                    privatedata.path.append(graph.vgeodesic_el(vmin, privatedata.vfromvalue, vmax, privatedata.vfromvalue))
                    privatedata.path.append(graph.vgeodesic_el(vmax, privatedata.vfromvalue, vmax, vvalue))
            if not done:
                if privatedata.rangeaxisindex:
                    privatedata.path.append(path.moveto_pt(*graph.vpos_pt(privatedata.vfromvalue, vmin)))
                    privatedata.path.append(graph.vgeodesic_el(privatedata.vfromvalue, vmin, privatedata.vfromvalue, vmax))
                    privatedata.path.append(graph.vgeodesic_el(privatedata.vfromvalue, vmax, vvalue, vmax))
                    privatedata.path.append(graph.vgeodesic_el(vvalue, vmax, vvalue, vmin))
                    privatedata.path.append(graph.vgeodesic_el(vvalue, vmin, privatedata.vfromvalue, vmin))
                    privatedata.path.append(path.closepath())
                else:
                    privatedata.path.append(path.moveto_pt(*graph.vpos_pt(vmin, privatedata.vfromvalue)))
                    privatedata.path.append(graph.vgeodesic_el(vmin, privatedata.vfromvalue, vmax, privatedata.vfromvalue))
                    privatedata.path.append(graph.vgeodesic_el(vmax, privatedata.vfromvalue, vmax, vvalue))
                    privatedata.path.append(graph.vgeodesic_el(vmax, vvalue, vmin, vvalue))
                    privatedata.path.append(graph.vgeodesic_el(vmin, vvalue, vmin, privatedata.vfromvalue))
                    privatedata.path.append(path.closepath())
        else:
            try:
                gap = abs(vmin - privatedata.lastvmax) > self.epsilon
            except (ArithmeticError, ValueError, TypeError):
                gap = 1
            if (privatedata.lastvvalue is not None and currentvalid and not gap and
                (self.steps or (privatedata.lastvvalue-privatedata.vfromvalue)*(vvalue-privatedata.vfromvalue) < 0)):
                self.vposline(privatedata, sharedata, graph,
                              vmin, privatedata.lastvvalue, vvalue)
            else:
                if privatedata.lastvvalue is not None and currentvalid:
                    currentbigger = abs(privatedata.lastvvalue-privatedata.vfromvalue) < abs(vvalue-privatedata.vfromvalue)
                if privatedata.lastvvalue is not None and (not currentvalid or not currentbigger or gap):
                    self.vposline(privatedata, sharedata, graph,
                                  privatedata.lastvmax, privatedata.lastvvalue, privatedata.vfromvalue)
                    if currentvalid:
                        self.vmoveto(privatedata, sharedata, graph,
                                     vmin, vvalue)
                if currentvalid and (privatedata.lastvvalue is None or currentbigger or gap):
                    self.vmoveto(privatedata, sharedata, graph,
                                 vmin, privatedata.vfromvalue)
                    self.vposline(privatedata, sharedata, graph,
                                  vmin, privatedata.vfromvalue, vvalue)
            if currentvalid:
                self.vvalueline(privatedata, sharedata, graph,
                                vvalue, vmin, vmax)
                privatedata.lastvvalue = vvalue
                privatedata.lastvmax = vmax
            else:
                privatedata.lastvvalue = privatedata.lastvmax = None

    def initdrawpoints(self, privatedata, sharedata, graph):
        privatedata.path = path.path()
        privatedata.lastvvalue = privatedata.lastvmax = None
        privatedata.vcurrentpoint = None
        privatedata.count = 0
        if self.fromvalue is not None:
            valueaxisname = sharedata.poscolumnnames[1-privatedata.rangeaxisindex]
            privatedata.vfromvalue = graph.axes[valueaxisname].convert(self.fromvalue)
            privatedata.vfromvaluecut = 0
            if privatedata.vfromvalue < 0:
                privatedata.vfromvalue = 0
                privatedata.vfromvaluecut = -1
            if privatedata.vfromvalue > 1:
                privatedata.vfromvalue = 1
                privatedata.vfromvaluecut = 1
            if self.frompathattrs is not None and privatedata.insertfrompath:
                graph.layer("data").stroke(graph.axes[valueaxisname].vgridpath(privatedata.vfromvalue),
                                           self.defaultfrompathattrs + self.frompathattrs)
        else:
            privatedata.vfromvalue = 0

    def drawpoint(self, privatedata, sharedata, graph, point):
        if privatedata.autohistogram:
            # automatic range handling
            privatedata.count += 1
            if privatedata.count == 2:
                if privatedata.rangeaxisindex:
                    privatedata.vrange = sharedata.vpos[1] - privatedata.lastvpos[1]
                    self.drawvalue(privatedata, sharedata, graph,
                                   privatedata.lastvpos[1] - self.autohistogrampointpos*privatedata.vrange,
                                   privatedata.lastvpos[1] + (1-self.autohistogrampointpos)*privatedata.vrange,
                                   privatedata.lastvpos[0])
                else:
                    privatedata.vrange = sharedata.vpos[0] - privatedata.lastvpos[0]
                    self.drawvalue(privatedata, sharedata, graph,
                                   privatedata.lastvpos[0] - self.autohistogrampointpos*privatedata.vrange,
                                   privatedata.lastvpos[0] + (1-self.autohistogrampointpos)*privatedata.vrange,
                                   privatedata.lastvpos[1])
            elif privatedata.count > 2:
                if privatedata.rangeaxisindex:
                    vrange = sharedata.vpos[1] - privatedata.lastvpos[1]
                else:
                    vrange = sharedata.vpos[0] - privatedata.lastvpos[0]
                if abs(privatedata.vrange - vrange) > self.epsilon:
                    raise ValueError("equal steps (in graph coordinates) needed for automatic width calculation")
            if privatedata.count > 1:
                if privatedata.rangeaxisindex:
                    self.drawvalue(privatedata, sharedata, graph,
                                   sharedata.vpos[1] - self.autohistogrampointpos*privatedata.vrange,
                                   sharedata.vpos[1] + (1-self.autohistogrampointpos)*privatedata.vrange,
                                   sharedata.vpos[0])
                else:
                    self.drawvalue(privatedata, sharedata, graph,
                                   sharedata.vpos[0] - self.autohistogrampointpos*privatedata.vrange,
                                   sharedata.vpos[0] + (1-self.autohistogrampointpos)*privatedata.vrange,
                                   sharedata.vpos[1])
            privatedata.lastvpos = sharedata.vpos[:]
        else:
            if privatedata.rangeaxisindex:
                self.drawvalue(privatedata, sharedata, graph,
                               sharedata.vrange[1][0], sharedata.vrange[1][1], sharedata.vpos[0])
            else:
                self.drawvalue(privatedata, sharedata, graph,
                               sharedata.vrange[0][0], sharedata.vrange[0][1], sharedata.vpos[1])

    def donedrawpoints(self, privatedata, sharedata, graph):
        self.drawvalue(privatedata, sharedata, graph, None, None, None)
        if privatedata.lineattrs is not None and len(privatedata.path):
           graph.layer("data").draw(privatedata.path, privatedata.lineattrs)

    def key_pt(self, privatedata, sharedata, graph, x_pt, y_pt, width_pt, height_pt):
        if privatedata.lineattrs is not None:
            if self.rectkey:
                p = path.rect_pt(x_pt, y_pt, width_pt, height_pt)
            else:
                p = path.line_pt(x_pt, y_pt+0.5*height_pt, x_pt+width_pt, y_pt+0.5*height_pt)
            graph.draw(p, privatedata.lineattrs)


class barpos(_style):

    providesdata = ["vpos", "vposmissing", "vposavailable", "vposvalid", "vbarrange", "barposcolumnnames", "barvalueindex", "lastbarvalue", "stackedbar", "stackedbardraw"]

    defaultfrompathattrs = []

    def __init__(self, fromvalue=None, frompathattrs=[], epsilon=1e-10):
        self.fromvalue = fromvalue
        self.frompathattrs = frompathattrs
        self.epsilon = epsilon

    def columnnames(self, privatedata, sharedata, graph, columnnames, dataaxisnames):
        sharedata.barposcolumnnames = []
        sharedata.barvalueindex = None
        for dimension, axisnames in enumerate(graph.axesnames):
            found = 0
            for axisname in axisnames:
                if axisname in columnnames:
                    if sharedata.barvalueindex is not None:
                        raise ValueError("multiple values")
                    sharedata.barvalueindex = dimension
                    sharedata.barposcolumnnames.append(axisname)
                    found += 1
                if (axisname + "name") in columnnames:
                    sharedata.barposcolumnnames.append(axisname + "name")
                    found += 1
                if found > 1:
                    raise ValueError("multiple names and value")
            if not found:
                raise ValueError("value/name missing")
        if sharedata.barvalueindex is None:
            raise ValueError("missing value")
        sharedata.vposmissing = []
        return sharedata.barposcolumnnames

    def addsubvalue(self, value, subvalue):
        try:
            value + ""
        except Exception:
            try:
                return value[0], self.addsubvalue(value[1], subvalue)
            except Exception:
                return value, subvalue
        else:
            return value, subvalue

    def adjustaxis(self, privatedata, sharedata, graph, plotitem, columnname, data):
        try:
            i = sharedata.barposcolumnnames.index(columnname)
        except ValueError:
            pass
        else:
            if i == sharedata.barvalueindex:
                if self.fromvalue is not None:
                    graph.axes[sharedata.barposcolumnnames[i]].adjustaxis([self.fromvalue])
                graph.axes[sharedata.barposcolumnnames[i]].adjustaxis(data)
            else:
                graph.axes[sharedata.barposcolumnnames[i][:-4]].adjustaxis([self.addsubvalue(x, 0) for x in data])
                graph.axes[sharedata.barposcolumnnames[i][:-4]].adjustaxis([self.addsubvalue(x, 1) for x in data])

    def selectstyle(self, privatedata, sharedata, graph, selectindex, selecttotal):
        privatedata.insertfrompath = selectindex == 0

    def initdrawpoints(self, privatedata, sharedata, graph):
        sharedata.vpos = [None]*(len(sharedata.barposcolumnnames))
        sharedata.vbarrange = [[None for i in builtinrange(2)] for x in sharedata.barposcolumnnames]
        sharedata.stackedbar = sharedata.stackedbardraw = 0

        if self.fromvalue is not None:
            privatedata.vfromvalue = graph.axes[sharedata.barposcolumnnames[sharedata.barvalueindex]].convert(self.fromvalue)
            if privatedata.vfromvalue < 0:
                privatedata.vfromvalue = 0
            if privatedata.vfromvalue > 1:
                privatedata.vfromvalue = 1
            if self.frompathattrs is not None and privatedata.insertfrompath:
                graph.layer("data").stroke(graph.axes[sharedata.barposcolumnnames[sharedata.barvalueindex]].vgridpath(privatedata.vfromvalue),
                                           self.defaultfrompathattrs + self.frompathattrs)
        else:
            privatedata.vfromvalue = 0

    def drawpoint(self, privatedata, sharedata, graph, point):
        sharedata.vposavailable = sharedata.vposvalid = 1
        for i, barname in enumerate(sharedata.barposcolumnnames):
            if i == sharedata.barvalueindex:
                sharedata.vbarrange[i][0] = privatedata.vfromvalue
                sharedata.lastbarvalue = point[barname]
                try:
                    sharedata.vpos[i] = sharedata.vbarrange[i][1] = graph.axes[barname].convert(sharedata.lastbarvalue)
                except (ArithmeticError, ValueError, TypeError):
                    sharedata.vpos[i] = sharedata.vbarrange[i][1] = None
            else:
                for j in builtinrange(2):
                    try:
                        sharedata.vbarrange[i][j] = graph.axes[barname[:-4]].convert(self.addsubvalue(point[barname], j))
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

registerdefaultprovider(barpos(), ["vbarrange", "barposcolumnnames", "barvalueindex", "lastbarvalue", "stackedbar", "stackedbardraw"])


class stackedbarpos(_style):

    # provides no additional data, but needs some data (and modifies some of them)
    needsdata = ["vbarrange", "barposcolumnnames", "barvalueindex", "lastbarvalue", "stackedbar", "stackedbardraw"]

    def __init__(self, stackname, addontop=0, epsilon=1e-10):
        self.stackname = stackname
        self.epsilon = epsilon
        self.addontop = addontop

    def columnnames(self, privatedata, sharedata, graph, columnnames, dataaxisnames):
        if self.stackname not in columnnames:
            raise ValueError("column '%s' missing" % self.stackname)
        return [self.stackname]

    def adjustaxis(self, privatedata, sharedata, graph, plotitem, columnname, data):
        if columnname == self.stackname:
            graph.axes[sharedata.barposcolumnnames[sharedata.barvalueindex]].adjustaxis(data)

    def initdrawpoints(self, privatedata, sharedata, graph):
        if sharedata.stackedbardraw: # do not count the start bar when not gets painted
            sharedata.stackedbar += 1

    def drawpoint(self, privatedata, sharedata, graph, point):
        sharedata.vbarrange[sharedata.barvalueindex][0] = sharedata.vbarrange[sharedata.barvalueindex][1]
        if self.addontop:
            try:
                sharedata.lastbarvalue += point[self.stackname]
            except (ArithmeticError, ValueError, TypeError):
                sharedata.lastbarvalue = None
        else:
            sharedata.lastbarvalue = point[self.stackname]
        try:
            sharedata.vpos[sharedata.barvalueindex] = sharedata.vbarrange[sharedata.barvalueindex][1] = graph.axes[sharedata.barposcolumnnames[sharedata.barvalueindex]].convert(sharedata.lastbarvalue)
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

    defaultbarattrs = [color.gradient.Rainbow, deco.stroked([color.grey.black])]

    def __init__(self, barattrs=[], epsilon=1e-10, gradient=color.gradient.RedBlack):
        self.barattrs = barattrs
        self.epsilon = epsilon
        self.gradient = gradient

    def lighting(self, angle, zindex):
        return self.gradient.getcolor(0.7-0.4*abs(angle)+0.1*zindex)

    def columnnames(self, privatedata, sharedata, graph, columnnames, dataaxisnames):
        return []

    def selectstyle(self, privatedata, sharedata, graph, selectindex, selecttotal):
        privatedata.barattrs = attr.selectattrs(self.defaultbarattrs + self.barattrs, selectindex, selecttotal)

    def initdrawpoints(self, privatedata, sharedata, graph):
        privatedata.barcanvas = graph.layer("filldata").insert(canvas.canvas())
        sharedata.stackedbardraw = 1
        privatedata.stackedbar = sharedata.stackedbar
        privatedata.todraw = []

    def drawpointfill(self, privatedata, p):
        if p:
            privatedata.barcanvas.fill(p, privatedata.barattrs)

    def drawpoint(self, privatedata, sharedata, graph, point):
        vbarrange = []
        for vmin, vmax in sharedata.vbarrange:
            if vmin is None or vmax is None:
                self.drawpointfill(privatedata, None)
                return
            if vmin > vmax:
                vmin, vmax = vmax, vmin
            if vmin > 1 or vmax < 0:
                self.drawpointfill(privatedata, None)
                return
            if vmin < 0:
                vmin = 0
            if vmax > 1:
                vmax = 1
            vbarrange.append((vmin, vmax))
        if len(vbarrange) == 2:
            p = graph.vgeodesic(vbarrange[0][0], vbarrange[1][0], vbarrange[0][1], vbarrange[1][0])
            p.append(graph.vgeodesic_el(vbarrange[0][1], vbarrange[1][0], vbarrange[0][1], vbarrange[1][1]))
            p.append(graph.vgeodesic_el(vbarrange[0][1], vbarrange[1][1], vbarrange[0][0], vbarrange[1][1]))
            p.append(graph.vgeodesic_el(vbarrange[0][0], vbarrange[1][1], vbarrange[0][0], vbarrange[1][0]))
            p.append(path.closepath())
            self.drawpointfill(privatedata, p)
        elif len(vbarrange) == 3:
            planes = []
            if abs(vbarrange[0][0] - vbarrange[0][1]) > self.epsilon and abs(vbarrange[1][0] - vbarrange[1][1]):
                planes.append((vbarrange[0][0], vbarrange[1][0], vbarrange[2][0],
                               vbarrange[0][1], vbarrange[1][0], vbarrange[2][0],
                               vbarrange[0][1], vbarrange[1][1], vbarrange[2][0],
                               vbarrange[0][0], vbarrange[1][1], vbarrange[2][0]))
                planes.append((vbarrange[0][0], vbarrange[1][0], vbarrange[2][1],
                               vbarrange[0][0], vbarrange[1][1], vbarrange[2][1],
                               vbarrange[0][1], vbarrange[1][1], vbarrange[2][1],
                               vbarrange[0][1], vbarrange[1][0], vbarrange[2][1]))
            if abs(vbarrange[0][0] - vbarrange[0][1]) > self.epsilon and abs(vbarrange[2][0] - vbarrange[2][1]):
                planes.append((vbarrange[0][0], vbarrange[1][0], vbarrange[2][0],
                               vbarrange[0][0], vbarrange[1][0], vbarrange[2][1],
                               vbarrange[0][1], vbarrange[1][0], vbarrange[2][1],
                               vbarrange[0][1], vbarrange[1][0], vbarrange[2][0]))
                planes.append((vbarrange[0][0], vbarrange[1][1], vbarrange[2][0],
                               vbarrange[0][1], vbarrange[1][1], vbarrange[2][0],
                               vbarrange[0][1], vbarrange[1][1], vbarrange[2][1],
                               vbarrange[0][0], vbarrange[1][1], vbarrange[2][1]))
            if abs(vbarrange[1][0] - vbarrange[1][1]) > self.epsilon and abs(vbarrange[2][0] - vbarrange[2][1]):
                planes.append((vbarrange[0][0], vbarrange[1][0], vbarrange[2][0],
                               vbarrange[0][0], vbarrange[1][1], vbarrange[2][0],
                               vbarrange[0][0], vbarrange[1][1], vbarrange[2][1],
                               vbarrange[0][0], vbarrange[1][0], vbarrange[2][1]))
                planes.append((vbarrange[0][1], vbarrange[1][0], vbarrange[2][0],
                               vbarrange[0][1], vbarrange[1][0], vbarrange[2][1],
                               vbarrange[0][1], vbarrange[1][1], vbarrange[2][1],
                               vbarrange[0][1], vbarrange[1][1], vbarrange[2][0]))
            v = [0.5 * (vbarrange[0][0] + vbarrange[0][1]),
                 0.5 * (vbarrange[1][0] + vbarrange[1][1]),
                 0.5 * (vbarrange[2][0] + vbarrange[2][1])]
            v[sharedata.barvalueindex] = 0.5
            zindex = graph.vzindex(*v)
            for v11, v12, v13, v21, v22, v23, v31, v32, v33, v41, v42, v43 in planes:
                angle = graph.vangle(v11, v12, v13, v21, v22, v23, v41, v42, v43)
                if angle > 0:
                    p = graph.vgeodesic(v11, v12, v13, v21, v22, v23)
                    p.append(graph.vgeodesic_el(v21, v22, v23, v31, v32, v33))
                    p.append(graph.vgeodesic_el(v31, v32, v33, v41, v42, v43))
                    p.append(graph.vgeodesic_el(v41, v42, v43, v11, v12, v13))
                    p.append(path.closepath())
                    if self.gradient:
                        privatedata.todraw.append((-zindex, p, privatedata.barattrs + [self.lighting(angle, zindex)]))
                    else:
                        privatedata.todraw.append((-zindex, p, privatedata.barattrs))
        else:
            raise TypeError("bar style restricted to two- and three dimensional graphs")

    def donedrawpoints(self, privatedata, sharedata, graph):
        privatedata.todraw.sort(key=lambda x: x[0])
        for vzindex, p, a in privatedata.todraw:
            privatedata.barcanvas.fill(p, a)

    def key_pt(self, privatedata, sharedata, graph, x_pt, y_pt, width_pt, height_pt):
        selectindex = privatedata.stackedbar
        selecttotal = sharedata.stackedbar + 1
        graph.fill(path.rect_pt(x_pt + width_pt*selectindex/float(selecttotal), y_pt, width_pt/float(selecttotal), height_pt), privatedata.barattrs)


class changebar(bar):

    def selectstyle(self, privatedata, sharedata, graph, selectindex, selecttotal):
        if selecttotal != 1:
            raise RuntimeError("Changebar can't change its appearance. Thus you can't use it to plot several bars side by side on a subaxis.")

    def initdrawpoints(self, privatedata, sharedata, graph):
        if len(graph.axesnames) != 2:
            raise TypeError("changebar style restricted on two-dimensional graphs (at least for the moment)")
        bar.initdrawpoints(self, privatedata, sharedata, graph)
        privatedata.bars = []

    def drawpointfill(self, privatedata, p):
        privatedata.bars.append(p)

    def donedrawpoints(self, privatedata, sharedata, graph):
        selecttotal = len(privatedata.bars)
        for selectindex, p in enumerate(privatedata.bars):
            if p:
                barattrs = attr.selectattrs(self.defaultbarattrs + self.barattrs, selectindex, selecttotal)
                privatedata.barcanvas.fill(p, barattrs)

    def key_pt(self, privatedata, sharedata, graph, x_pt, y_pt, width_pt, height_pt):
        raise RuntimeError("Style currently doesn't provide a graph key")


class gridpos(_style):

    needsdata = ["vpos", "vposmissing", "vposavailable", "vposvalid"]
    providesdata = ["values1", "values2", "data12", "data21", "index1", "index2"]

    def __init__(self, index1=0, index2=1, epsilon=1e-10):
        self.index1 = index1
        self.index2 = index2
        self.epsilon = epsilon

    def initdrawpoints(self, privatedata, sharedata, graph):
        sharedata.index1 = self.index1
        sharedata.index2 = self.index2
        sharedata.values1 = {}
        sharedata.values2 = {}
        sharedata.data12 = {}
        sharedata.data21 = {}

    def drawpoint(self, privatedata, sharedata, graph, point):
        if sharedata.vposavailable:
            sharedata.value1 = sharedata.vpos[self.index1]
            sharedata.value2 = sharedata.vpos[self.index2]
            if sharedata.value1 not in sharedata.values1:
                for hasvalue in list(sharedata.values1.keys()):
                    if hasvalue - self.epsilon <= sharedata.value1 <= hasvalue + self.epsilon:
                        sharedata.value1 = hasvalue
                        break
                else:
                    sharedata.values1[sharedata.value1] = 1
            if sharedata.value2 not in sharedata.values2:
                for hasvalue in list(sharedata.values2.keys()):
                    if hasvalue - self.epsilon <= sharedata.value2 <= hasvalue + self.epsilon:
                        sharedata.value2 = hasvalue
                        break
                else:
                    sharedata.values2[sharedata.value2] = 1
            data = sharedata.vposavailable, sharedata.vposvalid, sharedata.vpos[:]
            sharedata.data12.setdefault(sharedata.value1, {})[sharedata.value2] = data
            sharedata.data21.setdefault(sharedata.value2, {})[sharedata.value1] = data

registerdefaultprovider(gridpos(), gridpos.providesdata)


class grid(_line):

    needsdata = ["values1", "values2", "data12", "data21"]

    defaultgridattrs = [line.changelinestyle]

    def __init__(self, gridlines1=1, gridlines2=1, gridattrs=[], **kwargs):
        _line.__init__(self, **kwargs)
        self.gridlines1 = gridlines1
        self.gridlines2 = gridlines2
        self.gridattrs = gridattrs

    def selectstyle(self, privatedata, sharedata, graph, selectindex, selecttotal):
        if self.gridattrs is not None:
            privatedata.gridattrs = attr.selectattrs(self.defaultgridattrs + self.gridattrs, selectindex, selecttotal)
        else:
            privatedata.gridattrs = None

    def donedrawpoints(self, privatedata, sharedata, graph):
        values1 = list(sharedata.values1.keys())
        values1.sort()
        values2 = list(sharedata.values2.keys())
        values2.sort()
        if self.gridlines1:
            for value2 in values2:
                data1 = sharedata.data21[value2]
                self.initpointstopath(privatedata)
                for value1 in values1:
                    try:
                        data = data1[value1]
                    except KeyError:
                        self.addinvalid(privatedata)
                    else:
                        self.addpoint(privatedata, graph.vpos_pt, *data)
                p = self.donepointstopath(privatedata)
                if len(p):
                    graph.layer("data").stroke(p, privatedata.gridattrs)
        if self.gridlines2:
            for value1 in values1:
                data2 = sharedata.data12[value1]
                self.initpointstopath(privatedata)
                for value2 in values2:
                    try:
                        data = data2[value2]
                    except KeyError:
                        self.addinvalid(privatedata)
                    else:
                        self.addpoint(privatedata, graph.vpos_pt, *data)
                p = self.donepointstopath(privatedata)
                if len(p):
                    graph.layer("data").stroke(p, privatedata.gridattrs)


class surface(_keygraphstyle):

    needsdata = ["values1", "values2", "data12", "data21"]

    def __init__(self, gridlines1=0.05, gridlines2=0.05, gridcolor=None,
                       backcolor=color.gray.black, **kwargs):
        _keygraphstyle.__init__(self, **kwargs)
        self.gridlines1 = gridlines1
        self.gridlines2 = gridlines2
        self.gridcolor = gridcolor
        self.backcolor = backcolor

        colorspacestring = self.gradient.getcolor(0).colorspacestring()
        if self.gridcolor is not None and self.gridcolor.colorspacestring() != colorspacestring:
            raise RuntimeError("colorspace mismatch (gradient/grid)")
        if self.backcolor is not None and self.backcolor.colorspacestring() != colorspacestring:
            raise RuntimeError("colorspace mismatch (gradient/back)")

    def midvalue(self, v1, v2, v3, v4):
        return [0.25*sum(values) for values in zip(v1, v2, v3, v4)]

    def midcolor(self, c1, c2, c3, c4):
        return 0.25*(c1+c2+c3+c4)

    def lighting(self, angle, zindex):
        if angle < 0 and self.backcolor is not None:
            return self.backcolor
        return self.gradient.getcolor(0.7-0.4*abs(angle)+0.1*zindex)

    def columnnames(self, privatedata, sharedata, graph, columnnames, dataaxisnames):
        privatedata.colorize = self.colorname in columnnames
        if privatedata.colorize:
            return _keygraphstyle.columnnames(self, privatedata, sharedata, graph, columnnames, dataaxisnames)
        return []

    def initdrawpoints(self, privatedata, sharedata, graph):
        privatedata.colors = {}

    def drawpoint(self, privatedata, sharedata, graph, point):
        if privatedata.colorize:
            privatedata.colors.setdefault(sharedata.value1, {})[sharedata.value2] = point[self.colorname]

    def donedrawpoints(self, privatedata, sharedata, graph):
        v1 = [0]*len(graph.axesnames)
        v2 = [0]*len(graph.axesnames)
        v3 = [0]*len(graph.axesnames)
        v4 = [0]*len(graph.axesnames)
        v1[sharedata.index2] = 0.5
        v2[sharedata.index1] = 0.5
        v3[sharedata.index1] = 0.5
        v3[sharedata.index2] = 1
        v4[sharedata.index1] = 1
        v4[sharedata.index2] = 0.5
        sortElements = [-graph.vzindex(*v1),
                        -graph.vzindex(*v2),
                        -graph.vzindex(*v3),
                        -graph.vzindex(*v4)]

        values1 = list(sharedata.values1.keys())
        values1.sort()
        v1 = [0]*len(graph.axesnames)
        v2 = [0]*len(graph.axesnames)
        v1[sharedata.index1] = -1
        v2[sharedata.index1] = 1
        sign = 1
        if graph.vzindex(*v1) < graph.vzindex(*v2):
            values1.reverse()
            sign *= -1
            sortElements = [sortElements[3], sortElements[1], sortElements[2], sortElements[0]]

        values2 = list(sharedata.values2.keys())
        values2.sort()
        v1 = [0]*len(graph.axesnames)
        v2 = [0]*len(graph.axesnames)
        v1[sharedata.index2] = -1
        v2[sharedata.index2] = 1
        if graph.vzindex(*v1) < graph.vzindex(*v2):
            values2.reverse()
            sign *= -1
            sortElements = [sortElements[0], sortElements[2], sortElements[1], sortElements[3]]

        sortElements = [(zindex, i) for i, zindex in enumerate(sortElements)]
        sortElements.sort()

        nodes = []
        elements = []
        for value1a, value1b in zip(values1[:-1], values1[1:]):
            for value2a, value2b in zip(values2[:-1], values2[1:]):
                try:
                    available1, valid1, v1 = sharedata.data12[value1a][value2a]
                    available2, valid2, v2 = sharedata.data12[value1a][value2b]
                    available3, valid3, v3 = sharedata.data12[value1b][value2a]
                    available4, valid4, v4 = sharedata.data12[value1b][value2b]
                except KeyError:
                    continue
                if not available1 or not available2 or not available3 or not available4:
                    continue
                if not valid1 or not valid2 or not valid3 or not valid4:
                    logger.warning("surface elements partially outside of the graph are (currently) skipped completely")
                    continue
                def shrink(index, v1, v2, by):
                    v1 = v1[:]
                    v2 = v2[:]
                    for i in builtinrange(3):
                        if i != index:
                            v1[i], v2[i] = v1[i] + by*(v2[i]-v1[i]), v2[i] + by*(v1[i]-v2[i])
                    return v1, v2
                v1f, v2f, v3f, v4f = v1, v2, v3, v4
                if self.gridcolor is not None and self.gridlines1:
                    v1, v2 = shrink(sharedata.index1, v1, v2, self.gridlines1)
                    v3, v4 = shrink(sharedata.index1, v3, v4, self.gridlines1)
                if self.gridcolor is not None and self.gridlines2:
                    v1, v3 = shrink(sharedata.index2, v1, v3, self.gridlines2)
                    v2, v4 = shrink(sharedata.index2, v2, v4, self.gridlines2)
                v5 = self.midvalue(v1, v2, v3, v4)
                x1_pt, y1_pt = graph.vpos_pt(*v1)
                x2_pt, y2_pt = graph.vpos_pt(*v2)
                x3_pt, y3_pt = graph.vpos_pt(*v3)
                x4_pt, y4_pt = graph.vpos_pt(*v4)
                x5_pt, y5_pt = graph.vpos_pt(*v5)
                if privatedata.colorize:
                    c1 = privatedata.colors[value1a][value2a]
                    c2 = privatedata.colors[value1a][value2b]
                    c3 = privatedata.colors[value1b][value2a]
                    c4 = privatedata.colors[value1b][value2b]
                    c5 = self.midcolor(c1, c2, c3, c4)
                    c1a = c1b = self.color(privatedata, c1)
                    c2a = c2c = self.color(privatedata, c2)
                    c3b = c3d = self.color(privatedata, c3)
                    c4c = c4d = self.color(privatedata, c4)
                    c5a = c5b = c5c = c5d = self.color(privatedata, c5)
                    if self.backcolor is not None and sign*graph.vangle(*(v1+v2+v5)) < 0:
                        c1a = c2a = c5a = self.backcolor
                    if self.backcolor is not None and sign*graph.vangle(*(v3+v1+v5)) < 0:
                        c3b = c1b = c5b = self.backcolor
                    if self.backcolor is not None and sign*graph.vangle(*(v2+v4+v5)) < 0:
                        c2c = c4c = c5c = self.backcolor
                    if self.backcolor is not None and sign*graph.vangle(*(v4+v3+v5)) < 0:
                        c4d = c3d = c5d = self.backcolor
                else:
                    zindex = graph.vzindex(*v5)
                    c1a = c2a = c5a = self.lighting(sign*graph.vangle(*(v1+v2+v5)), zindex)
                    c3b = c1b = c5b = self.lighting(sign*graph.vangle(*(v3+v1+v5)), zindex)
                    c2c = c4c = c5c = self.lighting(sign*graph.vangle(*(v2+v4+v5)), zindex)
                    c4d = c3d = c5d = self.lighting(sign*graph.vangle(*(v4+v3+v5)), zindex)
                for zindex, i in sortElements:
                    if i == 0:
                        elements.append(mesh.element((mesh.node_pt((x1_pt, y1_pt), c1a),
                                                      mesh.node_pt((x2_pt, y2_pt), c2a),
                                                      mesh.node_pt((x5_pt, y5_pt), c5a))))
                        if self.gridcolor is not None and self.gridlines2:
                            elements.append(mesh.element((mesh.node_pt(graph.vpos_pt(*v1f), self.gridcolor),
                                                          mesh.node_pt(graph.vpos_pt(*v2), self.gridcolor),
                                                          mesh.node_pt(graph.vpos_pt(*v1), self.gridcolor))))
                            elements.append(mesh.element((mesh.node_pt(graph.vpos_pt(*v1f), self.gridcolor),
                                                          mesh.node_pt(graph.vpos_pt(*v2), self.gridcolor),
                                                          mesh.node_pt(graph.vpos_pt(*v2f), self.gridcolor))))
                    elif i == 1:
                        elements.append(mesh.element((mesh.node_pt((x3_pt, y3_pt), c3b),
                                                      mesh.node_pt((x1_pt, y1_pt), c1b),
                                                      mesh.node_pt((x5_pt, y5_pt), c5b))))
                        if self.gridcolor is not None and self.gridlines1:
                            elements.append(mesh.element((mesh.node_pt(graph.vpos_pt(*v1f), self.gridcolor),
                                                          mesh.node_pt(graph.vpos_pt(*v3), self.gridcolor),
                                                          mesh.node_pt(graph.vpos_pt(*v1), self.gridcolor))))
                            elements.append(mesh.element((mesh.node_pt(graph.vpos_pt(*v1f), self.gridcolor),
                                                          mesh.node_pt(graph.vpos_pt(*v3), self.gridcolor),
                                                          mesh.node_pt(graph.vpos_pt(*v3f), self.gridcolor))))
                    elif i == 2:
                        elements.append(mesh.element((mesh.node_pt((x2_pt, y2_pt), c2c),
                                                      mesh.node_pt((x4_pt, y4_pt), c4c),
                                                      mesh.node_pt((x5_pt, y5_pt), c5c))))
                        if self.gridcolor is not None and self.gridlines1:
                            elements.append(mesh.element((mesh.node_pt(graph.vpos_pt(*v2f), self.gridcolor),
                                                          mesh.node_pt(graph.vpos_pt(*v4), self.gridcolor),
                                                          mesh.node_pt(graph.vpos_pt(*v2), self.gridcolor))))
                            elements.append(mesh.element((mesh.node_pt(graph.vpos_pt(*v2f), self.gridcolor),
                                                          mesh.node_pt(graph.vpos_pt(*v4), self.gridcolor),
                                                          mesh.node_pt(graph.vpos_pt(*v4f), self.gridcolor))))
                    elif i == 3:
                        elements.append(mesh.element((mesh.node_pt((x4_pt, y4_pt), c4d),
                                                      mesh.node_pt((x3_pt, y3_pt), c3d),
                                                      mesh.node_pt((x5_pt, y5_pt), c5d))))
                        if self.gridcolor is not None and self.gridlines2:
                            elements.append(mesh.element((mesh.node_pt(graph.vpos_pt(*v3f), self.gridcolor),
                                                          mesh.node_pt(graph.vpos_pt(*v4), self.gridcolor),
                                                          mesh.node_pt(graph.vpos_pt(*v3), self.gridcolor))))
                            elements.append(mesh.element((mesh.node_pt(graph.vpos_pt(*v3f), self.gridcolor),
                                                          mesh.node_pt(graph.vpos_pt(*v4), self.gridcolor),
                                                          mesh.node_pt(graph.vpos_pt(*v4f), self.gridcolor))))
        m = mesh.mesh(elements, check=0)
        graph.layer("filldata").insert(m)

        if privatedata.colorize:
            _keygraphstyle.donedrawpoints(self, privatedata, sharedata, graph)


class density(_keygraphstyle):

    needsdata = ["values1", "values2", "data12", "data21"]

    def __init__(self, epsilon=1e-10, **kwargs):
        _keygraphstyle.__init__(self, **kwargs)
        self.epsilon = epsilon

    def initdrawpoints(self, privatedata, sharedata, graph):
        privatedata.colors = {}
        privatedata.vfixed = [None]*len(graph.axesnames)

    def drawpoint(self, privatedata, sharedata, graph, point):
        privatedata.colors.setdefault(sharedata.value1, {})[sharedata.value2] = point[self.colorname]
        if len(privatedata.vfixed) > 2 and sharedata.vposavailable:
            for i, (v1, v2) in enumerate(list(zip(privatedata.vfixed, sharedata.vpos))):
                if i != sharedata.index1 and i != sharedata.index2:
                    if v1 is None:
                        privatedata.vfixed[i] = v2
                    elif abs(v1-v2) > self.epsilon:
                        raise ValueError("data must be in a plane for the density style")

    def donedrawpoints(self, privatedata, sharedata, graph):
        privatedata.keygraph.doaxes()

        values1 = sorted(list(sharedata.values1.keys()))
        values2 = sorted(list(sharedata.values2.keys()))
        def equidistant(values):
            l = len(values) - 1
            if l < 1:
                raise ValueError("several data points required by the density style in each dimension")
            range = values[-1] - values[0]
            for i, value in enumerate(values):
                if abs(value - values[0] - i * range / l) > self.epsilon:
                    raise ValueError("data must be equidistant for the density style")
        equidistant(values1)
        equidistant(values2)
        needalpha = False
        for value2 in values2:
            for value1 in values1:
                try:
                    available, valid, v = sharedata.data12[value1][value2]
                except KeyError:
                    needalpha = True
                    break
                if not available:
                    needalpha = True
                    break
                try:
                    self.color(privatedata, privatedata.colors[value1][value2])
                except (ArithmeticError, ValueError, TypeError):
                    needalpha = True
                    break
            else:
                continue
            break
        mode = {"/DeviceGray": "L",
                "/DeviceRGB": "RGB",
                "/DeviceCMYK": "CMYK"}[self.gradient.getcolor(0).colorspacestring()]
        if needalpha:
            mode = mode + "A"
        empty = b"\0"*len(mode)
        data = io.BytesIO()
        for value2 in values2:
            for value1 in values1:
                try:
                    available, valid, v = sharedata.data12[value1][value2]
                except KeyError:
                    data.write(empty)
                    continue
                if not available:
                    data.write(empty)
                    continue
                c = privatedata.colors[value1][value2]
                try:
                    c = self.color(privatedata, c)
                except (ArithmeticError, ValueError, TypeError):
                    data.write(empty)
                    continue

                data.write(c.to8bitbytes())
                if needalpha:
                    data.write(bytes((255,)))
        i = bitmap.image(len(values1), len(values2), mode, data.getvalue())

        v1enlargement = (values1[-1]-values1[0])*0.5/(len(values1)-1)
        v2enlargement = (values2[-1]-values2[0])*0.5/(len(values2)-1)

        privatedata.vfixed[sharedata.index1] = values1[0]-v1enlargement
        privatedata.vfixed[sharedata.index2] = values2[-1]+v2enlargement
        x1_pt, y1_pt = graph.vpos_pt(*privatedata.vfixed)
        privatedata.vfixed[sharedata.index1] = values1[-1]+v1enlargement
        privatedata.vfixed[sharedata.index2] = values2[-1]+v2enlargement
        x2_pt, y2_pt = graph.vpos_pt(*privatedata.vfixed)
        privatedata.vfixed[sharedata.index1] = values1[0]-v1enlargement
        privatedata.vfixed[sharedata.index2] = values2[0]-v2enlargement
        x3_pt, y3_pt = graph.vpos_pt(*privatedata.vfixed)
        t = trafo.trafo_pt(((x2_pt-x1_pt, x3_pt-x1_pt), (y2_pt-y1_pt, y3_pt-y1_pt)), (x1_pt, y1_pt))

        privatedata.vfixed[sharedata.index1] = values1[-1]+v1enlargement
        privatedata.vfixed[sharedata.index2] = values2[0]-v2enlargement
        vx4, vy4 = t.inverse().apply_pt(*graph.vpos_pt(*privatedata.vfixed))
        if abs(vx4 - 1) > self.epsilon or abs(vy4 - 1) > self.epsilon:
            raise ValueError("invalid graph layout for density style (bitmap positioning by affine transformation failed)")

        p = path.path()
        privatedata.vfixed[sharedata.index1] = 0
        privatedata.vfixed[sharedata.index2] = 0
        p.append(path.moveto_pt(*graph.vpos_pt(*privatedata.vfixed)))
        vfixed2 = privatedata.vfixed + privatedata.vfixed
        vfixed2[sharedata.index1] = 0
        vfixed2[sharedata.index2] = 0
        vfixed2[sharedata.index1 + len(graph.axesnames)] = 1
        vfixed2[sharedata.index2 + len(graph.axesnames)] = 0
        p.append(graph.vgeodesic_el(*vfixed2))
        vfixed2[sharedata.index1] = 1
        vfixed2[sharedata.index2] = 0
        vfixed2[sharedata.index1 + len(graph.axesnames)] = 1
        vfixed2[sharedata.index2 + len(graph.axesnames)] = 1
        p.append(graph.vgeodesic_el(*vfixed2))
        vfixed2[sharedata.index1] = 1
        vfixed2[sharedata.index2] = 1
        vfixed2[sharedata.index1 + len(graph.axesnames)] = 0
        vfixed2[sharedata.index2 + len(graph.axesnames)] = 1
        p.append(graph.vgeodesic_el(*vfixed2))
        vfixed2[sharedata.index1] = 0
        vfixed2[sharedata.index2] = 1
        vfixed2[sharedata.index1 + len(graph.axesnames)] = 0
        vfixed2[sharedata.index2 + len(graph.axesnames)] = 0
        p.append(graph.vgeodesic_el(*vfixed2))
        p.append(path.closepath())

        c = canvas.canvas([canvas.clip(p)])
        b = bitmap.bitmap_trafo(t, i)
        c.insert(b)
        graph.layer("filldata").insert(c)

        _keygraphstyle.donedrawpoints(self, privatedata, sharedata, graph)



class gradient(_style):

    defaultbarattrs = [color.gradient.Rainbow, deco.stroked([color.grey.black])]

    def __init__(self, gradient=color.gradient.Gray, resolution=100, columnname="x"):
        self.gradient = gradient
        self.resolution = resolution
        self.columnname = columnname

    def columnnames(self, privatedata, sharedata, graph, columnnames, dataaxisnames):
        return [self.columnname]

    def adjustaxis(self, privatedata, sharedata, graph, plotitem, columnname, data):
        graph.axes[self.columnname].adjustaxis(data)

    def selectstyle(self, privatedata, sharedata, graph, selectindex, selecttotal):
        pass

    def initdrawpoints(self, privatedata, sharedata, graph):
        pass

    def drawpoint(self, privatedata, sharedata, graph, point):
        pass

    def donedrawpoints(self, privatedata, sharedata, graph):
        mode = {"/DeviceGray": "L",
                "/DeviceRGB": "RGB",
                "/DeviceCMYK": "CMYK"}[self.gradient.getcolor(0).colorspacestring()]
        data = io.BytesIO()
        for i in builtinrange(self.resolution):
            c = self.gradient.getcolor(i*1.0/self.resolution)
            data.write(c.to8bitbytes())
        i = bitmap.image(self.resolution, 1, mode, data.getvalue())

        llx_pt, lly_pt = graph.vpos_pt(0)
        urx_pt, ury_pt = graph.vpos_pt(1)

        if graph.direction == "horizontal":
            lly_pt -= 0.5*graph.height_pt
            ury_pt += 0.5*graph.height_pt
        else:
            llx_pt -= 0.5*graph.width_pt
            urx_pt += 0.5*graph.width_pt

        c = canvas.canvas([canvas.clip(path.rect_pt(llx_pt, lly_pt, urx_pt-llx_pt, ury_pt-lly_pt))])

        if graph.direction == "horizontal":
            add_pt = (urx_pt-llx_pt)*0.5/(self.resolution-1)
            llx_pt -= add_pt
            urx_pt += add_pt
        else:
            add_pt = (ury_pt-lly_pt)*0.5/(self.resolution-1)
            lly_pt -= add_pt
            ury_pt += add_pt

        if graph.direction == "horizontal":
            t = trafo.trafo_pt(((urx_pt-llx_pt,0 ), (0, ury_pt-lly_pt)), (llx_pt, lly_pt))
        else:
            t = trafo.trafo_pt(((0, urx_pt-llx_pt), (ury_pt-lly_pt, 0)), (llx_pt, lly_pt))

        b = bitmap.bitmap_trafo(t, i)
        c.insert(b)
        graph.layer("filldata").insert(c)
