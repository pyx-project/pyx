#!/usr/bin/env python
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


ColPattern = re.compile(r"\$-?[0-9]+")

class MathTreeValCol(mathtree.MathTreeValVar):

    def InitByParser(self, arg):
        Match = arg.MatchPattern(ColPattern)
        if Match:
            self.AddArg(Match)
            return 1


MathTreeValsWithCol = (mathtree.MathTreeValConst,
                       mathtree.MathTreeValVar,
                       MathTreeValCol)


class data:

    def __init__(self, titles, data, parser=mathtree.parser(MathTreeVals=MathTreeValsWithCol)):
        self.titles = titles
        self.data = data
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
        for key in tree.VarList():
            if key[0] == "$":
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

        varlist = context.copy()
        for data in self.data:
            try:
                for key in columnlist.keys():
                    varlist[key] = float(data[columnlist[key]])
            except (TypeError, ValueError):
                data.append(None)
            else:
                data.append(tree.Calc(**varlist))


class datafile(data):

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
                    linenumber += 1
                    linedata = [linenumber] + linedata
                    if len(linedata) > maxcolumns:
                        maxcolumns = len(linedata)
                    usedata.append(linedata)
        if linenumber:
            usetitles = [None] + usetitles[:maxcolumns-1]
            usetitles += [None] * (maxcolumns - len(usetitles))
            for line in usedata:
                line += [None] * (maxcolumns - len(line))
        else:
            usetitles = []
        data.__init__(self, usetitles, usedata, **args)



class sectionfile(data):

    def __init__(self, file, sectionstr = "section", **args):
        config = ConfigParser.ConfigParser()
        config.optionxform = str
        try:
            file = file + ''
        except TypeError:
            config.readfp(file)
        else:
            config.readfp(open(file, "r"))
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
        data.__init__(self, usetitles, usedata, **args)

