#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2002 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2002 André Wobst <wobsta@users.sourceforge.net>
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
import helper, mathtree


class ColumnError(Exception): pass

# XXX: for new mathtree parser
class MathTreeFuncCol(mathtree.MathTreeValVar):

    def __init__(self, *args):
        self.name = "_col_"
        self.VarName = None
        mathtree.MathTreeValVar.__init__(self, *args)

    def VarList(self):
        return [self]

    def ColNo(HIDDEN_self, **args):
        i = int(HIDDEN_self.Args[0].Calc(**args))
        HIDDEN_self.VarName = "_col_%d" % (i)
        return i

    def Calc(HIDDEN_self, **args):
        return mathtree.MathTreeValVar(HIDDEN_self.VarName).Calc(**args)

MathTreeFuncsWithCol = list(mathtree.DefaultMathTreeFuncs) + [MathTreeFuncCol]
# XXX: end of snip for new mathtree-parser
# XXX: begin of snip for old mathtree-parser
ColPattern = re.compile(r"\$(\(-?[0-9]+\)|-?[0-9]+)")

class MathTreeValCol(mathtree.MathTreeValVar):
    """column id pattern like "$1" or "$(1)"
    defines a new value pattern to identify columns by its number"""

    # __implements__ = ...    # TODO: mathtree interfaces

    def InitByParser(self, arg):
        Match = arg.MatchPattern(ColPattern)
        if Match:
            # just store the matched string -> handle this variable name later on
            self.AddArg(Match)
            return 1


# extent the list of possible values by MathTreeValCol
MathTreeValsWithCol = tuple(list(mathtree.DefaultMathTreeVals) + [MathTreeValCol])
# XXX: end of snip for old mathtree-parser


class _Idata:
    """interface definition of a data object
    data objects store data arranged in rows and columns"""

    titles = []
    """column titles
    - a list of strings storing the column titles
    - the length of the list must match the number of columns
    - any titles entry might be None, thus explicitly not providing a column title"""

    data = []
    """column/row data
    - a list of rows where each row represents a data point
    - each row contains a list, where each entry of the list represents a value for a column
    - the number of columns for each data point must match the number of columns
    - any column enty of any data point might be a float, a string, or None"""

    def getcolumnno(self, column):
        """returns a column number
        - the column parameter might be an integer to be used as a column number
        - a column number must be a valid list index (negative values are allowed)
        - the column parameter might be a string contained in the titles list;
          to be valid, the string must be unique within the titles list
        - the method raises ColumnError when the value of the column parameter is invalid"""

    def getcolumn(self, column):
        """returns a column
        - extracts a column out of self.data and returns it as a list
        - the column is identified by the parameter column as in getcolumnno"""

    def addcolumn(self, expression, context={}):
        """adds a column defined by a mathematical expression
        - evaluates the expression for each data row and adds a new column at
          the end of each data row
        - the expression must be a valid mathtree expression (see module mathtree)
          with an extended variable name syntax: strings like "$i" and "$(i)" are
          allowed where i is an integer
        - a variable of the mathematical expression might either be a column title
          or, by the extended variable name syntax, it defines an integer to be used
          as a list index within the column list for each row
        - context is a dictionary, where external variables and functions can be
          given; those are used in the evaluation of the expression
        - when the expression contains the character "=", everything after the last
          "=" is interpreted as the mathematical expression while everything before
          this character will be used as a column title for the new column; when no
          "=" is contained in the expression, the hole expression is taken as the
          mathematical expression and the column title is set to None"""


class _data:

    """an (minimal) implementor of _Idata
    other classes providing _Idata might be based on is class"""

    __implements__ = _Idata

    def __init__(self, data, titles, parser=mathtree.parser(
           MathTreeVals=MathTreeValsWithCol, MathTreeFuncs=MathTreeFuncsWithCol)):
        """initializes an instance
        - data and titles are just set as instance variables without further checks ---
          they must be valid in terms of _Idata (expecially their sizes must fit)
        - parser is used in addcolumn and thus must implement the expression parsing as
          defined in _Idata"""
        self.data = data
        self.titles = titles
        self.parser = parser

    def getcolumnno(self, column):
        if helper.isstring(column) and self.titles.count(column) == 1:
            return self.titles.index(column)
        try:
            self.titles[column]
        except (TypeError, IndexError, ValueError):
            raise ColumnError
        return column

    def getcolumn(self, column):
        columnno = self.getcolumnno(column)
        return [x[columnno] for x in self.data]

    def addcolumn(self, expression, context={}):
        try:
            split = expression.rindex("=")
        except ValueError:
            self.titles.append(None)
        else:
            self.titles.append(expression[:split])
            expression = expression[split+1:]
        tree = self.parser.parse(expression)
        columnlist = {}
        varlist = context.copy() # do not modify context
        if self.parser.isnewparser == 1: # XXX: switch between mathtree-parsers
            for key in tree.VarList():
                if isinstance(key, MathTreeFuncCol):
                    column = int(key.ColNo(**varlist))
                    try:
                        self.titles[column]
                    except:
                        raise ColumnError
                    columnlist["_col_%d" % (column)] = column
                elif key[0:5] == "_col_":
                    column = int(key[5:])
                    try:
                        self.titles[column]
                    except:
                        raise ColumnError
                    columnlist[key] = column
                else:
                    try:
                        columnlist[key] = self.getcolumnno(key)
                    except ColumnError, e:
                        if key not in context.keys():
                            raise e
        else:
            for key in tree.VarList():
                if key[0] == "$":
                    if key[1] == "(":
                        column = int(key[2:-1])
                    else:
                        column = int(key[1:])
                    try:
                        self.titles[column]
                    except:
                        raise ColumnError
                    columnlist[key] = column
                else:
                    try:
                        columnlist[key] = self.getcolumnno(key)
                    except ColumnError, e:
                        if key not in context.keys():
                            raise e

        for data in self.data:
            try:
                for key in columnlist.keys():
                    varlist[key] = float(data[columnlist[key]])
            except (TypeError, ValueError):
                data.append(None)
            else:
                data.append(tree.Calc(**varlist))


class data(_data):

    "an implementation of _Idata with an easy to use constructor"

    __implements__ = _Idata

    def __init__(self, data=[], titles=[], maxcolumns=helper.nodefault, **kwargs):
        """initializes an instance
        - data titles must be valid in terms of _Idata except for the number of
          columns for each row, especially titles might be the default, e.g. []
        - instead of lists for data, each row in data, and titles, tuples or
          any other data structure with sequence like behavior might be used,
          but they are converted to lists
        - maxcolumns is an integer; when not set, maxcolumns is evaluated out of
          the maximum column number in each row of data (not taking into account
          the titles list)
        - titles and each row in data is extended (or cutted) to fit maxcolumns;
          when extending those lists, None entries are appended
        - parser is used in addcolumn and thus must implement the expression parsing as
          defined in _Idata
        - further keyword arguments are passed to the constructor of _data"""
        if len(data):
            if maxcolumns is helper.nodefault:
                maxcolumns = len(data[0])
                for line in data[1:]:
                    if len(line) > maxcolumns:
                        maxcolumns = len(line)
            titles = list(titles[:maxcolumns])
            titles += [None] * (maxcolumns - len(titles))
            data = list(data)
            for i in range(len(data)):
                data[i] = list(data[i]) + [None] * (maxcolumns - len(data[i]))
        else:
            titles = []
        _data.__init__(self, data, titles, **kwargs)


class datafile(data):

    "an implementation of _Idata reading data from a file"

    __implements__ = _Idata

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

    def __init__(self, file, commentpattern=defaultcommentpattern,
                             stringpattern=defaultstringpattern,
                             columnpattern=defaultcolumnpattern,
                             skiphead=0, skiptail=0, every=1, **kwargs):
        """read data from a file
        - file might either be a string or a file instance (something, that
          provides readlines())
        - each non-empty line, which does not match the commentpattern, is
          considered to be a data row; columns are extracted by the splitline
          method using tofloat=1
        - the last line before a data line matching the commentpattern and
          containing further characters is considered as the title line;
          the title list is extracted by the splitline method using tofloat=0
        - the first skiphead data lines are skiped
        - the last skiptail data lines are skiped
        - only every "every" data line is used (starting at the skiphead + 1 line)
        - the number of columns is equalized between data and titles like
          in the data constructor without setting maxcolumns
        - further keyword arguments are passed to the constructor of data,
          keyword arguments data, titles, and maxcolumns excluded"""
        if helper.isstring(file):
            file = open(file, "r")
        usetitles = []
        usedata = []
        linenumber = 0
        maxcolumns = 0
        for line in file.readlines():
            line = line.strip()
            match = commentpattern.match(line)
            if match:
                if not len(usedata):
                    newtitles = self.splitline(line[match.end():], stringpattern, columnpattern, tofloat=0)
                    if len(newtitles):
                        usetitles = newtitles
            else:
                linedata = []
                for value in self.splitline(line, stringpattern, columnpattern, tofloat=1):
                    linedata.append(value)
                if len(linedata):
                    if linenumber >= skiphead and not ((linenumber - skiphead) % every):
                        linedata = [linenumber + 1] + linedata
                        if len(linedata) > maxcolumns:
                            maxcolumns = len(linedata)
                        usedata.append(linedata)
                    linenumber += 1
        if skiptail:
            del usedata[-skiptail:]
        data.__init__(self, data=usedata, titles=[None] + usetitles, maxcolumns=maxcolumns, **kwargs)



class sectionfile(_data):

    def __init__(self, file, sectionstr = "section", **kwargs):
        """read data from a config-like file
        - file might either be a string or a file instance (something, that
          is valid in config.readfp())
        - each row is defined by a section in the config-like file (see
          config module description)
        - the columns for each row are defined by lines in the section file;
          the title entries are used to identify the columns
        - further keyword arguments are passed to the constructor of _data,
          keyword arguments data and titles excluded"""
        config = ConfigParser.ConfigParser()
        config.optionxform = str
        if helper.isstring(file):
            config.readfp(open(file, "r"))
        else:
            config.readfp(file)
        usedata = []
        usetitles = [sectionstr]
        sections = config.sections()
        sections.sort()
        for section in sections:
            usedata.append([section] + [None for x in range(len(usetitles) - 1)])
            for option in config.options(section):
                if option == sectionstr:
                    raise ValueError("'%s' is already used as the section identifier" % sectionstr)
                try:
                    index = usetitles.index(option)
                except ValueError:
                    index = len(usetitles)
                    usetitles.append(option)
                    for line in usedata:
                        line.append(None)
                value = config.get(section, option)
                try:
                    usedata[-1][index] = float(value)
                except (TypeError, ValueError):
                    usedata[-1][index] = value
        _data.__init__(self, usedata, usetitles, **kwargs)

