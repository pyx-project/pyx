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
from pyx import mathtree, text
from pyx.graph import style

try:
    enumerate([])
except NameError:
    # fallback implementation for Python 2.2. and below
    def enumerate(list):
        return zip(xrange(len(list)), list)

class _Idata:
    """Interface for graph data

    Graph data consists in columns, where each column might
    be identified by a string or an integer. Each row in the
    resulting table refers to a data point.

    All methods except for the constructor should consider
    self to be readonly, since the data instance might be shared
    between several graphs simultaniously. The plotitem instance
    created by the graph is available as a container class."""

    def getcolumnpointsindex(self, column):
        """Data for a column

        This method returns data of a column by a tuple data, index.
        column identifies the column. If index is not None, the data
        of the column is found at position index for each element of
        the list data. If index is None, the data is the list of
        data.

        Some data might not be available by this function since it
        is dynamic, i.e. it depends on plotitem. An example are
        function data, which is available within a graph only. Thus
        this method might raise an exception."""
        raise NotImplementedError("call to an abstract method of %r" % self)

    def getcolumn(self, column):
        """Data for a column

        This method returns the data of a column in a list. column
        has the same meaning as in getcolumnpointsindex. Note, that
        this method typically has to create a new list, which needs
        time and memory. While its easy to the user, internally
        it should be avoided in favor of getcolumnpointsindex."""
        raise NotImplementedError("call to an abstract method of %r" % self)

    def getcount(self):
        """Number of points

        This method returns the number of points. All results by
        getcolumnpointsindex and getcolumn will fit this number.
        It might raise an exception as getcolumnpointsindex."""
        raise NotImplementedError("call to an abstract method of %r" % self)

    def getdefaultstyles(self):
        """Default styles for the data

        Returns a list of default styles for the data. Note to
        return the same instances when the graph should iterate
        over the styles using selectstyles."""
        raise NotImplementedError("call to an abstract method of %r" % self)

    def gettitle(self):
        """Title of the data

        This method returns a title string for the data to be used
        in graph keys and probably other locations. The method might
        return None to indicate, that there is no title and the data
        should be skiped in a graph key. Data titles does not need
        to be unique."""
        raise NotImplementedError("call to an abstract method of %r" % self)

    def initplotitem(self, plotitem, graph):
        """Initialize plotitem

        This function is called within the plotitem initialization
        procedure and allows to initialize the plotitem as a data
        container. For static data the method might just do nothing."""
        raise NotImplementedError("call to an abstract method of %r" % self)

    def getcolumnpointsindex_plotitem(self, plotitem, column):
        """Data for a column with plotitem

        Like getcolumnpointsindex but for use within a graph, i.e. with
        a plotitem container class. For static data being defined within
        the constructor already, the plotitem reference is not needed and
        the method can be implemented by calling getcolumnpointsindex."""
        raise NotImplementedError("call to an abstract method of %r" % self)

    def getcolumnnames(self, plotitem):
        """Return list of column names of the data

        This method returns a list of column names. It might
        depend on the graph. (*YES*, it might depend on the graph
        in case of a function, where function variables might be
        axis names. Other variables, not available by axes, will
        be taken from the context.)"""
        raise NotImplementedError("call to an abstract method of %r" % self)

    def adjustaxes(self, plotitem, graph, step):
        """Adjust axes ranges

        This method should call adjustaxis for all styles.
        On step == 0 axes with fixed data should be adjusted.
        On step == 1 the current axes ranges might be used to
        calculate further data (e.g. y data for a function y=f(x)
        where the y range depends on the x range). On step == 2
        axes ranges not previously set should be updated by data
        accumulated by step 1."""
        raise NotImplementedError("call to an abstract method of %r" % self)

    def draw(self, plotitem, graph):
        """Draw data

        This method should draw the data. Its called by plotinfo,
        since it can be implemented here more efficiently by avoiding
        some additional function calls."""
        raise NotImplementedError("call an abstract method of %r" % self)


class _data(_Idata):
    """Partly implements the _Idata interface"""

    defaultstyles = [style.symbol()]

    def getcolumn(self, column):
        data, index = self.getcolumnpointsindex(column)
        if index is None:
            return data
        else:
            return [point[index] for point in data]

    def getdefaultstyles(self):
        return self.defaultstyles

    def gettitle(self):
        return self.title

    def initplotitem(self, plotitem, graph):
        pass

    def draw(self, plotitem, graph):
        columnpointsindex = []
        l = None
        for column in self.getcolumnnames(plotitem):
            points, index = self.getcolumnpointsindex_plotitem(plotitem, column)
            columnpointsindex.append((column, points, index))
            if l is None:
                l = len(points)
            else:
                if l != len(points):
                    raise ValueError("points len differs")
        for privatedata, style in zip(plotitem.privatedatalist, plotitem.styles):
            style.initdrawpoints(privatedata, plotitem.sharedata, graph)
        if len(columnpointsindex):
            plotitem.sharedata.point = {}
            for i in xrange(l):
                for column, points, index in columnpointsindex:
                    if index is not None:
                        plotitem.sharedata.point[column] = points[i][index]
                    else:
                        plotitem.sharedata.point[column] = points[i]
                for privatedata, style in zip(plotitem.privatedatalist, plotitem.styles):
                    style.drawpoint(privatedata, plotitem.sharedata, graph)
        for privatedata, style in zip(plotitem.privatedatalist, plotitem.styles):
            style.donedrawpoints(privatedata, plotitem.sharedata, graph)


class _staticdata(_data):
    """Partly implements the _Idata interface

    This class partly implements the _Idata interface for static data
    using self.columns and self.points to be initialized by the constructor."""

    def getcolumnpointsindex(self, column):
        return self.points, self.columns[column]

    def getcount(self):
        return len(self.points)

    def getcolumnnames(self, plotitem):
        return self.columns.keys()

    def getcolumnpointsindex_plotitem(self, plotitem, column):
        return self.getcolumnpointsindex(column)

    def adjustaxes(self, plotitem, graph, step):
        if step == 0:
            for column in self.getcolumnnames(plotitem):
                points, index = self.getcolumnpointsindex_plotitem(plotitem, column)
                for privatedata, style in zip(plotitem.privatedatalist, plotitem.styles):
                    style.adjustaxis(privatedata, plotitem.sharedata, graph, column, points, index)


class _dynamicdata(_data):

    def getcolumnpointsindex(self, column):
        raise RuntimeError("dynamic data not available outside a graph")

    def getcount(self):
        raise RuntimeError("dynamic data typically has no fixed number of points")


class list(_staticdata):
    "Graph data from a list of points"

    def getcolumnpointsindex(self, column):
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
                    return range(1, 1+len(self.points)), None
            else:
                index = column
        return self.points, index

    def __init__(self, points, title="user provided list", addlinenumbers=1, **columns):
        if len(points):
            # be paranoid and check each row to have the same number of points
            l = len(points[0])
            for p in points[1:]:
                if l != len(p):
                    raise ValueError("different number of columns per point")
            for v in columns.values():
                if abs(v) > l or (not addlinenumbers and abs(v) == l):
                    raise ValueError("column number bigger than number of columns")
        self.points = points
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


class notitle:
    """this is a helper class to mark, that no title was privided
    (since a title equals None is a valid input, it needs to be
    distinguished from providing no title when a title will be
    created automatically)"""
    pass

class data(_staticdata):
    "creates a new data set out of an existing data set"

    def __init__(self, data, title=notitle, parser=dataparser(), context={}, **columns):
        # build a nice title
        if title is notitle:
            items = columns.items()
            items.sort() # we want sorted items (otherwise they would be unpredictable scrambled)
            self.title = "%s: %s" % (data.title,
                                     ", ".join(["%s=%s" % (text.escapestring(key),
                                                           text.escapestring(value))
                                                for key, value in items]))
        else:
            self.title = title

        self.orgdata = data

        # analyse the **columns argument
        self.columns = {}
        newcolumns = {}
        for column, value in columns.items():
            try:
                # try if it is a valid column identifier
                self.columns[column] = self.orgdata.getcolumnpointsindex(value)
            except (KeyError, ValueError):
                # take it as a mathematical expression
                tree = parser.parse(value)
                columndict = tree.columndict(**context)
                varpointsindex = []
                for var, value in columndict.items():
                    # column data accessed via $<column number>
                    points, index = self.orgdata.getcolumnpointsindex(value)
                    varpointsindex.append((var, points, index))
                for var in tree.VarList():
                    try:
                        # column data accessed via the name of the column
                        points, index = self.orgdata.getcolumnpointsindex(var)
                    except (KeyError, ValueError):
                        # other data available in context
                        if var not in context.keys():
                            raise ValueError("undefined variable '%s'" % var)
                    else:
                        varpointsindex.append((var, points, index))
                newdata = [None]*self.getcount()
                vars = context.copy() # do not modify context, use a copy vars instead
                for i in xrange(self.getcount()):
                    # insert column data as prepared in varpointsindex
                    for var, point, index in varpointsindex:
                        if index is not None:
                            vars[var] = points[i][index]
                        else:
                            vars[var] = points[i]
                    # evaluate expression
                    try:
                        newdata[i] = tree.Calc(**vars)
                    except (ArithmeticError, ValueError):
                        newdata[i] = None
                    # we could also do:
                    # point[newcolumnnumber] = eval(str(tree), vars)

                    # XXX: It might happen, that the evaluation of the expression
                    #      seems to work, but the result is NaN/Inf/-Inf. This
                    #      is highly plattform dependend.

                self.columns[column] = newdata, None

    def getcolumnpointsindex(self, column):
        return self.columns[column]

    def getcount(self):
        return self.orgdata.getcount()

    def getdefaultstyles(self):
        return self.orgdata.getdefaultstyles()


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


class function(_dynamicdata):

    defaultstyles = [style.line()]

    def __init__(self, expression, title=notitle, min=None, max=None,
                 points=100, parser=mathtree.parser(), context={}):

        if title is notitle:
            self.title = expression
        else:
            self.title = title
        self.min = min
        self.max = max
        self.numberofpoints = points
        self.context = context.copy() # be save on late evaluations
        self.yname, expression = [x.strip() for x in expression.split("=")]
        self.mathtree = parser.parse(expression)

    def getcolumnpointsindex_plotitem(self, plotitem, column):
        return plotitem.points, plotitem.columns[column]

    def initplotitem(self, plotitem, graph):
        self.xname = None
        for xname in self.mathtree.VarList():
            if xname in graph.axes.keys():
                if self.xname is None:
                    self.xname = xname
                else:
                    raise ValueError("multiple variables found")
        if self.xname is None:
            raise ValueError("no variable found")
        plotitem.columns = {self.xname: 0, self.yname: 1}

    def getcolumnnames(self, plotitem):
        return [self.xname, self.yname]

    def adjustaxes(self, plotitem, graph, step):
        if step == 0:
            points = []
            if self.min is not None:
                points.append(self.min)
            if self.max is not None:
                points.append(self.max)
            for privatedata, style in zip(plotitem.privatedatalist, plotitem.styles):
                style.adjustaxis(privatedata, plotitem.sharedata, graph, self.xname, points, None)
        elif step == 1:
            xaxis = graph.axes[self.xname]
            min, max = xaxis.getrange()
            if self.min is not None: min = self.min
            if self.max is not None: max = self.max
            vmin = xaxis.convert(min)
            vmax = xaxis.convert(max)
            plotitem.points = []
            for i in range(self.numberofpoints):
                v = vmin + (vmax-vmin)*i / (self.numberofpoints-1.0)
                x = xaxis.invert(v)
                self.context[self.xname] = x
                try:
                    y = self.mathtree.Calc(**self.context)
                except (ArithmeticError, ValueError):
                    y = None
                plotitem.points.append([x, y])
        elif step == 2:
            for privatedata, style in zip(plotitem.privatedatalist, plotitem.styles):
                style.adjustaxis(privatedata, plotitem.sharedata, graph, self.yname, plotitem.points, 1)


class paramfunction(_staticdata):

    defaultstyles = [style.line()]

    def __init__(self, varname, min, max, expression, title=notitle, points=100, parser=mathtree.parser(), context={}):
        if title is notitle:
            self.title = expression
        else:
            self.title = title
        varlist, expressionlist = expression.split("=")
        keys = varlist.split(",")
        mathtrees = parser.parse(expressionlist)
        if len(keys) != len(mathtrees):
            raise ValueError("unpack tuple of wrong size")
        l = len(keys)
        self.points = [None]*points
        self.columns = {}
        for index, key in enumerate(keys):
            self.columns[key.strip()] = index
        for i in range(points):
            param = min + (max-min)*i / (points-1.0)
            context[varname] = param
            self.points[i] = [None]*l
            for index, mathtree in enumerate(mathtrees):
                try:
                    self.points[i][index] = mathtree.Calc(**context)
                except (ArithmeticError, ValueError):
                    self.points[i][index] = None

