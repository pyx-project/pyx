import sys
if sys.path[0] != "../..":
    sys.path.insert(0, "../..")

import unittest, warnings, os, logging

from testfixtures import log_capture

from pyx import text, unit

# text.set(texdebug="bla.tex", usefiles=["bla.log"])

class MessageParserTestCase(unittest.TestCase):

    @log_capture(level=logging.WARNING)
    def testBadTeX(self, l):
        text.text(0, 0, r"\some \badly \broken \TeX", texmessages=[text.texmessage.warn])
        l.check(("pyx", "WARNING", r"""ignoring TeX warnings:
  *
  *! Undefined control sequence.
  <argument> \some 
                   \badly \broken \TeX 
  <*> }{1}
          %
  ! Undefined control sequence.
  <argument> \some \badly 
                          \broken \TeX 
  <*> }{1}
          %
  ! Undefined control sequence.
  <argument> \some \badly \broken 
                                  \TeX 
  <*> }{1}
          %
  
  
  *"""))

    @log_capture(level=logging.WARNING)
    def testFontWarning(self, l):
        text.text(0, 0, r"\fontseries{invalid}\selectfont{}hello, world", texmessages=[text.texmessage.font_warning])
        text.default_runner.instance.do_finish()
        l.check(("pyx", "WARNING", r"""ignoring font substitutions of NFSS:
LaTeX Font Warning: Font shape `OT1/cmr/invalid/n' undefined
(Font)              using `OT1/cmr/m/n' instead on input line 0."""),
                ("pyx", "WARNING", r"""ignoring font substitutions of NFSS:
LaTeX Font Warning: Some font shapes were not available, defaults substituted."""))

    @log_capture(level=logging.WARNING)
    def testOverfullHboxWarning(self, l):
        text.text(0, 0, r"hello, world", textattrs=[text.parbox(30*unit.u_pt)])
        l.check(("pyx", "WARNING", r"""ignoring overfull/underfull box:
Overfull \hbox (8.22089pt too wide) detected at line 0
[]\OT1/cmr/m/n/10 hello,"""))

    @log_capture(level=logging.WARNING)
    def testUnderfullHboxWarning(self, l):
        text.text(0, 0, r"\hbadness=0hello, world, hello", textattrs=[text.parbox(2.5)])
        l.check(("pyx", "WARNING", r"""ignoring overfull/underfull box:
Underfull \hbox (badness 171) detected at line 0
[]\OT1/cmr/m/n/10 hello, world,"""))

    @log_capture(level=logging.WARNING)
    def testOverfullVboxWarning(self, l):
        text.text(0, 0, r"\parindent=0pt\vbox to 1cm {hello, world, hello, world, hello, world}", textattrs=[text.parbox(1.9)])
        l.check(("pyx", "WARNING", r"""ignoring overfull/underfull box:
Overfull \vbox (2.4917pt too high) detected at line 0"""))

    @log_capture(level=logging.WARNING)
    def testUnderfullVboxWarning(self, l):
        text.text(0, 0, r"\parindent=0pt\vbox to 1cm {hello, world, hello, world}", textattrs=[text.parbox(1.9)])
        l.check(("pyx", "WARNING", r"""ignoring overfull/underfull box:
Underfull \vbox (badness 10000) detected at line 0"""))

    def testLoadLongFileNames(self):
        testfilename = "x"*100
        with open(testfilename + ".tex", "w") as f:
            f.write("\message{ignore this}")
        text.text(0, 0, "\\input %s\n" % testfilename, texmessages=[text.texmessage.load])
        os.remove(testfilename + ".tex")
        with open(testfilename + ".eps", "w") as f:
            f.write("%%BoundingBox: 0 0 10 10")
        text.text(0, 0, r"\includegraphics{%s}" % testfilename)
        os.remove(testfilename + ".eps")

    def setUp(self):
        text.set(engine=text.LatexEngine)
        text.preamble(r"\usepackage{graphicx}")

if __name__ == "__main__":
    unittest.main()
