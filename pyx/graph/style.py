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

    def key_pt(self, c, x_pt, y_pt, width_pt, height_pt, styledata):
        raise RuntimeError("style doesn't provide a key")

    def adjustaxes(self, points, columns, styledata):
        return

    def setdata(self, graph, columns, styledata):
        return columns

    def selectstyle(self, selectindex, selecttotal, styledata):
        pass

    def initdrawpoints(self, graph, styledata):
        pass

    def drawpoint(self, graph, styledata):
        pass

    def donedrawpoints(self, graph, styledata):
        pass


class pointpos(_style):

    def __init__(self, epsilon=1e-10):
        self.epsilon = epsilon

    def setdata(self, graph, columns, styledata):
        # analyse column information
        styledata.pointposaxisindex = []
        columns = columns.copy()
        for axisname in graph.axisnames:
            pattern = re.compile(r"(%s([2-9]|[1-9][0-9]+)?)$" % axisname)
            styledata.pointposaxisindex.append(self.setdatapattern(graph, columns, pattern)) # TODO: append "needed=1"
        return columns

    def adjustaxes(self, points, columns, styledata):
        for axis, index in styledata.pointposaxisindex:
            axis.adjustrange(points, index)

    def drawpoint(self, graph, styledata):
        # calculate vpos
        styledata.validvpos = 1 # valid position (but might be outside of the graph)
        styledata.drawsymbol = 1 # valid position inside the graph
        styledata.vpos = [axis.convert(styledata.point[index]) for axis, index in styledata.pointposaxisindex]
        # for axisname in graph.axisnames:
        #     try:
        #         v = styledata.axes[axisname].convert(styledata.point[styledata.index[axisname]["x"]])
        #     except (ArithmeticError, KeyError, ValueError, TypeError):
        #         styledata.validvpos = 0
        #         styledata.drawsymbol = 0
        #         styledata.vpos.append(None)
        #     else:
        #         if v < - self.epsilon or v > 1 + self.epsilon:
        #             styledata.drawsymbol = 0
        #         styledata.vpos.append(v)


class rangepos(_style):

    def setdata(self, graph, columns, styledata):
        """
        - the instance should be considered read-only
          (it might be shared between several data)
        - styledata is the place where to store information
        - returns the dictionary of columns not used by the style"""

        # analyse column information
        styledata.index = {} # a nested index dictionary containing
                        # column numbers, e.g. styledata.index["x"]["x"],
                        # styledata.index["y"]["dmin"] etc.; the first key is a axis
                        # name (without the axis number), the second is one of
                        # the datanames ["x", "min", "max", "d", "dmin", "dmax"]
        styledata.axes = {}  # mapping from axis name (without axis number) to the axis

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
                    if styledata.axes.has_key(axisname):
                        if styledata.axes[axisname] != axis:
                            raise ValueError("axis mismatch for axis name '%s'" % axisname)
                        styledata.index[axisname][dataname] = index
                    else:
                        styledata.index[axisname] = {dataname: index}
                        styledata.axes[axisname] = axis
            if not styledata.axes.has_key(axisname):
                raise ValueError("missing columns for axis name '%s'" % axisname)
            if ((styledata.index[axisname].has_key("min") and styledata.index[axisname].has_key("d")) or
                (styledata.index[axisname].has_key("min") and styledata.index[axisname].has_key("dmin")) or
                (styledata.index[axisname].has_key("d") and styledata.index[axisname].has_key("dmin")) or
                (styledata.index[axisname].has_key("max") and styledata.index[axisname].has_key("d")) or
                (styledata.index[axisname].has_key("max") and styledata.index[axisname].has_key("dmax")) or
                (styledata.index[axisname].has_key("d") and styledata.index[axisname].has_key("dmax"))):
                raise ValueError("multiple errorbar definition for axis name '%s'" % axisname)
            if (not styledata.index[axisname].has_key("x") and
                (styledata.index[axisname].has_key("d") or
                 styledata.index[axisname].has_key("dmin") or
                 styledata.index[axisname].has_key("dmax"))):
                raise ValueError("errorbar definition start value missing for axis name '%s'" % axisname)
        return columns

    def adjustaxes(self, points, columns, styledata):
        # reverse lookup for axisnames
        # TODO: the reverse lookup is ugly
        axisnames = []
        for column in columns:
            for axisname in styledata.index.keys():
                for thiscolumn in styledata.index[axisname].values():
                    if thiscolumn == column and axisname not in axisnames:
                        axisnames.append(axisname)
        # TODO: perform check to verify that all columns for a given axisname are available at the same time
        for axisname in axisnames:
            if styledata.index[axisname].has_key("x"):
                styledata.axes[axisname].adjustrange(points, styledata.index[axisname]["x"])
            if styledata.index[axisname].has_key("min"):
                styledata.axes[axisname].adjustrange(points, styledata.index[axisname]["min"])
            if styledata.index[axisname].has_key("max"):
                styledata.axes[axisname].adjustrange(points, styledata.index[axisname]["max"])
            if styledata.index[axisname].has_key("d"):
                styledata.axes[axisname].adjustrange(points, styledata.index[axisname]["x"], deltaindex=styledata.index[axisname]["d"])
            if styledata.index[axisname].has_key("dmin"):
                styledata.axes[axisname].adjustrange(points, styledata.index[axisname]["x"], deltaminindex=styledata.index[axisname]["dmin"])
            if styledata.index[axisname].has_key("dmax"):
                styledata.axes[axisname].adjustrange(points, styledata.index[axisname]["x"], deltamaxindex=styledata.index[axisname]["dmax"])

    def doerrorbars(self, styledata):
        # errorbar loop over the different direction having errorbars
        for erroraxisname, erroraxisindex in styledata.errorlist:

            # check for validity of other point components
            i = 0
            for v in styledata.vpos:
                if v is None and i != erroraxisindex:
                    break
                i += 1
            else:
                # calculate min and max
                errorindex = styledata.index[erroraxisname]
                try:
                    min = styledata.point[errorindex["x"]] - styledata.point[errorindex["d"]]
                except:
                    try:
                        min = styledata.point[errorindex["x"]] - styledata.point[errorindex["dmin"]]
                    except:
                        try:
                            min = styledata.point[errorindex["min"]]
                        except:
                            min = None
                try:
                    max = styledata.point[errorindex["x"]] + styledata.point[errorindex["d"]]
                except:
                    try:
                        max = styledata.point[errorindex["x"]] + styledata.point[errorindex["dmax"]]
                    except:
                        try:
                            max = styledata.point[errorindex["max"]]
                        except:
                            max = None

                # calculate vmin and vmax
                try:
                    vmin = styledata.axes[erroraxisname].convert(min)
                except:
                    vmin = None
                try:
                    vmax = styledata.axes[erroraxisname].convert(max)
                except:
                    vmax = None

                # create vminpos and vmaxpos
                vcaps = []
                if vmin is not None:
                    vminpos = styledata.vpos[:]
                    if vmin > - self.epsilon and vmin < 1 + self.epsilon:
                        vminpos[erroraxisindex] = vmin
                        vcaps.append(vminpos)
                    else:
                        vminpos[erroraxisindex] = 0
                elif styledata.vpos[erroraxisindex] is not None:
                    vminpos = styledata.vpos
                else:
                    break
                if vmax is not None:
                    vmaxpos = styledata.vpos[:]
                    if vmax > - self.epsilon and vmax < 1 + self.epsilon:
                        vmaxpos[erroraxisindex] = vmax
                        vcaps.append(vmaxpos)
                    else:
                        vmaxpos[erroraxisindex] = 1
                elif styledata.vpos[erroraxisindex] is not None:
                    vmaxpos = styledata.vpos
                else:
                    break


class symbol(_style):

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

    defaultsymbolattrs = [deco.stroked]

    def __init__(self, symbol=changecross,
                       size=0.2*unit.v_cm,
                       symbolattrs=[],
                       epsilon=1e-10):
        self.symbol = symbol
        self.size = size
        self.symbolattrs = symbolattrs
        self.epsilon = epsilon

    def selectstyle(self, selectindex, selecttotal, styledata):
        styledata.symbol = attr.selectattr(self.symbol, selectindex, selecttotal)
        styledata.size_pt = unit.topt(attr.selectattr(self.size, selectindex, selecttotal))
        if self.symbolattrs is not None:
            styledata.symbolattrs = attr.selectattrs(self.defaultsymbolattrs + self.symbolattrs, selectindex, selecttotal)
        else:
            styledata.symbolattrs = None

    def drawsymbol_pt(self, c, x_pt, y_pt, styledata, point=None):
        if styledata.symbolattrs is not None:
            c.draw(path.path(*styledata.symbol(self, x_pt, y_pt, styledata.size_pt)), styledata.symbolattrs)

    def drawpoint(self, graph, styledata):
        if styledata.drawsymbol:
            styledata.xpos, styledata.ypos = graph.vpos_pt(*styledata.vpos)
            self.drawsymbol_pt(graph, styledata.xpos, styledata.ypos, styledata, point=styledata.point)

    def key_pt(self, c, x_pt, y_pt, width_pt, height_pt, styledata):
        self.drawsymbol_pt(c, x_pt+0.5*width_pt, y_pt+0.5*height_pt, styledata)
#        if styledata.lineattrs is not None:
#            c.stroke(path.line_pt(x_pt, y_pt+0.5*height_pt, x_pt+width_pt, y_pt+0.5*height_pt), styledata.lineattrs)


class line(_style):

    changelinestyle = attr.changelist([style.linestyle.solid,
                                       style.linestyle.dashed,
                                       style.linestyle.dotted,
                                       style.linestyle.dashdotted])

    defaultlineattrs = [changelinestyle]

    def __init__(self, lineattrs=[]):
        self.lineattrs = lineattrs

    def selectstyle(self, selectindex, selecttotal, styledata):
        styledata.lineattrs = attr.selectattrs(self.defaultlineattrs + self.lineattrs, selectindex, selecttotal)

    def initdrawpoints(self, graph, styledata):
        styledata.linecanvas = graph.insert(canvas.canvas())
        styledata.path = path.path()
        styledata.linebasepoints = []
        styledata.lastvpos = None

    def appendlinebasepoints(self, graph, styledata):
        # append linebasepoints
        if styledata.validvpos:
            if len(styledata.linebasepoints):
                # the last point was inside the graph
                if styledata.drawsymbol: # this is wrong
                    # we always need the following line here:
                    styledata.xpos, styledata.ypos = graph.vpos_pt(*styledata.vpos)
                    styledata.linebasepoints.append((styledata.xpos, styledata.ypos))
                else:
                    # cut end
                    cut = 1
                    for vstart, vend in zip(styledata.lastvpos, styledata.vpos):
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
                        for vstart, vend in zip(styledata.lastvpos, styledata.vpos):
                            cutvpos.append(vstart + (vend - vstart) * cut)
                        styledata.linebasepoints.append(styledata.graph.vpos_pt(*cutvpos))
                        styledata.validvpos = 0 # clear linebasepoints below
            else:
                # the last point was outside the graph
                if styledata.lastvpos is not None:
                    if styledata.drawsymbol:
                        # cut beginning
                        cut = 0
                        for vstart, vend in zip(styledata.lastvpos, styledata.vpos):
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
                            for vstart, vend in zip(styledata.lastvpos, styledata.vpos):
                                cutvpos.append(vstart + (vend - vstart) * cut)
                            styledata.linebasepoints.append(graph.vpos_pt(*cutvpos))
                            styledata.linebasepoints.append(graph.vpos_pt(*styledata.vpos))
                    else:
                        # sometimes cut beginning and end
                        cutfrom = 0
                        cutto = 1
                        for vstart, vend in zip(styledata.lastvpos, styledata.vpos):
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
                                for vstart, vend in zip(styledata.lastvpos, styledata.vpos):
                                    cutfromvpos.append(vstart + (vend - vstart) * cutfrom)
                                    cuttovpos.append(vstart + (vend - vstart) * cutto)
                                styledata.linebasepoints.append(styledata.graph.vpos_pt(*cutfromvpos))
                                styledata.linebasepoints.append(styledata.graph.vpos_pt(*cuttovpos))
                        styledata.validvpos = 0 # clear linebasepoints below
            styledata.lastvpos = styledata.vpos
        else:
            styledata.lastvpos = None

    def addpointstopath(self, styledata):
        # add baselinepoints to styledata.path
        if len(styledata.linebasepoints) > 1:
            styledata.path.append(path.moveto_pt(*styledata.linebasepoints[0]))
            if len(styledata.linebasepoints) > 2:
                styledata.path.append(path.multilineto_pt(styledata.linebasepoints[1:]))
            else:
                styledata.path.append(path.lineto_pt(*styledata.linebasepoints[1]))
        styledata.linebasepoints = []

    def donedrawpoints(self, graph, styledata):
        self.addpointstopath(styledata)
        if styledata.lineattrs is not None and len(styledata.path.path):
            styledata.linecanvas.stroke(styledata.path, styledata.lineattrs)

    def drawpoint(self, graph, styledata):
        self.appendlinebasepoints(graph, styledata)
        if not styledata.validvpos:
            self.addpointstopath(styledata)


class errorbars(_style):

    defaulterrorbarattrs = []

    def __init__(self, size=0.1*unit.v_cm,
                       errorbarattrs=[],
                       epsilon=1e-10):
        self.size = size
        self.errorbarattrs = errorbarattrs
        self.epsilon = epsilon

    def selectstyle(self, selectindex, selecttotal, styledata):
        styledata.errorsize_pt = unit.topt(attr.selectattr(self.size, selectindex, selecttotal))
        styledata.errorbarattrs = attr.selectattrs(self.defaulterrorbarattrs + self.errorbarattrs, selectindex, selecttotal)

    def initdrawpoints(self, graph, styledata):
        styledata.errorbarcanvas = graph.insert(canvas.canvas())
        styledata.errorlist = []
        if styledata.errorbarattrs is not None:
            axisindex = 0
            for axisname in graph.axisnames:
                if styledata.index[axisname].keys() != ["x"]:
                    styledata.errorlist.append((axisname, axisindex))
                axisindex += 1

    def doerrorbars(self, styledata):
        # errorbar loop over the different direction having errorbars
        for erroraxisname, erroraxisindex in styledata.errorlist:
                # create path for errorbars
                errorpath = path.path()
                errorpath += styledata.graph.vgeodesic(*(vminpos + vmaxpos))
                for vcap in vcaps:
                    for axisname in styledata.graph.axisnames:
                        if axisname != erroraxisname:
                            errorpath += styledata.graph.vcap_pt(axisname, styledata.errorsize_pt, *vcap)

                # stroke errorpath
                if len(errorpath.path):
                    styledata.errorbarcanvas.stroke(errorpath, styledata.errorbarattrs)

    def drawpoint(self, graph, styledata):
        self.doerrorbars(styledata)


class text(symbol):

    defaulttextattrs = [textmodule.halign.center, textmodule.vshift.mathaxis]

    def __init__(self, textdx=0*unit.v_cm, textdy=0.3*unit.v_cm, textattrs=[], **kwargs):
        self.textdx = textdx
        self.textdy = textdy
        self.textattrs = textattrs
        symbol.__init__(self, **kwargs)

    def setdata(self, graph, columns, styledata):
        columns = columns.copy()
        styledata.textindex = columns["text"]
        del columns["text"]
        return symbol.setdata(self, graph, columns, styledata)

    def selectstyle(self, selectindex, selecttotal, styledata):
        if self.textattrs is not None:
            styledata.textattrs = attr.selectattrs(self.defaulttextattrs + self.textattrs, selectindex, selecttotal)
        else:
            styledata.textattrs = None
        symbol.selectstyle(self, selectindex, selecttotal, styledata)

    def drawsymbol_pt(self, c, x, y, styledata, point=None):
        symbol.drawsymbol_pt(self, c, x, y, styledata, point)
        if None not in (x, y, point[styledata.textindex]) and styledata.textattrs is not None:
            c.text_pt(x + styledata.textdx_pt, y + styledata.textdy_pt, str(point[styledata.textindex]), styledata.textattrs)

    def drawpoints(self, points, graph, styledata):
        styledata.textdx_pt = unit.topt(self.textdx)
        styledata.textdy_pt = unit.topt(self.textdy)
        symbol.drawpoints(self, points, graph, styledata)


class arrow(_style):

    defaultlineattrs = []
    defaultarrowattrs = []

    def __init__(self, linelength=0.25*unit.v_cm, arrowsize=0.15*unit.v_cm, lineattrs=[], arrowattrs=[], epsilon=1e-10):
        self.linelength = linelength
        self.arrowsize = arrowsize
        self.lineattrs = lineattrs
        self.arrowattrs = arrowattrs
        self.epsilon = epsilon

    def setdata(self, graph, columns, styledata):
        if len(graph.axisnames) != 2:
            raise TypeError("arrow style restricted on two-dimensional graphs")
        columns = columns.copy()
        styledata.xaxis, styledata.xindex = _style.setdatapattern(self, graph, columns, re.compile(r"(%s([2-9]|[1-9][0-9]+)?)$" % graph.axisnames[0]))
        styledata.yaxis, styledata.yindex = _style.setdatapattern(self, graph, columns, re.compile(r"(%s([2-9]|[1-9][0-9]+)?)$" % graph.axisnames[1]))
        styledata.sizeindex = columns["size"]
        del columns["size"]
        styledata.angleindex = columns["angle"]
        del columns["angle"]
        return columns

    def adjustaxes(self, points, columns, styledata):
        if styledata.xindex in columns:
            styledata.xaxis.adjustrange(points, styledata.xindex)
        if styledata.yindex in columns:
            styledata.yaxis.adjustrange(points, styledata.yindex)

    def selectstyle(self, selectindex, selecttotal, styledata):
        if self.lineattrs is not None:
            styledata.lineattrs = attr.selectattrs(self.defaultlineattrs + self.lineattrs, selectindex, selecttotal)
        else:
            styledata.lineattrs = None
        if self.arrowattrs is not None:
            styledata.arrowattrs = attr.selectattrs(self.defaultarrowattrs + self.arrowattrs, selectindex, selecttotal)
        else:
            styledata.arrowattrs = None

    def drawpoints(self, points, graph, styledata):
        if styledata.lineattrs is not None and styledata.arrowattrs is not None:
            linelength_pt = unit.topt(self.linelength)
            for point in points:
                xpos, ypos = graph.pos_pt(point[styledata.xindex], point[styledata.yindex], xaxis=styledata.xaxis, yaxis=styledata.yaxis)
                if point[styledata.sizeindex] > self.epsilon:
                    dx = math.cos(point[styledata.angleindex]*math.pi/180)
                    dy = math.sin(point[styledata.angleindex]*math.pi/180)
                    x1 = xpos-0.5*dx*linelength_pt*point[styledata.sizeindex]
                    y1 = ypos-0.5*dy*linelength_pt*point[styledata.sizeindex]
                    x2 = xpos+0.5*dx*linelength_pt*point[styledata.sizeindex]
                    y2 = ypos+0.5*dy*linelength_pt*point[styledata.sizeindex]
                    graph.stroke(path.line_pt(x1, y1, x2, y2), styledata.lineattrs +
                                 [deco.earrow(styledata.arrowattrs, size=self.arrowsize*point[styledata.sizeindex])])


class rect(_style):

    def __init__(self, palette=color.palette.Gray):
        self.palette = palette

    def setdata(self, graph, columns, styledata):
        if len(graph.axisnames) != 2:
            raise TypeError("arrow style restricted on two-dimensional graphs")
        columns = columns.copy()
        styledata.xaxis, styledata.xminindex = _style.setdatapattern(self, graph, columns, re.compile(r"(%s([2-9]|[1-9][0-9]+)?)min$" % graph.axisnames[0]))
        styledata.yaxis, styledata.yminindex = _style.setdatapattern(self, graph, columns, re.compile(r"(%s([2-9]|[1-9][0-9]+)?)min$" % graph.axisnames[1]))
        xaxis, styledata.xmaxindex = _style.setdatapattern(self, graph, columns, re.compile(r"(%s([2-9]|[1-9][0-9]+)?)max$" % graph.axisnames[0]))
        yaxis, styledata.ymaxindex = _style.setdatapattern(self, graph, columns, re.compile(r"(%s([2-9]|[1-9][0-9]+)?)max$" % graph.axisnames[1]))
        if xaxis != styledata.xaxis or yaxis != styledata.yaxis:
            raise ValueError("min/max values should use the same axes")
        styledata.colorindex = columns["color"]
        del columns["color"]
        return columns

    def selectstyle(self, selectindex, selecttotal, styledata):
        pass

    def adjustaxes(self, points, columns, styledata):
        if styledata.xminindex in columns:
            styledata.xaxis.adjustrange(points, styledata.xminindex)
        if styledata.xmaxindex in columns:
            styledata.xaxis.adjustrange(points, styledata.xmaxindex)
        if styledata.yminindex in columns:
            styledata.yaxis.adjustrange(points, styledata.yminindex)
        if styledata.ymaxindex in columns:
            styledata.yaxis.adjustrange(points, styledata.ymaxindex)

    def drawpoints(self, points, graph, styledata):
        # TODO: bbox shortcut
        c = graph.insert(canvas.canvas())
        lastcolorvalue = None
        for point in points:
            try:
                xvmin = styledata.xaxis.convert(point[styledata.xminindex])
                xvmax = styledata.xaxis.convert(point[styledata.xmaxindex])
                yvmin = styledata.yaxis.convert(point[styledata.yminindex])
                yvmax = styledata.yaxis.convert(point[styledata.ymaxindex])
                colorvalue = point[styledata.colorindex]
                if colorvalue != lastcolorvalue:
                    color = self.palette.getcolor(point[styledata.colorindex])
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

    def setdata(self, graph, columns, styledata):
        # TODO: remove limitation to 2d graphs
        if len(graph.axisnames) != 2:
            raise TypeError("arrow style currently restricted on two-dimensional graphs")
        columns = columns.copy()
        xvalue = _style.setdatapattern(self, graph, columns, re.compile(r"(%s([2-9]|[1-9][0-9]+)?)$" % graph.axisnames[0]))
        yvalue = _style.setdatapattern(self, graph, columns, re.compile(r"(%s([2-9]|[1-9][0-9]+)?)$" % graph.axisnames[1]))
        if (xvalue is None and yvalue is None) or (xvalue is not None and yvalue is not None):
            raise TypeError("must specify exactly one value axis")
        if xvalue is not None:
            styledata.valuepos = 0
            styledata.nameaxis, styledata.nameindex = _style.setdatapattern(self, graph, columns, re.compile(r"(%s([2-9]|[1-9][0-9]+)?)name$" % graph.axisnames[1]))
            styledata.valueaxis = xvalue[0]
            styledata.valueindices = [xvalue[1]]
        else:
            styledata.valuepos = 1
            styledata.nameaxis, styledata.nameindex = _style.setdatapattern(self, graph, columns, re.compile(r"(%s([2-9]|[1-9][0-9]+)?)name$" % graph.axisnames[0]))
            styledata.valueaxis = yvalue[0]
            styledata.valueindices = [yvalue[1]]
        i = 1
        while 1:
            try:
                valueaxis, valueindex = _style.setdatapattern(self, graph, columns, re.compile(r"(%s([2-9]|[1-9][0-9]+)?)stack%i$" % (graph.axisnames[styledata.valuepos], i)))
            except:
                break
            if styledata.valueaxis != valueaxis:
                raise ValueError("different value axes for stacked bars")
            styledata.valueindices.append(valueindex)
            i += 1
        return columns

    def selectstyle(self, selectindex, selecttotal, styledata):
        if selectindex:
            styledata.frompathattrs = None
        else:
            styledata.frompathattrs = self.defaultfrompathattrs + self.frompathattrs
        if selecttotal > 1:
            if self.barattrs is not None:
                styledata.barattrs = attr.selectattrs(self.defaultbarattrs + self.barattrs, selectindex, selecttotal)
            else:
                styledata.barattrs = None
        else:
            styledata.barattrs = self.defaultbarattrs + self.barattrs
        styledata.selectindex = selectindex
        styledata.selecttotal = selecttotal
        if styledata.selecttotal != 1 and self.subnames is not None:
            raise ValueError("subnames not allowed when iterating over bars")

    def adjustaxes(self, points, columns, styledata):
        if styledata.nameindex in columns:
            if styledata.selecttotal == 1:
                styledata.nameaxis.adjustrange(points, styledata.nameindex, subnames=self.subnames)
            else:
                for i in range(styledata.selecttotal):
                    styledata.nameaxis.adjustrange(points, styledata.nameindex, subnames=[i])
        for valueindex in styledata.valueindices:
            if valueindex in columns:
                styledata.valueaxis.adjustrange(points, valueindex)

    def drawpoints(self, points, graph, styledata):
        if self.fromvalue is not None:
            vfromvalue = styledata.valueaxis.convert(self.fromvalue)
            if vfromvalue < -self.epsilon:
                vfromvalue = 0
            if vfromvalue > 1 + self.epsilon:
                vfromvalue = 1
            if styledata.frompathattrs is not None and vfromvalue > self.epsilon and vfromvalue < 1 - self.epsilon:
                if styledata.valuepos:
                    p = graph.vgeodesic(0, vfromvalue, 1, vfromvalue)
                else:
                    p = graph.vgeodesic(vfromvalue, 0, vfromvalue, 1)
                graph.stroke(p, styledata.frompathattrs)
        else:
            vfromvalue = 0
        l = len(styledata.valueindices)
        if l > 1:
            barattrslist = []
            for i in range(l):
                barattrslist.append(attr.selectattrs(styledata.barattrs, i, l))
        else:
            barattrslist = [styledata.barattrs]
        for point in points:
            vvaluemax = vfromvalue
            for valueindex, barattrs in zip(styledata.valueindices, barattrslist):
                vvaluemin = vvaluemax
                try:
                    vvaluemax = styledata.valueaxis.convert(point[valueindex])
                except:
                    continue

                if styledata.selecttotal == 1:
                    try:
                        vnamemin = styledata.nameaxis.convert((point[styledata.nameindex], 0))
                    except:
                        continue
                    try:
                        vnamemax = styledata.nameaxis.convert((point[styledata.nameindex], 1))
                    except:
                        continue
                else:
                    try:
                        vnamemin = styledata.nameaxis.convert((point[styledata.nameindex], styledata.selectindex, 0))
                    except:
                        continue
                    try:
                        vnamemax = styledata.nameaxis.convert((point[styledata.nameindex], styledata.selectindex, 1))
                    except:
                        continue

                if styledata.valuepos:
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

    def key_pt(self, c, x_pt, y_pt, width_pt, height_pt, styledata):
        l = len(styledata.valueindices)
        if l > 1:
            for i in range(l):
                c.fill(path.rect_pt(x_pt+i*width_pt/l, y_pt, width_pt/l, height_pt), attr.selectattrs(styledata.barattrs, i, l))
        else:
            c.fill(path.rect_pt(x_pt, y_pt, width_pt, height_pt), styledata.barattrs)
