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
from pyx.graph.axis import axis, positioner


goldenmean = 0.5 * (math.sqrt(5) + 1)


class styledata:
    """style data storage class

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
        self.title = data.title

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
        columnnames = self.data.columnnames(graph)
        self.usedcolumnnames = []
        for privatedata, s in zip(self.privatedatalist, self.styles):
            self.usedcolumnnames.extend(s.columnnames(privatedata, self.sharedata, graph, columnnames))

    def selectstyles(self, graph, selectindex, selecttotal):
        for privatedata, style in zip(self.privatedatalist, self.styles):
            style.selectstyle(privatedata, self.sharedata, graph, selectindex, selecttotal)

    def adjustaxesstatic(self, graph):
        for columnname, data in self.data.columns.items():
            for privatedata, style in zip(self.privatedatalist, self.styles):
                style.adjustaxis(privatedata, self.sharedata, graph, columnname, data)

    def makedynamicdata(self, graph):
        self.dynamiccolumns = self.data.dynamiccolumns(graph)

    def adjustaxesdynamic(self, graph):
        for columnname, data in self.dynamiccolumns.items():
            for privatedata, style in zip(self.privatedatalist, self.styles):
                style.adjustaxis(privatedata, self.sharedata, graph, columnname, data)

    def draw(self, graph):
        for privatedata, style in zip(self.privatedatalist, self.styles):
            style.initdrawpoints(privatedata, self.sharedata, graph)
        point = {}
        useitems = []
        for columnname in self.usedcolumnnames:
            try:
                useitems.append((columnname, self.data.columns[columnname]))
            except:
                useitems.append((columnname, self.dynamiccolumns[columnname]))
        if not useitems:
            raise ValueError("cannot draw empty data")
        for i in xrange(len(useitems[0][1])):
            for columnname, data in useitems:
                point[columnname] = data[i]
            for privatedata, style in zip(self.privatedatalist, self.styles):
                style.drawpoint(privatedata, self.sharedata, graph, point)
        for privatedata, style in zip(self.privatedatalist, self.styles):
            style.donedrawpoints(privatedata, self.sharedata, graph)

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
        raise AttributeError("access to styledata attribute '%s' failed" % attr)



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
                    styles = d.defaultstyles
                elif styles != d.defaultstyles:
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

    def xvgridpath(self, vx):
        return path.line_pt(self.xpos_pt + vx*self.width_pt, self.ypos_pt,
                            self.xpos_pt + vx*self.width_pt, self.ypos_pt + self.height_pt)

    def yvgridpath(self, vy):
        return path.line_pt(self.xpos_pt, self.ypos_pt + vy*self.height_pt,
                            self.xpos_pt + self.width_pt, self.ypos_pt + vy*self.height_pt)

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

    def axistrafo(self, axis, t):
        c = canvas.canvas([t])
        c.insert(axis.canvas)
        axis.canvas = c

    def axisatv(self, axis, v):
        if axis.positioner.fixtickdirection[0]:
            # it is a y-axis
            self.axistrafo(axis, trafo.translate_pt(self.xpos_pt + v*self.width_pt - axis.positioner.x1_pt, 0))
        else:
            # it is an x-axis
            self.axistrafo(axis, trafo.translate_pt(0, self.ypos_pt + v*self.height_pt - axis.positioner.y1_pt))

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
        for plotitem in self.plotitems:
            plotitem.adjustaxesstatic(self)
        for plotitem in self.plotitems:
            plotitem.makedynamicdata(self)
        for plotitem in self.plotitems:
            plotitem.adjustaxesdynamic(self)

        # finish all axes
        keys = list(self.axes.keys())
        keys.sort() #TODO: alphabetical sorting breaks for axis numbers bigger than 9
        for key in keys:
            self.axes[key].create(self.texrunner)
            if key[1:]:
                num = int(key[1:])
            else:
                num = 1
            if num:
                nextkey = "%s%i" % (key[0], (num+2))
                if self.axes.has_key(nextkey):
                    sign = 2*(num % 2) - 1
                    if key[0] == "x":
                        y_pt = self.axes[key].positioner.y1_pt - sign * (self.axes[key].canvas.extent_pt + self.axesdist_pt)
                        apositioner = positioner.lineaxispos_pt(self.xpos_pt, y_pt,
                                                                self.xpos_pt + self.width_pt, y_pt,
                                                                (0, sign), self.xvgridpath)
                    else:
                        x_pt = self.axes[key].positioner.x1_pt - sign * (self.axes[key].canvas.extent_pt + self.axesdist_pt)
                        apositioner = positioner.lineaxispos_pt(x_pt, self.ypos_pt,
                                                                x_pt, self.ypos_pt + self.height_pt,
                                                                (sign, 0), self.yvgridpath)
                    self.axes[nextkey].setpositioner(apositioner)

        if self.xaxisat is not None:
            self.axisatv(self.axes["x"], self.axes["y"].convert(self.xaxisat))
        if self.yaxisat is not None:
            self.axisatv(self.axes["y"], self.axes["x"].convert(self.yaxisat))

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
            self.insert(axis.canvas)

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
        self.width = width
        self.height = height
        if width is None:
            if height is None:
                raise ValueError("specify width and/or height")
            else:
                self.width = ratio * self.height
        elif height is None:
            self.height = (1.0/ratio) * self.width
        self.width_pt = unit.topt(self.width)
        self.height_pt = unit.topt(self.height)

    def initaxes(self, axes):
        self.axes = {}
        for key, aaxis in axes.items():
            if aaxis is not None:
                if not isinstance(aaxis, axis.linkedaxis):
                    self.axes[key] = axis.anchoredaxis(aaxis, key)
                else:
                    self.axes[key] = aaxis
        for key, axisat in [("x", self.xaxisat), ("y", self.yaxisat)]:
            okey = key + "2"
            if not axes.has_key(key):
                if not axes.has_key(okey):
                    self.axes[key] = axis.anchoredaxis(axis.linear(), key)
                    self.axes[okey] = axis.linkedaxis(self.axes[key], okey)
                else:
                    self.axes[key] = axis.linkedaxis(self.axes[keyo], key)
            elif not axes.has_key(okey) and axisat is None:
                self.axes[okey] = axis.linkedaxis(self.axes[key], okey)

        if self.axes.has_key("x"):
            self.axes["x"].setpositioner(positioner.lineaxispos_pt(self.xpos_pt, self.ypos_pt,
                                                                   self.xpos_pt + self.width_pt, self.ypos_pt,
                                                                   (0, 1), self.xvgridpath))
            self.xbasepath = self.axes["x"].basepath
            self.xvbasepath = self.axes["x"].vbasepath
            self.xgridpath = self.axes["x"].gridpath
            self.xtickpoint_pt = self.axes["x"].tickpoint_pt
            self.xtickpoint = self.axes["x"].tickpoint
            self.xvtickpoint_pt = self.axes["x"].vtickpoint_pt
            self.xvtickpoint = self.axes["x"].tickpoint
            self.xtickdirection = self.axes["x"].tickdirection
            self.xvtickdirection = self.axes["x"].vtickdirection

        if self.axes.has_key("x2"):
            self.axes["x2"].setpositioner(positioner.lineaxispos_pt(self.xpos_pt, self.ypos_pt + self.height_pt,
                                                                    self.xpos_pt + self.width_pt, self.ypos_pt + self.height_pt,
                                                                    (0, -1), self.xvgridpath))
        if self.axes.has_key("y"):
            self.axes["y"].setpositioner(positioner.lineaxispos_pt(self.xpos_pt, self.ypos_pt,
                                                                   self.xpos_pt, self.ypos_pt + self.height_pt,
                                                                   (1, 0), self.yvgridpath))
            self.ybasepath = self.axes["y"].basepath
            self.yvbasepath = self.axes["y"].vbasepath
            self.ygridpath = self.axes["y"].gridpath
            self.ytickpoint_pt = self.axes["y"].tickpoint_pt
            self.ytickpoint = self.axes["y"].tickpoint
            self.yvtickpoint_pt = self.axes["y"].vtickpoint_pt
            self.yvtickpoint = self.axes["y"].tickpoint
            self.ytickdirection = self.axes["y"].tickdirection
            self.yvtickdirection = self.axes["y"].vtickdirection

        if self.axes.has_key("y2"):
            self.axes["y2"].setpositioner(positioner.lineaxispos_pt(self.xpos_pt + self.width_pt, self.ypos_pt,
                                                                    self.xpos_pt + self.width_pt, self.ypos_pt + self.height_pt,
                                                                    (-1, 0), self.yvgridpath))

        self.axesnames = ([], [])
        for key in self.axes.keys():
            if len(key) != 1 and (not key[1:].isdigit() or key[1:] == "1"):
                raise ValueError("invalid axis count")
            if key[0] == "x":
                self.axesnames[0].append(key)
            elif key[0] == "y":
                self.axesnames[1].append(key)
            else:
                raise ValueError("invalid axis name")

    def __init__(self, xpos=0, ypos=0, width=None, height=None, ratio=goldenmean,
                 key=None, backgroundattrs=None, axesdist=0.8*unit.v_cm,
                 xaxisat=None, yaxisat=None, **axes):
        canvas.canvas.__init__(self)
        self.xpos = xpos
        self.ypos = ypos
        self.xpos_pt = unit.topt(self.xpos)
        self.ypos_pt = unit.topt(self.ypos)
        self.xaxisat = xaxisat
        self.yaxisat = yaxisat
        self.initwidthheight(width, height, ratio)
        self.initaxes(axes)
        self.key = key
        self.backgroundattrs = backgroundattrs
        self.axesdist = axesdist
        self.axesdist_pt = unit.topt(axesdist)
        self.plotitems = []
        self.domethods = [self.dolayout, self.dobackground, self.doaxes, self.dodata, self.dokey]
        self.haslayout = 0

    def bbox(self):
        self.finish()
        return canvas.canvas.bbox(self)

    def registerresources(self, registry):
        self.finish()
        return canvas.canvas.registerresources(self, registry)

    def outputPS(self, file):
        self.finish()
        canvas.canvas.outputPS(self, file)

    def outputPDF(self, file):
        self.finish()
        canvas.canvas.outputPDF(self, file)



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
