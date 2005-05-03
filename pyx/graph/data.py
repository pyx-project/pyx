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


import math, re, ConfigParser, warnings
from pyx import mathtree, text
from pyx.graph import style

try:
    enumerate([])
except NameError:
    # fallback implementation for Python 2.2 and below
    def enumerate(list):
        return zip(xrange(len(list)), list)

try:
    dict()
except NameError:
    # fallback implementation for Python 2.1
    def dict(items):
        result = {}
        for key, value in items:
            result[key] = value
        return result


class _data:
    """graph data interface

    Graph data consists in columns, where each column might be identified by a
    string or an integer. Each row in the resulting table refers to a data
    point.

    All methods except for the constructor should consider self and its
    attributes to be readonly, since the data instance might be shared between
    several graphs simultaniously.

    The instance variable columns is a dictionary mapping column names to the
    data of the column (i.e. to a list). Only static columns (known at
    construction time) are contained in that dictionary. For data with numbered
    columns the column data is also available via the list columndata.
    Otherwise the columndata list should be missing and an access to a column
    number will fail.

    The instance variable title and defaultstyles contain the data title and
    the default styles (a list of styles), respectively.
    """

    def columnnames(self, graph):
        """return a list of column names

        Currently the column names might depend on the axes names. This dynamic
        nature is subject of removal for the future. Then the method could be
        replaced by an instance variable already initialized in the contructor.

        The result will be self.columns.keys() + self.dynamiccolums.keys(), but
        the later can only be called after the static axes ranges have been
        fixed. OTOH the column names are already needed in the initialization
        process of the styles sharedata and privatedata.
        """
        return self.columns.keys()

    def dynamiccolumns(self, graph):
        """create and return dynamic columns data

        Returns dynamic data matching the given axes (the axes range and other
        data might be used). The return value is a dictionary similar to the
        columns instance variable.
        """
        return {}


class list(_data):
    "Graph data from a list of points"

    defaultstyles = [style.symbol()]

    def __init__(self, points, title="user provided list", addlinenumbers=1, **columns):
        if len(points):
            l = len(points[0])
            self.columndata = [[x] for x in points[0]]
            for point in points[1:]:
                if l != len(point):
                    raise ValueError("different number of columns per point")
                for i, x in enumerate(point):
                    self.columndata[i].append(x)
            for v in columns.values():
                if abs(v) > l or (not addlinenumbers and abs(v) == l):
                    raise ValueError("column number bigger than number of columns")
            if addlinenumbers:
                self.columndata = [range(1, len(points) + 1)] + self.columndata
            self.columns = dict([(key, self.columndata[i]) for key, i in columns.items()])
        else:
            self.columns = dict([(key, []) for key, i in columns])
        self.title = title
        self.defaultstyles = [style.symbol()]



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
    pass

class data(_data):
    "creates a new data set out of an existing data set"

    def __init__(self, data, title=_notitle, parser=dataparser(), context={}, copy=1, **columns):
        # build a nice title
        if title is _notitle:
            items = columns.items()
            items.sort() # we want sorted items (otherwise they would be unpredictable scrambled)
            self.title = "%s: %s" % (data.title,
                                     ", ".join(["%s=%s" % (text.escapestring(key),
                                                           text.escapestring(value))
                                                for key, value in items]))
        else:
            self.title = title

        self.orgdata = data
        self.defaultstyles = self.orgdata.defaultstyles

        # analyse the **columns argument
        self.columns = {}
        for columnname, value in columns.items():
            try:
                self.columns[columnname] = self.orgdata.columns[value]
            except:
                pass
            try:
                self.columns[columnname] = self.orgdata.columndata[value]
            except:
                pass
            # value was not an valid column identifier
            if not self.columns.has_key(columnname):
                # take it as a mathematical expression
                tree = parser.parse(value)
                columndict = tree.columndict(**context)
                vars = {}
                for var, columnnumber in columndict.items():
                    # column data accessed via $<column number>
                    vars[var] = self.orgdata.columndata[columnnumber]
                for var in tree.VarList():
                    try:
                        # column data accessed via the name of the column
                        vars[var] = self.orgdata.columns[var]
                    except (KeyError, ValueError):
                        # other data available in context
                        if var not in context.keys():
                            raise ValueError("undefined variable '%s'" % var)
                newdata = []
                usevars = context.copy() # do not modify context, use a copy vars instead
                if self.orgdata.columns:
                    key, columndata = self.orgdata.columns.items()[0]
                    count = len(columndata)
                elif self.orgdata.columndata:
                    count = len(self.orgdata.columndata[0])
                else:
                    count = 0
                for i in xrange(count):
                    # insert column data as prepared in vars
                    for var, columndata in vars.items():
                        usevars[var] = columndata[i]
                    # evaluate expression
                    try:
                        newdata.append(tree.Calc(**usevars))
                    except (ArithmeticError, ValueError):
                        newdata.append(None)
                    # we could also do:
                    # point[newcolumnnumber] = eval(str(tree), vars)

                    # XXX: It might happen, that the evaluation of the expression
                    #      seems to work, but the result is NaN/Inf/-Inf. This
                    #      is highly plattform dependend.

                self.columns[columnname] = newdata

        if copy:
            # copy other, non-conflicting column names
            for columnname, columndata in self.orgdata.columns.items():
                if not self.columns.has_key(columnname):
                    self.columns[columnname] = columndata

    def getcolumnpointsindex(self, column):
        return self.columns[column]


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

        def readfile(file, title, self=self, commentpattern=commentpattern, stringpattern=stringpattern, columnpattern=columnpattern, skiphead=skiphead, skiptail=skiptail, every=every):
            columns = []
            columndata = []
            linenumber = 0
            maxcolumns = 0
            for line in file.readlines():
                line = line.strip()
                match = commentpattern.match(line)
                if match:
                    if not len(columndata):
                        columns = self.splitline(line[match.end():], stringpattern, columnpattern, tofloat=0)
                else:
                    linedata = []
                    for value in self.splitline(line, stringpattern, columnpattern, tofloat=1):
                        linedata.append(value)
                    if len(linedata):
                        if linenumber >= skiphead and not ((linenumber - skiphead) % every):
                            linedata = [linenumber + 1] + linedata
                            if len(linedata) > maxcolumns:
                                maxcolumns = len(linedata)
                            columndata.append(linedata)
                        linenumber += 1
            if skiptail >= every:
                skip, x = divmod(skiptail, every)
                del columndata[-skip:]
            for i in xrange(len(columndata)):
                if len(columndata[i]) != maxcolumns:
                    columndata[i].extend([None]*(maxcolumns-len(columndata[i])))
            return list(columndata, title=title, addlinenumbers=0,
                        **dict([(column, i+1) for i, column in enumerate(columns[:maxcolumns-1])]))

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
            columndata = [None]*len(sections)
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
                columndata[i] = point
            # wrap result into a data instance to remove column numbers
            result = data(list(columndata, addlinenumbers=0, **columns), title=title)
            # ... but reinsert sections as linenumbers
            result.columndata = [[x[0] for x in columndata]]
            return result

        try:
            filename.readlines
        except:
            # not a file-like object -> open it
            if not filecache.has_key(filename):
                filecache[filename] = readfile(open(filename), filename)
            data.__init__(self, filecache[filename], **kwargs)
        else:
            data.__init__(self, readfile(filename, "user provided file-like object"), **kwargs)


class function(_data):

    defaultstyles = [style.line()]

    assignmentpattern = re.compile(r"\s*([a-z_][a-z0-9_]*)\s*\(\s*([a-z_][a-z0-9_]*)\s*\)\s*=", re.IGNORECASE)

    def __init__(self, expression, title=_notitle, min=None, max=None,
                 points=100, parser=mathtree.parser(), context={}):

        if title is _notitle:
            self.title = expression
        else:
            self.title = title
        self.min = min
        self.max = max
        self.numberofpoints = points
        self.context = context.copy() # be save on late evaluations
        m = self.assignmentpattern.match(expression)
        if m:
            self.yname, self.xname = m.groups()
            expression = expression[m.end():]
        else:
            warnings.warn("implicit variables are deprecated, use y(x)=... and the like", DeprecationWarning)
            self.xname = None
            self.yname, expression = [x.strip() for x in expression.split("=")]
        self.mathtree = parser.parse(expression)
        self.columns = {}

    def columnnames(self, graph):
        if self.xname is None:
            for xname in self.mathtree.VarList():
                if xname in graph.axes.keys():
                    if self.xname is None:
                        self.xname = xname
                    else:
                        raise ValueError("multiple variables found")
            if self.xname is None:
                raise ValueError("no variable found")
        return [self.xname, self.yname]

    def dynamiccolumns(self, graph):
        dynamiccolumns = {self.xname: [], self.yname: []}

        xaxis = graph.axes[self.xname]
        from pyx.graph.axis import logarithmic
        logaxis = isinstance(xaxis.axis, logarithmic)
        if self.min is not None:
            min = self.min
        else:
            min = xaxis.data.min
        if self.max is not None:
            max = self.max
        else:
            max = xaxis.data.max
        if logaxis:
            min = math.log(min)
            max = math.log(max)
        for i in range(self.numberofpoints):
            x = min + (max-min)*i / (self.numberofpoints-1.0)
            if logaxis:
                x = math.exp(x)
            dynamiccolumns[self.xname].append(x)
            self.context[self.xname] = x
            try:
                y = self.mathtree.Calc(**self.context)
            except (ArithmeticError, ValueError):
                y = None
            dynamiccolumns[self.yname].append(y)
        return dynamiccolumns


class paramfunction(_data):

    defaultstyles = [style.line()]

    def __init__(self, varname, min, max, expression, title=_notitle, points=100, parser=mathtree.parser(), context={}):
        if title is _notitle:
            self.title = expression
        else:
            self.title = title
        varlist, expressionlist = expression.split("=")
        keys = [key.strip() for key in varlist.split(",")]
        mathtrees = parser.parse(expressionlist)
        if len(keys) != len(mathtrees):
            raise ValueError("unpack tuple of wrong size")
        self.columns = dict([(key, []) for key in keys])
        context = context.copy()
        for i in range(points):
            param = min + (max-min)*i / (points-1.0)
            context[varname] = param
            for key, mathtree in zip(keys, mathtrees):
                try:
                    self.columns[key].append(mathtree.Calc(**context))
                except (ArithmeticError, ValueError):
                    self.columns[key].append(None)
