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
from pyx import canvas, color, attr, text, style, unit, box, path
from pyx import trafo as trafomodule
from pyx.graph.axis import tick


goldenmean = 0.5 * (math.sqrt(5) + 1)


class axiscanvas(canvas.canvas):
    """axis canvas
    - an axis canvas is a regular canvas returned by an
      axispainters painter method
    - it contains a PyX length extent to be used for the
      alignment of additional axes; the axis extent should
      be handled by the axispainters painter method; you may
      apprehend this as a size information comparable to a
      bounding box, which must be handled manually
    - it contains a list of textboxes called labels which are
      used to rate the distances between the labels if needed
      by the axis later on; the painter method has not only to
      insert the labels into this canvas, but should also fill
      this list, when a rating of the distances should be
      performed by the axis"""

    # __implements__ = sole implementation

    def __init__(self, *args, **kwargs):
        """initializes the instance
        - sets extent to zero
        - sets labels to an empty list"""
        canvas.canvas.__init__(self, *args, **kwargs)
        self.extent = 0
        self.labels = []


class rotatetext:
    """create rotations accordingly to tick directions
    - upsidedown rotations are suppressed by rotating them by another 180 degree"""

    # __implements__ = sole implementation

    def __init__(self, direction, epsilon=1e-10):
        """initializes the instance
        - direction is an angle to be used relative to the tick direction
        - epsilon is the value by which 90 degrees can be exceeded before
          an 180 degree rotation is added"""
        self.direction = direction
        self.epsilon = epsilon

    def trafo(self, dx, dy):
        """returns a rotation transformation accordingly to the tick direction
        - dx and dy are the direction of the tick"""
        direction = self.direction + math.atan2(dy, dx) * 180 / math.pi
        while (direction > 180 + self.epsilon):
            direction -= 360
        while (direction < -180 - self.epsilon):
            direction += 360
        while (direction > 90 + self.epsilon):
            direction -= 180
        while (direction < -90 - self.epsilon):
            direction += 180
        return trafomodule.rotate(direction)


rotatetext.parallel = rotatetext(90)
rotatetext.orthogonal = rotatetext(180)


class _Iaxispainter:
    "class for painting axes"

    def paint(self, axispos, axis, ac=None):
        """paint the axis into an axiscanvas
        - returns the axiscanvas
        - when no axiscanvas is provided (the typical case), a new
          axiscanvas is created. however, when extending an painter
          by inheritance, painting on the same axiscanvas is supported
          by setting the axiscanvas attribute
        - axispos is an instance, which implements _Iaxispos to
          define the tick positions
        - the axis and should not be modified (we may
          add some temporary variables like axis.ticks[i].temp_xxx,
          which might be used just temporary) -- the idea is that
          all things can be used several times
        - also do not modify the instance (self) -- even this
          instance might be used several times; thus do not modify
          attributes like self.titleattrs etc. (use local copies)
        - the method might access some additional attributes from
          the axis, e.g. the axis title -- the axis painter should
          document this behavior and rely on the availability of
          those attributes -> it becomes a question of the proper
          usage of the combination of axis & axispainter
        - the axiscanvas is a axiscanvas instance and should be
          filled with ticks, labels, title, etc.; note that the
          extent and labels instance variables should be handled
          as documented in the axiscanvas"""


class _Iaxispos:
    """interface definition of axis tick position methods
    - these methods are used for the postitioning of the ticks
      when painting an axis"""
    # TODO: should we add a local transformation (for label text etc?)
    #       (this might replace tickdirection (and even tickposition?))

    def basepath(self, x1=None, x2=None):
        """return the basepath as a path
        - x1 is the start position; if not set, the basepath starts
          from the beginning of the axis, which might imply a
          value outside of the graph coordinate range [0; 1]
        - x2 is analogous to x1, but for the end position"""

    def vbasepath(self, v1=None, v2=None):
        """return the basepath as a path
        - like basepath, but for graph coordinates"""

    def gridpath(self, x):
        """return the gridpath as a path for a given position x
        - might return None when no gridpath is available"""

    def vgridpath(self, v):
        """return the gridpath as a path for a given position v
        in graph coordinates
        - might return None when no gridpath is available"""

    def tickpoint_pt(self, x):
        """return the position at the basepath as a tuple (x, y) in
        postscript points for the position x"""

    def tickpoint(self, x):
        """return the position at the basepath as a tuple (x, y) in
        in PyX length for the position x"""

    def vtickpoint_pt(self, v):
        "like tickpoint_pt, but for graph coordinates"

    def vtickpoint(self, v):
        "like tickpoint, but for graph coordinates"

    def tickdirection(self, x):
        """return the direction of a tick as a tuple (dx, dy) for the
        position x (the direction points towards the graph)"""

    def vtickdirection(self, v):
        """like tickposition, but for graph coordinates"""


class _axispos:
    """implements those parts of _Iaxispos which can be build
    out of the axis convert method and other _Iaxispos methods
    - base _Iaxispos methods, which need to be implemented:
      - vbasepath
      - vgridpath
      - vtickpoint_pt
      - vtickdirection
    - other methods needed for _Iaxispos are build out of those
      listed above when this class is inherited"""

    def __init__(self, convert):
        """initializes the instance
        - convert is a convert method from an axis"""
        self.convert = convert

    def basepath(self, x1=None, x2=None):
        if x1 is None:
            if x2 is None:
                return self.vbasepath()
            else:
                return self.vbasepath(v2=self.convert(x2))
        else:
            if x2 is None:
                return self.vbasepath(v1=self.convert(x1))
            else:
                return self.vbasepath(v1=self.convert(x1), v2=self.convert(x2))

    def gridpath(self, x):
        return self.vgridpath(self.convert(x))

    def tickpoint_pt(self, x):
        return self.vtickpoint_pt(self.convert(x))

    def tickpoint(self, x):
        return self.vtickpoint(self.convert(x))

    def vtickpoint(self, v):
        return [x * unit.t_pt for x in self.vtickpoint(v)]

    def tickdirection(self, x):
        return self.vtickdirection(self.convert(x))


class pathaxispos(_axispos):
    """axis tick position methods along an arbitrary path"""

    __implements__ = _Iaxispos

    def __init__(self, p, convert, direction=1):
        self.path = p
        self.normpath = path.normpath(p)
        self.arclen_pt = self.normpath.arclen_pt()
        self.arclen = self.arclen_pt * unit.t_pt
        _axispos.__init__(self, convert)
        self.direction = direction

    def vbasepath(self, v1=None, v2=None):
        if v1 is None:
            if v2 is None:
                return self.path
            else:
                return self.normpath.split(self.normpath.arclentoparam(v2 * self.arclen))[0]
        else:
            if v2 is None:
                return self.normpath.split(self.normpath.arclentoparam(v1 * self.arclen))[1]
            else:
                return self.normpath.split(*self.normpath.arclentoparam([v1 * self.arclen, v2 * self.arclen]))[1]

    def vgridpath(self, v):
        return None

    def vtickpoint_pt(self, v):
        return self.normpath.at_pt(self.normpath.arclentoparam(v * self.arclen))

    def vtickdirection(self, v):
        t= self.normpath.tangent(self.normpath.arclentoparam(v * self.arclen))
        tbegin = t.begin_pt()
        tend = t.end_pt()
        dx = tend[0]-tbegin[0]
        dy = tend[1]-tbegin[1]
        norm = math.hypot(dx, dy)
        if self.direction == 1:
            return -dy/norm, dx/norm
        elif self.direction == -1:
            return dy/norm, -dx/norm
        raise RuntimeError("unknown direction")


class _title:
    """class for painting an axis title
    - the axis must have a title attribute when using this painter;
      this title might be None"""

    __implements__ = _Iaxispainter

    defaulttitleattrs = [text.halign.center, text.vshift.mathaxis]

    def __init__(self, titledist=0.3*unit.v_cm,
                       titleattrs=[],
                       titledirection=rotatetext.parallel,
                       titlepos=0.5,
                       texrunner=text.defaulttexrunner):
        """initialized the instance
        - titledist is a visual PyX length giving the distance
          of the title from the axis extent already there (a title might
          be added after labels or other things are plotted already)
        - titleattrs is a list of attributes for a texrunners text
          method; a single is allowed without being a list; None
          turns off the title
        - titledirection is an instance of rotatetext or None
        - titlepos is the position of the title in graph coordinates
        - texrunner is the texrunner to be used to create text
          (the texrunner is available for further use in derived
          classes as instance variable texrunner)"""
        self.titledist = titledist
        self.titleattrs = titleattrs
        self.titledirection = titledirection
        self.titlepos = titlepos
        self.texrunner = texrunner

    def paint(self, axispos, axis, ac=None):
        if ac is None:
            ac = axiscanvas()
        if axis.title is not None and self.titleattrs is not None:
            x, y = axispos.vtickpoint_pt(self.titlepos)
            dx, dy = axispos.vtickdirection(self.titlepos)
            titleattrs = self.defaulttitleattrs + self.titleattrs
            if self.titledirection is not None:
                titleattrs.append(self.titledirection.trafo(dx, dy))
            title = self.texrunner.text_pt(x, y, axis.title, titleattrs)
            ac.extent += self.titledist
            title.linealign(ac.extent, -dx, -dy)
            ac.extent += title.extent(dx, dy)
            ac.insert(title)
        return ac


class geometricseries(attr.changeattr):

    def __init__(self, initial, factor):
        self.initial = initial
        self.factor = factor

    def select(self, index, total):
        return self.initial * (self.factor ** index)


class ticklength(geometricseries): pass

_base = 0.12 * unit.v_cm

ticklength.SHORT = ticklength(_base/math.sqrt(64), 1/goldenmean)
ticklength.SHORt = ticklength(_base/math.sqrt(32), 1/goldenmean)
ticklength.SHOrt = ticklength(_base/math.sqrt(16), 1/goldenmean)
ticklength.SHort = ticklength(_base/math.sqrt(8), 1/goldenmean)
ticklength.Short = ticklength(_base/math.sqrt(4), 1/goldenmean)
ticklength.short = ticklength(_base/math.sqrt(2), 1/goldenmean)
ticklength.normal = ticklength(_base, 1/goldenmean)
ticklength.long = ticklength(_base*math.sqrt(2), 1/goldenmean)
ticklength.Long = ticklength(_base*math.sqrt(4), 1/goldenmean)
ticklength.LOng = ticklength(_base*math.sqrt(8), 1/goldenmean)
ticklength.LONg = ticklength(_base*math.sqrt(16), 1/goldenmean)
ticklength.LONG = ticklength(_base*math.sqrt(32), 1/goldenmean)


class regular(_title):
    """class for painting the ticks and labels of an axis
    - the inherited _title is used to paint the title of
      the axis
    - note that the type of the elements of ticks given as an argument
      of the paint method must be suitable for the tick position methods
      of the axis"""

    __implements__ = _Iaxispainter

    defaulttickattrs = []
    defaultgridattrs = []
    defaultbasepathattrs = [style.linecap.square]
    defaultlabelattrs = [text.halign.center, text.vshift.mathaxis]

    def __init__(self, innerticklength=ticklength.normal,
                       outerticklength=None,
                       tickattrs=[],
                       gridattrs=None,
                       basepathattrs=[],
                       labeldist=0.3*unit.v_cm,
                       labelattrs=[],
                       labeldirection=None,
                       labelhequalize=0,
                       labelvequalize=1,
                       **kwargs):
        """initializes the instance
        - innerticklength and outerticklength are changable
          visual PyX lengths for ticks, subticks, etc. plotted inside
          and outside of the graph; None turns off ticks inside or
          outside of the graph
        - tickattrs are a list of stroke attributes for the ticks;
          None turns off ticks
        - gridattrs are a list of lists used as stroke
          attributes for ticks, subticks etc.; None turns off
          the grid
        - basepathattrs are a list of stroke attributes for the base line
          of the axis; None turns off the basepath
        - labeldist is a visual PyX length for the distance of the labels
          from the axis basepath
        - labelattrs is a list of attributes for a texrunners text
          method; None turns off the labels
        - labeldirection is an instance of rotatetext or None
        - labelhequalize and labelvequalize (booleans) perform an equal
          alignment for straight vertical and horizontal axes, respectively
        - futher keyword arguments are passed to _axistitle"""
        self.innerticklength = innerticklength
        self.outerticklength = outerticklength
        self.tickattrs = tickattrs
        self.gridattrs = gridattrs
        self.basepathattrs = basepathattrs
        self.labeldist = labeldist
        self.labelattrs = labelattrs
        self.labeldirection = labeldirection
        self.labelhequalize = labelhequalize
        self.labelvequalize = labelvequalize
        _title.__init__(self, **kwargs)

    def paint(self, axispos, axis, ac=None):
        if ac is None:
            ac = axiscanvas()
        for t in axis.ticks:
            t.temp_v = axis.convert(t)
            t.temp_x, t.temp_y = axispos.vtickpoint_pt(t.temp_v)
            t.temp_dx, t.temp_dy = axispos.vtickdirection(t.temp_v)
        maxticklevel, maxlabellevel = tick.maxlevels(axis.ticks)

        # create & align t.temp_labelbox
        for t in axis.ticks:
            if t.labellevel is not None:
                labelattrs = attr.selectattrs(self.labelattrs, t.labellevel, maxlabellevel)
                if labelattrs is not None:
                    labelattrs = self.defaultlabelattrs + labelattrs
                    if self.labeldirection is not None:
                        labelattrs.append(self.labeldirection.trafo(t.temp_dx, t.temp_dy))
                    if t.labelattrs is not None:
                        labelattrs.extend(t.labelattrs)
                    t.temp_labelbox = self.texrunner.text_pt(t.temp_x, t.temp_y, t.label, labelattrs)
        if len(axis.ticks) > 1:
            equaldirection = 1
            for t in axis.ticks[1:]:
                if t.temp_dx != axis.ticks[0].temp_dx or t.temp_dy != axis.ticks[0].temp_dy:
                    equaldirection = 0
        else:
            equaldirection = 0
        if equaldirection and ((not axis.ticks[0].temp_dx and self.labelvequalize) or
                               (not axis.ticks[0].temp_dy and self.labelhequalize)):
            if self.labelattrs is not None:
                box.linealignequal([t.temp_labelbox for t in axis.ticks if t.labellevel is not None],
                                   self.labeldist, -axis.ticks[0].temp_dx, -axis.ticks[0].temp_dy)
        else:
            for t in axis.ticks:
                if t.labellevel is not None and self.labelattrs is not None:
                    t.temp_labelbox.linealign(self.labeldist, -t.temp_dx, -t.temp_dy)

        for t in axis.ticks:
            if t.ticklevel is not None:
                tickattrs = attr.selectattrs(self.defaulttickattrs + self.tickattrs, t.ticklevel, maxticklevel)
                if tickattrs is not None:
                    innerticklength = attr.selectattr(self.innerticklength, t.ticklevel, maxticklevel)
                    outerticklength = attr.selectattr(self.outerticklength, t.ticklevel, maxticklevel)
                    if innerticklength is not None or outerticklength is not None:
                        if innerticklength is None:
                            innerticklength = 0
                        if outerticklength is None:
                            outerticklength = 0
                        innerticklength_pt = unit.topt(innerticklength)
                        outerticklength_pt = unit.topt(outerticklength)
                        x1 = t.temp_x + t.temp_dx * innerticklength_pt
                        y1 = t.temp_y + t.temp_dy * innerticklength_pt
                        x2 = t.temp_x - t.temp_dx * outerticklength_pt
                        y2 = t.temp_y - t.temp_dy * outerticklength_pt
                        ac.stroke(path.line_pt(x1, y1, x2, y2), tickattrs)
                        if outerticklength is not None and outerticklength > ac.extent:
                            ac.extent = outerticklength
                        if outerticklength is not None and -innerticklength > ac.extent:
                            ac.extent = -innerticklength
            if self.gridattrs is not None:
                gridattrs = attr.selectattrs(self.defaultgridattrs + self.gridattrs, t.ticklevel, maxticklevel)
                if gridattrs is not None:
                    ac.stroke(axispos.vgridpath(t.temp_v), gridattrs)
            if t.labellevel is not None and self.labelattrs is not None:
                ac.insert(t.temp_labelbox)
                ac.labels.append(t.temp_labelbox)
                extent = t.temp_labelbox.extent(t.temp_dx, t.temp_dy) + self.labeldist
                if extent > ac.extent:
                    ac.extent = extent
        if self.basepathattrs is not None:
            ac.stroke(axispos.vbasepath(), self.defaultbasepathattrs + self.basepathattrs)

        # for t in axis.ticks:
        #     del t.temp_v    # we've inserted those temporary variables ... and do not care any longer about them
        #     del t.temp_x
        #     del t.temp_y
        #     del t.temp_dx
        #     del t.temp_dy
        #     if t.labellevel is not None and self.labelattrs is not None:
        #         del t.temp_labelbox

        _title.paint(self, axispos, axis, ac=ac)

        return ac


class linked(regular):
    """class for painting a linked axis
    - the inherited regular is used to paint the axis
    - modifies some constructor defaults"""

    __implements__ = _Iaxispainter

    def __init__(self, labelattrs=None,
                       titleattrs=None,
                       **kwargs):
        """initializes the instance
        - the labelattrs default is set to None thus skipping the labels
        - the titleattrs default is set to None thus skipping the title
        - all keyword arguments are passed to regular"""
        regular.__init__(self, labelattrs=labelattrs,
                               titleattrs=titleattrs,
                               **kwargs)


class subaxispos:
    """implementation of the _Iaxispos interface for a subaxis"""

    __implements__ = _Iaxispos

    def __init__(self, convert, baseaxispos, vmin, vmax, vminover, vmaxover):
        """initializes the instance
        - convert is the subaxis convert method
        - baseaxispos is the axispos instance of the base axis
        - vmin, vmax is the range covered by the subaxis in graph coordinates
        - vminover, vmaxover is the extended range of the subaxis including
          regions between several subaxes (for basepath drawing etc.)"""
        self.convert = convert
        self.baseaxispos = baseaxispos
        self.vmin = vmin
        self.vmax = vmax
        self.vminover = vminover
        self.vmaxover = vmaxover

    def basepath(self, x1=None, x2=None):
        if x1 is not None:
            v1 = self.vmin+self.convert(x1)*(self.vmax-self.vmin)
        else:
            v1 = self.vminover
        if x2 is not None:
            v2 = self.vmin+self.convert(x2)*(self.vmax-self.vmin)
        else:
            v2 = self.vmaxover
        return self.baseaxispos.vbasepath(v1, v2)

    def vbasepath(self, v1=None, v2=None):
        if v1 is not None:
            v1 = self.vmin+v1*(self.vmax-self.vmin)
        else:
            v1 = self.vminover
        if v2 is not None:
            v2 = self.vmin+v2*(self.vmax-self.vmin)
        else:
            v2 = self.vmaxover
        return self.baseaxispos.vbasepath(v1, v2)

    def gridpath(self, x):
        return self.baseaxispos.vgridpath(self.vmin+self.convert(x)*(self.vmax-self.vmin))

    def vgridpath(self, v):
        return self.baseaxispos.vgridpath(self.vmin+v*(self.vmax-self.vmin))

    def tickpoint_pt(self, x, axis=None):
        return self.baseaxispos.vtickpoint_pt(self.vmin+self.convert(x)*(self.vmax-self.vmin))

    def tickpoint(self, x, axis=None):
        return self.baseaxispos.vtickpoint(self.vmin+self.convert(x)*(self.vmax-self.vmin))

    def vtickpoint_pt(self, v, axis=None):
        return self.baseaxispos.vtickpoint_pt(self.vmin+v*(self.vmax-self.vmin))

    def vtickpoint(self, v, axis=None):
        return self.baseaxispos.vtickpoint(self.vmin+v*(self.vmax-self.vmin))

    def tickdirection(self, x, axis=None):
        return self.baseaxispos.vtickdirection(self.vmin+self.convert(x)*(self.vmax-self.vmin))

    def vtickdirection(self, v, axis=None):
        return self.baseaxispos.vtickdirection(self.vmin+v*(self.vmax-self.vmin))


class split(_title):
    """class for painting a splitaxis
    - the inherited _title is used to paint the title of
      the axis
    - the splitaxis access the subaxes attribute of the axis"""

    __implements__ = _Iaxispainter

    defaultbreaklinesattrs = []

    def __init__(self, breaklinesdist=0.05*unit.v_cm,
                       breaklineslength=0.5*unit.v_cm,
                       breaklinesangle=-60,
                       breaklinesattrs=[],
                       **args):
        """initializes the instance
        - breaklinesdist is a visual length of the distance between
          the two lines of the axis break
        - breaklineslength is a visual length of the length of the
          two lines of the axis break
        - breaklinesangle is the angle of the lines of the axis break
        - breaklinesattrs are a list of stroke attributes for the
          axis break lines; a single entry is allowed without being a
          list; None turns off the break lines
        - futher keyword arguments are passed to _title"""
        self.breaklinesdist = breaklinesdist
        self.breaklineslength = breaklineslength
        self.breaklinesangle = breaklinesangle
        self.breaklinesattrs = breaklinesattrs
        _title.__init__(self, **args)

    def paint(self, axispos, axis, ac=None):
        if ac is None:
            ac = axiscanvas()
        for subaxis in axis.subaxes:
            subaxis.finish(subaxispos(subaxis.convert, axispos, subaxis.vmin, subaxis.vmax, subaxis.vminover, subaxis.vmaxover))
            ac.insert(subaxis.axiscanvas)
            if ac.extent < subaxis.axiscanvas.extent:
                ac.extent = subaxis.axiscanvas.extent
        if self.breaklinesattrs is not None:
            self.sin = math.sin(self.breaklinesangle*math.pi/180.0)
            self.cos = math.cos(self.breaklinesangle*math.pi/180.0)
            breaklinesextent = (0.5*self.breaklinesdist*math.fabs(self.cos) +
                                0.5*self.breaklineslength*math.fabs(self.sin))
            if ac.extent < breaklinesextent:
                ac.extent = breaklinesextent
            for subaxis1, subaxis2 in zip(axis.subaxes[:-1], axis.subaxes[1:]):
                # use a tangent of the basepath (this is independent of the tickdirection)
                v = 0.5 * (subaxis1.vmax + subaxis2.vmin)
                p = path.normpath(axispos.vbasepath(v, None))
                breakline = p.tangent(0, length=self.breaklineslength)
                widthline = p.tangent(0, length=self.breaklinesdist).transformed(trafomodule.rotate(self.breaklinesangle+90, *breakline.begin()))
                # XXX Uiiii
                tocenter = map(lambda x: 0.5*(x[0]-x[1]), zip(breakline.begin(), breakline.end()))
                towidth = map(lambda x: 0.5*(x[0]-x[1]), zip(widthline.begin(), widthline.end()))
                breakline = breakline.transformed(trafomodule.translate(*tocenter).rotated(self.breaklinesangle, *breakline.begin()))
                breakline1 = breakline.transformed(trafomodule.translate(*towidth))
                breakline2 = breakline.transformed(trafomodule.translate(-towidth[0], -towidth[1]))
                ac.fill(path.path(path.moveto_pt(*breakline1.begin_pt()),
                                  path.lineto_pt(*breakline1.end_pt()),
                                  path.lineto_pt(*breakline2.end_pt()),
                                  path.lineto_pt(*breakline2.begin_pt()),
                                  path.closepath()), [color.gray.white])
                ac.stroke(breakline1, self.defaultbreaklinesattrs + self.breaklinesattrs)
                ac.stroke(breakline2, self.defaultbreaklinesattrs + self.breaklinesattrs)
        _title.paint(self, axispos, axis, ac=ac)
        return ac


class linkedsplit(split):
    """class for painting a linked splitaxis
    - the inherited split is used to paint the axis
    - modifies some constructor defaults"""

    __implements__ = _Iaxispainter

    def __init__(self, titleattrs=None, **kwargs):
        """initializes the instance
        - the titleattrs default is set to None thus skipping the title
        - all keyword arguments are passed to split"""
        split.__init__(self, titleattrs=titleattrs, **kwargs)


class bar(_title):
    """class for painting a baraxis
    - the inherited _title is used to paint the title of
      the axis
    - the bar access the multisubaxis, names, and subaxis
      relsizes attributes"""

    __implements__ = _Iaxispainter

    defaulttickattrs = []
    defaultbasepathattrs = [style.linecap.square]
    defaultnameattrs = [text.halign.center, text.vshift.mathaxis]

    def __init__(self, innerticklength=None,
                       outerticklength=None,
                       tickattrs=[],
                       basepathattrs=[],
                       namedist=0.3*unit.v_cm,
                       nameattrs=[],
                       namedirection=None,
                       namepos=0.5,
                       namehequalize=0,
                       namevequalize=1,
                       **args):
        """initializes the instance
        - innerticklength and outerticklength are a visual length of
          the ticks to be plotted at the axis basepath to visually
          separate the bars; if neither innerticklength nor
          outerticklength are set, not ticks are plotted
        - breaklinesattrs are a list of stroke attributes for the
          axis tick; a single entry is allowed without being a
          list; None turns off the ticks
        - namedist is a visual PyX length for the distance of the bar
          names from the axis basepath
        - nameattrs is a list of attributes for a texrunners text
          method; a single entry is allowed without being a list;
          None turns off the names
        - namedirection is an instance of rotatetext or None
        - namehequalize and namevequalize (booleans) perform an equal
          alignment for straight vertical and horizontal axes, respectively
        - futher keyword arguments are passed to _title"""
        self.innerticklength = innerticklength
        self.outerticklength = outerticklength
        self.tickattrs = tickattrs
        self.basepathattrs = basepathattrs
        self.namedist = namedist
        self.nameattrs = nameattrs
        self.namedirection = namedirection
        self.namepos = namepos
        self.namehequalize = namehequalize
        self.namevequalize = namevequalize
        _title.__init__(self, **args)

    def paint(self, axispos, axis, ac=None):
        if ac is None:
            ac = axiscanvas()
        if axis.multisubaxis is not None:
            for subaxis in axis.subaxis:
                subaxis.finish(subaxispos(subaxis.convert, axispos, subaxis.vmin, subaxis.vmax, None, None))
                ac.insert(subaxis.axiscanvas)
                if ac.extent < subaxis.axiscanvas.extent:
                    ac.extent = subaxis.axiscanvas.extent
        namepos = []
        for name in axis.names:
            v = axis.convert((name, self.namepos))
            x, y = axispos.vtickpoint_pt(v)
            dx, dy = axispos.vtickdirection(v)
            namepos.append((v, x, y, dx, dy))
        nameboxes = []
        if self.nameattrs is not None:
            for (v, x, y, dx, dy), name in zip(namepos, axis.names):
                nameattrs = self.defaultnameattrs + self.nameattrs
                if self.namedirection is not None:
                    nameattrs.append(self.namedirection.trafo(tick.temp_dx, tick.temp_dy))
                nameboxes.append(self.texrunner.text_pt(x, y, str(name), nameattrs))
        labeldist = ac.extent + self.namedist
        if len(namepos) > 1:
            equaldirection = 1
            for np in namepos[1:]:
                if np[3] != namepos[0][3] or np[4] != namepos[0][4]:
                    equaldirection = 0
        else:
            equaldirection = 0
        if equaldirection and ((not namepos[0][3] and self.namevequalize) or
                               (not namepos[0][4] and self.namehequalize)):
            box.linealignequal(nameboxes, labeldist, -namepos[0][3], -namepos[0][4])
        else:
            for namebox, np in zip(nameboxes, namepos):
                namebox.linealign(labeldist, -np[3], -np[4])
        if self.basepathattrs is not None:
            p = axispos.vbasepath()
            if p is not None:
                ac.stroke(p, self.defaultbasepathattrs + self.basepathattrs)
        if self.tickattrs is not None and (self.innerticklength is not None or
                                           self.outerticklength is not None):
            if self.innerticklength is not None:
                innerticklength_pt = unit.topt(self.innerticklength)
                if ac.extent < -self.innerticklength:
                    ac.extent = -self.innerticklength
            elif self.outerticklength is not None:
                innerticklength_pt = 0
            if self.outerticklength is not None:
                outerticklength_pt = unit.topt(self.outerticklength)
                if ac.extent < self.outerticklength:
                    ac.extent = self.outerticklength
            elif self.innerticklength is not None:
                outerticklength_pt = 0
            for pos in axis.relsizes:
                if pos == axis.relsizes[0]:
                    pos -= axis.firstdist
                elif pos != axis.relsizes[-1]:
                    pos -= 0.5 * axis.dist
                v = pos / axis.relsizes[-1]
                x, y = axispos.vtickpoint_pt(v)
                dx, dy = axispos.vtickdirection(v)
                x1 = x + dx * innerticklength_pt
                y1 = y + dy * innerticklength_pt
                x2 = x - dx * outerticklength_pt
                y2 = y - dy * outerticklength_pt
                ac.stroke(path.line_pt(x1, y1, x2, y2), self.defaulttickattrs + self.tickattrs)
        for (v, x, y, dx, dy), namebox in zip(namepos, nameboxes):
            newextent = namebox.extent(dx, dy) + labeldist
            if ac.extent < newextent:
                ac.extent = newextent
        for namebox in nameboxes:
            ac.insert(namebox)
        _title.paint(self, axispos, axis, ac=ac)
        return ac


class linkedbar(bar):
    """class for painting a linked baraxis
    - the inherited bar is used to paint the axis
    - modifies some constructor defaults"""

    __implements__ = _Iaxispainter

    def __init__(self, nameattrs=None, titleattrs=None, **kwargs):
        """initializes the instance
        - the titleattrs default is set to None thus skipping the title
        - the nameattrs default is set to None thus skipping the names
        - all keyword arguments are passed to bar"""
        bar.__init__(self, nameattrs=nameattrs, titleattrs=titleattrs, **kwargs)
