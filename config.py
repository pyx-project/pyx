# -*- encoding: utf-8 -*-
#
#
# Copyright (C) 2003-2011 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2003-2011 André Wobst <wobsta@users.sourceforge.net>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

import configparser, os.path, warnings
import os, io, warnings, pkgutil

from . import pycompat

builtinopen = open

try:
    import pykpathsea as pykpathsea_module
    has_pykpathsea = True
except ImportError:
    has_pykpathsea = False


# Locators implement an open method which returns a list of functions
# by searching for a file according to a specific rule. Each of the functions
# returned can be called (multiple times) and return an open file. The
# opening of the file might fail with a IOError which indicates, that the
# file could not be found at the given location.
# names is a list of kpsewhich format names to be used for searching where as
# extensions is a list of file extensions to be tried (including the dot). Note
# that the list of file extenions should include an empty string to not add
# an extension at all.

locator_classes = {}

class local:
    """locates files in the current directory"""

    def openers(self, filename, names, extensions):
        return [lambda extension=extension: builtinopen(filename+extension, "rb") for extension in extensions]

locator_classes["local"] = local


class internal:
    """locates files within the PyX data tree"""

    def openers(self, filename, names, extensions):
        for extension in extensions:
            full_filename = filename+extension
            dir = os.path.splitext(full_filename)[1][1:]
            try:
                data = pkgutil.get_data("pyx", "data/%s/%s" % (dir, full_filename))
            except IOError:
                pass
            else:
                if data:
                    return [lambda: io.BytesIO(data)]
        return []

locator_classes["internal"] = internal


class recursivedir:
    """locates files by searching recursively in a list of directories"""

    def __init__(self):
        self.dirs = getlist("filelocator", "recursivedir")
        self.full_filenames = {}

    def openers(self, filename, names, extensions):
        for extension in extensions:
            if filename+extension in self.full_filenames:
                return [lambda: builtinopen(self.full_filenames[filename], "rb")]
        while self.dirs:
            dir = self.dirs.pop(0)
            for item in os.listdir(dir):
                full_item = os.path.join(dir, item)
                if os.path.isdir(full_item):
                    self.dirs.insert(0, full_item)
                else:
                    self.full_filenames[item] = full_item
            for extension in extensions:
                if filename+extension in self.full_filenames:
                    return [lambda: builtinopen(self.full_filenames[filename], "rb")]
        return []

locator_classes["recursivedir"] = recursivedir


class ls_R:
    """locates files by searching a list of ls-R files"""

    def __init__(self):
        self.ls_Rs = getlist("filelocator", "ls-R")
        self.full_filenames = {}

    def openers(self, filename, names, extensions):
        while self.ls_Rs and not any([filename+extension in self.full_filenames for extension in extensions]):
            lsr = self.ls_Rs.pop(0)
            base_dir = os.path.dirname(lsr)
            dir = None
            first = True
            with builtinopen(lsr, "r", encoding="ascii", errors="surrogateescape") as lsrfile:
                for line in lsrfile:
                    line = line.rstrip()
                    if first and line.startswith("%"):
                        continue
                    first = False
                    if line.endswith(":"):
                        dir = os.path.join(base_dir, line[:-1])
                    elif line:
                        self.full_filenames[line] = os.path.join(dir, line)
        for extension in extensions:
            if filename+extension in self.full_filenames:
                def _opener():
                    try:
                        return builtinopen(self.full_filenames[filename+extension], "rb")
                    except IOError:
                        warnings.warn("'%s' should be available at '%s' according to the ls-R file, "
                                      "but the file is not available at this location; "
                                      "update your ls-R file" % (filename, self.full_filenames[filename]))
                return [_opener]
        return []

locator_classes["ls-R"] = ls_R


class pykpathsea:
    """locate files by pykpathsea (a C extension module wrapping libkpathsea)"""

    def openers(self, filename, names, extensions):
        if not has_pykpathsea:
            return []
        for name in names:
            full_filename = pykpathsea_module.find_file(filename, name)
            if full_filename:
                break
        else:
            return []
        def _opener():
            try:
                return builtinopen(full_filename, "rb")
            except IOError:
                warnings.warn("'%s' should be available at '%s' according to libkpathsea, "
                              "but the file is not available at this location; "
                              "update your kpsewhich database" % (filename, full_filename))
        return [_opener]

locator_classes["pykpathsea"] = pykpathsea


# class libkpathsea:
#     """locate files by libkpathsea using ctypes"""
# 
#     def openers(self, filename, names, extensions):
#         raise NotImplemented
# 
# locator_classes["libpathsea"] = libkpathsea


class kpsewhich:
    """locate files using the kpsewhich executable"""

    def openers(self, filename, names, extensions):
        for name in names:
            try:
                with pycompat.popen('kpsewhich --format="%s" "%s"' % (name, filename)) as output:
                    full_filenames = output.read()
            except OSError:
                return []
            if full_filenames:
                break
        else:
            return []
        full_filename = full_filenames.decode("ascii").split("\n")[0].rstrip("\r")

        # Detect Cygwin kpsewhich on Windows Python
        if os.name == "nt" and full_filename.startswith("/"):
            full_filename = pycompat.popen('cygpath -w "%s"' % full_filename).read().strip()

        def _opener():
            try:
                return builtinopen(full_filename, "rb")
            except IOError:
                warnings.warn("'%s' should be available at '%s' according to kpsewhich, "
                              "but the file is not available at this location; "
                              "update your kpsewhich database" % (filename, full_filename))
        return [_opener]

locator_classes["kpsewhich"] = kpsewhich


class locate:
    """locate files using a locate executable"""

    def openers(self, filename, names, extensions):
        for extension in extensions:
            full_filenames = pycompat.popen("locate \"%s\"" % (filename+extension)).read()
            if full_filenames:
                break
        else:
            return []
        full_filename = full_filenames.split("\n")[0].rstrip("\r")
        def _opener():
            try:
                return builtinopen(full_filenames, "rb")
            except IOError:
                warnings.warn("'%s' should be available at '%s' according to the locate, "
                              "but the file is not available at this location; "
                              "update your locate database" % (filename, self.full_filenames[filename]))
        return [_opener]

locator_classes["locate"] = locate



class _marker: pass

config = configparser.ConfigParser()
config.read_string(locator_classes["internal"]().openers("pyxrc", [], [""])[0]().read().decode("utf-8"), source="(internal pyxrc)")
if os.name == "nt":
    user_pyxrc = os.path.join(os.environ['APPDATA'], "pyxrc")
else:
    user_pyxrc = os.path.expanduser("~/.pyxrc")
config.read(user_pyxrc, encoding="utf-8")

def get(section, option, default=_marker):
    if default is _marker:
        return config.get(section, option)
    else:
        try:
            return config.get(section, option)
        except configparser.Error:
            return default

def getint(section, option, default=_marker):
    if default is _marker:
        return config.getint(section, option)
    else:
        try:
            return config.getint(section, option)
        except configparser.Error:
            return default

def getfloat(section, option, default=_marker):
    if default is _marker:
        return config.getfloat(section, option)
    else:
        try:
            return config.getfloat(section, option)
        except configparser.Error:
            return default

def getboolean(section, option, default=_marker):
    if default is _marker:
        return config.getboolean(section, option)
    else:
        try:
            return config.getboolean(section, option)
        except configparser.Error:
            return default

def getlist(section, option, default=_marker):
    if default is _marker:
        l = config.get(section, option).split()
    else:
        try:
            l = config.get(section, option).split()
        except configparser.Error:
            return default
    if space:
        l = [item.replace(space, " ") for item in l]
    return l


space = get("general", "space", "SPACE")
formatWarnings = get("general", "warnings", "default")
if formatWarnings not in ["default", "short", "shortest"]:
    raise RuntimeError("invalid config value for option 'warnings' in section 'general'")
if formatWarnings != "default":
    def formatwarning(message, category, filename, lineno, line=None):
        if formatWarnings == "short":
            return "%s:%s: %s: %s\n" % (filename, lineno, category.__name__, message)
        else:
            return "%s\n" % message
    warnings.formatwarning = formatwarning


methods = [locator_classes[method]()
           for method in getlist("filelocator", "methods", ["local", "internal", "pykpathsea", "kpsewhich"])]
opener_cache = {}


def open(filename, formats, ascii=False):
    """returns an open file searched according the list of formats"""

    # When using an empty list of formats, the names list is empty
    # and the extensions list contains an empty string only. For that
    # case some locators (notably local and internal) return an open
    # function for the requested file whereas other locators might not
    # return anything (like pykpathsea and kpsewhich).
    # This is useful for files not to be searched in the latex
    # installation at all (like lfs files).
    extensions = set([""])
    for format in formats:
        for extension in format.extensions:
            extensions.add(extension)
    names = tuple([format.name for format in formats])
    if (filename, names) in opener_cache:
        file = opener_cache[(filename, names)]()
    else:
        for method in methods:
            openers = method.openers(filename, names, extensions)
            for opener in openers:
                try:
                    file = opener()
                except EnvironmentError:
                    file = None
                if file:
                    opener_cache[(filename, names)] = opener
                    break
            # break two loops here
            else:
                continue
            break
        else:
            raise IOError("Could not locate the file '%s'." % filename)
    if ascii:
        return io.TextIOWrapper(file, encoding="ascii", errors="surrogateescape")
    else:
        return file


class format:
    def __init__(self, name, extensions):
        self.name = name
        self.extensions = extensions

format.tfm = format("tfm", [".tfm"])
format.afm = format("afm", [".afm"])
format.fontmap = format("map", [])
format.pict = format("graphic/figure", [".eps", ".epsi"])
format.tex_ps_header = format("PostScript header", [".pro"])                    # contains also: enc files
format.type1 = format("type1 fonts", [".pfa", ".pfb"])
format.vf = format("vf", [".vf"])
format.dvips_config = format("dvips config", [])
