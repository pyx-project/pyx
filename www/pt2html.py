#!/usr/bin/env python2.2

import sys, os.path, codecs, encodings
from zope.pagetemplate.pagetemplate import PageTemplate

class example:
    def __init__(self, name):
        self.name = name
        self.basename = os.path.basename(name)
        self.png = self.basename+".png"
        self.eps = self.basename+".eps"
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
    # path = os.path.join(os.path.expanduser(outpath), filename)
    # print "Writing %s ..." % path
    open(filename, "w").write(string)

maintemplate = PageTemplateFromFile("maintemplate.pt")

pagename = sys.argv[1]
if pagename.endswith(".pt"): pagename = pagename[:-3]

examples = [example("hello"), 
            example("pattern"),
            example("vector"),
            example("tree"),
            example("sierpinski"),
            example("graphs/arrows"),
            example("graphs/step"),
            example("graphs/piaxis")]

write_file("%s.html" % pagename,
           PageTemplateFromFile("%s.pt" % pagename)(maintemplate=maintemplate,
                                                   pagename="%s.html" % pagename,
                                                   examples=examples))

