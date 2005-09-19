#!/usr/bin/env python

import sys, os, os.path, cgi, StringIO, codecs, glob, re
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

class MakeHtml:

    def fromPython(self, input):
        input = StringIO.StringIO(input)
        self.output = StringIO.StringIO()
        self.col = 0
        self.tokclass = None
        self.output.write("<pre id=python>")
        tokenize.tokenize(input.readline, self.tokeneater)
        if self.tokclass is not None:
            self.output.write('</span>')
        self.output.write("</pre>\n")
        return self.output.getvalue()

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

    emptypattern = re.compile(r"\s*$")
    parpattern = re.compile(r"([ \t]*\n)*(?P<data>(\S[^\n]*\n)+)(([ \t]*\n)+.*)?")
    parmakeline = re.compile(r"\s*[\r\n]\s*")
    parmakeinline = re.compile(r"`([^`]*)`")
    parmakeitalic = re.compile(r"''([^`]*)''")
    parmakebold = re.compile(r"'''([^`]*)'''")
    codepattern = re.compile(r"([ \t]*\n)*(?P<data>(([ \t]+[^\n]*)?\n)+)")
    indentpattern = re.compile(r"([ \t]*\n)*(?P<indent>[ \t]+)")

    def fromText(self, input):
        pos = 0
        output = StringIO.StringIO()
        while not self.emptypattern.match(input, pos):
            par = self.parpattern.match(input, pos)
            if par:
                pos = par.end("data")
                par = par.group("data").strip()
                par = par.replace("__version__", pyx.__version__)
                par = par.replace("&", "&amp;")
                par = par.replace("<", "&lt;")
                par = par.replace(">", "&gt;")
                par = par.replace("\"", "&quot;")
                par = self.parmakeline.subn(" ", par)[0]
                par = self.parmakeinline.subn(r"<code>\1</code>", par)[0]
                par = self.parmakeitalic.subn(r"<em>\1</em>", par)[0]
                par = self.parmakebold.subn(r"<strong>\1</strong>", par)[0]
                output.write("<p>%s</p>\n" % par)
            else:
                code = self.codepattern.match(input, pos)
                if not code:
                    raise RuntimeError("couldn't parse text file")
                pos = code.end("data")
                code = code.group("data")
                indent = self.indentpattern.match(code).group("indent")
                code = re.subn(r"\s*[\r\n]%s" % indent, "\n", code.strip())[0]
                output.write("<div class=\"codeindent\">%s</div>\n" % self.fromPython(code + "\n"))
        return output.getvalue()

makehtml = MakeHtml()


class example:

    def __init__(self, basename, dir=None):
        self.title = basename
        if dir:
            name = os.path.join(dir, basename)
        else:
            name = basename
        relname = os.path.join("..", "examples", name)
        self.code = makehtml.fromPython(codecs.open("%s.py" % relname, encoding="iso-8859-1").read())
        self.png = "%s.png" % basename
        self.width, self.height = Image.open("%s.png" % relname).size
        self.downloads = []
        for suffix in ["py", "dat", "jpg", "eps", "pdf"]:
            try:
                filesize = "%.1f KB" % (os.path.getsize("%s.%s" % (relname, suffix)) / 1024.0)
            except OSError:
                pass
            else:
                self.downloads.append({"filename": "%s.%s" % (basename, suffix),
                                       "suffixname": ".%s" % suffix,
                                       "filesize": filesize,
                                       "iconname": "%s.png" % suffix})
        if os.path.exists("%s.txt" % relname):
            self.text = makehtml.fromText(codecs.open("%s.txt" % relname, encoding="iso-8859-1").read())
        else:
            self.text = None


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
    if ptname not in ["maintemplate.pt", "examples.pt", "example.pt"]:
        htmlname = "%s.html" % ptname[:-3]
        template = MyPageTemplateFile(ptname)
        content = template(pagename=htmlname,
                           maintemplate=maintemplate,
                           examplepages=[],
                           mkrellink=mkrellink,
                           version=pyx.__version__,
                           news=news)
        codecs.open("build/%s" % htmlname, "w", encoding="iso-8859-1").write(content)

examplestemplate = MyPageTemplateFile("examples.pt")
exampletemplate = MyPageTemplateFile("example.pt")
examplepages = [item[:-2]
                for item in open("../examples/INDEX").readlines()
                if item[-2] == "/"]

for dir in [None] + examplepages:
    srcdir = "../examples"
    destdir = "examples"
    if dir:
        srcdir = os.path.join(srcdir, dir)
        destdir = os.path.join(destdir, dir)
    try:
        abstract = makehtml.fromText(open(os.path.join(srcdir, "README")).read())
    except IOError:
        abstract = ""
    examples = [example(item.strip(), dir)
                for item in open(os.path.join(srcdir, "INDEX")).readlines()
                if item[-2] != "/"]
    htmlname = os.path.join(destdir, "index.html")
    content = examplestemplate(pagename=htmlname,
                               maintemplate=maintemplate,
                               abstract=abstract,
                               examples=examples,
                               examplepages=examplepages,
                               mkrellink=mkrellink)
    codecs.open("build/%s" % htmlname, "w", encoding="iso-8859-1").write(content)
    for aexample in examples:
        if aexample.text:
            htmlname = os.path.join(destdir, "%s.html" % aexample.title)
            content = exampletemplate(pagename=htmlname,
                                      maintemplate=maintemplate,
                                      abstract=abstract,
                                      example=aexample,
                                      examplepages=examplepages,
                                      mkrellink=mkrellink)
            codecs.open("build/%s" % htmlname, "w", encoding="iso-8859-1").write(content)

