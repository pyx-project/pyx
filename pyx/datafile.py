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

class datafile:

    def splitline(self, line, stringpattern, columnpattern, tofloat=1):
        result = []
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
        return result

    def __init__(self, filename, commentpattern=re.compile(r"(#+|!+|%+)\s*"),
                                 stringpattern=re.compile(r"\"(.*?)\"(\s+|$)"),
                                 columnpattern=re.compile(r"(.*?)(\s+|$)")):
        self.filename = filename
        file = open(filename, "r")
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
                linedata = [linenumber]
                for value in self.splitline(line, stringpattern, columnpattern, tofloat=1):
                    linedata.append(value)
                if len(linedata) > 1:
                    if len(linedata) > maxcolumns:
                        maxcolumns = len(linedata)
                    linenumber += 1
                    self.data.append(linedata)
        if linenumber:
            self.titles = [None] + self.titles[:maxcolumns-1]
            self.titles += [None] * (maxcolumns - len(self.titles))
            for line in self.data:
                line += [None] * (maxcolumns - len(line))

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

    def addcolumn(self, expression, **columns):
        split = expression.rindex("=")
        if split > 0:
            self.titles.append(expression[:split])
            expression = expression[split+1:]
        else:
            self.titles.append(None)
        tree = mathtree.ParseMathTree(mathtree.ParseStr(expression))
        columnlist = {}
        for key, column in columns.items():
            columnlist[key] = self.getcolumnno(column)
        for key in tree.VarList():
            if key not in columnlist.keys():
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
