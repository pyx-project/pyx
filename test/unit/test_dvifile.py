import sys
if sys.path[0] != "../..":
    sys.path.insert(0, "../..")

import cStringIO, os, re, unittest

from pyx import dvifile


class DvifileTestCase(unittest.TestCase):

    def testDvitype(self):
        usedvifile = "../../manual/manual.dvi"

        dvitypefile = os.popen("dvitype %s" % usedvifile)
        dvitypelines = dvitypefile.readlines()
        dvitypelineno = dvitypelines.index(" \n") + 1

        pyxdvifile = cStringIO.StringIO()
        df = dvifile.dvifile(usedvifile, dvifile.readfontmap(["psfonts.map"]),
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

            pyxdvifilelinere = pyxdvifileline.replace("+", "\\+").replace("(", "\\(").replace(")", "\\)").replace("???", "-?\\d+") + "$"
            if re.match(pyxdvifilelinere, dvitypeline):
                dvitypelineno += 1
                pyxdvifilelineno += 1
            else:
                raise ValueError("difference:\n%s|\n%s|" % (dvitypeline, pyxdvifileline))

        # don't be strict about empty tailing lines
        while dvitypelineno < len(dvitypelines) and not dvitypelines[dvitypelineno].strip():
            dvitypelineno += 1
        while pyxdvifilelineno < len(pyxdvifilelines) and not pyxdvifilelines[pyxdvifilelineno].strip():
            pyxdvifilelineno += 1

        assert dvitypelineno == len(dvitypelines)
        assert pyxdvifilelineno == len(pyxdvifilelines)


if __name__ == "__main__":
    unittest.main()
