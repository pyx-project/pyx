#!/usr/bin/env python

import sys, os, os.path, cgi, StringIO, codecs, glob
import keyword, token, tokenize
import xml.dom.minidom
from zope.pagetemplate.pagetemplatefile import PageTemplateFile
import Image

sys.path[:0]=[".."]
import pyx

_KEYWORD = token.NT_OFFSET

tokclasses = {token.NUMBER: 'number',
              token.OP: 'op',
              token.STRING: 'string',
              tokenize.COMMENT: 'comment',
              token.NAME: 'name',
              _KEYWORD: 'keyword'}

class py2html:

    def __init__(self, input, output):
        self.output = output
        self.col = 0
        self.tokclass = None
        self.output.write("<pre id=python>")
        tokenize.tokenize(input.readline, self.tokeneater)
        if self.tokclass is not None:
            self.output.write('</span>')
        self.output.write("</pre>\n")

    def tokeneater(self, toktype, toktext, (srow, scol), (erow, ecol), line):
        if toktype == token.ERRORTOKEN:
            raise RuntimeError("ErrorToken occured")
        if toktype in [token.NEWLINE, tokenize.NL]:
            self.output.write('\n')
            self.col = 0
        else:
            # map token type to a color group
            if token.LPAR <= toktype and toktype <= token.OP:
                toktype = token.OP
            elif toktype == token.NAME and keyword.iskeyword(toktext):
                toktype = _KEYWORD

            # restore whitespace
            assert scol >= self.col
            self.output.write(" "*(scol-self.col))

            try:
                tokclass = tokclasses[toktype]
            except KeyError:
                tokclass = None
            if self.tokclass is not None and tokclass != self.tokclass:
                self.output.write('</span>')
            if tokclass is not None and tokclass != self.tokclass:
                self.output.write('<span class="%s">' % tokclass)
            self.output.write(cgi.escape(toktext))
            self.tokclass = tokclass

            # calculate new column position
            self.col = scol + len(toktext)
            newline = toktext.rfind("\n")
            if newline != -1:
                self.col = len(toktext) - newline - 1

class example:

    def __init__(self, name):
        if name.startswith("./"):
            name = name[2:]
        self.name = name
        self.png = "%s.png" % os.path.basename(self.name)
        self.eps = "%s.eps" % os.path.basename(self.name)
        htmlbuffer = StringIO.StringIO()
        self.width, self.height = Image.open("../examples/%s.png" % name).size
        py2html(codecs.open("../examples/%s.py" % name, encoding="iso-8859-1"), htmlbuffer)
        self.code = htmlbuffer.getvalue()


class MyPageTemplateFile(PageTemplateFile):

    def write(self, text):
        if isinstance(text, str):
            text = unicode(text, encoding="iso-8859-1")
        return PageTemplateFile.write(self, text)


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

maintemplate = MyPageTemplateFile("maintemplate.pt")

latestnews = 2
newsdom = xml.dom.minidom.parse("news.pt")
news = "".join(["%s%s" % (dt.toxml(), dd.toxml())
                for dt, dd in zip(newsdom.getElementsByTagName("dt")[:latestnews],
                                  newsdom.getElementsByTagName("dd")[:latestnews])])

for ptname in glob.glob("*.pt"):
    if ptname in ["maintemplate.pt", "examples.pt"]:
        continue
    htmlname = "%s.html" % ptname[:-3]
    print htmlname
    template = MyPageTemplateFile(ptname)
    content = template(pagename=htmlname,
                       maintemplate=maintemplate,
                       examplepages=[],
                       mkrellink=mkrellink,
                       version=pyx.__version__,
                       news=news)
    codecs.open("build/%s" % htmlname, "w", encoding="iso-8859-1").write(content)

examplestemplate = MyPageTemplateFile("examples.pt")
examplepages = [item[:-2] for item in open("../examples/INDEX").readlines() if item[-2] == "/"]

for dir in ["."] + examplepages:
    try:
        abstract = open("../examples/%s/README" % dir).read().replace("__version__", pyx.__version__).replace("\PyX{}", "PyX")
    except IOError:
        abstract = ""
    examples = [example(dir + "/" + item.strip()) for item in open("../examples/%s/INDEX" % dir).readlines() if item[-2] != "/"]
    if dir != ".":
        htmlname = "examples/%s/index.html" % dir
    else:
        htmlname = "examples/index.html"
    print htmlname
    content = examplestemplate(pagename=htmlname,
                               maintemplate=maintemplate,
                               abstract=abstract,
                               examples=examples,
                               examplepages=examplepages,
                               mkrellink=mkrellink)
    codecs.open("build/%s" % htmlname, "w", encoding="iso-8859-1").write(content)

