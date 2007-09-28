# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2002-2004 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2003-2004 Michael Schindler <m-schindler@users.sourceforge.net>
# Copyright (C) 2002-2006 André Wobst <wobsta@users.sourceforge.net>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA


import math, re, string, warnings
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
        self.usedcolumnnames = []
        for privatedata, s in zip(self.privatedatalist, self.styles):
            self.usedcolumnnames.extend(s.columnnames(privatedata, self.sharedata, graph, self.data.columnnames))

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
                useitems.append((columnname, self.dynamiccolumns[columnname]))
            except KeyError:
                useitems.append((columnname, self.data.columns[columnname]))
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


class graph(canvas.canvas):

    def __init__(self):
        canvas.canvas.__init__(self)
        self.axes = {}
        self.plotitems = []
        self._calls = {}
        self.didranges = 0
        self.didstyles = 0

    def did(self, method, *args, **kwargs):
        if not self._calls.has_key(method):
            self._calls[method] = []
        for callargs in self._calls[method]:
            if callargs == (args, kwargs):
                return 1
        self._calls[method].append((args, kwargs))
        return 0

    def bbox(self):
        self.finish()
        return canvas.canvas.bbox(self)

    def registerPS(self, registry):
        self.finish()
        canvas.canvas.registerPS(self, registry)

    def registerPDF(self, registry):
        self.finish()
        canvas.canvas.registerPDF(self, registry)

    def processPS(self, file, writer, context, registry, bbox):
        self.finish()
        canvas.canvas.processPS(self, file, writer, context, registry, bbox)

    def processPDF(self, file, writer, context, registry, bbox):
        self.finish()
        canvas.canvas.processPDF(self, file, writer, context, registry, bbox)

    def plot(self, data, styles=None, rangewarning=1):
        if self.didranges and rangewarning:
            warnings.warn("axes ranges have already been analysed; no further adjustments will be performed")
        if self.didstyles:
            raise RuntimeError("can't plot further data after dostyles() has been executed")
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
        if self.didranges:
            for aplotitem in plotitems:
                aplotitem.makedynamicdata(self)
        if singledata:
            return plotitems[0]
        else:
            return plotitems

    def doranges(self):
        if self.did(self.doranges):
            return
        for plotitem in self.plotitems:
            plotitem.adjustaxesstatic(self)
        for plotitem in self.plotitems:
            plotitem.makedynamicdata(self)
        for plotitem in self.plotitems:
            plotitem.adjustaxesdynamic(self)
        self.didranges = 1

    def doaxiscreate(self, axisname):
        if self.did(self.doaxiscreate, axisname):
            return
        self.doaxispositioner(axisname)
        self.axes[axisname].create()

    def dolayout(self):
        raise NotImplementedError

    def dobackground(self):
        pass

    def doaxes(self):
        raise NotImplementedError

    def dostyles(self):
        if self.did(self.dostyles):
            return
        self.dolayout()
        self.dobackground()

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
            plotitem.selectstyles(self, styleindex[stylesid(plotitem.styles)],
                                        styletotal[stylesid(plotitem.styles)])

        self.didstyles = 1

    def doplot(self, plotitem):
        if self.did(self.doplot, plotitem):
            return
        self.dostyles()
        plotitem.draw(self)

    def dodata(self):
        for plotitem in self.plotitems:
            self.doplot(plotitem)

    def dokey(self):
        raise NotImplementedError

    def finish(self):
        self.dobackground()
        self.doaxes()
        self.dodata()
        self.dokey()


class graphxy(graph):

    def __init__(self, xpos=0, ypos=0, width=None, height=None, ratio=goldenmean,
                 key=None, backgroundattrs=None, axesdist=0.8*unit.v_cm,
                 xaxisat=None, yaxisat=None, **axes):
        graph.__init__(self)

        self.xpos = xpos
        self.ypos = ypos
        self.xpos_pt = unit.topt(self.xpos)
        self.ypos_pt = unit.topt(self.ypos)
        self.xaxisat = xaxisat
        self.yaxisat = yaxisat
        self.key = key
        self.backgroundattrs = backgroundattrs
        self.axesdist_pt = unit.topt(axesdist)

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

        for axisname, aaxis in axes.items():
            if aaxis is not None:
                if not isinstance(aaxis, axis.linkedaxis):
                    self.axes[axisname] = axis.anchoredaxis(aaxis, self.texrunner, axisname)
                else:
                    self.axes[axisname] = aaxis
        for axisname, axisat in [("x", xaxisat), ("y", yaxisat)]:
            okey = axisname + "2"
            if not axes.has_key(axisname):
                if not axes.has_key(okey):
                    self.axes[axisname] = axis.anchoredaxis(axis.linear(), self.texrunner, axisname)
                    self.axes[okey] = axis.linkedaxis(self.axes[axisname], okey)
                else:
                    self.axes[axisname] = axis.linkedaxis(self.axes[okey], axisname)
            elif not axes.has_key(okey) and axisat is None:
                self.axes[okey] = axis.linkedaxis(self.axes[axisname], okey)

        if self.axes.has_key("x"):
            self.xbasepath = self.axes["x"].basepath
            self.xvbasepath = self.axes["x"].vbasepath
            self.xgridpath = self.axes["x"].gridpath
            self.xtickpoint_pt = self.axes["x"].tickpoint_pt
            self.xtickpoint = self.axes["x"].tickpoint
            self.xvtickpoint_pt = self.axes["x"].vtickpoint_pt
            self.xvtickpoint = self.axes["x"].tickpoint
            self.xtickdirection = self.axes["x"].tickdirection
            self.xvtickdirection = self.axes["x"].vtickdirection

        if self.axes.has_key("y"):
            self.ybasepath = self.axes["y"].basepath
            self.yvbasepath = self.axes["y"].vbasepath
            self.ygridpath = self.axes["y"].gridpath
            self.ytickpoint_pt = self.axes["y"].tickpoint_pt
            self.ytickpoint = self.axes["y"].tickpoint
            self.yvtickpoint_pt = self.axes["y"].vtickpoint_pt
            self.yvtickpoint = self.axes["y"].tickpoint
            self.ytickdirection = self.axes["y"].tickdirection
            self.yvtickdirection = self.axes["y"].vtickdirection

        self.axesnames = ([], [])
        for axisname, aaxis in self.axes.items():
            if axisname[0] not in "xy" or (len(axisname) != 1 and (not axisname[1:].isdigit() or
                                                                   axisname[1:] == "1")):
                raise ValueError("invalid axis name")
            if axisname[0] == "x":
                self.axesnames[0].append(axisname)
            else:
                self.axesnames[1].append(axisname)
            aaxis.setcreatecall(self.doaxiscreate, axisname)


    def pos_pt(self, x, y, xaxis=None, yaxis=None):
        if xaxis is None:
            xaxis = self.axes["x"]
        if yaxis is None:
            yaxis = self.axes["y"]
        return (self.xpos_pt + xaxis.convert(x)*self.width_pt,
                self.ypos_pt + yaxis.convert(y)*self.height_pt)

    def pos(self, x, y, xaxis=None, yaxis=None):
        if xaxis is None:
            xaxis = self.axes["x"]
        if yaxis is None:
            yaxis = self.axes["y"]
        return (self.xpos + xaxis.convert(x)*self.width,
                self.ypos + yaxis.convert(y)*self.height)

    def vpos_pt(self, vx, vy):
        return (self.xpos_pt + vx*self.width_pt,
                self.ypos_pt + vy*self.height_pt)

    def vpos(self, vx, vy):
        return (self.xpos + vx*self.width,
                self.ypos + vy*self.height)

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

    def doaxispositioner(self, axisname):
        if self.did(self.doaxispositioner, axisname):
            return
        self.doranges()
        if axisname == "x":
            self.axes["x"].setpositioner(positioner.lineaxispos_pt(self.xpos_pt, self.ypos_pt,
                                                                   self.xpos_pt + self.width_pt, self.ypos_pt,
                                                                   (0, 1), self.xvgridpath))
        elif axisname == "x2":
            self.axes["x2"].setpositioner(positioner.lineaxispos_pt(self.xpos_pt, self.ypos_pt + self.height_pt,
                                                                    self.xpos_pt + self.width_pt, self.ypos_pt + self.height_pt,
                                                                    (0, -1), self.xvgridpath))
        elif axisname == "y":
            self.axes["y"].setpositioner(positioner.lineaxispos_pt(self.xpos_pt, self.ypos_pt,
                                                                   self.xpos_pt, self.ypos_pt + self.height_pt,
                                                                   (1, 0), self.yvgridpath))
        elif axisname == "y2":
            self.axes["y2"].setpositioner(positioner.lineaxispos_pt(self.xpos_pt + self.width_pt, self.ypos_pt,
                                                                    self.xpos_pt + self.width_pt, self.ypos_pt + self.height_pt,
                                                                    (-1, 0), self.yvgridpath))
        else:
            if axisname[1:] == "3":
                dependsonaxisname = axisname[0]
            else:
                dependsonaxisname = "%s%d" % (axisname[0], int(axisname[1:]) - 2)
            self.doaxiscreate(dependsonaxisname)
            sign = 2*(int(axisname[1:]) % 2) - 1
            if axisname[0] == "x":
                y_pt = self.axes[dependsonaxisname].positioner.y1_pt - sign * (self.axes[dependsonaxisname].canvas.extent_pt + self.axesdist_pt)
                self.axes[axisname].setpositioner(positioner.lineaxispos_pt(self.xpos_pt, y_pt,
                                                                            self.xpos_pt + self.width_pt, y_pt,
                                                                            (0, sign), self.xvgridpath))
            else:
                x_pt = self.axes[dependsonaxisname].positioner.x1_pt - sign * (self.axes[dependsonaxisname].canvas.extent_pt + self.axesdist_pt)
                self.axes[axisname].setpositioner(positioner.lineaxispos_pt(x_pt, self.ypos_pt,
                                                                            x_pt, self.ypos_pt + self.height_pt,
                                                                            (sign, 0), self.yvgridpath))

    def dolayout(self):
        if self.did(self.dolayout):
            return
        for axisname in self.axes.keys():
            self.doaxiscreate(axisname)
        if self.xaxisat is not None:
            self.axisatv(self.axes["x"], self.axes["y"].convert(self.xaxisat))
        if self.yaxisat is not None:
            self.axisatv(self.axes["y"], self.axes["x"].convert(self.yaxisat))

    def dobackground(self):
        if self.did(self.dobackground):
            return
        if self.backgroundattrs is not None:
            self.draw(path.rect_pt(self.xpos_pt, self.ypos_pt, self.width_pt, self.height_pt),
                      self.backgroundattrs)

    def doaxes(self):
        if self.did(self.doaxes):
            return
        self.dolayout()
        self.dobackground()
        for axis in self.axes.values():
            self.insert(axis.canvas)

    def dokey(self):
        if self.did(self.dokey):
            return
        self.dobackground()
        self.dostyles()
        if self.key is not None:
            c = self.key.paint(self.plotitems)
            bbox = c.bbox()
            def parentchildalign(pmin, pmax, cmin, cmax, pos, dist, inside):
                ppos = pmin+0.5*(cmax-cmin)+dist+pos*(pmax-pmin-cmax+cmin-2*dist)
                cpos = 0.5*(cmin+cmax)+(1-inside)*(1-2*pos)*(cmax-cmin+2*dist)
                return ppos-cpos
            if bbox:
                x = parentchildalign(self.xpos_pt, self.xpos_pt+self.width_pt,
                                     bbox.llx_pt, bbox.urx_pt,
                                     self.key.hpos, unit.topt(self.key.hdist), self.key.hinside)
                y = parentchildalign(self.ypos_pt, self.ypos_pt+self.height_pt,
                                     bbox.lly_pt, bbox.ury_pt,
                                     self.key.vpos, unit.topt(self.key.vdist), self.key.vinside)
                self.insert(c, [trafo.translate_pt(x, y)])


class graphxyz(graphxy):

    class central:

        def __init__(self, distance, phi, theta, anglefactor=math.pi/180):
            phi *= anglefactor
            theta *= anglefactor

            self.a = (-math.sin(phi), math.cos(phi), 0)
            self.b = (-math.cos(phi)*math.sin(theta),
                      -math.sin(phi)*math.sin(theta),
                      math.cos(theta))
            self.eye = (distance*math.cos(phi)*math.cos(theta),
                        distance*math.sin(phi)*math.cos(theta),
                        distance*math.sin(theta))

        def point(self, x, y, z):
            d0 = (self.a[0]*self.b[1]*(z-self.eye[2])
                + self.a[2]*self.b[0]*(y-self.eye[1])
                + self.a[1]*self.b[2]*(x-self.eye[0])
                - self.a[2]*self.b[1]*(x-self.eye[0])
                - self.a[0]*self.b[2]*(y-self.eye[1])
                - self.a[1]*self.b[0]*(z-self.eye[2]))
            da = (self.eye[0]*self.b[1]*(z-self.eye[2])
                + self.eye[2]*self.b[0]*(y-self.eye[1])
                + self.eye[1]*self.b[2]*(x-self.eye[0])
                - self.eye[2]*self.b[1]*(x-self.eye[0])
                - self.eye[0]*self.b[2]*(y-self.eye[1])
                - self.eye[1]*self.b[0]*(z-self.eye[2]))
            db = (self.a[0]*self.eye[1]*(z-self.eye[2])
                + self.a[2]*self.eye[0]*(y-self.eye[1])
                + self.a[1]*self.eye[2]*(x-self.eye[0])
                - self.a[2]*self.eye[1]*(x-self.eye[0])
                - self.a[0]*self.eye[2]*(y-self.eye[1])
                - self.a[1]*self.eye[0]*(z-self.eye[2]))
            return da/d0, db/d0


    class parallel:

        def __init__(self, phi, theta, anglefactor=math.pi/180):
            phi *= anglefactor
            theta *= anglefactor

            self.a = (-math.sin(phi), math.cos(phi), 0)
            self.b = (-math.cos(phi)*math.sin(theta),
                      -math.sin(phi)*math.sin(theta),
                      math.cos(theta))

        def point(self, x, y, z):
            return self.a[0]*x+self.a[1]*y+self.a[2]*z, self.b[0]*x+self.b[1]*y+self.b[2]*z


    def __init__(self, xpos=0, ypos=0, size=None,
                 xscale=1, yscale=1, zscale=1/goldenmean,
                 projector=central(10, -30, 30),
                 key=None, backgroundattrs=None,
                 **axes):
        graph.__init__(self)

        self.xpos = xpos
        self.ypos = ypos
        self.size = size
        self.xpos_pt = unit.topt(xpos)
        self.ypos_pt = unit.topt(ypos)
        self.size_pt = unit.topt(size)
        self.xscale = xscale
        self.yscale = yscale
        self.zscale = zscale
        self.projector = projector
        self.key = key
        self.backgroundattrs = backgroundattrs

        for axisname, aaxis in axes.items():
            if aaxis is not None:
                if not isinstance(aaxis, axis.linkedaxis):
                    self.axes[axisname] = axis.anchoredaxis(aaxis, self.texrunner, axisname)
                else:
                    self.axes[axisname] = aaxis

        for axisname in ["x", "y", "z"]:
            if not axes.has_key(axisname):
                self.axes[axisname] = axis.anchoredaxis(axis.linear(), self.texrunner, axisname)

        if self.axes.has_key("x"):
            self.xbasepath = self.axes["x"].basepath
            self.xvbasepath = self.axes["x"].vbasepath
            self.xgridpath = self.axes["x"].gridpath
            self.xtickpoint_pt = self.axes["x"].tickpoint_pt
            self.xtickpoint = self.axes["x"].tickpoint
            self.xvtickpoint = self.axes["x"].tickpoint
            self.xtickdirection = self.axes["x"].tickdirection

        if self.axes.has_key("y"):
            self.ybasepath = self.axes["y"].basepath
            self.yvbasepath = self.axes["y"].vbasepath
            self.ygridpath = self.axes["y"].gridpath
            self.ytickpoint_pt = self.axes["y"].tickpoint_pt
            self.ytickpoint = self.axes["y"].tickpoint
            self.yvtickpoint = self.axes["y"].tickpoint
            self.ytickdirection = self.axes["y"].tickdirection

        if self.axes.has_key("z"):
            self.zbasepath = self.axes["z"].basepath
            self.zvbasepath = self.axes["z"].vbasepath
            self.zgridpath = self.axes["z"].gridpath
            self.ztickpoint_pt = self.axes["z"].tickpoint_pt
            self.ztickpoint = self.axes["z"].tickpoint
            self.zvtickpoint = self.axes["z"].tickpoint
            self.ztickdirection = self.axes["z"].tickdirection

        self.axesnames = ([], [], [])
        for axisname, aaxis in self.axes.items():
            if axisname[0] not in "xyz" or (len(axisname) != 1 and (not axisname[1:].isdigit() or
                                                                    axisname[1:] == "1")):
                raise ValueError("invalid axis name")
            if axisname[0] == "x":
                self.axesnames[0].append(axisname)
            elif axisname[0] == "y":
                self.axesnames[1].append(axisname)
            else:
                self.axesnames[2].append(axisname)
            aaxis.setcreatecall(self.doaxiscreate, axisname)

    def pos_pt(self, x, y, z, xaxis=None, yaxis=None, zaxis=None):
        if xaxis is None:
            xaxis = self.axes["x"]
        if yaxis is None:
            yaxis = self.axes["y"]
        if zaxis is None:
            zaxis = self.axes["z"]
        return self.vpos_pt(xaxis.convert(x), yaxis.convert(y), zaxis.convert(y))

    def pos(self, x, y, z, xaxis=None, yaxis=None, zaxis=None):
        if xaxis is None:
            xaxis = self.axes["x"]
        if yaxis is None:
            yaxis = self.axes["y"]
        if zaxis is None:
            zaxis = self.axes["z"]
        return self.vpos(xaxis.convert(x), yaxis.convert(y), zaxis.convert(y))

    def vpos_pt(self, vx, vy, vz):
        x, y = self.projector.point(2*self.xscale*(vx - 0.5),
                                    2*self.yscale*(vy - 0.5),
                                    2*self.zscale*(vz - 0.5))
        return self.xpos_pt+x*self.size_pt, self.ypos_pt+y*self.size_pt

    def vpos(self, vx, vy, vz):
        x, y = self.projector.point(2*self.xscale*(vx - 0.5),
                                    2*self.yscale*(vy - 0.5),
                                    2*self.zscale*(vz - 0.5))
        return self.xpos+x*self.size, self.ypos+y*self.size

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
#         return (path.line_pt(*(self.vpos_pt(v1, 0, 0) + self.vpos_pt(v2, 0, 0))) +
#                 path.line_pt(*(self.vpos_pt(v1, 0, 1) + self.vpos_pt(v2, 0, 1))) +
#                 path.line_pt(*(self.vpos_pt(v1, 1, 1) + self.vpos_pt(v2, 1, 1))) +
#                 path.line_pt(*(self.vpos_pt(v1, 1, 0) + self.vpos_pt(v2, 1, 0))))
# 
#     def vybaseline(self, axis, v1, v2):
#         return (path.line_pt(*(self.vpos_pt(0, v1, 0) + self.vpos_pt(0, v2, 0))) +
#                 path.line_pt(*(self.vpos_pt(0, v1, 1) + self.vpos_pt(0, v2, 1))) +
#                 path.line_pt(*(self.vpos_pt(1, v1, 1) + self.vpos_pt(1, v2, 1))) +
#                 path.line_pt(*(self.vpos_pt(1, v1, 0) + self.vpos_pt(1, v2, 0))))
# 
#     def vzbaseline(self, axis, v1, v2):
#         return (path.line_pt(*(self.vpos_pt(0, 0, v1) + self.vpos_pt(0, 0, v2))) +
#                 path.line_pt(*(self.vpos_pt(0, 1, v1) + self.vpos_pt(0, 1, v2))) +
#                 path.line_pt(*(self.vpos_pt(1, 1, v1) + self.vpos_pt(1, 1, v2))) +
#                 path.line_pt(*(self.vpos_pt(1, 0, v1) + self.vpos_pt(1, 0, v2))))

    def vgeodesic(self, vx1, vy1, vz1, vx2, vy2, vz2):
        """returns a geodesic path between two points in graph coordinates"""
        return path.line_pt(*(self.vpos_pt(vx1, vy1, vz1) + self.vpos_pt(vx2, vy2, vz2)))

    def vgeodesic_el(self, vx1, vy1, vz1, vx2, vy2, vz2):
        """returns a geodesic path element between two points in graph coordinates"""
        return path.lineto_pt(*(self.vpos_pt(vx1, vy1, vz1) + self.vpos_pt(vx2, vy2, vz2)))

    def vcap_pt(self, coordinate, length_pt, vx, vy, vz):
        """returns an error cap path for a given coordinate, lengths and
        point in graph coordinates"""
        raise NotImplementedError
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

    def xvtickpoint_pt(self, vx):
        return self.vpos_pt(vx, 0, 0)

    def yvtickpoint_pt(self, vy):
        return self.vpos_pt(1, vy, 0)

    def zvtickpoint_pt(self, vz):
        return self.vpos_pt(0, 0, vz)

    def xvtickdirection(self, vx):
        x1_pt, y1_pt = self.vpos_pt(vx, 0, 0)
        x2_pt, y2_pt = self.vpos_pt(vx, 1, 0)
        dx_pt = x2_pt - x1_pt
        dy_pt = y2_pt - y1_pt
        norm = math.hypot(dx_pt, dy_pt)
        return dx_pt/norm, dy_pt/norm

    def yvtickdirection(self, vy):
        x1_pt, y1_pt = self.vpos_pt(1, vy, 0)
        x2_pt, y2_pt = self.vpos_pt(0, vy, 0)
        dx_pt = x2_pt - x1_pt
        dy_pt = y2_pt - y1_pt
        norm = math.hypot(dx_pt, dy_pt)
        return dx_pt/norm, dy_pt/norm

    def zvtickdirection(self, vz):
        x1_pt, y1_pt = self.vpos_pt(0, 0, vz)
        x2_pt, y2_pt = self.vpos_pt(1, 1, vz)
        dx_pt = x2_pt - x1_pt
        dy_pt = y2_pt - y1_pt
        norm = math.hypot(dx_pt, dy_pt)
        return dx_pt/norm, dy_pt/norm

    def yvgridpath(self, vy):
        raise NotImplementedError

    def zvgridpath(self, vz):
        raise NotImplementedError

    def xvgridpath(self, vx):
        raise NotImplementedError

    def yvgridpath(self, vy):
        raise NotImplementedError

    def zvgridpath(self, vz):
        raise NotImplementedError

    def doaxispositioner(self, axisname):
        if self.did(self.doaxispositioner, axisname):
            return
        self.doranges()
        if axisname == "x":
            x1_pt, y1_pt = self.vpos_pt(0, 0, 0)
            x2_pt, y2_pt = self.vpos_pt(1, 0, 0)
            self.axes["x"].setpositioner(positioner.flexlineaxispos_pt(self.xvtickpoint_pt, self.xvtickdirection, self.xvgridpath))
        elif axisname == "y":
            x1_pt, y1_pt = self.vpos_pt(1, 0, 0)
            x2_pt, y2_pt = self.vpos_pt(1, 1, 0)
            self.axes["y"].setpositioner(positioner.flexlineaxispos_pt(self.yvtickpoint_pt, self.yvtickdirection, self.yvgridpath))
        elif axisname == "z":
            x1_pt, y1_pt = self.vpos_pt(0, 0, 0)
            x2_pt, y2_pt = self.vpos_pt(0, 0, 1)
            self.axes["z"].setpositioner(positioner.flexlineaxispos_pt(self.zvtickpoint_pt, self.zvtickdirection, self.yvgridpath))
        else:
            raise NotImplementedError("multiple axes not yet supported")

    def dolayout(self):
        if self.did(self.dolayout):
            return
        for axisname in self.axes.keys():
            self.doaxiscreate(axisname)

    def dobackground(self):
        if self.did(self.dobackground):
            return

    def doaxes(self):
        if self.did(self.doaxes):
            return
        self.dolayout()
        self.dobackground()
        for axis in self.axes.values():
            self.insert(axis.canvas)

    def dokey(self):
        if self.did(self.dokey):
            return
        self.dobackground()
        self.dostyles()
        if self.key is not None:
            c = self.key.paint(self.plotitems)
            bbox = c.bbox()
            def parentchildalign(pmin, pmax, cmin, cmax, pos, dist, inside):
                ppos = pmin+0.5*(cmax-cmin)+dist+pos*(pmax-pmin-cmax+cmin-2*dist)
                cpos = 0.5*(cmin+cmax)+(1-inside)*(1-2*pos)*(cmax-cmin+2*dist)
                return ppos-cpos
            if bbox:
                x = parentchildalign(self.xpos_pt, self.xpos_pt+self.width_pt,
                                     bbox.llx_pt, bbox.urx_pt,
                                     self.key.hpos, unit.topt(self.key.hdist), self.key.hinside)
                y = parentchildalign(self.ypos_pt, self.ypos_pt+self.height_pt,
                                     bbox.lly_pt, bbox.ury_pt,
                                     self.key.vpos, unit.topt(self.key.vdist), self.key.vinside)
                self.insert(c, [trafo.translate_pt(x, y)])
