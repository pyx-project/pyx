#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-

import sys, os, os.path
from zope.pagetemplate.pagetemplate import PageTemplate

sys.path[:0]=[".."]
import pyx

class example:
    def __init__(self, name):
        self.name = name
        self.png = "%s.png" % os.path.basename(self.name)
        self.eps = "%s.eps" % os.path.basename(self.name)
        self.code = open("../examples/%s.py.html" % name, "r").read()
        self.code = self.code.replace("ä", "&auml;")
        self.code = self.code.replace("Ä", "&Auml;")
        self.code = self.code.replace("ö", "&ouml;")
        self.code = self.code.replace("Ö", "&Ouml;")
        self.code = self.code.replace("ü", "&uuml;")
        self.code = self.code.replace("Ü", "&Uuml;")
        self.code = self.code.replace("ß", "&szlig;")
        self.code = self.code.replace("é", "&eacute;")
    def __getattr__(self, attr):
        return self.__dict__[attr]

def PageTemplateFromFile(filename):
    pt = PageTemplate()
    pt.write(open(filename, "r").read())
    return pt

def write_file(filename, string):
    try:
        open(filename, "w").write(string)
    except IOError:
        os.mkdir(os.path.dirname(filename)) # do not need to create directory recursively when called in proper order
        open(filename, "w").write(string)

maintemplate = PageTemplateFromFile("maintemplate.pt")

htmlname = sys.argv[1]

def mkrellink(linkname, options):
    # returns a string containing the relative url for linkname (an absolute url)
    pagename = options["pagename"]
    while linkname.find("/") != -1 and pagename.find("/") != -1:
        linknamefirst, linknameother = linkname.split("/", 1)
        pagenamefirst, pagenameother = pagename.split("/", 1)
        if linknamefirst == pagenamefirst:
            linkname = linknameother
            pagename = pagenameother
        else:
            break
    for i in pagename.split("/")[:-1]:
        linkname = "../" + linkname
    return linkname

if htmlname.startswith("examples"):
    dir = htmlname[9:-10]
    examplepages = [item[:-2] for item in open("../examples/INDEX").readlines() if item[-2] == "/"]
    try:
        abstract = open("../examples/%sREADME" % dir).read().replace("__version__", pyx.__version__).replace("\PyX{}", "PyX")
    except IOError:
        abstract = ""
    examples = [example(dir + item.strip()) for item in open("../examples/%sINDEX" % dir).readlines() if item[-2] != "/"]
    write_file("build/%s" % htmlname, PageTemplateFromFile("examples.pt")(pagename=htmlname,
                                                                          maintemplate=maintemplate,
                                                                          abstract=abstract,
                                                                          examples=examples,
                                                                          examplepages=examplepages,
                                                                          mkrellink=mkrellink))
else:
    write_file("build/%s" % htmlname, PageTemplateFromFile("%s.pt" % htmlname[:-5])(pagename=htmlname,
                                                                                    maintemplate=maintemplate,
                                                                                    examplepages=[],
                                                                                    mkrellink=mkrellink,
                                                                                    version=pyx.__version__))

