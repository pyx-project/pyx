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


import re
from pyx import mathtree
from pyx.graph import style


class _Idata:
    """interface definition of a data object
    data objects store data arranged in rows and columns"""

    columns = {}
    """a dictionary mapping column titles to column numbers"""

    points = []
    """column/row data
    - a list of rows where each row represents a data point
    - each row contains a list, where each entry of the list represents a value for a column
    - the number of columns for each data point must match the number of columns
    - any column enty of any data point might be a float, a string, or None"""

    title = ""
    """a string (for printing in PyX, e.g. in a graph key)
    - None is allowed, which marks the data instance to have no title,
      e.g. it should be skiped in a graph key etc.
    - the title does need to be unique"""

    def getcolumnnumber(self, column):
        """returns a column number
        - the column parameter might be an integer to be used as a column number
        - a column number must be a valid list index (negative values are allowed)
        - the column parameter might be a string contained in the columns list;
          to be valid, the string must be unique within the columns list"""

    def getcolumn(self, column):
        """returns a column
        - extracts a column out of self.data and returns it as a list
        - the column is identified by the parameter column as in getcolumnnumber"""


class _data:

    defaultstyle = style.symbol()

    def getcolumnnumber(self, key):
        try:
            key + ""
        except:
            return key + 0
        else:
            return self.columns[key.strip()]

    def getcolumn(self, key):
        columnno = self.getcolumnnumber(key)
        return [point[columnno] for point in self.points]

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


class list(_data):
    "creates data out of points"

    def __init__(self, points, title="unknown", maxcolumns=None, addlinenumbers=1, **columns):
        if maxcolumns is None and len(points):
            maxcolumns = max([len(point) for point in points])
        if addlinenumbers:
            for i in xrange(len(points)):
                points[i] = [i+1] + points[i] + [None] * (maxcolumns - len(points[i]))
        else:
            for i in xrange(len(points)):
                points[i] = points[i] + [None] * (maxcolumns - len(points[i]))
        self.points = points
        self.columns = columns
        self.title = title


##############################################################
# math tree enhanced by column handling
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


class copycolumn:
    # a helper storage class to mark a new column to copied
    # out of data from an old column
    def __init__(self, newcolumntitle, oldcolumnnumber):
        self.newcolumntitle = newcolumntitle
        self.oldcolumnnumber = oldcolumnnumber

class mathcolumn:
    """a helper storage class to mark a new column to created
    by evaluating a mathematical expression"""
    def __init__(self, newcolumntitle, expression, tree, varitems):
        # - expression is a string
        # - tree is a parsed mathematical tree, e.g. we can have
        #   call tree.Calc(**vars), where the dict vars maps variable
        #   names to values
        # - varitems is a list of (key, value) pairs, where the key
        #   stands is a variable name in the mathematical tree and
        #   the value is its value"""
        self.newcolumntitle = newcolumntitle
        self.expression = expression
        self.tree = tree
        self.varitems = varitems

class notitle:
    """this is a helper class to mark, that no title was privided
    (since a title equals None is a valid input, it needs to be
    distinguished from providing no title when a title will be
    created automatically)"""
    pass

class data(_data):
    "creates a new data set out of an existing data set"

    def __init__(self, data, title=notitle, parser=dataparser(), context={}, **columns):
        defaultstyle = data.defaultstyle

        # build a nice title
        if title is notitle:
            items = columns.items()
            items.sort() # we want sorted items (otherwise they would be unpredictable scrambled)
            self.title = data.title + ": " + ", ".join(["%s=%s" % item for item in items])
        else:
            self.title = title

        # analyse the **columns argument
        newcolumns = []
        hasmathcolumns = 0
        for newcolumntitle, columnexpr in columns.items():
            try:
                # try if it is a valid column identifier
                oldcolumnnumber = data.getcolumnnumber(columnexpr)
            except:
                # if not it should be a mathematical expression
                tree = parser.parse(columnexpr)
                columndict = tree.columndict(**context)
                for var in tree.VarList():
                    try:
                        columndict[var] = data.getcolumnnumber(var)
                    except KeyError, e:
                        if var not in context.keys():
                            raise e
                newcolumns.append(mathcolumn(newcolumntitle, columnexpr, tree, columndict.items()))
                hasmathcolumns = 1
            else:
                newcolumns.append(copycolumn(newcolumntitle, oldcolumnnumber))

        # ensure to copy the zeroth column (line number)
        # if we already do, place it first again, otherwise add it to the front
        i = 0
        for newcolumn in newcolumns:
            if isinstance(newcolumn, copycolumn) and not newcolumn.oldcolumnnumber:
                newcolumns.pop(i)
                newcolumns.insert(0, newcolumn)
                firstcolumnwithtitle = 0
                break
            i += 1
        else:
            newcolumns.insert(0, copycolumn(None, 0))
            firstcolumnwithtitle = 1

        if hasmathcolumns:
            # new column data needs to be calculated
            vars = context.copy() # do not modify context, use a copy vars instead
            self.points = [None]*len(data.points)
            countcolumns = len(newcolumns)
            for i in xrange(len(data.points)):
                datapoint = data.points[i]
                point = [None]*countcolumns
                newcolumnnumber = 0
                for newcolumn in newcolumns:
                    if isinstance(newcolumn, copycolumn):
                        point[newcolumnnumber] = datapoint[newcolumn.oldcolumnnumber]
                    else:
                        # update the vars
                        # TODO: we could update it once for all varitems
                        for newcolumntitle, value in newcolumn.varitems:
                            vars[newcolumntitle] = datapoint[value]
                        point[newcolumnnumber] = newcolumn.tree.Calc(**vars)
                        # we could also do:
                        # point[newcolumnnumber] = eval(str(newcolumn.tree), vars)
                    newcolumnnumber += 1
                self.points[i] = point

            # store the column titles
            self.columns = {}
            newcolumnnumber = firstcolumnwithtitle
            for newcolumn in newcolumns[firstcolumnwithtitle:]:
                self.columns[newcolumn.newcolumntitle] = newcolumnnumber
                newcolumnnumber += 1
        else:
            # since only column copies are needed, we can share the original points
            self.points = data.points

            # store the new column titles
            self.columns = {}
            for newcolumn in newcolumns[firstcolumnwithtitle:]:
                self.columns[newcolumn.newcolumntitle] = newcolumn.oldcolumnnumber


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
        cachekey = self.getcachekey(filename, commentpattern, stringpattern, columnpattern, skiphead, skiptail, every)
        if not filecache.has_key(cachekey):
            file = open(filename)
            self.title = filename
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
                            i += 1
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
            if skiptail:
                del points[-skiptail:]
            filecache[cachekey] = list(points, title=filename, maxcolumns=maxcolumns, addlinenumbers=0, **columns)
        data.__init__(self, filecache[cachekey], **kwargs)



class function:

    defaultstyle = style.line()

    def __init__(self, expression, title=notitle, min=None, max=None, points=100, parser=mathtree.parser(), context={}):
        if title is notitle:
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

    def __init__(self, varname, min, max, expression, title=notitle, points=100, parser=mathtree.parser(), context={}):
        if title is notitle:
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
        keys = varlist.split(",")
        mtrees = parser.parse(expressionlist)
        if len(keys) != len(mtrees):
            raise ValueError("unpack tuple of wrong size")
        for i in range(len(keys)):
            key = keys[i].strip()
            if self.mathtrees.has_key(key):
                raise ValueError("multiple assignment in tuple")
            self.mathtrees[key] = mtrees[i]
        if len(keys) != len(self.mathtrees.keys()):
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
            self.style.adjustaxes(range(len(self.mathtrees.items())), self)

    def draw(self, graph):
        self.style.drawpoints(graph, self)

