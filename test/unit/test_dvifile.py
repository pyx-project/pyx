import sys
if sys.path[0] != "../..":
    sys.path.insert(0, "../..")

import cStringIO, os, re, unittest

from pyx import dvifile


class DvifileTestCase(unittest.TestCase):

    def dvitypetester(self, advifile):
        dvitypefile = os.popen("dvitype %s" % advifile)
        dvitypelines = dvitypefile.readlines()
        dvitypelineno = dvitypelines.index(" \n") + 1

        pyxdvifile = cStringIO.StringIO()
        df = dvifile.dvifile(advifile, dvifile.readfontmap(["psfonts.map"]),
                             debug=1, debugfile=pyxdvifile)
        while df.readpage():
            pass
        pyxdvifilelines = list(pyxdvifile.getvalue().split("\n"))
        pyxdvifilelineno = 0

        while dvitypelineno < len(dvitypelines) and pyxdvifilelineno < len(pyxdvifilelines):
            dvitypeline = dvitypelines[dvitypelineno].rstrip()
            if dvitypeline.startswith("[") and dvitypeline.endswith("]"):
                dvitypelineno += 1
                continue

            pyxdvifileline = pyxdvifilelines[pyxdvifilelineno].rstrip()
            if pyxdvifileline.startswith("[") and pyxdvifileline.endswith("]"):
                pyxdvifilelineno += 1
                continue

            pyxdvifilelinere = (pyxdvifileline.replace("+", "\\+")
                                              .replace("(", "\\(")
                                              .replace(")", "\\)")
                                              .replace("???", "-?\\d+") +
                                              "( warning: \\|h\\|>\\d+!)?" +
                                              "$")
            if re.match(pyxdvifilelinere, dvitypeline):
                dvitypelineno += 1
                pyxdvifilelineno += 1
            else:
                raise ValueError("difference:\n%s\n%s" % (dvitypeline, pyxdvifileline))
                # print "difference:"
                # print "\t", dvitypeline
                # print "\t", pyxdvifileline
                # dvitypelineno += 1
                # pyxdvifilelineno += 1

        # don't be strict about empty tailing lines
        while dvitypelineno < len(dvitypelines) and not dvitypelines[dvitypelineno].strip():
            dvitypelineno += 1
        while pyxdvifilelineno < len(pyxdvifilelines) and not pyxdvifilelines[pyxdvifilelineno].strip():
            pyxdvifilelineno += 1

        assert dvitypelineno == len(dvitypelines)
        assert pyxdvifilelineno == len(pyxdvifilelines)

    def testDvitypeSample2e(self):
        os.system("latex sample2e.tex > /dev/null 2> /dev/null")
        self.dvitypetester("sample2e.dvi")
        os.system("rm sample2e.*")

    def testDvitypeBigScale(self):
        texfile = open("bigscale.tex", "w")
        texfile.write("\\nopagenumbers\n"
                      "\\font\\myfont=cmr10 at 145.678pt\\myfont\n"
                      "i\\par\n"
                      "\\font\\myfont=cmr10 at 457.12346pt\\myfont\n"
                      "m\\par\n"
                      "\\bye\n")
        texfile.close()
        os.system("tex bigscale.tex > /dev/null 2> /dev/null")
        self.dvitypetester("bigscale.dvi")
        os.system("rm bigscale.*")


if __name__ == "__main__":
    unittest.main()
