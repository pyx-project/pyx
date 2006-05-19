import sys, os, os.path, cgi, StringIO, codecs, glob, re, warnings
import keyword, token, tokenize
import xml.dom.minidom
from zope.pagetemplate.pagetemplatefile import PageTemplateFile
import Image

# make zope 3.2.1 run:
import zope.pagetemplate.pagetemplatefile as pagetemplatefile
pagetemplatefile.DEFAULT_ENCODING = "latin1"

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
    parmakeinline = re.compile(r"`(.*?)`")
    parmakebold = re.compile(r"'''(.*?)'''")
    parmakeitalic = re.compile(r"''(.*?)''")
    parmakeref = re.compile(r"\[([^]]*)\s([^\s]*)\]")
    codepattern = re.compile(r"([ \t]*\n)*(?P<data>(([ \t]+[^\n]*)?\n)+)")
    indentpattern = re.compile(r"([ \t]*\n)*(?P<indent>[ \t]+)")

    def fromText(self, input, bend=""):
        title = None
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
                par = self.parmakebold.subn(r"<strong>\1</strong>", par)[0]
                par = self.parmakeitalic.subn(r"<em>\1</em>", par)[0]
                par = self.parmakeref.subn(r'<a href="\2">\1</a>', par)[0]
                if not title:
                    title = par
                else:
                    bends = 0
                    while par.startswith("!"):
                        if not bend:
                            warnings.warn("ignore bend sign")
                            break
                        bends += 1
                        par = par[1:]
                    output.write("%s<p>%s</p>\n" % (bend*bends, par))
            else:
                code = self.codepattern.match(input, pos)
                if not code:
                    raise RuntimeError("couldn't parse text file")
                pos = code.end("data")
                code = code.group("data")
                indent = self.indentpattern.match(code).group("indent")
                code = re.subn(r"\s*[\r\n]%s" % indent, "\n", code.strip())[0]
                if len(indent.expandtabs()) >= 4:
                    code = self.fromPython(code + "\n")
                else:
                    code = "<pre>%s</pre>" % code
                output.write("<div class=\"codeindent\">%s</div>\n" % code)
        text = output.getvalue()
        shorttext = text.split("...")[0]
        text = text.replace("...", "", 1)
        return title, shorttext, text

makehtml = MakeHtml()


class example:

    def __init__(self, basesrcdir, dir, basename):
        self.basename = basename
        if dir:
            name = os.path.join(dir, basename)
        else:
            name = basename
        relname = os.path.join(basesrcdir, name)
        self.filename = "%s.py" % name
        self.code = makehtml.fromPython(codecs.open("%s.py" % relname, encoding="iso-8859-1").read())
        self.html = "%s.html" % basename
        self.png = "%s.png" % basename
        self.width, self.height = Image.open("%s.png" % relname).size
        self.thumbpng = "%s_thumb.png" % basename
        self.thumbwidth, self.thumbheight = Image.open("%s_thumb.png" % relname).size
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
            self.title, self.shorttext, self.text = makehtml.fromText(codecs.open("%s.txt" % relname, encoding="iso-8859-1").read(), bend="<div class=\"examplebend\"><img src=\"../../bend.png\" width=22 height=31></div>\n")
        else:
            self.title = basename
            self.shorttext = self.text = None


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
    if ptname not in ["maintemplate.pt", "exampleindex.pt", "examples.pt", "example.pt"]:
        htmlname = "%s.html" % ptname[:-3]
        template = MyPageTemplateFile(ptname)
        content = template(pagename=htmlname,
                           maintemplate=maintemplate,
                           subtype=None,
                           mkrellink=mkrellink,
                           version=pyx.__version__,
                           news=news)
        codecs.open("build/%s" % htmlname, "w", encoding="iso-8859-1").write(content)


def processexamples(basedir):
    exampleindextemplate = MyPageTemplateFile("exampleindex.pt")
    examplestemplate = MyPageTemplateFile("examples.pt")
    exampletemplate = MyPageTemplateFile("example.pt")

    exampledirs = [None]
    examplepages = []
    for dir in open(os.path.join("..", basedir, "INDEX")).readlines():
        dir = dir.strip()
        if dir.endswith("/"):
            exampledirs.append(dir)
            dir = dir.rstrip("/")
            try:
                title = open(os.path.join("..", basedir, dir, "README")).readline().strip()
            except IOError:
                title = dir
            examplepages.append({"dir": dir, "title": title})

    prev = None
    for dirindex, dir in enumerate(exampledirs):
        if dir:
            srcdir = os.path.join("..", basedir, dir)
            destdir = os.path.join(basedir, dir)
            bend = "<div class=\"examplebend\"><img src=\"../../bend.png\" width=22 height=31></div>\n"
        else:
            srcdir = os.path.join("..", basedir)
            destdir = basedir
            bend = "<div class=\"examplebend\"><img src=\"../bend.png\" width=22 height=31></div>\n"
        try:
            nextdir = exampledirs[dirindex + 1]
            nextdir = os.path.join(basedir, nextdir)
        except IndexError:
            nextdir = None
        try:
            title, shorttext, text = makehtml.fromText(open(os.path.join(srcdir, "README")).read(), bend=bend)
        except IOError:
            title = dir
            text = ""
        examples = [example(os.path.join("..", basedir), dir, item.strip())
                    for item in open(os.path.join(srcdir, "INDEX")).readlines()
                    if item[-2] != "/"]
        htmlname = os.path.join(destdir, "index.html")
        if dir:
            template = examplestemplate
            next = os.path.join(destdir, examples[0].html)
        else:
            template = exampleindextemplate
            next = os.path.join(nextdir, "index.html")
        content = template(pagename=htmlname,
                           maintemplate=maintemplate,
                           dir=dir,
                           title=title,
                           text=text,
                           examples=examples,
                           subtype=basedir,
                           subpages=examplepages,
                           mkrellink=mkrellink,
                           prev=prev,
                           next=next)
        codecs.open("build/%s" % htmlname, "w", encoding="iso-8859-1").write(content)
        prev = os.path.join(destdir, "index.html")
        if dir:
            for exampleindex, aexample in enumerate(examples):
                try:
                    next = os.path.join(destdir, examples[exampleindex+1].html)
                except (TypeError, IndexError):
                    if nextdir:
                        next = os.path.join(nextdir, "index.html")
                    else:
                        next = None
                htmlname = os.path.join(destdir, "%s.html" % aexample.basename)
                content = exampletemplate(pagename=htmlname,
                                          maintemplate=maintemplate,
                                          dir=dir,
                                          example=aexample,
                                          subtype=basedir,
                                          subpages=examplepages,
                                          mkrellink=mkrellink,
                                          prev=prev,
                                          next=next)
                codecs.open("build/%s" % htmlname, "w", encoding="iso-8859-1").write(content)
                prev = os.path.join(destdir, aexample.html)


processexamples("examples")
processexamples("gallery")
