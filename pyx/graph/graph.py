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


import math, re, string
from pyx import canvas, path, trafo, unit
from pyx.graph import style
from pyx.graph.axis import painter, axis


goldenmean = 0.5 * (math.sqrt(5) + 1)


class lineaxispos:
    """an axispos linear along a line with a fix direction for the ticks"""

    def __init__(self, convert, x1, y1, x2, y2, fixtickdirection):
        """initializes the instance
        - only the convert method is needed from the axis
        - x1, y1, x2, y2 are PyX lengths (start and end position of the line)
        - fixtickdirection is a tuple tick direction (fixed along the line)"""
        self.convert = convert
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.x1_pt = unit.topt(x1)
        self.y1_pt = unit.topt(y1)
        self.x2_pt = unit.topt(x2)
        self.y2_pt = unit.topt(y2)
        self.fixtickdirection = fixtickdirection

    def vbasepath(self, v1=None, v2=None):
        if v1 is None:
            v1 = 0
        if v2 is None:
            v2 = 1
        return path.line_pt((1-v1)*self.x1_pt+v1*self.x2_pt,
                            (1-v1)*self.y1_pt+v1*self.y2_pt,
                            (1-v2)*self.x1_pt+v2*self.x2_pt,
                            (1-v2)*self.y1_pt+v2*self.y2_pt)

    def basepath(self, x1=None, x2=None):
        if x1 is None:
            v1 = 0
        else:
            v1 = self.convert(x1)
        if x2 is None:
            v2 = 1
        else:
            v2 = self.convert(x2)
        return path.line_pt((1-v1)*self.x1_pt+v1*self.x2_pt,
                            (1-v1)*self.y1_pt+v1*self.y2_pt,
                            (1-v2)*self.x1_pt+v2*self.x2_pt,
                            (1-v2)*self.y1_pt+v2*self.y2_pt)

    def gridpath(self, x):
        raise RuntimeError("gridpath not available")

    def vgridpath(self, v):
        raise RuntimeError("gridpath not available")

    def vtickpoint_pt(self, v):
        return (1-v)*self.x1_pt+v*self.x2_pt, (1-v)*self.y1_pt+v*self.y2_pt

    def vtickpoint(self, v):
        return (1-v)*self.x1+v*self.x2, (1-v)*self.y1+v*self.y2

    def tickpoint_pt(self, x):
        v = self.convert(x)
        return (1-v)*self.x1_pt+v*self.x2_pt, (1-v)*self.y1_pt+v*self.y2_pt

    def tickpoint(self, x):
        v = self.convert(x)
        return (1-v)*self.x1+v*self.x2, (1-v)*self.y1+v*self.y2

    def tickdirection(self, x):
        return self.fixtickdirection

    def vtickdirection(self, v):
        return self.fixtickdirection


class lineaxisposlinegrid(lineaxispos):
    """an axispos linear along a line with a fix direction for the ticks
    with support for grid lines for a rectangular graphs"""

    __implements__ = painter._Iaxispos

    def __init__(self, convert, x1, y1, x2, y2, fixtickdirection, startgridlength, endgridlength):
        """initializes the instance
        - only the convert method is needed from the axis
        - x1, y1, x2, y2 are PyX lengths (start and end position of the line)
        - fixtickdirection is a tuple tick direction (fixed along the line)
        - startgridlength and endgridlength are PyX lengths for the starting
          and end point of the grid, respectively; the gridpath is a line along
          the fixtickdirection"""
        lineaxispos.__init__(self, convert, x1, y1, x2, y2, fixtickdirection)
        self.startgridlength = startgridlength
        self.endgridlength = endgridlength
        self.startgridlength_pt = unit.topt(self.startgridlength)
        self.endgridlength_pt = unit.topt(self.endgridlength)

    def gridpath(self, x):
        v = self.convert(x)
        return path.line_pt((1-v)*self.x1_pt+v*self.x2_pt+self.fixtickdirection[0]*self.startgridlength_pt,
                          (1-v)*self.y1_pt+v*self.y2_pt+self.fixtickdirection[1]*self.startgridlength_pt,
                          (1-v)*self.x1_pt+v*self.x2_pt+self.fixtickdirection[0]*self.endgridlength_pt,
                          (1-v)*self.y1_pt+v*self.y2_pt+self.fixtickdirection[1]*self.endgridlength_pt)

    def vgridpath(self, v):
        return path.line_pt((1-v)*self.x1_pt+v*self.x2_pt+self.fixtickdirection[0]*self.startgridlength_pt,
                          (1-v)*self.y1_pt+v*self.y2_pt+self.fixtickdirection[1]*self.startgridlength_pt,
                          (1-v)*self.x1_pt+v*self.x2_pt+self.fixtickdirection[0]*self.endgridlength_pt,
                          (1-v)*self.y1_pt+v*self.y2_pt+self.fixtickdirection[1]*self.endgridlength_pt)


class styledata:
    """Styledata storage class

    Instances of this class are used to store data from the styles
    and to pass point data to the styles by instances named privatedata
    and sharedata. sharedata is shared between all the style(s) in use
    by a data instance, while privatedata is private to each style and
    used as a storage place instead of self to prevent side effects when
    using a style several times."""
    pass


class plotitem:

    def __init__(self, graph, data, styles):
        self.data = data

        # add styles to ensure all needs of the given styles
        provided = [] # already provided sharedata variables
        addstyles = [] # a list of style instances to be added in front
        for s in styles:
            for n in s.needsdata:
                if n not in provided:
                    defaultprovider = style.getdefaultprovider(n)
                    addstyles.append(defaultprovider)
                    provided.extend(defaultprovider.providesdata)
            provided.extend(s.providesdata)

        self.styles = addstyles + styles
        self.sharedata = styledata()
        self.privatedatalist = [styledata() for s in self.styles]

        # perform setcolumns to all styles
        self.data.initplotitem(self, graph)
        columns = self.data.getcolumnnames(self)
        usedcolumns = []
        for privatedata, s in zip(self.privatedatalist, self.styles):
            usedcolumns.extend(s.columns(privatedata, self.sharedata, graph, columns))
        for column in columns:
            if column not in usedcolumns:
                raise ValueError("unused column '%s'" % column)

    def selectstyles(self, graph, selectindex, selecttotal):
        for privatedata, style in zip(self.privatedatalist, self.styles):
            style.selectstyle(privatedata, self.sharedata, graph, selectindex, selecttotal)

    def adjustaxes(self, graph, step):
        self.data.adjustaxes(self, graph, step)

    def draw(self, graph):
        self.data.draw(self, graph)

    def gettitle(self):
        return self.data.gettitle()

    def key_pt(self, graph, x_pt, y_pt, width_pt, height_pt):
        for privatedata, style in zip(self.privatedatalist, self.styles):
            style.key_pt(privatedata, self.sharedata, graph, x_pt, y_pt, width_pt, height_pt)

    def __getattr__(self, attr):
        # read only access to the styles privatedata
        stylesdata = [getattr(styledata, attr)
                      for styledata in self.privatedatalist
                      if hasattr(styledata, attr)]
        if len(stylesdata) > 1:
            return stylesdata
        elif len(stylesdata) == 1:
            return stylesdata[0]
        raise AttributeError("access to styledata attributes failed")



class graphxy(canvas.canvas):

    def plot(self, data, styles=None):
        if self.haslayout:
            raise RuntimeError("layout setup was already performed")
        singledata = 0
        try:
            for d in data:
                pass
        except:
            usedata = [data]
            singledata = 1
        else:
            usedata = data
        if styles is None:
            for d in usedata:
                if styles is None:
                    styles = d.getdefaultstyles()
                elif styles != d.getdefaultstyles():
                    raise RuntimeError("defaultstyles differ")
        plotitems = []
        for d in usedata:
            plotitems.append(plotitem(self, d, styles))
        self.plotitems.extend(plotitems)
        if singledata:
            return plotitems[0]
        else:
            return plotitems

    def pos_pt(self, x, y, xaxis=None, yaxis=None):
        if xaxis is None:
            xaxis = self.axes["x"]
        if yaxis is None:
            yaxis = self.axes["y"]
        return self.xpos_pt + xaxis.convert(x)*self.width_pt, self.ypos_pt + yaxis.convert(y)*self.height_pt

    def pos(self, x, y, xaxis=None, yaxis=None):
        if xaxis is None:
            xaxis = self.axes["x"]
        if yaxis is None:
            yaxis = self.axes["y"]
        return self.xpos + xaxis.convert(x)*self.width, self.ypos + yaxis.convert(y)*self.height

    def vpos_pt(self, vx, vy):
        return self.xpos_pt + vx*self.width_pt, self.ypos_pt + vy*self.height_pt

    def vpos(self, vx, vy):
        return self.xpos + vx*self.width, self.ypos + vy*self.height

    def vgeodesic(self, vx1, vy1, vx2, vy2):
        """returns a geodesic path between two points in graph coordinates"""
        return path.line_pt(self.xpos_pt + vx1*self.width_pt,
                            self.ypos_pt + vy1*self.height_pt,
                            self.xpos_pt + vx2*self.width_pt,
                            self.ypos_pt + vy2*self.height_pt)

    def vgeodesic_el(self, vx1, vy1, vx2, vy2):
        """returns a geodesic path element between two points in graph coordinates"""
        return path.lineto_pt(self.xpos_pt + vx2*self.width_pt,
                              self.ypos_pt + vy2*self.height_pt)

    def vcap_pt(self, coordinate, length_pt, vx, vy):
        """returns an error cap path for a given coordinate, lengths and
        point in graph coordinates"""
        if coordinate == 0:
            return path.line_pt(self.xpos_pt + vx*self.width_pt - 0.5*length_pt,
                                self.ypos_pt + vy*self.height_pt,
                                self.xpos_pt + vx*self.width_pt + 0.5*length_pt,
                                self.ypos_pt + vy*self.height_pt)
        elif coordinate == 1:
            return path.line_pt(self.xpos_pt + vx*self.width_pt,
                                self.ypos_pt + vy*self.height_pt - 0.5*length_pt,
                                self.xpos_pt + vx*self.width_pt,
                                self.ypos_pt + vy*self.height_pt + 0.5*length_pt)
        else:
            raise ValueError("direction invalid")

    def keynum(self, key):
        try:
            while key[0] in string.letters:
                key = key[1:]
            return int(key)
        except IndexError:
            return 1

    def removedomethod(self, method):
        hadmethod = 0
        while 1:
            try:
                self.domethods.remove(method)
                hadmethod = 1
            except ValueError:
                return hadmethod

    def dolayout(self):
        if not self.removedomethod(self.dolayout): return

        # count the usage of styles and perform selects
        styletotal = {}
        def stylesid(styles):
            return ":".join([str(id(style)) for style in styles])
        for plotitem in self.plotitems:
            try:
                styletotal[stylesid(plotitem.styles)] += 1
            except:
                styletotal[stylesid(plotitem.styles)] = 1
        styleindex = {}
        for plotitem in self.plotitems:
            try:
                styleindex[stylesid(plotitem.styles)] += 1
            except:
                styleindex[stylesid(plotitem.styles)] = 0
            plotitem.selectstyles(self, styleindex[stylesid(plotitem.styles)], styletotal[stylesid(plotitem.styles)])

        # adjust the axes ranges
        for step in range(3):
            for plotitem in self.plotitems:
                plotitem.adjustaxes(self, step)

        # finish all axes
        XPattern = re.compile(r"x([2-9]|[1-9][0-9]+)?$")
        YPattern = re.compile(r"y([2-9]|[1-9][0-9]+)?$")
        xaxisextents = [0, 0]
        yaxisextents = [0, 0]
        needxaxisdist = [0, 0]
        needyaxisdist = [0, 0]
        items = list(self.axes.items())
        items.sort() #TODO: alphabetical sorting breaks for axis numbers bigger than 9
        # TODO: linked axes are not taken into account (consider x being a link to x2)
        for key, axis in items:
            num = self.keynum(key)
            num2 = 1 - num % 2 # x1 -> 0, x2 -> 1, x3 -> 0, x4 -> 1, ...
            num3 = 2 * (num % 2) - 1 # x1 -> 1, x2 -> -1, x3 -> 1, x4 -> -1, ...
            if XPattern.match(key):
                if needxaxisdist[num2]:
                    xaxisextents[num2] += self.axesdist
                self.axespos[key] = lineaxisposlinegrid(axis.convert,
                                                        self.xpos,
                                                        self.ypos + num2*self.height - num3*xaxisextents[num2],
                                                        self.xpos + self.width,
                                                        self.ypos + num2*self.height - num3*xaxisextents[num2],
                                                        (0, num3),
                                                        xaxisextents[num2], xaxisextents[num2] + self.height)
                if num == 1:
                    self.xbasepath = self.axespos[key].basepath
                    self.xvbasepath = self.axespos[key].vbasepath
                    self.xgridpath = self.axespos[key].gridpath
                    self.xvgridpath = self.axespos[key].vgridpath
                    self.xtickpoint_pt = self.axespos[key].tickpoint_pt
                    self.xtickpoint = self.axespos[key].tickpoint
                    self.xvtickpoint_pt = self.axespos[key].vtickpoint_pt
                    self.xvtickpoint = self.axespos[key].tickpoint
                    self.xtickdirection = self.axespos[key].tickdirection
                    self.xvtickdirection = self.axespos[key].vtickdirection
            elif YPattern.match(key):
                if needyaxisdist[num2]:
                    yaxisextents[num2] += self.axesdist
                self.axespos[key] = lineaxisposlinegrid(axis.convert,
                                                        self.xpos + num2*self.width - num3*yaxisextents[num2],
                                                        self.ypos,
                                                        self.xpos + num2*self.width - num3*yaxisextents[num2],
                                                        self.ypos + self.height,
                                                        (num3, 0),
                                                        yaxisextents[num2], yaxisextents[num2] + self.width)
                if num == 1:
                    self.ybasepath = self.axespos[key].basepath
                    self.yvbasepath = self.axespos[key].vbasepath
                    self.ygridpath = self.axespos[key].gridpath
                    self.yvgridpath = self.axespos[key].vgridpath
                    self.ytickpoint_pt = self.axespos[key].tickpoint_pt
                    self.ytickpoint = self.axespos[key].tickpoint
                    self.yvtickpoint_pt = self.axespos[key].vtickpoint_pt
                    self.yvtickpoint = self.axespos[key].tickpoint
                    self.ytickdirection = self.axespos[key].tickdirection
                    self.yvtickdirection = self.axespos[key].vtickdirection
            else:
                raise ValueError("Axis key '%s' not allowed" % key)
            axis.finish(self.axespos[key])
            if XPattern.match(key):
                xaxisextents[num2] += axis.axiscanvas.extent
                needxaxisdist[num2] = 1
            if YPattern.match(key):
                yaxisextents[num2] += axis.axiscanvas.extent
                needyaxisdist[num2] = 1
        self.haslayout = 1

    def dobackground(self):
        self.dolayout()
        if not self.removedomethod(self.dobackground): return
        if self.backgroundattrs is not None:
            self.draw(path.rect_pt(self.xpos_pt, self.ypos_pt, self.width_pt, self.height_pt),
                      self.backgroundattrs)

    def doaxes(self):
        self.dolayout()
        if not self.removedomethod(self.doaxes): return
        for axis in self.axes.values():
            self.insert(axis.axiscanvas)

    def dodata(self):
        self.dolayout()
        if not self.removedomethod(self.dodata): return
        for plotitem in self.plotitems:
            plotitem.draw(self)

    def dokey(self):
        self.dolayout()
        if not self.removedomethod(self.dokey): return
        if self.key is not None:
            c = self.key.paint(self.plotitems)
            bbox = c.bbox()
            def parentchildalign(pmin, pmax, cmin, cmax, pos, dist, inside):
                ppos = pmin+0.5*(cmax-cmin)+dist+pos*(pmax-pmin-cmax+cmin-2*dist)
                cpos = 0.5*(cmin+cmax)+(1-inside)*(1-2*pos)*(cmax-cmin+2*dist)
                return ppos-cpos
            x = parentchildalign(self.xpos_pt, self.xpos_pt+self.width_pt,
                                 bbox.llx_pt, bbox.urx_pt,
                                 self.key.hpos, unit.topt(self.key.hdist), self.key.hinside)
            y = parentchildalign(self.ypos_pt, self.ypos_pt+self.height_pt,
                                 bbox.lly_pt, bbox.ury_pt,
                                 self.key.vpos, unit.topt(self.key.vdist), self.key.vinside)
            self.insert(c, [trafo.translate_pt(x, y)])

    def finish(self):
        while len(self.domethods):
            self.domethods[0]()

    def initwidthheight(self, width, height, ratio):
        if (width is not None) and (height is None):
             self.width = width
             self.height = (1.0/ratio) * self.width
        elif (height is not None) and (width is None):
             self.height = height
             self.width = ratio * self.height
        else:
             self.width = width
             self.height = height
        self.width_pt = unit.topt(self.width)
        self.height_pt = unit.topt(self.height)
        if self.width_pt <= 0: raise ValueError("width <= 0")
        if self.height_pt <= 0: raise ValueError("height <= 0")

    def initaxes(self, axes, addlinkaxes=0):
        for key in ["x", "y"]:
            if not axes.has_key(key):
                axes[key] = axis.linear()
            elif axes[key] is None:
                del axes[key]
            if addlinkaxes:
                if not axes.has_key(key + "2") and axes.has_key(key):
                    axes[key + "2"] = axes[key].createlinkaxis()
                elif axes[key + "2"] is None:
                    del axes[key + "2"]
        self.axes = axes
        self.axesnames = ([], [])
        for key in axes.keys():
            if len(key) != 1 and (not key[1:].isdigit() or key[1:] == "1"):
                raise ValueError("invalid axis count")
            if key[0] == "x":
                self.axesnames[0].append(key)
            elif key[0] == "y":
                self.axesnames[1].append(key)
            else:
                raise ValueError("invalid axis name")

    def __init__(self, xpos=0, ypos=0, width=None, height=None, ratio=goldenmean,
                 key=None, backgroundattrs=None, axesdist=0.8*unit.v_cm, **axes):
        canvas.canvas.__init__(self)
        self.xpos = xpos
        self.ypos = ypos
        self.xpos_pt = unit.topt(self.xpos)
        self.ypos_pt = unit.topt(self.ypos)
        self.initwidthheight(width, height, ratio)
        self.initaxes(axes, 1)
        self.axescanvas = {}
        self.axespos = {}
        self.key = key
        self.backgroundattrs = backgroundattrs
        self.axesdist = axesdist
        self.plotitems = []
        self.domethods = [self.dolayout, self.dobackground, self.doaxes, self.dodata, self.dokey]
        self.haslayout = 0
        self.addkeys = []

    def bbox(self):
        self.finish()
        return canvas.canvas.bbox(self)

    def prolog(self):
        self.finish()
        return canvas.canvas.prolog(self)

    def outputPS(self, file):
        self.finish()
        canvas.canvas.outputPS(self, file)



# some thoughts, but deferred right now
# 
# class graphxyz(graphxy):
# 
#     axisnames = "x", "y", "z"
# 
#     def _vxtickpoint(self, axis, v):
#         return self._vpos(v, axis.vypos, axis.vzpos)
# 
#     def _vytickpoint(self, axis, v):
#         return self._vpos(axis.vxpos, v, axis.vzpos)
# 
#     def _vztickpoint(self, axis, v):
#         return self._vpos(axis.vxpos, axis.vypos, v)
# 
#     def vxtickdirection(self, axis, v):
#         x1, y1 = self._vpos(v, axis.vypos, axis.vzpos)
#         x2, y2 = self._vpos(v, 0.5, 0)
#         dx, dy = x1 - x2, y1 - y2
#         norm = math.hypot(dx, dy)
#         return dx/norm, dy/norm
# 
#     def vytickdirection(self, axis, v):
#         x1, y1 = self._vpos(axis.vxpos, v, axis.vzpos)
#         x2, y2 = self._vpos(0.5, v, 0)
#         dx, dy = x1 - x2, y1 - y2
#         norm = math.hypot(dx, dy)
#         return dx/norm, dy/norm
# 
#     def vztickdirection(self, axis, v):
#         return -1, 0
#         x1, y1 = self._vpos(axis.vxpos, axis.vypos, v)
#         x2, y2 = self._vpos(0.5, 0.5, v)
#         dx, dy = x1 - x2, y1 - y2
#         norm = math.hypot(dx, dy)
#         return dx/norm, dy/norm
# 
#     def _pos(self, x, y, z, xaxis=None, yaxis=None, zaxis=None):
#         if xaxis is None: xaxis = self.axes["x"]
#         if yaxis is None: yaxis = self.axes["y"]
#         if zaxis is None: zaxis = self.axes["z"]
#         return self._vpos(xaxis.convert(x), yaxis.convert(y), zaxis.convert(z))
# 
#     def pos(self, x, y, z, xaxis=None, yaxis=None, zaxis=None):
#         if xaxis is None: xaxis = self.axes["x"]
#         if yaxis is None: yaxis = self.axes["y"]
#         if zaxis is None: zaxis = self.axes["z"]
#         return self.vpos(xaxis.convert(x), yaxis.convert(y), zaxis.convert(z))
# 
#     def _vpos(self, vx, vy, vz):
#         x, y, z = (vx - 0.5)*self._depth, (vy - 0.5)*self._width, (vz - 0.5)*self._height
#         d0 = float(self.a[0]*self.b[1]*(z-self.eye[2])
#                  + self.a[2]*self.b[0]*(y-self.eye[1])
#                  + self.a[1]*self.b[2]*(x-self.eye[0])
#                  - self.a[2]*self.b[1]*(x-self.eye[0])
#                  - self.a[0]*self.b[2]*(y-self.eye[1])
#                  - self.a[1]*self.b[0]*(z-self.eye[2]))
#         da = (self.eye[0]*self.b[1]*(z-self.eye[2])
#             + self.eye[2]*self.b[0]*(y-self.eye[1])
#             + self.eye[1]*self.b[2]*(x-self.eye[0])
#             - self.eye[2]*self.b[1]*(x-self.eye[0])
#             - self.eye[0]*self.b[2]*(y-self.eye[1])
#             - self.eye[1]*self.b[0]*(z-self.eye[2]))
#         db = (self.a[0]*self.eye[1]*(z-self.eye[2])
#             + self.a[2]*self.eye[0]*(y-self.eye[1])
#             + self.a[1]*self.eye[2]*(x-self.eye[0])
#             - self.a[2]*self.eye[1]*(x-self.eye[0])
#             - self.a[0]*self.eye[2]*(y-self.eye[1])
#             - self.a[1]*self.eye[0]*(z-self.eye[2]))
#         return da/d0 + self._xpos, db/d0 + self._ypos
# 
#     def vpos(self, vx, vy, vz):
#         tx, ty = self._vpos(vx, vy, vz)
#         return unit.t_pt(tx), unit.t_pt(ty)
# 
#     def xbaseline(self, axis, x1, x2, xaxis=None):
#         if xaxis is None: xaxis = self.axes["x"]
#         return self.vxbaseline(axis, xaxis.convert(x1), xaxis.convert(x2))
# 
#     def ybaseline(self, axis, y1, y2, yaxis=None):
#         if yaxis is None: yaxis = self.axes["y"]
#         return self.vybaseline(axis, yaxis.convert(y1), yaxis.convert(y2))
# 
#     def zbaseline(self, axis, z1, z2, zaxis=None):
#         if zaxis is None: zaxis = self.axes["z"]
#         return self.vzbaseline(axis, zaxis.convert(z1), zaxis.convert(z2))
# 
#     def vxbaseline(self, axis, v1, v2):
#         return (path._line(*(self._vpos(v1, 0, 0) + self._vpos(v2, 0, 0))) +
#                 path._line(*(self._vpos(v1, 0, 1) + self._vpos(v2, 0, 1))) +
#                 path._line(*(self._vpos(v1, 1, 1) + self._vpos(v2, 1, 1))) +
#                 path._line(*(self._vpos(v1, 1, 0) + self._vpos(v2, 1, 0))))
# 
#     def vybaseline(self, axis, v1, v2):
#         return (path._line(*(self._vpos(0, v1, 0) + self._vpos(0, v2, 0))) +
#                 path._line(*(self._vpos(0, v1, 1) + self._vpos(0, v2, 1))) +
#                 path._line(*(self._vpos(1, v1, 1) + self._vpos(1, v2, 1))) +
#                 path._line(*(self._vpos(1, v1, 0) + self._vpos(1, v2, 0))))
# 
#     def vzbaseline(self, axis, v1, v2):
#         return (path._line(*(self._vpos(0, 0, v1) + self._vpos(0, 0, v2))) +
#                 path._line(*(self._vpos(0, 1, v1) + self._vpos(0, 1, v2))) +
#                 path._line(*(self._vpos(1, 1, v1) + self._vpos(1, 1, v2))) +
#                 path._line(*(self._vpos(1, 0, v1) + self._vpos(1, 0, v2))))
# 
#     def xgridpath(self, x, xaxis=None):
#         assert 0
#         if xaxis is None: xaxis = self.axes["x"]
#         v = xaxis.convert(x)
#         return path._line(self._xpos+v*self._width, self._ypos,
#                           self._xpos+v*self._width, self._ypos+self._height)
# 
#     def ygridpath(self, y, yaxis=None):
#         assert 0
#         if yaxis is None: yaxis = self.axes["y"]
#         v = yaxis.convert(y)
#         return path._line(self._xpos, self._ypos+v*self._height,
#                           self._xpos+self._width, self._ypos+v*self._height)
# 
#     def zgridpath(self, z, zaxis=None):
#         assert 0
#         if zaxis is None: zaxis = self.axes["z"]
#         v = zaxis.convert(z)
#         return path._line(self._xpos, self._zpos+v*self._height,
#                           self._xpos+self._width, self._zpos+v*self._height)
# 
#     def vxgridpath(self, v):
#         return path.path(path._moveto(*self._vpos(v, 0, 0)),
#                          path._lineto(*self._vpos(v, 0, 1)),
#                          path._lineto(*self._vpos(v, 1, 1)),
#                          path._lineto(*self._vpos(v, 1, 0)),
#                          path.closepath())
# 
#     def vygridpath(self, v):
#         return path.path(path._moveto(*self._vpos(0, v, 0)),
#                          path._lineto(*self._vpos(0, v, 1)),
#                          path._lineto(*self._vpos(1, v, 1)),
#                          path._lineto(*self._vpos(1, v, 0)),
#                          path.closepath())
# 
#     def vzgridpath(self, v):
#         return path.path(path._moveto(*self._vpos(0, 0, v)),
#                          path._lineto(*self._vpos(0, 1, v)),
#                          path._lineto(*self._vpos(1, 1, v)),
#                          path._lineto(*self._vpos(1, 0, v)),
#                          path.closepath())
# 
#     def _addpos(self, x, y, dx, dy):
#         assert 0
#         return x+dx, y+dy
# 
#     def _connect(self, x1, y1, x2, y2):
#         assert 0
#         return path._lineto(x2, y2)
# 
#     def doaxes(self):
#         self.dolayout()
#         if not self.removedomethod(self.doaxes): return
#         axesdist_pt = unit.topt(self.axesdist)
#         XPattern = re.compile(r"%s([2-9]|[1-9][0-9]+)?$" % self.axisnames[0])
#         YPattern = re.compile(r"%s([2-9]|[1-9][0-9]+)?$" % self.axisnames[1])
#         ZPattern = re.compile(r"%s([2-9]|[1-9][0-9]+)?$" % self.axisnames[2])
#         items = list(self.axes.items())
#         items.sort() #TODO: alphabetical sorting breaks for axis numbers bigger than 9
#         for key, axis in items:
#             num = self.keynum(key)
#             num2 = 1 - num % 2 # x1 -> 0, x2 -> 1, x3 -> 0, x4 -> 1, ...
#             num3 = 1 - 2 * (num % 2) # x1 -> -1, x2 -> 1, x3 -> -1, x4 -> 1, ...
#             if XPattern.match(key):
#                 axis.vypos = 0
#                 axis.vzpos = 0
#                 axis._vtickpoint = self._vxtickpoint
#                 axis.vgridpath = self.vxgridpath
#                 axis.vbaseline = self.vxbaseline
#                 axis.vtickdirection = self.vxtickdirection
#             elif YPattern.match(key):
#                 axis.vxpos = 0
#                 axis.vzpos = 0
#                 axis._vtickpoint = self._vytickpoint
#                 axis.vgridpath = self.vygridpath
#                 axis.vbaseline = self.vybaseline
#                 axis.vtickdirection = self.vytickdirection
#             elif ZPattern.match(key):
#                 axis.vxpos = 0
#                 axis.vypos = 0
#                 axis._vtickpoint = self._vztickpoint
#                 axis.vgridpath = self.vzgridpath
#                 axis.vbaseline = self.vzbaseline
#                 axis.vtickdirection = self.vztickdirection
#             else:
#                 raise ValueError("Axis key '%s' not allowed" % key)
#             if axis.painter is not None:
#                 axis.dopaint(self)
# #            if XPattern.match(key):
# #                self._xaxisextents[num2] += axis._extent
# #                needxaxisdist[num2] = 1
# #            if YPattern.match(key):
# #                self._yaxisextents[num2] += axis._extent
# #                needyaxisdist[num2] = 1
# 
#     def __init__(self, tex, xpos=0, ypos=0, width=None, height=None, depth=None,
#                  phi=30, theta=30, distance=1,
#                  backgroundattrs=None, axesdist=0.8*unit.v_cm, **axes):
#         canvas.canvas.__init__(self)
#         self.tex = tex
#         self.xpos = xpos
#         self.ypos = ypos
#         self._xpos = unit.topt(xpos)
#         self._ypos = unit.topt(ypos)
#         self._width = unit.topt(width)
#         self._height = unit.topt(height)
#         self._depth = unit.topt(depth)
#         self.width = width
#         self.height = height
#         self.depth = depth
#         if self._width <= 0: raise ValueError("width < 0")
#         if self._height <= 0: raise ValueError("height < 0")
#         if self._depth <= 0: raise ValueError("height < 0")
#         self._distance = distance*math.sqrt(self._width*self._width+
#                                             self._height*self._height+
#                                             self._depth*self._depth)
#         phi *= -math.pi/180
#         theta *= math.pi/180
#         self.a = (-math.sin(phi), math.cos(phi), 0)
#         self.b = (-math.cos(phi)*math.sin(theta),
#                   -math.sin(phi)*math.sin(theta),
#                   math.cos(theta))
#         self.eye = (self._distance*math.cos(phi)*math.cos(theta),
#                     self._distance*math.sin(phi)*math.cos(theta),
#                     self._distance*math.sin(theta))
#         self.initaxes(axes)
#         self.axesdist = axesdist
#         self.backgroundattrs = backgroundattrs
# 
#         self.data = []
#         self.domethods = [self.dolayout, self.dobackground, self.doaxes, self.dodata]
#         self.haslayout = 0
#         self.defaultstyle = {}
# 
#     def bbox(self):
#         self.finish()
#         return bbox._bbox(self._xpos - 200, self._ypos - 200, self._xpos + 200, self._ypos + 200)
