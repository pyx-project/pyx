#!/usr/bin/env python
#
# $Header$
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


import re
import mathtree


class ColumnError(Exception): pass


class _datafile:

    def __init__(self, parser=mathtree.parser(MathTreeVals=mathtree.MathTreeValsWithCol)):
        self.parser = parser

    def getcolumnno(self, column):
        if self.titles.count(column) == 1:
            return self.titles.index(column)
        try:
            self.titles[column]
        except (TypeError, IndexError, ValueError):
            raise ColumnError
        return column

    def getcolumn(self, column):
        columnno = self.getcolumnno(column)
        return [x[columnno] for x in self.data]

    def _addcolumn(self, expression, **columns):
        try:
            split = expression.rindex("=")
        except ValueError:
            self.titles.append(None)
        else:
            self.titles.append(expression[:split])
            expression = expression[split+1:]
        tree = self.parser.parse(expression)
        columnlist = {}
        for key in tree.VarList():
            if key[0] == "$":
                column = int(key[1])
                try:
                    self.titles[column]
                except:
                    raise ColumnError
                columnlist[key] = column
            else:
                try:
                    columnlist[key] = self.getcolumnno(columns[key])
                except KeyError:
                    columnlist[key] = self.getcolumnno(key)
        varlist = {}
        for data in self.data:
            try:
                for key in columnlist.keys():
                    varlist[key] = float(data[columnlist[key]])
            except (TypeError, ValueError):
                data.append(None)
            else:
                data.append(tree.Calc(varlist))
        return columnlist.keys()

    def addcolumn(self, expression, **columns):
        usedkeys = self._addcolumn(expression, **columns)
        unusedkeys = [key for key in columns.keys() if key not in usedkeys]
        if len(unusedkeys):
            raise KeyError("unused keys %s" % unusedkeys)
        return self



class datafile(_datafile):
    defaultcommentpattern = re.compile(r"(#+|!+|%+)\s*")
    defaultstringpattern = re.compile(r"\"(.*?)\"(\s+|$)")
    defaultcolumnpattern = re.compile(r"(.*?)(\s+|$)")

    def splitline(self, line, stringpattern, columnpattern, tofloat=1):
        result = []
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
                             columnpattern=defaultcolumnpattern, **args):
        _datafile.__init__(self, **args)
        try:
            file + ''
        except TypeError:
            pass
        else:
            file = open(file, "r")
        self.titles = []
        self.data = []
        linenumber = 0
        maxcolumns = 0
        for line in file.readlines():
            line = line.strip()
            match = commentpattern.match(line)
            if match:
                if not len(self.data):
                    newtitles = self.splitline(line[match.end():], stringpattern, columnpattern, tofloat=0)
                    if len(newtitles):
                        self.titles = newtitles
            else:
                linedata = []
                for value in self.splitline(line, stringpattern, columnpattern, tofloat=1):
                    linedata.append(value)
                if len(linedata):
                    linenumber += 1
                    linedata = [linenumber] + linedata
                    if len(linedata) > maxcolumns:
                        maxcolumns = len(linedata)
                    self.data.append(linedata)
        if linenumber:
            self.titles = [None] + self.titles[:maxcolumns-1]
            self.titles += [None] * (maxcolumns - len(self.titles))
            for line in self.data:
                line += [None] * (maxcolumns - len(line))
