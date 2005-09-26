class encoding:

    def __init__(self, encvector):
        self.encvector = encvector

    def decode(self, char):
        return self.encvector[char]

    def outputPS(self, file, name):
        file.write("%%%%BeginProcSet: %s\n" % name)
        file.write("/%s\n"
                   "[" % self.name)
        for i, glyphname in enumerate(self.encvector):
            if i and not (i % 8):
                file.write("\n")
            else:
                file.write(" ")
            file.write(glyphname)
        file.write(" ] def\n"
                   "%%EndProcSet\n")

    def outputPDF(self, file):
        file.write("<<\n"
                   "/Type /Encoding\n"
                   "/Differences\n"
                   "[ 0")
        for i, glyphname in enumerate(self.encvector):
            if i and not (i % 8):
                file.write("\n")
            else:
                file.write(" ")
            file.write(glyphname)
        file.write(" ]\n"
                   ">>\n")

adobestandardencoding = encoding([None, None, None, None, None, None, None, None,
                                  None, None, None, None, None, None, None, None,
                                  None, None, None, None, None, None, None, None,
                                  None, None, None, None, None, None, None, None,
                                  "space", "exclam", "quotedbl", "numbersign", "dollar", "percent", "ampersand", "quoteright",
                                  "parenleft", "parenright", "asterisk", "plus", "comma", "hyphen", "period", "slash",
                                  "zero", "one", "two", "three", "four", "five", "six", "seven",
                                  "eight", "nine", "colon", "semicolon", "less", "equal", "greater", "question",
                                  "at", "A", "B", "C", "D", "E", "F", "G",
                                  "H", "I", "J", "K", "L", "M", "N", "O",
                                  "P", "Q", "R", "S", "T", "U", "V", "W",
                                  "X", "Y", "Z", "bracketleft", "backslash", "bracketright", "asciicircum", "underscore",
                                  "quoteleft", "a", "b", "c", "d", "e", "f", "g",
                                  "h", "i", "j", "k", "l", "m", "n", "o",
                                  "p", "q", "r", "s", "t", "u", "v", "w",
                                  "x", "y", "z", "braceleft", "bar", "braceright", "asciitilde", None,
                                  None, None, None, None, None, None, None, None,
                                  None, None, None, None, None, None, None, None,
                                  None, None, None, None, None, None, None, None,
                                  None, None, None, None, None, None, None, None,
                                  None, "exclamdown", "cent", "sterling", "fraction", "yen", "florin", "section",
                                  "currency", "quotesingle", "quotedblleft", "guillemotleft", "guilsinglleft", "guilsinglright", "fi", "fl",
                                  None, "endash", "dagger", "daggerdbl", "periodcentered", None, "paragraph", "bullet",
                                  "quotesinglbase", "quotedblbase", "quotedblright", "guillemotright", "ellipsis", "perthousand", None, "questiondown",
                                  None, "grave", "acute", "circumflex", "tilde", "macron", "breve", "dotaccent",
                                  "dieresis", None, "ring", "cedilla", None, "hungarumlaut", "ogonek", "caron",
                                  "emdash", None, None, None, None, None, None, None,
                                  None, None, None, None, None, None, None, None,
                                  None, "AE", None, "ordfeminine", None, None, None, None,
                                  "Lslash", "Oslash", "OE", "ordmasculine", None, None, None, None,
                                  None, "ae", None, None, None, "dotlessi", None, None,
                                  "lslash", "oslash", "oe", "germandbls", None, None, None, None])
