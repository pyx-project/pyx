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


import re, ConfigParser
from pyx import mathtree
from pyx.graph import style


class _Idata:
    """Interface for graph data

    Graph data consists in columns, where each column might
    be identified by a string or an integer. Each row in the
    resulting table refers to a data point."""

    def getcolumndataindex(self, column):
        """Data for a column

        This method returns data of a column by a tuple data, index.
        column identifies the column. If index is not None, the data
        of the column is found at position index for each element of
        the list data. If index is None, the data is the list of
        data."""

    def getcolumn(self, column):
        """Data for a column

        This method returns the data of a column in a list. column
        has the same meaning as in getcolumndataindex. Note, that
        this method typically has to create this list, which needs
        time and memory. While its easy to the user, internally it
        should be avoided in favor of getcolumndataindex. The method
        can be implemented as follows:"""
        data, index = self.getcolumndataindex(column)
        if index is None:
            return data
        else:
            return [point[index] for point in data]

    def getcount(self):
        """Number of points

        This method returns the number of points. All results by
        getcolumndataindex and getcolumn will fit this number."""

    def getdefaultstyles(self):
        """Default styles for the data

        Returns a list of default styles for the data. Note to
        return the same instances when the graph should iterate
        over the styles using selectstyles. The following default
        implementation returns the value of the defaultstyle
        class variable."""

    def gettitle(self):
        """Title of the data

        This method returns a title string for the data to be used
        in graph keys and probably other locations. The method might
        return None to indicate, that there is no title and the data
        should be skiped in a graph key. A data title does not need
        to be unique."""

    def setstyles(self, graph, styles):
        """Attach graph styles to data

        This method is called by the graph to attach styles to the
        data instance."""

    def selectstyles(self, graph, selectindex, selecttotal):
        """Perform select on the styles

        This method should perfrom selectstyle calls on all styles."""
        for style in self.styles:
            style.selectstyle(self.styledata, graph, selectindex, selecttotal)

    def adjustaxes(self, graph, step):
        """Adjust axes ranges

        This method should call adjustaxis for all styles.
        On step == 0 axes with fixed data should be adjusted.
        On step == 1 the current axes ranges might be used to
        calculate further data (e.g. y data for a function y=f(x)
        where the y range depends on the x range). On step == 2
        axes ranges not previously set should be updated by data
        accumulated by step 1."""

    def draw(self, graph):
        """Draw data

        This method should draw the data."""

    def key_pt(self, graph, x_pt, y_pt, width_pt, height_pt):
        """Draw graph key

        This method should draw a graph key at the given position
        x_pt, y_pt indicating the lower left corner of the given
        area width_pt, height_pt."""


class styledata:
    """Styledata storage class

    Instances of this class are used to store data from the styles
    and to pass point data to the styles.  is shared
    between all the style(s) in use by a data instance"""
    pass


class _data(_Idata):
    """Partly implements the _Idata interface

    This class partly implements the _Idata interface. In order
    to do so, it makes use of various instance variables:

        self.data:
        self.columns:
        self.styles:
        self.styledata:
        self.title: the title of the data
        self.defaultstyles:"""

    defaultstyles = [style.symbol()]

    def getcolumndataindex(self, column):
        return self.data, self.columns[column]

    def getcount(self):
        return len(self.data)

    def gettitle(self):
        return self.title

    def getdefaultstyles(self):
        return self.defaultstyles

    def addneededstyles(self, styles):
        """helper method (not part of the interface)

        This is a helper method, which returns a list of styles where
        provider styles are added in front to fullfill all needs of the
        given styles."""
        provided = [] # already provided styledata variables
        addstyles = [] # a list of style instances to be added in front
        for s in styles:
            for n in s.need:
                if n not in provided:
                    addstyles.append(style.provider[n])
                    provided.extend(style.provider[n].provide)
            provided.extend(s.provide)
        return addstyles + styles

    def setcolumns(self, styledata, graph, styles, columns):
        """helper method (not part of the interface)

        This is a helper method to perform setcolumn to all styles."""
        usedcolumns = []
        for style in styles:
            usedcolumns.extend(style.columns(self.styledata, graph, columns))
        for column in columns:
            if column not in usedcolumns:
                raise ValueError("unused column '%s'" % column)

    def setstyles(self, graph, styles):
        self.styledata = styledata()
        self.styles = self.addneededstyles(styles)
        self.setcolumns(self.styledata, graph, self.styles, self.columns.keys())

    def selectstyles(self, graph, selectindex, selecttotal):
        for style in self.styles:
            style.selectstyle(self.styledata, graph, selectindex, selecttotal)

    def adjustaxes(self, graph, step):
        if step == 0:
            for column in self.columns.keys():
                data, index = self.getcolumndataindex(column)
                for style in self.styles:
                    style.adjustaxis(self.styledata, graph, column, data, index)

    def draw(self, graph):
        columndataindex = []
        for column in self.columns.keys():
            data, index = self.getcolumndataindex(column)
            columndataindex.append((column, data, index))
        if len(columndataindex):
            column, data, index = columndataindex[0]
            l = len(data)
            for column, data, index in columndataindex[1:]:
                if l != len(data):
                    raise ValueError("data len differs")
            self.styledata.point = {}
            for style in self.styles:
                style.initdrawpoints(self.styledata, graph)
            for i in xrange(l):
                for column, data, index in columndataindex:
                    if index is not None:
                        self.styledata.point[column] = data[i][index]
                    else:
                        self.styledata.point[column] = data[i]
                for style in self.styles:
                    style.drawpoint(self.styledata, graph)
            for style in self.styles:
                style.donedrawpoints(self.styledata, graph)

    def key_pt(self, graph, x_pt, y_pt, width_pt, height_pt):
        for style in self.styles:
            style.key_pt(self.styledata, graph, x_pt, y_pt, width_pt, height_pt)


class list(_data):
    "Graph data from a list of points"

    def getcolumndataindex(self, column):
        try:
            if self.addlinenumbers:
                index = self.columns[column]-1
            else:
                index = self.columns[column]
        except KeyError:
            try:
                if type(column) != type(column + 0):
                    raise ValueError("integer expected")
            except:
                raise ValueError("integer expected")
            if self.addlinenumbers:
                if column > 0:
                    index = column-1
                elif column < 0:
                    index = column
                else:
                    return range(1, 1+len(self.data)), None
            else:
                index = column
        return self.data, index

    def __init__(self, data, title="user provided list", addlinenumbers=1, **columns):
        if len(data):
            # be paranoid and check each row to have the same number of data
            l = len(data[0])
            for p in data[1:]:
                if l != len(p):
                    raise ValueError("different number of columns per point")
            for v in columns.values():
                if abs(v) > l or (not addlinenumbers and abs(v) == l):
                    raise ValueError("column number bigger than number of columns")
        self.data = data
        self.columns = columns
        self.title = title
        self.addlinenumbers = addlinenumbers


##############################################################
# math tree enhanced by column number variables
##############################################################

class MathTreeFuncCol(mathtree.MathTreeFunc1):

    def __init__(self, *args):
        mathtree.MathTreeFunc1.__init__(self, "_column_", *args)

    def VarList(self):
        # we misuse VarList here:
        # - instead of returning a string, we return this instance itself
        # - before calculating the expression, you must call ColumnNameAndNumber
        #   once (when limiting the context to external defined variables,
        #   otherwise you have to call it each time)
        return [self]

    def ColumnNameAndNumber(_hidden_self, **args):
        number = int(_hidden_self.Args[0].Calc(**args))
        _hidden_self.varname = "_column_%i" % number
        return _hidden_self.varname, number

    def __str__(self):
        return self.varname

    def Calc(_hidden_self, **args):
        return args[_hidden_self.varname]

MathTreeFuncsWithCol = mathtree.DefaultMathTreeFuncs + [MathTreeFuncCol]


class columntree:

    def __init__(self, tree):
        self.tree = tree
        self.Calc = tree.Calc
        self.__str__ = tree.__str__

    def VarList(self):
        # returns a list of regular variables (strings) like the original mathtree
        return [var for var in self.tree.VarList() if not isinstance(var, MathTreeFuncCol) and var[:8] != "_column_"]

    def columndict(_hidden_self, **context):
        # returns a dictionary of column names (keys) and column numbers (values)
        columndict = {}
        for var in _hidden_self.tree.VarList():
            if isinstance(var, MathTreeFuncCol):
                name, number = var.ColumnNameAndNumber(**context)
                columndict[name] = number
            elif var[:8] == "_column_":
                columndict[var] = int(var[8:])
        return columndict


class dataparser(mathtree.parser):
    # mathtree parser enhanced by column handling
    # parse returns a columntree instead of a regular tree

    def __init__(self, MathTreeFuncs=MathTreeFuncsWithCol, **kwargs):
        mathtree.parser.__init__(self, MathTreeFuncs=MathTreeFuncs, **kwargs)

    def parse(self, expr):
        return columntree(mathtree.parser.parse(self, expr.replace("$", "_column_")))

##############################################################


class _notitle:
    """this is a helper class to mark, that no title was privided
    (since a title equals None is a valid input, it needs to be
    distinguished from providing no title when a title will be
    created automatically)"""
    pass

class data(_data):
    "creates a new data set out of an existing data set"

    def __init__(self, data, title=_notitle, parser=dataparser(), context={}, **columns):
        # build a nice title
        if title is _notitle:
            items = columns.items()
            items.sort() # we want sorted items (otherwise they would be unpredictable scrambled)
            self.title = data.title + ": " + ", ".join(["%s=%s" % item for item in items])
        else:
            self.title = title

        self.orgdata = data

        # analyse the **columns argument
        self.columns = {}
        newcolumns = {}
        for column, value in columns.items():
            try:
                # try if it is a valid column identifier
                self.columns[column] = self.orgdata.getcolumndataindex(value)
            except (KeyError, ValueError):
                # take it as a mathematical expression
                tree = parser.parse(value)
                columndict = tree.columndict(**context)
                vardataindex = []
                for var, value in columndict.items():
                    # column data accessed via $<column number>
                    data, index = self.orgdata.getcolumndataindex(value)
                    vardataindex.append((var, data, index))
                for var in tree.VarList():
                    try:
                        # column data accessed via the name of the column
                        data, index = self.orgdata.getcolumndataindex(var)
                    except (KeyError, ValueError):
                        # other data available in context
                        if var not in context.keys():
                            raise ValueError("undefined variable '%s'" % var)
                    else:
                        vardataindex.append((var, data, index))
                newdata = [None]*self.getcount()
                vars = context.copy() # do not modify context, use a copy vars instead
                for i in xrange(self.getcount()):
                    # insert column data as prepared in vardataindex
                    for var, data, index in vardataindex:
                        if index is not None:
                            vars[var] = data[i][index]
                        else:
                            vars[var] = data[i]
                    # evaluate expression
                    newdata[i] = tree.Calc(**vars)
                    # we could also do:
                    # point[newcolumnnumber] = eval(str(tree), vars)

                    # TODO: It might happen, that the evaluation of the expression
                    #       seems to work, but the result is NaN. It depends on the
                    #       plattform and configuration. The NaN handling is an
                    #       open issue.
                self.columns[column] = newdata, None

    def getcolumndataindex(self, column):
        return self.columns[column]

    def getcount(self):
        return self.orgdata.getcount()

    def getdefaultstyle(self):
        return self.orgdata.getdefaultstyle()


filecache = {}

class file(data):

    defaultcommentpattern = re.compile(r"(#+|!+|%+)\s*")
    defaultstringpattern = re.compile(r"\"(.*?)\"(\s+|$)")
    defaultcolumnpattern = re.compile(r"(.*?)(\s+|$)")

    def splitline(self, line, stringpattern, columnpattern, tofloat=1):
        """returns a tuple created out of the string line
        - matches stringpattern and columnpattern, adds the first group of that
          match to the result and and removes those matches until the line is empty
        - when stringpattern matched, the result is always kept as a string
        - when columnpattern matched and tofloat is true, a conversion to a float
          is tried; when this conversion fails, the string is kept"""
        result = []
        # try to gain speed by skip matching regular expressions
        if line.find('"')!=-1 or \
           stringpattern is not self.defaultstringpattern or \
           columnpattern is not self.defaultcolumnpattern:
            while len(line):
                match = stringpattern.match(line)
                if match:
                    result.append(match.groups()[0])
                    line = line[match.end():]
                else:
                    match = columnpattern.match(line)
                    if tofloat:
                        try:
                            result.append(float(match.groups()[0]))
                        except (TypeError, ValueError):
                            result.append(match.groups()[0])
                    else:
                        result.append(match.groups()[0])
                    line = line[match.end():]
        else:
            if tofloat:
                try:
                    return map(float, line.split())
                except (TypeError, ValueError):
                    result = []
                    for r in line.split():
                        try:
                            result.append(float(r))
                        except (TypeError, ValueError):
                            result.append(r)
            else:
                return line.split()
        return result

    def getcachekey(self, *args):
        return ":".join([str(x) for x in args])

    def __init__(self, filename,
                       commentpattern=defaultcommentpattern,
                       stringpattern=defaultstringpattern,
                       columnpattern=defaultcolumnpattern,
                       skiphead=0, skiptail=0, every=1,
                       **kwargs):

        def readfile(file, title):
            columns = {}
            points = []
            linenumber = 0
            maxcolumns = 0
            for line in file.readlines():
                line = line.strip()
                match = commentpattern.match(line)
                if match:
                    if not len(points):
                        keys = self.splitline(line[match.end():], stringpattern, columnpattern, tofloat=0)
                        i = 0
                        for key in keys:
                            i += 1 # the first column is number 1 since a linenumber is added in front
                            columns[key] = i
                else:
                    linedata = []
                    for value in self.splitline(line, stringpattern, columnpattern, tofloat=1):
                        linedata.append(value)
                    if len(linedata):
                        if linenumber >= skiphead and not ((linenumber - skiphead) % every):
                            linedata = [linenumber + 1] + linedata
                            if len(linedata) > maxcolumns:
                                maxcolumns = len(linedata)
                            points.append(linedata)
                        linenumber += 1
            if skiptail >= every:
                skip, x = divmod(skiptail, every)
                del points[-skip:]
            for i in xrange(len(points)):
                if len(points[i]) != maxcolumns:
                    points[i].extend([None]*(maxcolumns-len(points[i])))
            return list(points, title=title, addlinenumbers=0, **columns)

        try:
            filename.readlines
        except:
            # not a file-like object -> open it
            cachekey = self.getcachekey(filename, commentpattern, stringpattern, columnpattern, skiphead, skiptail, every)
            if not filecache.has_key(cachekey):
                filecache[cachekey] = readfile(open(filename), filename)
            data.__init__(self, filecache[cachekey], **kwargs)
        else:
            data.__init__(self, readfile(filename, "user provided file-like object"), **kwargs)


conffilecache = {}

class conffile(data):

    def __init__(self, filename, **kwargs):
        """read data from a config-like file
        - filename is a string
        - each row is defined by a section in the config-like file (see
          config module description)
        - the columns for each row are defined by lines in the section file;
          the option entries identify and name the columns
        - further keyword arguments are passed to the constructor of data,
          keyword arguments data and titles excluded"""

        def readfile(file, title):
            config = ConfigParser.ConfigParser()
            config.optionxform = str
            config.readfp(file)
            sections = config.sections()
            sections.sort()
            points = [None]*len(sections)
            maxcolumns = 1
            columns = {}
            for i in xrange(len(sections)):
                point = [sections[i]] + [None]*(maxcolumns-1)
                for option in config.options(sections[i]):
                    value = config.get(sections[i], option)
                    try:
                        value = float(value)
                    except:
                        pass
                    try:
                        index = columns[option]
                    except KeyError:
                        columns[option] = maxcolumns
                        point.append(value)
                        maxcolumns += 1
                    else:
                        point[index] = value
                points[i] = point
            return list(points, title=title, addlinenumbers=0, **columns)

        try:
            filename.readlines
        except:
            # not a file-like object -> open it
            if not filecache.has_key(filename):
                filecache[filename] = readfile(open(filename), filename)
            data.__init__(self, filecache[filename], **kwargs)
        else:
            data.__init__(self, readfile(filename, "user provided file-like object"), **kwargs)


class _linedata(_data):

    defaultstyle = [style.line()]


# class function:
# 
#     defaultstyle = style.line()
# 
#     def __init__(self, expression, title=_notitle, min=None, max=None,
#     points=100, parser=mathtree.parser(), context={}):
# 
#         if title is _notitle:
#             self.title = expression
#         else:
#             self.title = title
#         self.min = min
#         self.max = max
#         self.numberofpoints = points
#         self.context = context.copy() # be save on late evaluations
#         self.result, expression = [x.strip() for x in expression.split("=")]
#         self.mathtree = parser.parse(expression)
#         self.variable = None
# 
#     def setstyles(self, graph, styles):
#         self.styles = styles
#         self.styledata = styledata()
#         for variable in self.mathtree.VarList():
#             if variable in graph.axes.keys():
#                 if self.variable is None:
#                     self.variable = variable
#                 else:
#                     raise ValueError("multiple variables found")
#         if self.variable is None:
#             raise ValueError("no variable found")
#         self.xaxis = graph.axes[self.variable]
#         self.columns = {self.variable: 1, self.result: 2}
#         unhandledcolumns = self.columns
#         for style in self.styles:
#             unhandledcolumns = style.setdata(graph, unhandledcolumns, self.styledata)
#         unhandledcolumnkeys = unhandledcolumns.keys()
#         if len(unhandledcolumnkeys):
#             raise ValueError("style couldn't handle column keys %s" % unhandledcolumnkeys)
# 
#     def selectstyles(self, graph, selectindex, selecttotal):
#         for style in self.styles:
#             style.selectstyle(selectindex, selecttotal, self.styledata)
# 
#     def adjustaxes(self, graph, step):
#         """
#         - on step == 0 axes with fixed data should be adjusted
#         - on step == 1 the current axes ranges might be used to
#           calculate further data (e.g. y data for a function y=f(x)
#           where the y range depends on the x range)
#         - on step == 2 axes ranges not previously set should be
#           updated by data accumulated by step 1"""
#         if step == 0:
#             self.points = []
#             if self.min is not None:
#                 self.points.append([None, self.min])
#             if self.max is not None:
#                 self.points.append([None, self.max])
#             for style in self.styles:
#                 style.adjustaxes(self.points, [1], self.styledata)
#         elif step == 1:
#             min, max = graph.axes[self.variable].getrange()
#             if self.min is not None: min = self.min
#             if self.max is not None: max = self.max
#             vmin = self.xaxis.convert(min)
#             vmax = self.xaxis.convert(max)
#             self.points = []
#             for i in range(self.numberofpoints):
#                 v = vmin + (vmax-vmin)*i / (self.numberofpoints-1.0)
#                 x = self.xaxis.invert(v)
#                 # caution: the virtual coordinate might differ once
#                 # the axis rescales itself to include further ticks etc.
#                 self.points.append([v, x, None])
#             for point in self.points:
#                 self.context[self.variable] = point[1]
#                 try:
#                     point[2] = self.mathtree.Calc(**self.context)
#                 except (ArithmeticError, ValueError):
#                     pass
#         elif step == 2:
#             for style in self.styles:
#                 style.adjustaxes(self.points, [2], self.styledata)
# 
#     def draw(self, graph):
#         # TODO code dublication
#         for style in self.styles:
#             style.initdrawpoints(graph, self.styledata)
#         for point in self.points:
#             self.styledata.point = point
#             for style in self.styles:
#                 style.drawpoint(graph, self.styledata)
#         for style in self.styles:
#             style.donedrawpoints(graph, self.styledata)


class paramfunction(_linedata):

    def __init__(self, varname, min, max, expression, title=_notitle, points=100, parser=mathtree.parser(), context={}):
        if title is _notitle:
            self.title = expression
        else:
            self.title = title
        varlist, expressionlist = expression.split("=")
        keys = varlist.split(",")
        mathtrees = parser.parse(expressionlist)
        if len(keys) != len(mathtrees):
            raise ValueError("unpack tuple of wrong size")
        self.data = [None]*points
        emptyresult = [None]*len(keys)
        self.columns = {}
        i = 1
        for key in keys:
            self.columns[key.strip()] = i
            i += 1
        for i in range(points):
            param = min + (max-min)*i / (points-1.0)
            context[varname] = param
            self.data[i] = [param] + emptyresult
            column = 1
            for key, column in self.columns.items():
                self.data[i][column] = mathtrees[column-1].Calc(**context)
                column += 1

