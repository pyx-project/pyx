builtinopen = open

import os, cStringIO, warnings, pkgutil

import config, pycompat


# Locator methods implement a open method similar to the builtin open
# function by searching for a file according to a specific rule.

locator_classes = {}

class local:
    # locates files in the current directory

    def openers(self, filename, names, extensions, mode):
        return [lambda: builtinopen(filename+extension, mode) for extension in extensions]

locator_classes["local"] = local


class internal_pkgutil:
    # locates files within the pyx data tree

    def openers(self, filename, names, extensions, mode):
        for extension in extensions:
            full_filename = filename+extension
            dir = os.path.splitext(full_filename)[1][1:]
            try:
                data = pkgutil.get_data("pyx", "data/%s/%s" % (dir, full_filename))
            except IOError:
                pass
            else:
                if data:
                    # ignoring mode?!
                    return [lambda: cStringIO.StringIO(data)]

class internal_open:
    # locates files within the pyx data tree

    def openers(self, filename, names, extensions, mode):
        result = []
        for extension in extensions:
            full_filename = filename+extension
            dir = os.path.splitext(full_filename)[1][1:]
            result.append(lambda: builtinopen(os.path.join(os.path.dirname(__file__), "data", dir, full_filename), mode))
        return result

try:
    pkgutil.get_data
except AttributeError:
    locator_classes["internal"] = internal_open
else:
    locator_classes["internal"] = internal_pkgutil


class recursivedir:
    # locates files by searching recursively in a list of directories

    def __init__(self):
        self.dirs = config.getlist("locator", "recursivedir")
        self.full_filenames = {}

    def openers(self, filename, names, extensions, mode):
        for extension in extensions:
            if filename+extension in self.full_filenames:
                return [lambda: builtinopen(self.full_filenames[filename], mode)]
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
                    return [lambda: builtinopen(self.full_filenames[filename], mode)]

locator_classes["recursivedir"] = recursivedir


class ls_R:
    # locates files by searching a list of ls-R files

    def __init__(self):
        self.ls_Rs = config.getlist("locator", "ls-R")
        self.full_filenames = {}

    def openers(self, filename, names, extensions, mode):
        while self.ls_Rs and not any([filename+extension in self.full_filenames for extension in extensions]):
            lsr = self.ls_Rs.pop(0)
            base_dir = os.path.dirname(lsr)
            dir = None
            first = True
            for line in builtinopen(lsr):
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
                        return lambda: builtinopen(self.full_filenames[filename], mode)
                    except IOError:
                        warnings.warn("'%s' should be available at '%s' according to the ls-R file, "
                                      "but the file is not available at this location; "
                                      "update your ls-R file" % (filename, self.full_filenames[filename]))
            return [_opener]

locator_classes["ls-R"] = ls_R


class pykpathsea:

    def openers(self, filename, names, extensions, mode):
        import pykpathsea
        for name in names:
            full_filename = pykpathsea.find_file(filename, name)
            if full_filename:
                break
        else:
            return
        return [lambda: builtinopen(full_filename, mode)]

locator_classes["pykpathsea"] = pykpathsea


# class libkpathsea:
#     # locate files by libkpathsea using ctypes
# 
#     def openers(self, filename, names, extensions, mode):
#         pass
# 
# locator_classes["libpathsea"] = libkpathsea


class kpsewhich:

    def openers(self, filename, names, extensions, mode):
        for name in names:
            try:
                full_filenames = os.popen('kpsewhich --format="%s" "%s"' % (name, filename)).read()
            except OSError:
                return
            if full_filenames:
                break
        else:
            return
        full_filename = full_filenames.split("\n")[0]
        def _opener():
            try:
                return builtinopen(full_filename, mode)
            except IOError:
                warnings.warn("'%s' should be available at '%s' according to kpsewhich, "
                              "but the file is not available at this location; "
                              "update your kpsewhich database" % (filename, full_filename))
        return [_opener]

locator_classes["kpsewhich"] = kpsewhich


class locate:

    def openers(self, filename, names, extensions, mode):
        for extension in extensions:
            full_filenames = pycompat.popen("locate \"%s\"" % (filename+extension)).read()
            if full_filenames:
                break
        else:
            return
        full_filename = full_filenames.split("\n")[0]
        def _opener():
            try:
                return builtinopen(full_filenames, mode)
            except IOError:
                warnings.warn("'%s' should be available at '%s' according to the locate database, "
                              "but the file is not available at this location; "
                              "update your locate database" % (filename, self.full_filenames[filename]))
        return [_opener]

locator_classes["locate"] = locate


methods = [locator_classes[method]()
           for method in config.getlist("locator", "methods", "local internal pykpathsea kpsewhich")]

opener_cache = {}

def open(filename, formats, mode="r"):
    extensions = pycompat.set([""])
    for format in formats:
        for extension in format.extensions:
            extensions.add(extension)
    names = tuple([format.name for format in formats])
    if (filename, names) in opener_cache:
        return opener_cache[(filename, names)]()
    for method in methods:
        openers = method.openers(filename, names, extensions, mode)
        if openers:
            for opener in openers:
                try:
                    file = opener()
                except IOError:
                    file = None
                if file:
                    opener_cache[(filename, names)] = opener
                    return file
    raise IOError("Could not locate the file '%s'." % filename)


class format:
    def __init__(self, name, extensions):
        self.name = name
        self.extensions = extensions

format.tfm = format("tfm", [".tfm"])
format.afm = format("afm", [".afm"])
format.fontmap = format("map", [])
format.pict = format("graphics/figure", [".eps", ".epsi"])
format.tex_ps_header = format("PostScript header", [".pro"])                    # contains also: enc files
format.type1 = format("type1 fonts", [".pfa", ".pfb"])
format.vf = format("vf", [".vf"])
format.dvips_config = format("dvips config", [])
