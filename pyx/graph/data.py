# -*- encoding: utf-8 -*-
#
#
# Copyright (C) 2002-2004 Jörg Lehmann <joerg@pyx-project.org>
# Copyright (C) 2003-2004 Michael Schindler <m-schindler@users.sourceforge.net>
# Copyright (C) 2002-2012 André Wobst <wobsta@pyx-project.org>
#
# This file is part of PyX (https://pyx-project.org/).
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

import math, re, configparser, struct
from pyx import text
from . import style
builtinlist = list


def splitatvalue(value, *splitpoints):
    section = 0
    while section < len(splitpoints) and splitpoints[section] < value:
        section += 1
    if len(splitpoints) > 1:
        if section % 2:
            section = None
        else:
            section >>= 1
    return (section, value)


_mathglobals = {"neg": lambda x: -x,
                "abs": lambda x: x < 0 and -x or x,
                "sgn": lambda x: x < 0 and -1 or 1,
                "sqrt": math.sqrt,
                "exp": math.exp,
                "log": math.log,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "asin": math.asin,
                "acos": math.acos,
                "atan": math.atan,
                "sind": lambda x: math.sin(math.pi/180*x),
                "cosd": lambda x: math.cos(math.pi/180*x),
                "tand": lambda x: math.tan(math.pi/180*x),
                "asind": lambda x: 180/math.pi*math.asin(x),
                "acosd": lambda x: 180/math.pi*math.acos(x),
                "atand": lambda x: 180/math.pi*math.atan(x),
                "norm": lambda x, y: math.hypot(x, y),
                "splitatvalue": splitatvalue,
                "pi": math.pi,
                "e": math.e}


class _data:
    """graph data interface

    Graph data consists of columns, where each column might be identified by a
    string or an integer. Each row in the resulting table refers to a data
    point.

    All methods except for the constructor should consider self and its
    attributes to be readonly, since the data instance might be shared between
    several graphs simultaneously.

    The instance variable columns is a dictionary mapping column names to the
    data of the column (i.e. to a list). Only static columns (known at
    construction time) are contained in that dictionary. For data with numbered
    columns the column data is also available via the list columndata.
    Otherwise the columndata list should be missing and an access to a column
    number will fail.

    The names of all columns (static and dynamic) must be fixed at the constructor
    and stated in the columnnames dictionary.

    The instance variable title and defaultstyles contain the data title and
    the default styles (a list of styles), respectively. If defaultstyles is None,
    the data cannot be plotted without user provided styles.
    """

    def dynamiccolumns(self, graph, axisnames):
        """create and return dynamic columns data

        Returns dynamic data matching the given axes (the axes range and other
        data might be used). The return value is a dictionary similar to the
        columns instance variable. However, the static and dynamic data does
        not need to be correlated in any way, i.e. the number of data points in
        self.columns might differ from the number of data points represented by
        the return value of the dynamiccolumns method.
        """
        return {}


defaultsymbols = [style.symbol()]
defaultlines = [style.line()]


class values(_data):

    defaultstyles = defaultsymbols

    def __init__(self, title="user provided values", **columns):
        for i, values in enumerate(list(columns.values())):
            if i and len(values) != l:
                raise ValueError("different number of values")
            else:
                l = len(values)
        self.columns = columns
        self.columnnames = list(columns.keys())
        self.title = title


class points(_data):
    "Graph data from a list of points"

    defaultstyles = defaultsymbols

    def __init__(self, points, title="user provided points", addlinenumbers=1, **columns):
        if len(points):
            l = len(points[0])
            self.columndata = [[x] for x in points[0]]
            for point in points[1:]:
                if l != len(point):
                    raise ValueError("different number of columns per point")
                for i, x in enumerate(point):
                    self.columndata[i].append(x)
            for v in list(columns.values()):
                if abs(v) > l or (not addlinenumbers and abs(v) == l):
                    raise ValueError("column number bigger than number of columns")
            if addlinenumbers:
                self.columndata = [list(range(1, len(points) + 1))] + self.columndata
            self.columns = dict([(key, self.columndata[i]) for key, i in list(columns.items())])
        else:
            self.columns = dict([(key, []) for key, i in list(columns.items())])
        self.columnnames = list(self.columns.keys())
        self.title = title


class _notitle:
    pass

_columnintref = re.compile(r"\$(-?\d+)", re.IGNORECASE)

class data(_data):
    "creates a new data set out of an existing data set"

    def __init__(self, data, title=_notitle, context={}, copy=1,
                       replacedollar=1, columncallback="__column__", **columns):
        # build a nice title
        if title is _notitle:
            items = list(columns.items())
            items.sort() # we want sorted items (otherwise they would be unpredictable scrambled)
            self.title = "%s: %s" % (text.escapestring(data.title or "unknown source"),
                                     ", ".join(["%s=%s" % (text.escapestring(key),
                                                           text.escapestring(str(value)))
                                                for key, value in items]))
        else:
            self.title = title

        self.orgdata = data
        self.defaultstyles = self.orgdata.defaultstyles

        # analyse the **columns argument
        self.columns = {}
        for columnname, value in list(columns.items()):
            # search in the columns dictionary
            try:
                self.columns[columnname] = self.orgdata.columns[value]
            except KeyError:
                # search in the columndata list
                try:
                    self.columns[columnname] = self.orgdata.columndata[value]
                except (AttributeError, TypeError):
                    # value was not an valid column identifier
                    # i.e. take it as a mathematical expression
                    if replacedollar:
                        m = _columnintref.search(value)
                        while m:
                            value = "%s%s(%s)%s" % (value[:m.start()], columncallback, m.groups()[0], value[m.end():])
                            m = _columnintref.search(value)
                        value = value.replace("$", columncallback)
                    expression = compile(value.strip(), "<string>", "eval")
                    context = context.copy()
                    context[columncallback] = self.columncallback
                    if self.orgdata.columns:
                        key, columndata = list(self.orgdata.columns.items())[0]
                        count = len(columndata)
                    elif self.orgdata.columndata:
                        count = len(self.orgdata.columndata[0])
                    else:
                        count = 0
                    newdata = []
                    for i in range(count):
                        self.columncallbackcount = i
                        for key, values in list(self.orgdata.columns.items()):
                            context[key] = values[i]
                        try:
                            newdata.append(eval(expression, _mathglobals, context))
                        except (ArithmeticError, ValueError):
                            newdata.append(None)
                    self.columns[columnname] = newdata

        if copy:
            # copy other, non-conflicting column names
            for columnname, columndata in list(self.orgdata.columns.items()):
                if columnname not in self.columns:
                    self.columns[columnname] = columndata

        self.columnnames = list(self.columns.keys())

    def columncallback(self, value):
        try:
            return self.orgdata.columndata[value][self.columncallbackcount]
        except Exception:
            return self.orgdata.columns[value][self.columncallbackcount]


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
                    return list(map(float, line.split()))
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
            for i in range(len(columndata)):
                if len(columndata[i]) != maxcolumns:
                    columndata[i].extend([None]*(maxcolumns-len(columndata[i])))
            return points(columndata, title=title, addlinenumbers=0,
                          **dict([(column, i+1) for i, column in enumerate(columns[:maxcolumns-1])]))

        try:
            filename.readlines
        except Exception:
            # not a file-like object -> open it
            cachekey = self.getcachekey(filename, commentpattern, stringpattern, columnpattern, skiphead, skiptail, every)
            if cachekey not in filecache:
                with open(filename) as f:
                    filecache[cachekey] = readfile(f, filename)
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
            config = configparser.ConfigParser(strict=False)
            config.optionxform = str
            config.read_file(file)
            sections = config.sections()
            sections.sort()
            columndata = [None]*len(sections)
            maxcolumns = 1
            columns = {}
            for i in range(len(sections)):
                point = [sections[i]] + [None]*(maxcolumns-1)
                for option in config.options(sections[i]):
                    value = config.get(sections[i], option)
                    try:
                        value = float(value)
                    except Exception:
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
            result = data(points(columndata, addlinenumbers=0, **columns), title=title)
            # ... but reinsert sections as linenumbers
            result.columndata = [[x[0] for x in columndata]]
            return result

        try:
            filename.readlines
        except Exception:
            # not a file-like object -> open it
            if filename not in filecache:
                filecache[filename] = readfile(open(filename), filename)
            data.__init__(self, filecache[filename], **kwargs)
        else:
            data.__init__(self, readfile(filename, "user provided file-like object"), **kwargs)


cbdfilecache = {}

class cbdfile(data):

    defaultstyles = defaultlines

    def getcachekey(self, *args):
        return ":".join([str(x) for x in args])

    def __init__(self, filename, minrank=None, maxrank=None, **kwargs):

        class cbdhead:

            def __init__(self, file):
                (self.magic,
                 self.dictaddr,
                 self.segcount,
                 self.segsize,
                 self.segmax,
                 self.fill) = struct.unpack("<5i20s", file.read(40))
                if self.magic != 0x20770002:
                    raise ValueError("bad magic number")

        class segdict:

            def __init__(self, file, i):
                self.index = i
                (self.segid,
                 self.maxlat,
                 self.minlat,
                 self.maxlong,
                 self.minlong,
                 self.absaddr,
                 self.nbytes,
                 self.rank) = struct.unpack("<6i2h", file.read(28))

        class segment:

            def __init__(self, file, sd):
                file.seek(sd.absaddr)
                (self.orgx,
                 self.orgy,
                 self.id,
                 self.nstrokes,
                 self.dummy) = struct.unpack("<3i2h", file.read(16))
                oln, olt = self.orgx, self.orgy
                self.points = [(olt, oln)]
                for i in range(self.nstrokes):
                    c1, c2 = struct.unpack("2c", file.read(2))
                    if ord(c2) & 0x40:
                        if c1 > "\177":
                            dy = ord(c1) - 256
                        else:
                            dy = ord(c1)
                        if c2 > "\177":
                            dx = ord(c2) - 256
                        else:
                            dx = ord(c2) - 64
                    else:
                        c3, c4, c5, c6, c7, c8 = struct.unpack("6c", file.read(6))
                        if c2 > "\177":
                            c2 = chr(ord(c2) | 0x40)
                        dx, dy = struct.unpack("<2i", c3+c4+c1+c2+c7+c8+c5+c6)
                    oln += dx
                    olt += dy
                    self.points.append((olt, oln))
                sd.nstrokes = self.nstrokes

        def readfile(file, title):
            h = cbdhead(file)
            file.seek(h.dictaddr)
            sds = [segdict(file, i+1) for i in range(h.segcount)]
            sbs = [segment(file, sd) for sd in sds]

            # remove jumps at long +/- 180
            for sd, sb in zip(sds, sbs):
                if sd.minlong < -150*3600 and sd.maxlong > 150*3600:
                    for i, (lat, int) in enumerate(sb.points):
                         if int < 0:
                             sb.points[i] = lat, int + 360*3600

            columndata = []
            for sd, sb in zip(sds, sbs):
                if ((minrank is None or sd.rank >= minrank) and
                    (maxrank is None or sd.rank <= maxrank)):
                    if columndata:
                        columndata.append((None, None))
                    columndata.extend([(int/3600.0, lat/3600.0)
                                       for lat, int in sb.points])

            result = points(columndata, title=title)
            result.defaultstyles = self.defaultstyles
            return result


        try:
            filename.readlines
        except Exception:
            # not a file-like object -> open it
            cachekey = self.getcachekey(filename, minrank, maxrank)
            if cachekey not in cbdfilecache:
                cbdfilecache[cachekey] = readfile(open(filename, "rb"), filename)
            data.__init__(self, cbdfilecache[cachekey], **kwargs)
        else:
            data.__init__(self, readfile(filename, "user provided file-like object"), **kwargs)


class function(_data):

    defaultstyles = defaultlines

    assignmentpattern = re.compile(r"\s*([a-z_][a-z0-9_]*)\s*\(\s*([a-z_][a-z0-9_]*)\s*\)\s*=", re.IGNORECASE)

    def __init__(self, expression, title=_notitle, min=None, max=None,
                 points=100, context={}):

        if title is _notitle:
            self.title = expression
        else:
            self.title = title
        self.min = min
        self.max = max
        self.numberofpoints = points
        self.context = context.copy() # be safe on late evaluations
        m = self.assignmentpattern.match(expression)
        if m:
            self.yname, self.xname = m.groups()
            expression = expression[m.end():]
        else:
            raise ValueError("y(x)=... or similar expected")
        if self.xname in context:
            raise ValueError("xname in context")
        self.expression = compile(expression.strip(), "<string>", "eval")
        self.columns = {}
        self.columnnames = [self.xname, self.yname]

    def dynamiccolumns(self, graph, axisnames):
        dynamiccolumns = {self.xname: [], self.yname: []}

        xaxis = graph.axes[axisnames.get(self.xname, self.xname)]
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
                y = eval(self.expression, _mathglobals, self.context)
            except (ArithmeticError, ValueError):
                y = None
            dynamiccolumns[self.yname].append(y)
        return dynamiccolumns


class functionxy(function):

    def __init__(self, f, min=None, max=None, **kwargs):
        function.__init__(self, "y(x)=f(x)", context={"f": f}, min=min, max=max, **kwargs)


class paramfunction(_data):

    defaultstyles = defaultlines

    def __init__(self, varname, min, max, expression, title=_notitle, points=100, context={}):
        if varname in context:
            raise ValueError("varname in context")
        if title is _notitle:
            self.title = expression
        else:
            self.title = title
        varlist, expression = expression.split("=")
        expression = compile(expression.strip(), "<string>", "eval")
        keys = [key.strip() for key in varlist.split(",")]
        self.columns = dict([(key, []) for key in keys])
        context = context.copy()
        for i in range(points):
            param = min + (max-min)*i / (points-1.0)
            context[varname] = param
            values = eval(expression, _mathglobals, context)
            for key, value in zip(keys, values):
                self.columns[key].append(value)
        if len(keys) != len(values):
            raise ValueError("unpack tuple of wrong size")
        self.columnnames = list(self.columns.keys())


class paramfunctionxy(paramfunction):

    def __init__(self, f, min, max, **kwargs):
        paramfunction.__init__(self, "t", min, max, "x, y = f(t)", context={"f": f}, **kwargs)


class _nodefaultstyles:
    pass


class join(_data):
    "creates a new data set by joining from a list of data, it does however *not* combine points, but fills data with None if necessary"

    def merge_lists(self, lists):
        "merges list items w/o duplications, resulting order is arbitrary"
        result = set()
        for l in lists:
            result.update(set(l))
        return builtinlist(result)

    def merge_dicts(self, dicts):
        """merge dicts containing lists as values (with equal number of items
        per list in each dict), missing data is padded by None"""
        keys = self.merge_lists([list(d.keys()) for d in dicts])
        empties = []
        for d in dicts:
            if len(list(d.keys())) == len(keys):
                empties.append(None) # won't be needed later on
            else:
                values = list(d.values())
                if len(values):
                    empties.append([None]*len(values[0]))
                else:
                    # has no data at all -> do not add anything
                    empties.append([])
        result = {}
        for key in keys:
            result[key] = []
            for d, e in zip(dicts, empties):
                result[key].extend(d.get(key, e))
        return result

    def __init__(self, data, title=_notitle, defaultstyles=_nodefaultstyles):
        """takes a list of data, a title (if it should not be autoconstructed)
        and a defaultstyles list if there is no common defaultstyles setting
        for in the provided data"""
        assert len(data)
        self.data = data
        self.columnnames = self.merge_lists([d.columnnames for d in data])
        self.columns = self.merge_dicts([d.columns for d in data])
        if title is _notitle:
            self.title = " + ".join([d.title for d in data])
        else:
            self.title = title
        if defaultstyles is _nodefaultstyles:
            self.defaultstyles = data[0].defaultstyles
            for d in data[1:]:
                if d.defaultstyles is not self.defaultstyles:
                    self.defaultstyles = None
                    break
        else:
            self.defaultstyles = defaultstyles

    def dynamiccolumns(self, graph, axisnames):
        return self.merge_dicts([d.dynamiccolumns(graph, axisnames) for d in self.data])
