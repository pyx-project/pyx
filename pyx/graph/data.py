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


from pyx import helper, mathtree
from pyx import data as datamodule
from pyx.graph import style


class data:

    defaultstyle = style.symbol()

    def __init__(self, file, title=helper.nodefault, context={}, **columns):
        self.title = title
        if helper.isstring(file):
            self.data = datamodule.datafile(file)
        else:
            self.data = file
        if title is helper.nodefault:
            self.title = "(unknown)"
        else:
            self.title = title
        self.columns = {}
        for key, column in columns.items():
            try:
                self.columns[key] = self.data.getcolumnno(column)
            except datamodule.ColumnError:
                self.columns[key] = len(self.data.titles)
                self.data.addcolumn(column, context=context)
        self.points = self.data.data

    def setstyle(self, graph, style):
        self.style = style
        unhandledcolumns = self.style.setdata(graph, self.columns, self)
        unhandledcolumnkeys = unhandledcolumns.keys()
        if len(unhandledcolumnkeys):
            raise ValueError("style couldn't handle column keys %s" % unhandledcolumnkeys)

    def selectstyle(self, graph, selectindex, selecttotal):
        self.style.selectstyle(selectindex, selecttotal, self)

    def adjustaxes(self, graph, step):
        """
        - on step == 0 axes with fixed data should be adjusted
        - on step == 1 the current axes ranges might be used to
          calculate further data (e.g. y data for a function y=f(x)
          where the y range depends on the x range)
        - on step == 2 axes ranges not previously set should be
          updated by data accumulated by step 1"""
        if step == 0:
            self.style.adjustaxes(self.columns.values(), self)

    def draw(self, graph):
        self.style.drawpoints(graph, self)


class function:

    defaultstyle = style.line()

    def __init__(self, expression, title=helper.nodefault, min=None, max=None, points=100, parser=mathtree.parser(), context={}):
        if title is helper.nodefault:
            self.title = expression
        else:
            self.title = title
        self.min = min
        self.max = max
        self.nopoints = points
        self.context = context
        self.result, expression = [x.strip() for x in expression.split("=")]
        self.mathtree = parser.parse(expression)
        self.variable = None

    def setstyle(self, graph, style):
        self.style = style
        for variable in self.mathtree.VarList():
            if variable in graph.axes.keys():
                if self.variable is None:
                    self.variable = variable
                else:
                    raise ValueError("multiple variables found")
        if self.variable is None:
            raise ValueError("no variable found")
        self.xaxis = graph.axes[self.variable]
        unhandledcolumns = self.style.setdata(graph, {self.variable: 0, self.result: 1}, self)
        unhandledcolumnkeys = unhandledcolumns.keys()
        if len(unhandledcolumnkeys):
            raise ValueError("style couldn't handle column keys %s" % unhandledcolumnkeys)

    def selectstyle(self, graph, selectindex, selecttotal):
        self.style.selectstyle(selectindex, selecttotal, self)

    def adjustaxes(self, graph, step):
        """
        - on step == 0 axes with fixed data should be adjusted
        - on step == 1 the current axes ranges might be used to
          calculate further data (e.g. y data for a function y=f(x)
          where the y range depends on the x range)
        - on step == 2 axes ranges not previously set should be
          updated by data accumulated by step 1"""
        if step == 0:
            min, max = graph.axes[self.variable].getrange()
            if self.min is not None: min = self.min
            if self.max is not None: max = self.max
            vmin = self.xaxis.convert(min)
            vmax = self.xaxis.convert(max)
            self.points = []
            for i in range(self.nopoints):
                x = self.xaxis.invert(vmin + (vmax-vmin)*i / (self.nopoints-1.0))
                self.points.append([x])
            self.style.adjustaxes([0], self)
        elif step == 1:
            for point in self.points:
                self.context[self.variable] = point[0]
                try:
                    point.append(self.mathtree.Calc(**self.context))
                except (ArithmeticError, ValueError):
                    point.append(None)
        elif step == 2:
            self.style.adjustaxes([1], self)

    def draw(self, graph):
        self.style.drawpoints(graph, self)


class paramfunction:

    defaultstyle = style.line()

    def __init__(self, varname, min, max, expression, title=helper.nodefault, points=100, parser=mathtree.parser(), context={}):
        if title is helper.nodefault:
            self.title = expression
        else:
            self.title = title
        self.varname = varname
        self.min = min
        self.max = max
        self.nopoints = points
        self.expression = {}
        self.mathtrees = {}
        varlist, expressionlist = expression.split("=")
        if mathtree.__useparser__ == mathtree.__newparser__: # XXX: switch between mathtree-parsers
            keys = varlist.split(",")
            mtrees = helper.ensurelist(parser.parse(expressionlist))
            if len(keys) != len(mtrees):
                raise ValueError("unpack tuple of wrong size")
            for i in range(len(keys)):
                key = keys[i].strip()
                if self.mathtrees.has_key(key):
                    raise ValueError("multiple assignment in tuple")
                self.mathtrees[key] = mtrees[i]
            if len(keys) != len(self.mathtrees.keys()):
                raise ValueError("unpack tuple of wrong size")
        else:
            parsestr = mathtree.ParseStr(expressionlist)
            for key in varlist.split(","):
                key = key.strip()
                if self.mathtrees.has_key(key):
                    raise ValueError("multiple assignment in tuple")
                try:
                    self.mathtrees[key] = parser.ParseMathTree(parsestr)
                    break
                except mathtree.CommaFoundMathTreeParseError, e:
                    self.mathtrees[key] = e.MathTree
            else:
                raise ValueError("unpack tuple of wrong size")
            if len(varlist.split(",")) != len(self.mathtrees.keys()):
                raise ValueError("unpack tuple of wrong size")
        self.points = []
        for i in range(self.nopoints):
            context[self.varname] = self.min + (self.max-self.min)*i / (self.nopoints-1.0)
            line = []
            for key, tree in self.mathtrees.items():
                line.append(tree.Calc(**context))
            self.points.append(line)

    def setstyle(self, graph, style):
        self.style = style
        columns = {}
        index = 0
        for key in self.mathtrees.keys():
            columns[key] = index
            index += 1
        unhandledcolumns = self.style.setdata(graph, columns, self)
        unhandledcolumnkeys = unhandledcolumns.keys()
        if len(unhandledcolumnkeys):
            raise ValueError("style couldn't handle column keys %s" % unhandledcolumnkeys)

    def selectstyle(self, graph, selectindex, selecttotal):
        self.style.selectstyle(selectindex, selecttotal, self)

    def adjustaxes(self, graph, step):
        if step == 0:
            self.style.adjustaxes(list(range(len(self.mathtrees.items()))), self)

    def draw(self, graph):
        self.style.drawpoints(graph, self)

