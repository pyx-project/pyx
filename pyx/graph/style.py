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


import re, math
from pyx import attr, deco, style, color, unit, canvas, path
from pyx import text as textmodule


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
        if data.lineattrs is not None:
            # TODO: bbox shortcut
            linecanvas = graph.insert(canvas.canvas())
        if data.errorbarattrs is not None:
            # TODO: bbox shortcut
            errorbarcanvas = graph.insert(canvas.canvas())
        data.path = path.path()
        linebasepoints = []
        lastvpos = None
        errorlist = []
        if data.errorbarattrs is not None:
            axisindex = 0
            for axisname in graph.axisnames:
                if data.index[axisname].keys() != ["x"]:
                    errorlist.append((axisname, axisindex))
                axisindex += 1

        for point in data.points:
            # calculate vpos
            vpos = [] # list containing the graph coordinates of the point
            validvpos = 1 # valid position (but might be outside of the graph)
            drawsymbol = 1 # valid position inside the graph
            for axisname in graph.axisnames:
                try:
                    v = data.axes[axisname].convert(point[data.index[axisname]["x"]])
                except:
                    validvpos = 0
                    drawsymbol = 0
                    vpos.append(None)
                else:
                    if v < - self.epsilon or v > 1 + self.epsilon:
                        drawsymbol = 0
                    vpos.append(v)

            # draw symbol
            if drawsymbol:
                xpos, ypos = graph.vpos_pt(*vpos)
                self.drawsymbol_pt(graph, xpos, ypos, data, point=point)

            # append linebasepoints
            if validvpos:
                if len(linebasepoints):
                    # the last point was inside the graph
                    if drawsymbol:
                        linebasepoints.append((xpos, ypos))
                    else:
                        # cut end
                        cut = 1
                        for vstart, vend in zip(lastvpos, vpos):
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
                        for vstart, vend in zip(lastvpos, vpos):
                            cutvpos.append(vstart + (vend - vstart) * cut)
                        linebasepoints.append(graph.vpos_pt(*cutvpos))
                        validvpos = 0 # clear linebasepoints below
                else:
                    # the last point was outside the graph
                    if lastvpos is not None:
                        if drawsymbol:
                            # cut beginning
                            cut = 0
                            for vstart, vend in zip(lastvpos, vpos):
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
                            for vstart, vend in zip(lastvpos, vpos):
                                cutvpos.append(vstart + (vend - vstart) * cut)
                            linebasepoints.append(graph.vpos_pt(*cutvpos))
                            linebasepoints.append(graph.vpos_pt(*vpos))
                        else:
                            # sometimes cut beginning and end
                            cutfrom = 0
                            cutto = 1
                            for vstart, vend in zip(lastvpos, vpos):
                                newcutfrom = None
                                if vstart > 1:
                                    # 1 = vstart + (vend - vstart) * cutfrom
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
                            if cutfrom < cutto:
                                cutfromvpos = []
                                cuttovpos = []
                                for vstart, vend in zip(lastvpos, vpos):
                                    cutfromvpos.append(vstart + (vend - vstart) * cutfrom)
                                    cuttovpos.append(vstart + (vend - vstart) * cutto)
                                linebasepoints.append(graph.vpos_pt(*cutfromvpos))
                                linebasepoints.append(graph.vpos_pt(*cuttovpos))
                                validvpos = 0 # clear linebasepoints below
                lastvpos = vpos
            else:
                lastvpos = None

            if not validvpos:
                # add baselinepoints to data.path
                if len(linebasepoints) > 1:
                    data.path.append(path.moveto_pt(*linebasepoints[0]))
                    if len(linebasepoints) > 2:
                        data.path.append(path.multilineto_pt(linebasepoints[1:]))
                    else:
                        data.path.append(path.lineto_pt(*linebasepoints[1]))
                linebasepoints = []

            # errorbar loop over the different direction having errorbars
            for erroraxisname, erroraxisindex in errorlist:

                # check for validity of other point components
                i = 0
                for v in vpos:
                    if v is None and i != erroraxisindex:
                        break
                    i += 1
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
                        errorbarcanvas.stroke(errorpath, data.errorbarattrs)

        # add baselinepoints to data.path
        if len(linebasepoints) > 1:
            data.path.append(path.moveto_pt(*linebasepoints[0]))
            if len(linebasepoints) > 2:
                data.path.append(path.multilineto_pt(linebasepoints[1:]))
            else:
                data.path.append(path.lineto_pt(*linebasepoints[1]))

        # stroke data.path
        if data.lineattrs is not None:
            linecanvas.stroke(data.path, data.lineattrs)

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

    def drawpoints(self, graph, data):
        data.textdx = unit.length(self.textdx_str, default_type="v")
        data.textdy = unit.length(self.textdy_str, default_type="v")
        data.textdx_pt = unit.topt(data.textdx)
        data.textdy_pt = unit.topt(data.textdy)
        symbol.drawpoints(self, graph, data)


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


class rect(_style):

    def __init__(self, palette=color.palette.Gray):
        self.palette = palette

    def setdata(self, graph, columns, data):
        if len(graph.axisnames) != 2:
            raise TypeError("arrow style restricted on two-dimensional graphs")
        columns = columns.copy()
        data.xaxis, data.xminindex = _style.setdatapattern(self, graph, columns, re.compile(r"(%s([2-9]|[1-9][0-9]+)?)min$" % graph.axisnames[0]))
        data.yaxis, data.yminindex = _style.setdatapattern(self, graph, columns, re.compile(r"(%s([2-9]|[1-9][0-9]+)?)min$" % graph.axisnames[1]))
        xaxis, data.xmaxindex = _style.setdatapattern(self, graph, columns, re.compile(r"(%s([2-9]|[1-9][0-9]+)?)max$" % graph.axisnames[0]))
        yaxis, data.ymaxindex = _style.setdatapattern(self, graph, columns, re.compile(r"(%s([2-9]|[1-9][0-9]+)?)max$" % graph.axisnames[1]))
        if xaxis != data.xaxis or yaxis != data.yaxis:
            raise ValueError("min/max values should use the same axes")
        data.colorindex = columns["color"]
        del columns["color"]
        return columns

    def selectstyle(self, selectindex, selecttotal, data):
        pass

    def adjustaxes(self, columns, data):
        if data.xminindex in columns:
            data.xaxis.adjustrange(data.points, data.xminindex)
        if data.xmaxindex in columns:
            data.xaxis.adjustrange(data.points, data.xmaxindex)
        if data.yminindex in columns:
            data.yaxis.adjustrange(data.points, data.yminindex)
        if data.ymaxindex in columns:
            data.yaxis.adjustrange(data.points, data.ymaxindex)

    def drawpoints(self, graph, data):
        # TODO: bbox shortcut
        c = graph.insert(canvas.canvas())
        lastcolorvalue = None
        for point in data.points:
            try:
                xvmin = data.xaxis.convert(point[data.xminindex])
                xvmax = data.xaxis.convert(point[data.xmaxindex])
                yvmin = data.yaxis.convert(point[data.yminindex])
                yvmax = data.yaxis.convert(point[data.ymaxindex])
                colorvalue = point[data.colorindex]
                if colorvalue != lastcolorvalue:
                    color = self.palette.getcolor(point[data.colorindex])
            except:
                continue
            if ((xvmin < 0 and xvmax < 0) or (xvmin > 1 and xvmax > 1) or
                (yvmin < 0 and yvmax < 0) or (yvmin > 1 and yvmax > 1)):
                continue
            if xvmin < 0:
                xvmin = 0
            elif xvmin > 1:
                xvmin = 1
            if xvmax < 0:
                xvmax = 0
            elif xvmax > 1:
                xvmax = 1
            if yvmin < 0:
                yvmin = 0
            elif yvmin > 1:
                yvmin = 1
            if yvmax < 0:
                yvmax = 0
            elif yvmax > 1:
                yvmax = 1
            p = graph.vgeodesic(xvmin, yvmin, xvmax, yvmin)
            p.append(graph.vgeodesic_el(xvmax, yvmin, xvmax, yvmax))
            p.append(graph.vgeodesic_el(xvmax, yvmax, xvmin, yvmax))
            p.append(graph.vgeodesic_el(xvmin, yvmax, xvmin, yvmin))
            p.append(path.closepath())
            if colorvalue != lastcolorvalue:
                c.set([color])
            c.fill(p)

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
        i = 1
        while 1:
            try:
                valueaxis, valueindex = _style.setdatapattern(self, graph, columns, re.compile(r"(%s([2-9]|[1-9][0-9]+)?)stack%i$" % (graph.axisnames[data.valuepos], i)))
            except:
                break
            if data.valueaxis != valueaxis:
                raise ValueError("different value axes for stacked bars")
            data.valueindices.append(valueindex)
            i += 1
        return columns

    def selectstyle(self, selectindex, selecttotal, data):
        if selectindex:
            data.frompathattrs = None
        else:
            data.frompathattrs = self.defaultfrompathattrs + self.frompathattrs
        if selecttotal > 1:
            if self.barattrs is not None:
                data.barattrs = attr.selectattrs(self.defaultbarattrs + self.barattrs, selectindex, selecttotal)
            else:
                data.barattrs = None
        else:
            data.barattrs = self.defaultbarattrs + self.barattrs
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
                    p = graph.vgeodesic(vnamemin, vvaluemin, vnamemin, vvaluemax)
                    p.append(graph.vgeodesic_el(vnamemin, vvaluemax, vnamemax, vvaluemax))
                    p.append(graph.vgeodesic_el(vnamemax, vvaluemax, vnamemax, vvaluemin))
                    p.append(graph.vgeodesic_el(vnamemax, vvaluemin, vnamemin, vvaluemin))
                    p.append(path.closepath())
                else:
                    p = graph.vgeodesic(vvaluemin, vnamemin, vvaluemin, vnamemax)
                    p.append(graph.vgeodesic_el(vvaluemin, vnamemax, vvaluemax, vnamemax))
                    p.append(graph.vgeodesic_el(vvaluemax, vnamemax, vvaluemax, vnamemin))
                    p.append(graph.vgeodesic_el(vvaluemax, vnamemin, vvaluemin, vnamemin))
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
