from globex import *
from const import *

class Tex(Globex):

    ExportMethods = [ "amove", "text", "textwd", "textht", "textdp" ]

    BaseFilename = "example"

    def TexCreateBoxCmd(self, texstr, parmode, valign):

        # we use two "{{" to ensure, that everything goes into the box
        CmdBegin = "\\setbox\\mybox=\\hbox{{"
        CmdEnd = "}}"

        if parmode != None:
             # TODO: check that parmode is a valid TeX length
             if valign == top or valign == None:
                  CmdBegin = CmdBegin + "\\begin{minipage}[t]{" + parmode + "}"
                  CmdEnd = "\\end{minipage}" + CmdEnd
             elif valign == center:
                  CmdBegin = CmdBegin + "\\begin{minipage}{" + parmode + "}"
                  CmdEnd = "\\end{minipage}" + CmdEnd
             elif valign == bottom:
                  CmdBegin = CmdBegin + "\\begin{minipage}[b]{" + parmode + "}"
                  CmdEnd = "\\end{minipage}" + CmdEnd
             else:
                  assert "valign unknown"
        else:
             if valign != None:
                  assert "parmode needed to use valign"
        
        Cmd = CmdBegin + texstr + CmdEnd + "\n"
        return Cmd
    
    def TexCopyBoxCmd(self, texstr, halign, angle):

        CmdBegin = ""
        CmdEnd = ""

        if angle != None and angle != 0:
            isnumber(angle)
            CmdBegin = CmdBegin + "\\begin{rotate}{" + str(angle) + "}"
            CmdEnd = "\\end{rotate}" + CmdEnd

        if halign != None:
            if halign == left:
                pass
            elif halign == center:
                CmdBegin = CmdBegin + "\\hbox{\\kern-.5\\wd\\mybox}"
            elif halign == right:
                CmdBegin = CmdBegin + "\\hbox{\\kern-\\wd\\mybox}"
            else:
                assert "halign unknown"

        Cmd = CmdBegin + "\\copy\\mybox" + CmdEnd
        return Cmd

    def TexHexMD5(self, texstr):
        import md5, string
        h = string.hexdigits
        r = ''
        s = md5.md5(self.TexInitStr + texstr).digest()
        for c in s:
            i = ord(c)
            r = r + h[(i >> 4) & 0xF] + h[i & 0xF]
        return r
        
    TexExpressions = [ ]
    TexInitStr = ""
    
    def TexAddToFile(self, Cmd):
        # TODO: store stack in markers to create detailed error messages
        MarkerBegin = "\\immediate\\write16{MarkerBegin}\n"
        MarkerEnd = "\\immediate\\write16{MarkerEnd}\n"

        Cmd = MarkerBegin + Cmd + MarkerEnd
        self.TexExpressions = self.TexExpressions + [ Cmd, ]

    def TexRun(self):

        import os

        file = open(self.BaseFilename + ".tex", "w")

        file.write("""\\nonstopmode
\\documentclass{article}
\\usepackage{rotating}
\\setlength{\\textheight}{29.7truecm}
\\setlength{\\textwidth}{21truecm}
\\setlength{\\topmargin}{0truecm}
\\setlength{\\headheight}{0truecm}
\\setlength{\\headsep}{0truecm}
\\setlength{\\marginparwidth}{0truecm}
\\setlength{\\marginparsep}{0truecm}
\\setlength{\\oddsidemargin}{0truecm}
\\setlength{\\evensidemargin}{0truecm}
\\setlength{\\hoffset}{-1truein}
\\setlength{\\voffset}{-1truein}
\\setlength{\\parindent}{0truecm}
\\pagestyle{empty}
\\immediate\\write16{MarkerBegin TexInitStr}
""" + self.TexInitStr + """
\\immediate\\write16{MarkerEnd TexInitStr}
\\begin{document}
\\newwrite\\myfile
\\newbox\\mybox
\\immediate\\openout\\myfile=""" + self.BaseFilename + """.size
\\setlength{\\unitlength}{1truecm}
\\begin{picture}(21,29.7)(0,0)
\\multiput(0,0)(1,0){22}{\\line(0,1){29.7}}
\\multiput(0,0)(0,1){30}{\\line(1,0){21}}\n""")

        file.writelines(self.TexExpressions)

        file.write("""\\end{picture}
\\immediate\\closeout\\myfile
\\end{document}\n""")
        file.close()

        # TODO: ordentliche Fehlerbehandlung,
        #       Auswertung der Marker auf Fehler beim TeX'en
        if os.system("latex " + self.BaseFilename + " > /dev/null 2>&1"):
            assert "LaTeX exit code not zero"
        
        # TODO: ordentliche Fehlerbehandlung,
        #       Schnittstelle zur Kommandozeile
        if os.system("dvips -o " + self.BaseFilename + ".tex.ps " +
                     self.BaseFilename + " > /dev/null 2>&1"):
            assert "dvips exit code not zero"
        
    TexResults = None

    def TexResult(self, Str):

        if self.TexResults == None:
            try:
                file = open(self.BaseFilename + ".size", "r")
                self.TexResults = file.readlines()
                file.close()
            except IOError: self.TexResults = [ ]

        for TexResult in self.TexResults:
            if TexResult[:len(Str)] == Str:
                return TexResult[len(Str):-1]
 
        return 1

    def amove(self,x,y):
        isnumber(x)
        isnumber(y)
        self.x=x
        self.y=y
    
    def text(self, texstr, halign=None, parmode=None, valign=None, angle=None):
        TexCreateBoxCmd = self.TexCreateBoxCmd(texstr, parmode, valign)
        self.TexAddToFile(TexCreateBoxCmd +
                          "\\put(" + str(self.x) + "," + str(self.y) + "){" +
                          self.TexCopyBoxCmd(texstr, halign, angle) + "}\n")

    def textwd(self, texstr, parmode=None):
        TexCreateBoxCmd = self.TexCreateBoxCmd(texstr, parmode, None)
        TexHexMD5=self.TexHexMD5(TexCreateBoxCmd)
        self.TexAddToFile(TexCreateBoxCmd +
                          "\\immediate\\write\\myfile{" + TexHexMD5 +
                          ":wd:\\the\\wd\\mybox}\n")
        return self.TexResult(TexHexMD5 + ":wd:")

    def textht(self, texstr, parmode=None, valign=None):
        TexCreateBoxCmd = self.TexCreateBoxCmd(texstr, parmode, valign)
        TexHexMD5=self.TexHexMD5(TexCreateBoxCmd)
        self.TexAddToFile(TexCreateBoxCmd +
                          "\\immediate\\write\\myfile{" + TexHexMD5 +
                          ":ht:\\the\\ht\\mybox}\n")
        return self.TexResult(TexHexMD5 + ":ht:")

    def textdp(self, texstr, parmode=None, valign=None):
        TexCreateBoxCmd = self.TexCreateBoxCmd(texstr, parmode, valign)
        TexHexMD5=self.TexHexMD5(TexCreateBoxCmd)
        self.TexAddToFile(TexCreateBoxCmd +
                          "\\immediate\\write\\myfile{" + TexHexMD5 +
                          ":dp:\\the\\dp\\mybox}\n")
        return self.TexResult(TexHexMD5 + ":dp:")


def tex():
    DefaultTex=Tex()
    DefaultTex.AddNamespace("DefaultTex",GetCallerGlobalNamespace())

