#!/usr/bin/env python2.2

import sys
from zope.pagetemplate.pagetemplate import PageTemplate

class example:
    def __init__(self, name):
        self.name = name
        self.path = name+".png"
        self.code = open("examples/%s.py.html" % name, "r").read()
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

examples = [example("hello"), example("pattern"), example("vector"), example("step"), example("piaxis")]

write_file("%s.html" % pagename,
           PageTemplateFromFile("%s.pt" % pagename)(maintemplate=maintemplate,
                                                   pagename="%s.html" % pagename,
                                                   examples=examples))

